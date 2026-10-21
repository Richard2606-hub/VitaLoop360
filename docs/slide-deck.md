# VitaLoop 360 — 8-Slide Submission Deck

---

## Slide 1 — Title & Vision
- **VitaLoop 360**: Verifiable Product-Operations Intelligence Platform
- **Tagline**: *One Lot. Five Teams. Every Number Locked to Deterministic Math.*
- **Resident AI Stack**: Google **Gemma-4-31B-IT** (`gemma-3-27b-it` compatible) on **AMD Token Factory (Radeon Cloud)** & **AMD Instinct MI300X (ROCm vLLM)**
- **Scenario**: Lumora Wellness — tracing Production Lot `2610-07` from Penang SMT-04 to clinics and homes in Kuala Lumpur and Milan.

---

## Slide 2 — The Problem: Disconnected Operations & Unverified AI
- **Operational Silos**: When a manufacturing excursion occurs, Quality, Procurement, Demand Planning, Brand Onboarding, and Care Support act on fragmented state.
- **The LLM Reliability Gap**: Standard generative AI hallucinates savings percentages, invents SOP citations, leaks customer PII into logs, or crosses clinical advice boundaries.
- **Our Principle**: *Deterministic math computes the numbers; Gemma on AMD synthesizes the cited narrative; an adversarial twin verifier and human approval gate every consequential action.*

---

## Slide 3 — Shared Core Architecture (6 Verifiable Services)
1. **AMD / Gemma Model Gateway (`backend/gateway.py`)**: OpenAI-compatible client for AMD Token Factory (`https://developer.amd.com.cn/radeon/api/v1`) and ROCm vLLM on MI300X, tracking latency (last/median/p95), token usage, and `$1.99/hr` MI300X GPU-time unit economics.
2. **Restricted-Namespace Calculation Engine (`backend/analytics.py`, `packs/*/calc/formulas.py`)**: Executes all domain formulas deterministically before model prompting.
3. **Hybrid BM25 + 3-Gram Cosine Retrieval (`backend/retrieval.py`)**: Version- and lot-filtered passage retrieval across EN, BM, and IT documents.
4. **Fact-and-Citation Verifier (`backend/verifier.py`)**: Rejects any draft whose numbers deviate from locked facts ($>0.5\%$ tolerance) or whose `[DOC-ID]` citations do not resolve.
5. **Pre-Inference Safety Guard & PII Redactor (`backend/guard.py`)**: Refuses medication/diagnosis queries before model invocation, escalates red-flag symptoms, and scrubs PII.
6. **SHA-256 Hash-Chained Audit Ledger (`backend/ledger.py`)**: Append-only JSONL ledger with 5 materialised views (`cost`, `verification`, `guard`, `approvals`, `lot`).

---

## Slide 4 — Packs 1 & 2: Factory Sentinel & Compliance Order Hub
- **Pack 1 — Factory Sentinel (`ThermoYield`, Track 1)**:
  - Computes `0.453 kWh/unit` (`+7.9%`), `4.09%` scrap (`+63.6%`), and **ESWI = 119.3** across 32 shift windows using Median+MAD ($z > 3.5$) and a seeded 64-tree Isolation Forest ($\text{score} > 0.64$).
  - Adversarial twin rejects planted `37%` savings and fake `[SOP-999-v1.0]` citations.
- **Pack 2 — Compliance & Order Hub (`ProcureGuard MCP`, Track 2)**:
  - Normalizes multilingual Italian/Malay/English PO, Invoice, and GRN documents.
  - Catches the unlisted `+€80.00` (`+3.70%`) calibration service under `[TERMS-008-v1.0-3]` and reallocates 100 units (`ORD-1041..1043`) from held Lot `2610-07` to released Lot `2610-05`.

---

## Slide 5 — Packs 3, 4 & 5: Demand Brain, Unboxing Studio & SafeCare Navigator
- **Pack 3 — Demand & Retention Brain (`QuantPulse`, Track 3)**:
  - Non-LLM **Holt–Winters** forecasting ($\alpha=0.35, \beta=0.10, \gamma=0.25, m=7$) beating seasonal naive on 14-day backtest (`MAE 0.612` vs. `1.000`), paired with **Weibull survival churn** ($S(7\text{d})=74.95\%, P(\text{churn})=34.04\%$) and `RM 14.40` net EV per customer.
- **Pack 4 — Adaptive Unboxing Studio (`PersonaStage`, Track 4)**:
  - Audience- and language-adaptive (EN / BM / IT) onboarding at `$0.00` template preview cost, guarded by `[BRAND-v1.0-2]` health-claim blocker.
- **Pack 5 — SafeCare Navigator (`SafeBridge`, Track 5)**:
  - Lot-bound `IFU-v2.1` guidance, pre-inference clinical boundary refusal, PII redaction, and dual-extractor agreement (`2/2 extractors agree`).

---

## Slide 6 — Google Gemma on AMD Hardware & Cloud Integration
- **Live Cloud Inference**: Integrated with **AMD Token Factory (Radeon Cloud)** running **`Gemma-4-31B-IT`** (`1,003` tokens, `11.3s` measured round-trip, `100%` citation & numeric lock pass).
- **Self-Hosted ROCm vLLM Path**: Ready-to-run `deploy/vllm-rocm-mi300x.yaml` targeting a single **AMD Instinct MI300X (192 GB HBM3)** container (`rocm/vllm:latest`), holding the full BF16 model plus multi-pack KV cache on one GPU.
- **Graceful Resilience**: Seamless fallback across live AMD endpoint, recorded reference ledger replay (`--replay`), and browser-native Web Crypto offline mode.

---

## Slide 7 — Quantitative Evaluation & 18-Case Readiness Suite
- **18 / 18 Automated Readiness & Adversarial Twin Cases Passed (`100.0%`)** via `python run.py --batch`.
- **0.0% Unsupported Claim Escape Rate**: Every planted numeric fabrication (`37%` saving), fake citation (`[SOP-999-v1.0]`), and mismatched lot ID (`9999-88`) is blocked.
- **100.0% Three-Way Match, Brand Guardrail, and Clinical Boundary Accuracy** across English, Bahasa Melayu, and Italian test inputs.
- **100.0% SHA-256 Ledger Integrity**: Every mutating action and verification event is cryptographically chained and verifiable via CLI or browser.

---

## Slide 8 — Extensibility (6th Pack Drop-In) & Open-Source Deliverables
- **Zero-Core-Edit Plugin Architecture**: Adding a 6th pack (`packs/<name>/manifest.json`, `calc/formulas.py`, `prompts/`, `rules/`, `tests/readiness.json`) auto-registers on boot (`discover_pack_folders()`).
- **Documented 6th-Pack Blueprints**: `WaferWise`, `PalmTrace`, `InvoisBridge`, `ProofLog`, `LiveLore`, and `ReferralRelay` (`docs/pack-specification.md`).
- **Complete Repository**: Zero-dependency Python stdlib backend + ES-module frontend, 13 unit/integration test suites (`tests/test_core.py`), browser-domain verification (`tests/test_demo.mjs`), and live Vercel deployment.
