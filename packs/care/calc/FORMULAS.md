# SafeCare Navigator Calculation Formulas (`packs/care/calc/`)

- **Dual-Extractor Agreement Indicator**:
  `A(x) = 1.0` if Lexical Rule Extractor $E_1(x)$ and Structural Cue Extractor $E_2(x)$ produce the identical triage class (`refused`, `urgent`, `review`, `routine`); `0.5` on any divergence (which automatically routes to `review` for nurse takeover). Explicitly labelled as an agreement indicator, never a clinical probability.
- **Deterministic PII Redaction Count**:
  `R_total = count(EMAIL) + count(PHONE) + count(ID) + count(ADDRESS) + count(PERSON)` scrubbed prior to guard evaluation or ledger persistence.
