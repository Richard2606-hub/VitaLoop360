# SafeBridge — SafeCare Navigator Standalone Pack Proposal

- **Track**: Track 2 — Health and Wellbeing
- **Pack ID**: `care` (`v0.1.0`, Specified walkthrough)
- **Primary User**: Family Caregiver & Transitional-Care Nurse
- **Track 2 Mandatory Safety Rules**:
  1. **No autonomous diagnosis or treatment advice**: Deterministic multilingual (EN/BM/IT) deny-list (`care_guard`) refuses dosage, diagnosis, medication change, and clinical interpretation requests before any model call.
  2. **Sensitive information protection**: Deterministic PII redaction (`redact_pii`) scrubs names, emails, phone numbers, national IDs, and street addresses; raw caregiver check-in text is never persisted to the JSONL ledger.
  3. **Visible uncertainty**: Computes an explicit dual-extractor agreement indicator (`care_agreement`, `1.00` vs `0.50`) between independent lexical and structural classifiers, labelled as an agreement measure rather than a clinical probability.
  4. **High-risk escalation & human takeover**: Red-flag symptoms (`urgent`) and device/skin irritation (`review`, per `[IFU-v2.1-4]`) open a task in the Transitional-Care Nurse queue (`nurse_resolve`).
