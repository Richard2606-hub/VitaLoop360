# ProcureGuard MCP — Compliance & Order Hub Standalone Pack Proposal

- **Track**: Track 5 — Evolus Business Agents on AMD
- **Pack ID**: `order` (`v0.1.0`, Specified walkthrough; first post-event build)
- **Primary User**: Accounts-Payable & Order-Management Clerk (Milan / Penang)
- **Operational Problem**: When lot `2610-07` is held on the line, the back office must reconcile multilingual certificates (`CERT-2610-07`), purchase orders (`PO-2026-0842`), goods receipts (`GRN-2026-0218`), and supplier invoices (`INV-2026-0391`) across Italian, English, and Bahasa Melayu, while re-pointing affected pharmacy orders (`ORD-1041..1043`) to released reserve lot `2610-05`.
- **Evolus 5-Requirement Architecture**:
  1. Built inside an Evolus event workspace created with the event code.
  2. Main agent served on self-hosted `vLLM` on ROCm (`deploy/vllm-rocm-mi300x.yaml`) running `Gemma-4-31B-IT` on an AMD Developer Cloud MI300X instance.
  3. Uses Evolus Document Extractor + Evolus Knowledge Library (`TERMS-008-v1.0-3`) + Evolus Exception Workflow.
  4. Driven programmatically from VitaLoop via Evolus REST API and OpenAI-compatible endpoint.
  5. Containerised application (`Dockerfile`) with an MCP connector stub for ERP reallocation posting after human clerk sign-off.
