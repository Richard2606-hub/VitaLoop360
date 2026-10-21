"""Deterministic unit economics and style-bible quality gate calculations for Adaptive Unboxing Studio (Track 4)."""

MI300X_HOURLY_USD = 1.99


def compute_experience_unit_cost(prompt_tokens=0, completion_tokens=0, latency_ms=0, input_price_per_m=0.0, output_price_per_m=0.0):
    api_cost_usd = (prompt_tokens * input_price_per_m + completion_tokens * output_price_per_m) / 1_000_000.0
    gpu_time_cost_usd = (max(0, latency_ms) / 1000.0) * (MI300X_HOURLY_USD / 3600.0)
    return {
        "api_cost_usd": round(api_cost_usd, 6),
        "mi300x_gpu_time_cost_usd": round(gpu_time_cost_usd, 6),
        "mi300x_hourly_assumption_usd": MI300X_HOURLY_USD,
        "payer": "Brand Experience & Customer Retention Budget",
    }
