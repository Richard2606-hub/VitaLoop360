"""Published deterministic Factory Sentinel, Demand & Retention, and Three-Way Match calculations."""
import math
import random
import statistics

from .data import BASELINE, CUSTOMER_COHORTS, HISTORICAL_DEMAND


def isolation_scores(values, seed=360, trees=64):
    """Small, dependency-free Isolation Forest (random feature/threshold splits).

    Fits to the supplied synthetic shift, not an industrial training dataset.
    Scores are diagnostic outlier scores, never probabilities of equipment failure.
    """
    rng = random.Random(seed)
    n = len(values)
    if n < 3:
        return [0.0] * n
    height = math.ceil(math.log2(n))

    def c(size):
        if size <= 1:
            return 0.0
        if size == 2:
            return 1.0
        return 2 * (math.log(size - 1) + 0.5772156649) - 2 * (size - 1) / size

    def build(rows, depth):
        eligible = [k for k in range(len(values[0])) if min(row[k] for row in rows) < max(row[k] for row in rows)]
        if len(rows) <= 1 or depth >= height or not eligible:
            return len(rows)
        feature = rng.choice(eligible)
        cut = rng.uniform(min(row[feature] for row in rows), max(row[feature] for row in rows))
        return (feature, cut, build([r for r in rows if r[feature] < cut], depth + 1), build([r for r in rows if r[feature] >= cut], depth + 1))

    def path(row, node, depth=0):
        if isinstance(node, int):
            return depth + c(node)
        feature, cut, left, right = node
        return path(row, left if row[feature] < cut else right, depth + 1)

    forest = [build(values, 0) for _ in range(trees)]
    return [round(2 ** (-(sum(path(row, tree) for tree in forest) / trees) / c(n)), 4) for row in values]


