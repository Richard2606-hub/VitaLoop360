# Adaptive Unboxing Studio Calculation Formulas (`packs/experience/calc/`)

- **API Token Spend per Experience**:
  `C_api = (prompt_tokens * P_in + completion_tokens * P_out) / 1,000,000`
- **Self-Hosted AMD MI300X GPU-Time Equivalent Cost**:
  `C_gpu = (latency_ms / 1000) * ($1.99 / 3600)` (published AMD Developer Cloud single-MI300X reference rate)
- **Style-Bible Quality Gate (`BRAND-v1.0-2`)**:
  Deterministic phrase filter across English, Bahasa Melayu, and Italiano blocking any therapeutic, diagnostic, or clinical cure claim (`diagnos*`, `cure*`, `heal*`, `treat*`, `merawat`, `menyembuhkan`, `guarigione`, `clinically proven`).
- **Stated Payer**: Brand Experience & Customer Retention Budget (justifies retention spend against cohort LTV).
