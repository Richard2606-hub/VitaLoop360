# Architectural Lineage & Code Reuse Disclosure

**Project:** VitaLoop 360 — Verifiable Product-Operations Intelligence Platform  
**Hackathon:** AMD Open Innovation AI Hackathon (Upgraded Submission)  
**Target Stack:** Google Gemma (`Gemma-4-31B-IT` / `gemma-3-27b-it`) on AMD Token Factory & AMD Instinct MI300X (ROCm vLLM)

---

## 1. Summary of Disclosure

In accordance with the hackathon's transparency and code-reuse rules (Proposal Section 15 & Appendix E), this document explicitly separates **architectural inspiration from prior systems** from **100% newly written code, synthetic data, and tests created specifically for VitaLoop 360**.

**Zero source files, datasets, models, or UI components were copied from any prior project.** Every file in this repository (`backend/`, `dist/`, `packs/`, `api/`, `tests/`, `docs/`, `data/`) was written from scratch for VitaLoop 360.

---

## 2. Prior Architectural Inspiration vs. New Implementation

| Prior System (Conceptual Inspiration Only) | Concept Adapted | Newly Written VitaLoop 360 Implementation |
|---|---|---|
| **RouteWiser** | Multi-factor operational anomaly scoring and threshold gating | Newly authored `backend/analytics.py` (`analyze_shift`), Energy & Scrap Waste Index (ESWI), Median + MAD robust z-score, and pure-Python seeded 64-tree Isolation Forest (`packs/factory/calc/formulas.py`). |
| **FourCast** | Non-LLM deterministic time-series backtesting paired with survival-hazard cohort analysis | Newly authored `backend/demand_analytics.py` and `packs/demand/calc/formulas.py` implementing additive Holt–Winters forecasting ($\alpha=0.35, \beta=0.10, \gamma=0.25, m=7$), 14-day held-out backtesting vs. 7-day seasonal naive baseline, RFM scoring, and Weibull survival churn $S(t)=\exp(-(t/\lambda)^k)$. |
| **GuildHouse** | Manifest-driven plugin discovery and hash-linked audit trails | Newly authored `backend/data.py` (`discover_pack_folders`, `_load_restricted_calc`), `backend/ledger.py` (append-only JSONL SHA-256 hash chain + 5 materialised views), and `packs/*/manifest.json` across 5 lifecycle capability packs. |

---

## 3. Newly Created Artefacts in This Repository

1. **Shared Verifiable Core (`backend/` & `api/`)**:
   - `backend/runtime.py`: Orchestration across all 5 capability packs, digital thread (`lot_id`), human-in-the-loop approval state machine, and 18-case readiness runner.
   - `backend/gateway.py`: OpenAI-compatible HTTP client for AMD Token Factory (`https://developer.amd.com.cn/radeon/api/v1`) and self-hosted ROCm vLLM endpoints with `Gemma-4-31B-IT`, sliding-window rate limiting, retry backoff, latency percentiles (median/p95), and AMD MI300X (`$1.99/hr`) GPU-time cost accounting.
   - `backend/verifier.py`: Deterministic fact-and-citation verifier (numeric tolerance lock, `[DOC-ID]` resolution, and locked identifier verification).
   - `backend/guard.py`: Pre-inference clinical boundary refuser, red-flag symptom escalator, PII redactor (names, phone numbers, emails, NRIC/IDs), and dual-extractor agreement indicator.
   - `backend/retrieval.py`: Hybrid BM25 ($\text{k1}=1.5, b=0.75$) + character 3-gram cosine retrieval with metadata filtering (`pack`, `version`, `lot_id`).
2. **Five Capability Packs (`packs/{factory,order,demand,experience,care}`)**:
   - `manifest.json`, `screens.json`, `PROPOSAL.md`, `prompts/*.md`, `rules/*.json`, `calc/formulas.py`, `calc/FORMULAS.md`, `data/*`, `docs/*.md`, and `tests/readiness.json`.
3. **Interactive Console (`dist/`)**:
   - Zero-framework ES-module browser console (`dist/index.html`, `dist/app.js`, `dist/packs.js`, `dist/demo.js`, `dist/styles.css`) with dual-mode execution (live Python/Vercel API + browser-native Web Crypto SHA-256 offline mode).
4. **Synthetic Reference Scenario (`Lumora Wellness`)**:
   - Authored 100% synthetic telemetry, lots (`2610-07`, `2610-05`, `2610-08`), multilingual procurement documents (EN/IT/BM), retail demand history, brand style bible, and version-locked non-clinical device instructions (`IFU-v2.1`).
