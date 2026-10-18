# Capability pack contract and roadmap

The local product demonstrates one shared console and factory calculation flow, with four labelled walkthroughs. The following contract captures the proposal's intended extension boundary. It is a design specification, not a claim that arbitrary third-party folders can already be installed safely.

## Intended pack contents

| Part | Required contents |
| --- | --- |
| Manifest | Stable ID, name, version, track, owner role, implementation status, granted capabilities, published/subscribed event types, and approval roles. |
| Calculations | Deterministic functions, units, input validation, documented formulas, and reproducible sample inputs. |
| Rules | Thresholds, refusal conditions, escalation roles, coverage floor, and redaction policy. |
| Schemas | Validated input, model-output, and event-payload contracts. |
| Prompts | Stage templates populated only with locked facts and retrieved sources. |
| Documents | Source owner, version, stable passage identifiers, explicit fictional/synthetic labels when appropriate, and lot-to-version binding. |
| Screens | Evidence, calculations, draft status, approval action, and implementation-status labels. |
| Readiness cases | Happy paths and adversarial cases for fabricated facts, unknown citations, unsafe requests, and unauthorized transitions. |

## Shared event vocabulary

Events should carry an event ID, timestamp, run/request IDs, lot, pack/version, payload, provenance, and approving person when relevant. Expected event types include `anomaly.flagged`, `lot.held`, `lot.released`, `stock.reallocated`, `order.exception`, `offer.proposed`, `experience.generated`, `instructions.bound`, and `care.escalated`.

A walkthrough event must retain a machine-readable and visible walkthrough marker. Publishing an event reports a fact; it must not authorize a different department to act. Each consequential transition needs the receiving department's own approval policy.

## Roadmap by pack

| Pack | Proposed behavior beyond the demonstration |
| --- | --- |
| Factory Sentinel | Licensed telemetry adapters, the complete specified waste index, robust MAD and Isolation Forest anomaly methods, operational SOP retrieval, validated fact locking, and verified AMD-hosted Gemma explanations. |
| Compliance and Order Hub | Evolus document extraction, knowledge library, exception workflow, ERP adapter, deterministic three-way match, multilingual evidence, and a main agent on a verified AMD vLLM deployment. |
| Demand and Retention Brain | Holt-Winters with seasonal-naive backtests, an explicit reorder-point formula, RFM, Weibull survival modeling, calibrated retention assumptions, and planner-approved commercial actions. |
| Adaptive Unboxing Studio | Context-sensitive story graph, versioned style bible, two audience paths, quality checks, ROCm image generation, and provider-measured session cost. |
| SafeCare Navigator | Reviewed lot-bound instructions, validated refusal/escalation rules, privacy controls, agreement-based uncertainty, a staffed nurse workflow, and comprehensive safety evaluation. |

## Installation acceptance

Before calling a future pack installable, validate its complete manifest and schemas; reject unknown capabilities; restrict document access to the pack's scope; enforce version binding; quarantine malformed packs with useful diagnostics; register subscriptions; run readiness cases; and ledger the installation. Importing Python in a reduced namespace does not by itself sandbox untrusted code. Execute only reviewed trusted pack code unless a separate isolation boundary is implemented.