def calculate(rows, tariff=0.48):
    if not rows:
        raise ValueError("Telemetry must contain at least one window.")
    for row in rows:
        for name in ("energy", "good_units", "scrap", "idle_energy", "reactive_kvarh"):
            value = row.get(name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid telemetry field: {name}")
        if row["good_units"] == 0 or row["energy"] == 0 or row["idle_energy"] > row["energy"]:
            raise ValueError("Each window requires positive good units and energy; idle energy cannot exceed total energy.")
    energy = sum(r["energy"] for r in rows)
    good = sum(r["good_units"] for r in rows)
    scrap = sum(r["scrap"] for r in rows)
    per_unit = energy / good
    scrap_rate = scrap / (good + scrap) * 100
    idle_share = sum(r["idle_energy"] for r in rows) / energy * 100
    reactive = sum(r["reactive_kvarh"] for r in rows) / energy
    # 100 is baseline. 40% energy, 35% scrap, 15% idle, 10% reactive.
    waste = 100 * (0.40 * per_unit / BASELINE["energy_per_unit"] + 0.35 * scrap_rate / BASELINE["scrap_rate"] + 0.15 * idle_share / BASELINE["idle_share"] + 0.10 * reactive / BASELINE["reactive_ratio"])
    features = [[r["energy"] / r["good_units"], r["scrap"] / (r["good_units"] + r["scrap"]), r["idle_energy"] / r["energy"], r["reactive_kvarh"] / r["energy"]] for r in rows]
    median = statistics.median(row[0] for row in features)
    mad = statistics.median(abs(row[0] - median) for row in features)
    scores = isolation_scores(features)
    decorated = []
    for row, feature, isolation in zip(rows, features, scores):
        robust = 0.6745 * abs(feature[0] - median) / max(mad, 1e-9)
        decorated.append({**row, "energy_per_unit": round(feature[0], 4), "scrap_rate": round(feature[1] * 100, 2), "robust_z": round(robust, 2), "isolation_score": isolation, "anomaly": robust > 3.5 or isolation > 0.64})
    metrics = {"energy_per_unit": round(per_unit, 3), "scrap_rate": round(scrap_rate, 2), "idle_share": round(idle_share, 2), "reactive_ratio": round(reactive, 3), "waste_index": round(waste, 1), "energy_delta": round((per_unit / BASELINE["energy_per_unit"] - 1) * 100, 1), "scrap_delta": round((scrap_rate / BASELINE["scrap_rate"] - 1) * 100, 1), "good_units": good, "scrap_units": scrap, "energy_kwh": round(energy, 2), "estimated_excess_cost": round(max(0, energy - good * BASELINE["energy_per_unit"]) * tariff, 2), "tariff": tariff, "anomaly_count": sum(row["anomaly"] for row in decorated)}
    return metrics, decorated


def holt_winters_forecast(series=None, alpha=0.35, beta=0.10, gamma=0.25, season_length=7, horizon=7):
    """Additive Holt-Winters triple exponential smoothing with Seasonal Naive backtest."""
    y = [float(v) for v in (HISTORICAL_DEMAND if series is None else series)]
    m = int(season_length)
    if len(y) < 2 * m or m < 2:
        raise ValueError("Holt-Winters requires at least two full seasonal cycles.")
    if any(not math.isfinite(v) or v < 0 for v in y):
        raise ValueError("Demand series must contain finite nonnegative values.")
    first_mean = sum(y[:m]) / m
    second_mean = sum(y[m : 2 * m]) / m
    level = first_mean
    trend = (second_mean - first_mean) / m
    seasonals = [y[i] - first_mean for i in range(m)]

    hw_fitted = []
    naive_fitted = []
    actuals = []
    for t in range(len(y)):
        s_prev = seasonals[t % m]
        pred = max(0.0, level + trend + s_prev)
        if t >= m:
            hw_fitted.append(round(pred, 2))
            naive_fitted.append(round(y[t - m], 2))
            actuals.append(y[t])
        prev_level = level
        level = alpha * (y[t] - s_prev) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        seasonals[t % m] = gamma * (y[t] - level) + (1 - gamma) * s_prev

    def error_metrics(preds, trues):
        n = len(trues)
        mae = sum(abs(p - a) for p, a in zip(preds, trues)) / n
        rmse = math.sqrt(sum((p - a) ** 2 for p, a in zip(preds, trues)) / n)
        mape = sum(abs(p - a) / max(a, 1e-6) for p, a in zip(preds, trues)) / n * 100
        return {"mae": round(mae, 3), "rmse": round(rmse, 3), "mape_pct": round(mape, 2)}

    hw_metrics = error_metrics(hw_fitted, actuals)
    naive_metrics = error_metrics(naive_fitted, actuals)
    forecast = [
        round(max(0.0, level + (h + 1) * trend + seasonals[(len(y) + h) % m]), 2)
        for h in range(horizon)
    ]
    return {
        "method": "Additive Holt-Winters Triple Exponential Smoothing",
        "parameters": {"alpha": alpha, "beta": beta, "gamma": gamma, "season_length": m, "horizon": horizon},
        "historical": y,
        "forecast": forecast,
        "forecast_total": round(sum(forecast), 1),
        "forecast_daily_mean": round(sum(forecast) / max(1, len(forecast)), 2),
        "level": round(level, 3),
        "trend": round(trend, 3),
        "seasonals": [round(s, 3) for s in seasonals],
        "backtest": {
            "evaluation_days": len(actuals),
            "holt_winters": hw_metrics,
            "seasonal_naive": naive_metrics,
            "beats_baseline": hw_metrics["mae"] <= naive_metrics["mae"],
        },
    }


def weibull_survival_churn(delay_days=7, scale_lambda=14.0, shape_k=1.8, base_churn=0.12):
    """Deterministic Weibull survival S(t) = exp(-(t/lambda)^k) and delay-adjusted churn risk."""
    if delay_days < 0 or scale_lambda <= 0 or shape_k <= 0 or not (0 <= base_churn <= 1):
        raise ValueError("Invalid Weibull survival parameters.")
    survival = math.exp(-((delay_days / scale_lambda) ** shape_k)) if delay_days > 0 else 1.0
    churn_prob = min(0.95, base_churn + (1.0 - survival) * (1.0 - base_churn))
    curve = []
    for day in range(0, 15, 2):
        s_d = math.exp(-((day / scale_lambda) ** shape_k)) if day > 0 else 1.0
        c_d = min(0.95, base_churn + (1.0 - s_d) * (1.0 - base_churn))
        curve.append({"delay_days": day, "survival": round(s_d, 4), "churn_probability": round(c_d, 4)})
    return {
        "model": "Weibull Survival Hazard Model",
        "formula": "S(t) = exp(-(t / λ)^k); P(churn|t) = base + (1 - S(t)) × (1 - base)",
        "parameters": {"scale_lambda": scale_lambda, "shape_k": shape_k, "base_churn": base_churn, "delay_days": delay_days},
        "survival_probability": round(survival, 4),
        "churn_probability": round(churn_prob, 4),
        "curve": curve,
    }


def demand_and_retention_analytics(assumptions=None):
    """Complete Track 3 deterministic calculation bundle: Holt-Winters, ROP, RFM, and Weibull EV."""
    defaults = {"mean": 18.0, "std": 4.2, "lead": 10, "z": 1.65, "churn": 0.35, "ltv": 420.0, "uplift": 0.2, "offerCost": 15.0}
    if assumptions:
        defaults.update(assumptions)
    safety = defaults["z"] * defaults["std"] * math.sqrt(defaults["lead"])
    rop = math.ceil(defaults["mean"] * defaults["lead"] + safety)
    ev = defaults["churn"] * defaults["ltv"] * defaults["uplift"] - defaults["offerCost"]
    hw = holt_winters_forecast()
    weibull = weibull_survival_churn(delay_days=7)
    cohorts = []
    for c in CUSTOMER_COHORTS:
        w = weibull_survival_churn(delay_days=c["delay_days"])
        cohort_ev = round(w["churn_probability"] * c["monetary_rm"] * defaults["uplift"] - defaults["offerCost"], 2)
        cohorts.append({**c, "survival_prob": w["survival_probability"], "weibull_churn": w["churn_probability"], "expected_net_value_rm": cohort_ev})
    return {
        "safety_stock": round(safety, 2),
        "reorder_point": rop,
        "expected_value_per_customer": round(ev, 2),
        "expected_value_cohort_total": round(ev * 24, 2),
        "holt_winters": hw,
        "weibull": weibull,
        "rfm_cohorts": cohorts,
    }


def three_way_match_calc(invoice, tolerance=1.0, po_qty=12, po_price=180.0):
    """Deterministic three-way match between PO, Goods Receipt, and Supplier Invoice."""
    q = float(invoice.get("quantity", 12))
    p = float(invoice.get("unitPrice", 180.0))
    received = float(invoice.get("receivedQuantity", 12))
    sq = float(invoice.get("serviceQuantity", 1))
    sp = float(invoice.get("serviceUnitPrice", 80.0))
    po_total = round(po_qty * po_price, 2)
    element_total = round(q * p, 2)
    service_total = round(sq * sp, 2)
    invoice_total = round(element_total + service_total, 2)
    variance = round(invoice_total - po_total, 2)
    unauthorized_service = sq > 0
    qty_mismatch = (q != po_qty) or (received != po_qty) or (q != received)
    price_mismatch = abs(p - po_price) > (po_price * tolerance / 100.0 + 1e-6)
    matched = not (unauthorized_service or qty_mismatch or price_mismatch)
    reasons = []
    if unauthorized_service:
        reasons.append("unlisted_service_line")
    if qty_mismatch:
        reasons.append("quantity_mismatch")
    if price_mismatch:
        reasons.append("unit_price_variance")
    return {
        "matched": matched,
        "po_total": po_total,
        "element_total": element_total,
        "service_total": service_total,
        "invoice_total": invoice_total,
        "variance": variance,
        "variance_pct": round((variance / po_total) * 100, 2) if po_total else 0.0,
        "tolerance_pct": tolerance,
        "reasons": reasons,
        "citation": "TERMS-008-v1.0-3",
    }


FORMULAS = {
    "energy_per_unit": "sum(energy_kwh) / sum(good_units)",
    "scrap_rate": "100 × sum(scrap_units) / (sum(good_units) + sum(scrap_units))",
    "idle_share": "100 × sum(idle_energy_kwh) / sum(energy_kwh)",
    "reactive_ratio": "sum(reactive_kvarh) / sum(energy_kwh); diagnostic proxy, not a billed penalty",
    "waste_index": "100 × (0.40×energy/baseline + 0.35×scrap/baseline + 0.15×idle/baseline + 0.10×reactive/baseline); baseline = 100",
    "estimated_excess_cost": "max(0, energy_kwh − good_units × 0.42 kWh/unit) × RM0.48/kWh; counterfactual estimate, not realized savings",
    "anomaly_count": "Count windows where energy robust MAD z-score > 3.5 OR seeded Isolation Forest score > 0.64 (64 trees, seed 360)",
    "reorder_point": "ceil(mean_daily_demand × lead_time + z × std_daily_demand × sqrt(lead_time))",
    "holt_winters": "L_t = α(y_t − S_{t−m}) + (1−α)(L_{t−1} + T_{t−1}); T_t = β(L_t − L_{t−1}) + (1−β)T_{t−1}; S_t = γ(y_t − L_t) + (1−γ)S_{t−m}",
    "weibull_survival": "S(t) = exp(−(t / λ)^k); P(churn | delay=t) = base_churn + (1 − S(t)) × (1 − base_churn)",
    "retention_ev": "P(churn) × LTV × relative_uplift − offer_cost",
}
