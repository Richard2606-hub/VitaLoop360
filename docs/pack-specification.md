# Capability Pack Contract, Installed Packs & 6th-Pack Extension Blueprints

VitaLoop 360 implements the complete **Proposal Section 7 & Appendix A** capability pack contract across all five lifecycle packs (`packs/{factory,order,demand,experience,care}`) and supports zero-core-edit discovery via `discover_pack_folders()` and restricted-namespace calculation loading (`_load_restricted_calc()`).

---

## 1. Appendix A Pack Folder Contract

Every installed pack in `packs/<pack_id>/` provides the following standardized structure:

| Artefact | Purpose | Installed Across All 5 Packs |
|---|---|---|
| `manifest.json` | Stable ID, name, version, track, standalone title, granted capabilities, published/subscribed events, approval roles, and entrypoints. | Yes (`packs/*/manifest.json`) |
| `calc/formulas.py` & `calc/FORMULAS.md` | Pure deterministic domain calculations executed in a restricted namespace (`math`, `statistics`, safe builtins) before any model call. | Yes (`packs/*/calc/`) |
| `rules/*.json` | Thresholds, pre-inference refusal patterns, red-flag escalation triggers, coverage floors, and PII redaction rules. | Yes (`packs/*/rules.json`) |
| `schemas/*.json` | Input, model-output, and event-payload JSON contracts. | Yes (`packs/*/schemas/`) |
| `prompts/*.txt` | Stage prompt templates populated strictly with locked calculation facts and retrieved source passages. | Yes (`packs/*/prompts/`) |
| `docs/*.md` | Versioned synthetic source documents with stable citation identifiers (`[SOP-017-v3.2-4.2]`, `[TERMS-008-v1.0-3]`, `[RETAIL-v1.0-1]`, `[BRAND-v1.0-2]`, `[IFU-v2.1-1]`). | Yes (`packs/*/docs/`) |
| `screens.json` | Declarative UI screen, evidence card, and approval gate definitions. | Yes (`packs/*/screens.json`) |
| `tests/readiness.json` | Happy-path and adversarial twin test cases executed by `python run.py --batch`. | Yes (`packs/*/readiness/cases.json`) |
| `PROPOSAL.md` | Standalone single-track technical proposal (`ThermoYield`, `ProcureGuard MCP`, `QuantPulse`, `PersonaStage`, `SafeBridge`). | Yes (`packs/*/PROPOSAL.md`) |

---

## 2. Installed Capability Packs (Tracks 1–5)

| Pack ID | Console Name | Standalone Track Proposal | Deterministic Math (`calc/formulas.py`) | Resident Model Role (`Gemma-4-31B-IT`) |
|---|---|---|---|---|
| `factory` | **Factory Sentinel** | **ThermoYield** (Track 1) | Energy intensity (`0.453 kWh/unit`), scrap (`4.09%`), **ESWI (`119.3`)**, Median+MAD ($z>3.5$), 64-tree Isolation Forest | Synthesizes shift excursion hypothesis grounded in `[SOP-017-v3.2-4.2]` |
| `order` | **Compliance & Order Hub** | **ProcureGuard MCP** (Track 2) | 3-way PO/GRN/Invoice match (`+€80.00` / `+3.70%` variance) & reserve stock check (`2610-05`) | Drafts multilingual (EN/IT/BM) exception & reallocation memo citing `[TERMS-008-v1.0-3]` |
| `demand` | **Demand & Retention Brain** | **QuantPulse** (Track 3) | Additive Holt–Winters ($\alpha=0.35,\beta=0.10,\gamma=0.25,m=7$), safety stock (`21.9`), ROP (`202`), Weibull survival churn $S(t)=\exp(-(t/\lambda)^k)$ | Summarizes non-LLM backtest (`MAE 0.612` vs `1.000`) & retention EV (`RM 14.40`) citing `[RETAIL-v1.0-1..2]` |
| `experience` | **Adaptive Unboxing Studio** | **PersonaStage** (Track 4) | Prohibited clinical/health claim regex gate (EN/BM/IT) & unit-cost calculator (`$0.00` template preview) | Drafts persona-adapted onboarding copy within `[BRAND-v1.0-2]` |
| `care` | **SafeCare Navigator** | **SafeBridge** (Track 5) | Pre-inference clinical boundary refuser, red-flag escalator, PII redactor, & dual-extractor agreement (`2/2`) | Summarizes lot-bound `IFU-v2.1` non-clinical setup steps (`[IFU-v2.1-1..4]`) |

---

## 3. Candidate 6th-Pack Extension Blueprints (Proposal Section 14)

Because the shared core discovers packs dynamically from `packs/*/manifest.json`, any of the six regional/domain extension packs defined in the proposal can be dropped into `packs/<id>/` without modifying core runtime logic:

| Candidate 6th Pack | Track Alignment | Target Domain & Deterministic Formula | Shared Thread Event Subscription |
|---|---|---|---|
| **WaferWise** | Track 1 · Semiconductor OSAT (Penang) | Die-bond thermal drift & wafer map yield excursion index | Subscribes to `anomaly.flagged`, emits `wafer.map.held` |
| **PalmTrace** | Track 2 · Agricommodity & EUDR Supply Chain | Mass-balance mill extraction ratio & geolocation polygon compliance check | Subscribes to `lot.held`, emits `traceability.exception` |
| **InvoisBridge** | Track 2 · LHDN MyInvois Cross-Border e-Invoicing | Peppol / UBL 2.1 tax-code & SST line-item reconciliation | Subscribes to `stock.reallocated`, emits `einvoice.validated` |
| **ProofLog** | Track 1/2 · Cold-Chain & ESG Carbon Ledger | Scope 2 grid-emission factor ($\text{kg CO}_2\text{e/unit}$) & cold-chain degree-hour integral | Subscribes to `lot.released`, emits `carbon.certificate.locked` |
| **LiveLore** | Track 4 · Multilingual Live-Commerce Companion | Real-time promo margin floor calculator & prohibited-claim filter (EN/BM/ZH) | Subscribes to `offer.proposed`, emits `livestream.script.approved` |
| **ReferralRelay** | Track 5 · Community Pharmacy & Clinic Hand-Off | Non-clinical triage SLA timer & anonymised clinic-slot matcher | Subscribes to `care.escalated`, emits `clinic.handoff.logged` |
