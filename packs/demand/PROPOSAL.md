# QuantPulse — Demand & Retention Brain Standalone Pack Proposal

- **Track**: Track 3 — Reinvent Commerce
- **Pack ID**: `demand` (`v0.1.0`, Specified walkthrough)
- **Primary User**: Demand Planner & Customer-Retention Lead
- **Operational Problem**: Allocating 100 reserve units from `2610-05` after the hold on `2610-07` lowers available buffer inventory in Kuala Lumpur and delays replacement shipments by 7 days, raising customer churn risk.
- **Track 3 Compliance (No LLM Forecasting)**:
  - Demand is forecast strictly by additive Holt-Winters exponential smoothing ($\alpha=0.35, \beta=0.10, \gamma=0.25, m=7$) with a held-out MAE/RMSE/MAPE backtest against a 7-day Seasonal Naive baseline (`MAE 0.612 vs 1.000`).
  - Reorder point is computed via $\text{ROP} = \lceil \mu_d L + z \sigma_d \sqrt{L} \rceil$.
  - Churn hazard is scored via a Weibull survival model $S(t) = \exp(-(t/\lambda)^k)$ across RFM cohorts (`COH-KL-REPL`, `COH-MI-REPL`, `COH-KL-FIRST`).
  - `Gemma-4-31B-IT` is used strictly to explain the locked statistical outputs and draft the human-approved apology offer and purchase-order note.
