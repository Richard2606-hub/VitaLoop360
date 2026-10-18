"""Single-process HTTP API and static console; binds to localhost by default."""
import json
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .runtime import ActionError


def make_handler(runtime, dist):
    root = Path(dist).resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "VitaLoop360/0.1"

        def _send(self, status, body, content_type="application/json; charset=utf-8", filename=None):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False).encode("utf-8")
            elif isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urllib.parse.urlsplit(self.path).path
            if path == "/api/state":
                return self._send(200, runtime.state())
            if path == "/api/ledger":
                if not runtime.ledger.verify():
                    return self._send(409, {"error": "Ledger integrity check failed."})
                return self._send(200, runtime.ledger.jsonl(), "application/x-ndjson; charset=utf-8", "vitaloop-audit.jsonl")
            if path == "/api/health":
                valid = runtime.ledger.verify()
                return self._send(200 if valid else 503, {"status": "ready" if valid else "integrity_failed", "ledger_valid": valid, "mode": runtime.state()["mode"]})
            if path.startswith("/api/"):
                return self._send(404, {"error": "API route not found."})
            relative = urllib.parse.unquote(path).lstrip("/") or "index.html"
            target = (root / relative).resolve()
            if root not in target.parents:
                return self._send(403, {"error": "Forbidden path."})
            if not target.is_file():
                return self._send(404, {"error": "File not found."})
            mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if mime.startswith("text/") or mime in {"application/javascript", "application/json"}:
                mime += "; charset=utf-8"
            self._send(200, target.read_bytes(), mime)

        def do_POST(self):
            path = urllib.parse.urlsplit(self.path).path
            if path != "/api/action":
                return self._send(404, {"error": "API route not found."})
            origin = self.headers.get("Origin")
            if origin:
                parsed = urllib.parse.urlsplit(origin)
                if parsed.scheme not in {"http", "https"} or parsed.netloc != self.headers.get("Host"):
                    return self._send(403, {"error": "Cross-origin writes are not allowed."})
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                return self._send(415, {"error": "Content-Type must be application/json."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 65536:
                    return self._send(413, {"error": "JSON body must be between 1 and 65536 bytes."})
                payload = json.loads(self.rfile.read(length))
                return self._send(200, runtime.action(payload))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._send(400, {"error": "Malformed JSON body."})
            except ActionError as exc:
                return self._send(exc.status, {"error": str(exc)})
            except ValueError as exc:
                return self._send(400, {"error": str(exc)})
            except Exception:
                return self._send(500, {"error": "The action could not be completed; inspect the local service."})

    return Handler


def serve(runtime, dist, host="127.0.0.1", port=8765):
    server = ThreadingHTTPServer((host, port), make_handler(runtime, dist))
    print(f"VitaLoop 360 is ready at http://{host}:{server.server_port}", flush=True)
    print("Fictional scenario. Four packs are simulated walkthroughs. Ctrl+C stops the local service.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
