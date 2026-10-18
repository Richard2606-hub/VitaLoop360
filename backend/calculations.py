"""Published deterministic Factory Sentinel calculations and seeded anomaly models."""
import math
import random
import statistics

from .data import BASELINE


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


FORMULAS = {
    "energy_per_unit": "sum(energy_kwh) / sum(good_units)",
    "scrap_rate": "100 × sum(scrap_units) / (sum(good_units) + sum(scrap_units))",
    "idle_share": "100 × sum(idle_energy_kwh) / sum(energy_kwh)",
    "reactive_ratio": "sum(reactive_kvarh) / sum(energy_kwh); diagnostic proxy, not a billed penalty",
    "waste_index": "100 × (0.40×energy/baseline + 0.35×scrap/baseline + 0.15×idle/baseline + 0.10×reactive/baseline); baseline = 100",
    "estimated_excess_cost": "max(0, energy_kwh − good_units × 0.42 kWh/unit) × RM0.48/kWh; counterfactual estimate, not realized savings",
    "anomaly_count": "Count windows where energy robust MAD z-score > 3.5 OR seeded Isolation Forest score > 0.64 (64 trees, seed 360)",
}
