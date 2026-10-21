"""Deterministic forecasting, safety stock, and Weibull survival churn module for Demand & Retention Brain (Track 3)."""
import math


def compute_safety_stock_and_rop(mean_daily, std_daily, lead_days, z_score):
    safety = z_score * std_daily * math.sqrt(lead_days)
    rop = math.ceil(mean_daily * lead_days + safety)
    return {"safety_stock": round(safety, 2), "reorder_point": rop}


def compute_weibull_churn(delay_days, scale_lambda=14.0, shape_k=1.6):
    survival = math.exp(-((max(0.0, delay_days) / scale_lambda) ** shape_k))
    return {"survival_probability": round(survival, 4), "churn_probability": round(1.0 - survival, 4)}
