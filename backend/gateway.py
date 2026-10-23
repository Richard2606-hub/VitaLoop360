"""Server-only OpenAI-compatible gateway; no unverified inference claims."""
import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque

DEFAULT_TOKEN_FACTORY_URL = "https://developer.amd.com.cn/radeon/api/v1"
DEFAULT_TOKEN_FACTORY_MODEL = "Gemma-4-31B-IT"


class GatewayError(RuntimeError):
    pass


class Gateway:
    def __init__(self, env=None, on_call=None):
        env = os.environ if env is None else env
        self.api_key = env.get("VITALOOP_API_KEY", "").strip()
        self.base_url = env.get("VITALOOP_BASE_URL", "").strip().rstrip("/") or (DEFAULT_TOKEN_FACTORY_URL if self.api_key else "")
        self.model = env.get("VITALOOP_MODEL", "").strip() or (DEFAULT_TOKEN_FACTORY_MODEL if self.api_key else "")
        self.provider = env.get("VITALOOP_PROVIDER", "AMD Token Factory (Radeon Cloud)" if self.api_key else "Configured OpenAI-compatible endpoint")
        self.timeout = min(30, max(1, float(env.get("VITALOOP_TIMEOUT_SECONDS", "25"))))
        self.input_price = self._price(env.get("VITALOOP_INPUT_PRICE_PER_MILLION"))
        self.output_price = self._price(env.get("VITALOOP_OUTPUT_PRICE_PER_MILLION"))
        self.mi300x_hourly_usd = float(env.get("VITALOOP_MI300X_HOURLY_USD", "1.99"))
        self.semaphore = threading.BoundedSemaphore(6)
        self.lock = threading.RLock()
        self.starts = deque()
        self.cache = {}
        self.calls = self.tokens = self.input_tokens = self.output_tokens = 0
        self.cost = 0.0
        self.latency_ms = 0
        self.latencies = []
        self.successful = False
        self.usage_complete = True
        self.last_error = None
        self.on_call = on_call
        parsed = urllib.parse.urlsplit(self.base_url)
        self.configured = bool(self.model and self.base_url and parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password)
        self.endpoint = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", "")) if self.configured else "Not configured"

    @staticmethod
    def _price(value):
        if value in (None, ""):
            return None
        parsed = float(value)
        if parsed < 0 or not __import__("math").isfinite(parsed):
            raise ValueError("Model prices must be finite and nonnegative.")
        return parsed

    @staticmethod
    def _parse_json_content(raw_content):
        cleaned = re.sub(r"<think>.*?</think>", "", str(raw_content or ""), flags=re.DOTALL).strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL).strip()
        if not cleaned.startswith("{") and "{" in cleaned and "}" in cleaned:
            cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
        return json.loads(cleaned)

    def reset_stats(self):
        with self.lock:
            self.calls = self.tokens = self.input_tokens = self.output_tokens = 0
            self.cost = 0.0
            self.latency_ms = 0
            self.latencies = []
            self.successful = False
            self.usage_complete = True
            self.last_error = None
            self.cache.clear()
            self.starts.clear()

    def status(self):
        with self.lock:
            now = time.monotonic()
            while self.starts and self.starts[0] < now - 60:
                self.starts.popleft()
            calls_last_min = len(self.starts)
            sorted_lat = sorted(self.latencies)
            p50 = sorted_lat[len(sorted_lat) // 2] if sorted_lat else self.latency_ms
            p95 = sorted_lat[min(len(sorted_lat) - 1, int(round(0.95 * (len(sorted_lat) - 1))))] if sorted_lat else self.latency_ms
            total_lat_s = sum(sorted_lat) / 1000.0 if sorted_lat else (self.latency_ms / 1000.0)
            mi300x_gpu_cost = round(total_lat_s * (self.mi300x_hourly_usd / 3600.0), 6) if self.calls > 0 else 0.0
        return {
            "configured": self.configured,
            "provider": self.provider if self.configured else "Deterministic synthetic demo",
            "model": self.model if self.configured else "No model connected",
            "endpoint": self.endpoint,
            "calls": self.calls,
            "calls_last_minute": calls_last_min,
            "rate_limit_rpm": 20,
            "concurrency_ceiling": 6,
            "tokens": self.tokens if self.usage_complete else None,
            "input_tokens": self.input_tokens if self.usage_complete else None,
            "output_tokens": self.output_tokens if self.usage_complete else None,
            "cost": round(self.cost, 8) if self.usage_complete and self.input_price is not None and self.output_price is not None else None,
            "mi300x_gpu_time_cost_usd": mi300x_gpu_cost,
            "mi300x_hourly_rate_usd": self.mi300x_hourly_usd,
            "latency_ms": self.latency_ms,
            "median_latency_ms": p50,
            "p95_latency_ms": p95,
            "successful": self.successful,
            "pricing_configured": self.input_price is not None and self.output_price is not None,
            "usage_available": self.usage_complete,
            "hardware_verified": False,
            "last_error": self.last_error,
            "note": "Hardware/provider names are operator configuration; the app cannot attest which GPU serves an endpoint.",
        }

    def complete(self, messages, bypass_cache=False):
        if not self.configured:
            raise GatewayError("No model endpoint and model are configured. Deterministic demo remains available.")
        body = {"model": self.model, "messages": messages, "temperature": 0, "max_tokens": 550, "response_format": {"type": "json_object"}}
        key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        with self.lock:
            if key in self.cache and not bypass_cache:
                return self.cache[key]
        with self.semaphore:
            for attempt in range(3):
                with self.lock:
                    now = time.monotonic()
                    while self.starts and self.starts[0] < now - 60:
                        self.starts.popleft()
                    if len(self.starts) >= 20:
                        raise GatewayError("Local rate limit reached (20 calls/minute); retry in a minute.")
                    self.starts.append(now)
                started = time.perf_counter()
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "VitaLoop360/1.0 (OpenAI-Compatible; Python)",
                }
                if self.api_key:
                    headers["Authorization"] = "Bearer " + self.api_key
                url = self.base_url if self.base_url.endswith("/chat/completions") else self.base_url + "/chat/completions"
                request = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        raw = response.read(2_000_001)
                    if len(raw) > 2_000_000:
                        raise GatewayError("Model response exceeded the response-size limit.")
                    payload = json.loads(raw)
                    measured_ms = round((time.perf_counter() - started) * 1000)
                    elapsed = int(payload["latency_ms"]) if isinstance(payload.get("latency_ms"), (int, float)) and measured_ms < 5 else measured_ms
                    usage = payload.get("usage") or {}
                    prompt_tokens, completion_tokens = usage.get("prompt_tokens"), usage.get("completion_tokens")
                    metered = all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (prompt_tokens, completion_tokens))
                    with self.lock:
                        self.calls += 1
                        self.latency_ms = elapsed
                        self.latencies.append(elapsed)
                        self.successful = True
                        self.last_error = None
                        self.usage_complete = self.usage_complete and metered
                        if metered:
                            self.input_tokens += prompt_tokens
                            self.output_tokens += completion_tokens
                            self.tokens += prompt_tokens + completion_tokens
                            if self.input_price is not None and self.output_price is not None:
                                self.cost += (prompt_tokens * self.input_price + completion_tokens * self.output_price) / 1_000_000
                    if self.on_call:
                        self.on_call({"endpoint": self.endpoint, "model": payload.get("model", self.model), "latency_ms": elapsed, "prompt_tokens": prompt_tokens if metered else None, "completion_tokens": completion_tokens if metered else None, "usage_available": metered, "input_price_per_million": self.input_price, "output_price_per_million": self.output_price})
                    content = payload["choices"][0]["message"]["content"]
                    parsed = self._parse_json_content(content)
                    if not isinstance(parsed, dict) or not isinstance(parsed.get("text"), str) or not parsed["text"].strip() or len(parsed["text"]) > 10000:
                        raise GatewayError('Model schema rejected: expected {"text": "nonempty cited explanation"}.')
                    self.cache[key] = parsed["text"]
                    return parsed["text"]
                except urllib.error.HTTPError as exc:
                    self.last_error = f"Provider returned HTTP {exc.code}."
                    if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                        raise GatewayError(self.last_error) from None
                except (TimeoutError, OSError) as exc:
                    self.last_error = "Model connection failed or timed out."
                    if attempt == 2:
                        raise GatewayError(self.last_error) from None
                except (ValueError, KeyError, IndexError, TypeError) as exc:
                    self.last_error = "Provider response failed the structured-output schema."
                    raise GatewayError(self.last_error) from None
                if attempt < 2:
                    time.sleep(0.5 * 2 ** attempt)
        raise GatewayError("Model call failed.")
