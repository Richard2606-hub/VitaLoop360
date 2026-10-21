# Appendix E — Hackathon Submission Package Copy

Use the fields below directly when completing the hackathon submission form.

---

## 1. Basic Project Metadata

- **Project Title**: `VitaLoop 360`
- **One-Line Tagline (119 chars)**:
  `Verifiable product-operations intelligence on Google Gemma & AMD across factory, orders, demand, onboarding & care.`
- **Primary Track & Multi-Track Coverage**:
  - **Shared Platform**: VitaLoop 360 (All 5 Capability Packs connected by `lot_id = 2610-07`)
  - **Track 1 (Smart Manufacturing)**: Pack 1 — *Factory Sentinel* (`ThermoYield`)
  - **Track 2 (Agentic Supply Chain & Finance)**: Pack 2 — *Compliance & Order Hub* (`ProcureGuard MCP`)
  - **Track 3 (Predictive Retail & Demand)**: Pack 3 — *Demand & Retention Brain* (`QuantPulse`)
  - **Track 4 (Creative & Brand Experience)**: Pack 4 — *Adaptive Unboxing Studio* (`PersonaStage`)
  - **Track 5 (Healthcare & Safe Care Navigation)**: Pack 5 — *SafeCare Navigator* (`SafeBridge`)
- **Repository URL**: `https://github.com/Richard2606-hub/VitaLoop360`
- **Cover Image**: [`dist/cover.svg`](../dist/cover.svg)
- **Slide Deck**: [`docs/slide-deck.md`](slide-deck.md)
- **Video Script**: [`docs/video-script.md`](video-script.md)
- **Architectural & Code-Reuse Disclosure**: [`DISCLOSURE.md`](../DISCLOSURE.md)

---

## 2. Short Description (Paste-Ready)

**VitaLoop 360** is a verifiable product-operations intelligence platform powered by **Google Gemma (`Gemma-4-31B-IT`) on AMD Token Factory (Radeon Cloud) and AMD Instinct MI300X (ROCm vLLM)**. When an excursion occurs on a manufacturing line (`Lot 2610-07`), VitaLoop 360 connects five operational capability packs—**Factory Sentinel**, **Compliance & Order Hub**, **Demand & Retention Brain**, **Adaptive Unboxing Studio**, and **SafeCare Navigator**—through a single SHA-256 hash-chained digital thread. Every numeric metric (ESWI waste index, 3-way match variance, Holt–Winters forecast, Weibull survival churn, and reorder points) is computed deterministically in Python before Gemma drafts cited operational guidance, while an adversarial twin verifier, pre-inference clinical/brand guardrails, and named human approval gates prevent hallucinations, PII leaks, and unsafe actions.

---

## 3. Google Partner Prize Statement (How Google Gemma Is Used)

VitaLoop 360 uses **Google Gemma (`Gemma-4-31B-IT` / `gemma-3-27b-it`)** as its resident open-weights reasoning and multilingual synthesis engine across all five capability packs:
1. **Factory Sentinel**: Synthesizes shift anomaly hypotheses grounded in locked telemetry calculations (`0.453 kWh/unit`, `4.09%` scrap, `ESWI 119.3`) and retrieved SOP passages (`[SOP-017-v3.2-4.2]`).
2. **Compliance & Order Hub**: Drafts cross-border procurement exception memos across Italian, Bahasa Melayu, and English source documents (`[TERMS-008-v1.0-3]`).
3. **Demand & Retention Brain**: Translates non-LLM Holt–Winters forecast backtests and Weibull survival churn parameters into auditable replenishment and retention briefs (`[RETAIL-v1.0-1]`, `[RETAIL-v1.0-2]`).
4. **Adaptive Unboxing Studio**: Adapts persona-specific onboarding guidance within strict `[BRAND-v1.0-2]` non-medical phrasing boundaries.
5. **SafeCare Navigator**: Summarizes version-bound `IFU-v2.1` caregiver checklists after pre-inference clinical boundary and PII redaction guards pass.

Every Gemma completion is verified against locked calculation facts and retrieved citation IDs before reaching the operator.

---

## 4. AMD Partner Prize Statement (How AMD Hardware & Software Are Used)

VitaLoop 360 is architected specifically for **AMD AI infrastructure**:
1. **AMD Token Factory (Radeon Cloud)**: Configured out of the box (`https://developer.amd.com.cn/radeon/api/v1`) to run live `Gemma-4-31B-IT` inference via [`backend/gateway.py`](../backend/gateway.py) and serverless [`api/index.py`](../api/index.py).
2. **AMD Instinct MI300X (192 GB HBM3) + ROCm vLLM**: Includes a production Docker Compose deployment ([`deploy/vllm-rocm-mi300x.yaml`](../deploy/vllm-rocm-mi300x.yaml)) using `rocm/vllm:latest` in `BF16` (`--max-model-len 16384`, `--gpu-memory-utilization 0.90`). A single MI300X holds the entire 31B/27B Gemma model in HBM3 with over 120 GB of headroom for low-latency KV caching across all five operational packs.
3. **Transparent AMD Telemetry & Unit Economics**: A persistent telemetry strip on every screen reports live endpoint status, `Gemma-4-31B-IT` model ID, last/median/p95 latency, sliding-window RPM, token usage, and GPU-time cost benchmarked against the published AMD Developer Cloud single-MI300X rate (`$1.99/hr`).
