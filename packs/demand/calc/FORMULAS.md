# Demand & Retention Brain Calculation Formulas (`packs/demand/calc/`)

- **Additive Holt-Winters Triple Exponential Smoothing** ($\alpha=0.35, \beta=0.10, \gamma=0.25, m=7$):
  - Level: $\ell_t = \alpha(y_t - s_{t-m}) + (1-\alpha)(\ell_{t-1} + b_{t-1})$
  - Trend: $b_t = \beta(\ell_t - \ell_{t-1}) + (1-\beta)b_{t-1}$
  - Seasonal: $s_t = \gamma(y_t - \ell_{t-1} - b_{t-1}) + (1-\gamma)s_{t-m}$
  - Forecast: $\hat{y}_{t+h} = \ell_t + h b_t + s_{t-m+((h-1)\bmod m)+1}$
- **Safety Stock & Reorder Point**:
  - $\text{SS} = z \cdot \sigma_d \cdot \sqrt{L}$
  - $\text{ROP} = \lceil \mu_d \cdot L + \text{SS} \rceil$
- **Weibull Survival Churn Model**:
  - $S(t) = \exp(-(t/\lambda)^k)$, $P(\text{churn} \mid t) = 1 - S(t)$ ($\lambda=14.0, k=1.6$)
- **Retention Offer Expected Net Value**:
  - $\text{EV} = P(\text{churn}) \cdot \text{LTV} \cdot \text{uplift} - C_{\text{offer}}$
