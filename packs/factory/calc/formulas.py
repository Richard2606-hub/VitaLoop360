"""Deterministic calculation module for Factory Sentinel (Track 1: Intelligent Industry)."""

BASELINE_ENERGY_PER_UNIT = 0.42
BASELINE_SCRAP_RATE = 2.1
BASELINE_IDLE_SHARE = 12.0
BASELINE_REACTIVE_RATIO = 0.12
TARIFF_MYR_PER_KWH = 0.48


def compute_waste_index(energy_per_unit, scrap_rate, idle_share, reactive_ratio):
    """Weighted Energy and Scrap Waste Index (baseline = 100.0)."""
    return round(
        100.0
        * (
            0.40 * (energy_per_unit / BASELINE_ENERGY_PER_UNIT)
            + 0.35 * (scrap_rate / BASELINE_SCRAP_RATE)
            + 0.15 * (idle_share / BASELINE_IDLE_SHARE)
            + 0.10 * (reactive_ratio / BASELINE_REACTIVE_RATIO)
        ),
        1,
    )
