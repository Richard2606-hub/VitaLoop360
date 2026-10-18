# Proposal requirements and implementation scope

Source: the supplied `01_VitaLoop360_Proposal.docx` and its extracted text. This document compares product behavior with that proposal; it does not validate the proposal's external event, legal, pricing, or platform claims.

**Implemented** means a local code path exists. **Partial** means a bounded subset or demonstration exists. **External/unverified** requires infrastructure, data, access, or evidence not supplied. **Roadmap** is not implemented as the proposal's complete feature.

| Proposal requirement | Status in this build | Evidence and remaining work |
| --- | --- | --- |
| One shared console and lot identity | Implemented locally | Python runtime serves the browser console and reconstructs lot events. The synthetic incident flow is specifically lot `2610-07`; `2610-05` is illustrative reserve stock. This is not a general MES/ERP adapter. |
| Factory energy/scrap metrics and waste index | Implemented on synthetic input | `backend/calculations.py` computes energy intensity, scrap, idle share, reactive ratio, weighted waste index, and estimated excess energy cost. See [factory methodology](factory-methodology.md). No licensed public or plant dataset is incorporated. |
| Robust MAD and Isolation Forest anomaly flags | Implemented as diagnostic demonstration | Robust energy score plus a small seeded, dependency-free Isolation Forest over the sample shift. No independent benchmark or industrial calibration is supplied. |
| Model gateway with interchangeable compatible endpoints | Partial | Server-side chat-completions request, environment configuration, bounded concurrency, local rate limit, retries, timeout, response checks, and request cache. Actual endpoint compatibility must be tested with operator credentials. |
| Gemma running on AMD, including self-hosted ROCm/vLLM | External/unverified | The gateway can target a compatible deployment. No AMD key, verified deployment, model availability confirmation, or real AMD run was supplied. A configured provider name cannot attest hardware. |
| Locked facts and source verification | Partial | Numeric membership, resolvable citations, sentence coverage, and a planted fabricated-number challenge exist. They do not validate semantic entailment, every identifier, metric/unit association, or causal correctness. |
| Scoped lexical evidence retrieval | Implemented locally | BM25-style passage scoring filters by pack and optional version. Sources are an authored in-memory fixture catalog, not a document ingestion pipeline or production approved document repository. |
| One directed regeneration then refusal | Implemented factory path | The runtime retries a model draft with named findings and withholds a repeated failure. No configured live endpoint was exercised by the offline build checks. |
| Human approval before consequences | Partial | Named actor and evidence notes gate local hold, release, corrective work, and downstream approvals. Release requires corrective approval after the latest hold. Names are user-supplied, without authentication or role enforcement. No external consequences occur. |
| SHA-256 audit ledger and persistence | Implemented locally | JSONL records chain to the previous digest; invalid on-disk chains block appends. There is no independent signature, trusted checkpoint, or guarantee against complete rewriting/truncation. |
| Shared event thread | Partial | Manifest-declared event types, subscriber metadata, local lot history, and downstream approval projections exist. This is not a durable distributed broker or fully general subscriber execution engine. |
| Installable packs and quarantine | Partial | Static manifests receive required-field, duplicate-ID, and list-shape checks with quarantine markers. Folder discovery, complete schema/capability validation, module isolation, and independent pack installation remain roadmap work. |
| Cost and inference telemetry | Partial | Configured-model responses can supply token usage and measured request latency; prices are operator assumptions. No provider-independent GPU attestation or GPU-time meter is included. The offline demo makes no inference call. |
| Privacy redaction and sensitive-data policy | Partial | The factory model prompt uses fictional fixture facts/passages; care question text is not stored or sent to a model. Presidio, general PII redaction, authenticated access, and production retention controls are not implemented. |
| Compliance and Order Hub | Walkthrough | Approval-gated fictional invoice exception and stock allocation. No Evolus workspace, extraction service, ERP write, payment, or supplier contact. |
| Demand and Retention Brain | Walkthrough | Planning and offer examples with local approval. No trained Holt-Winters forecast, seasonal backtest, RFM pipeline, Weibull model, purchase order, or sent offer. |
| Adaptive Unboxing Studio | Walkthrough | Two authored contexts and local review flow. No generated imagery, ROCm image pipeline, model judge, or measured generated-experience economics. |
| SafeCare Navigator | Walkthrough | Fictional versioned instructions and deterministic refusal/review examples; a simulated task is visible. No diagnosis, clinical approval, independent extraction agreement, translation model, staffed nurse integration, or actual contact. |
| Serve, recorded replay, and input-directory batch modes | Partial | Local serving and export of a fresh synthetic snapshot exist. A synthetic snapshot is not a recorded AMD run. The proposal's complete replay/batch separation remains roadmap work. |
| Public submission and portfolio | External/unverified | Local source and documentation are provided. Actual event submission, public repository, video, slides, external URL validation, and six separately released repositories are separate deliverables. |

## Validation boundary

The automated test command and manual acceptance checklist are in the [README](../README.md). Test execution verifies only the code paths and fixtures covered. A successful local run does not establish hackathon eligibility, regulatory compliance, clinical suitability, industrial effectiveness, or compatibility with an untested external endpoint.

Before a later release changes a walkthrough badge to a live capability, implement and test that pack's complete rules and integrations, update [data provenance](data-provenance.md), and retain real run evidence. This follows the proposal's explicit priority: a completed hero flow with honestly labelled downstream scope.
