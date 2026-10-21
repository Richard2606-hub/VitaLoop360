# Factory Sentinel Calculation Formulas (`packs/factory/calc/`)

- **Energy per good unit**: `E_unit = sum(energy_kwh) / sum(good_units)` (baseline `0.420 kWh/unit`)
- **Scrap rate (%)**: `S_rate = 100 * sum(scrap) / sum(good_units + scrap)` (baseline `2.10%`)
- **Idle-load share (%)**: `I_share = 100 * sum(idle_energy) / sum(energy_kwh)` (baseline `12.00%`)
- **Reactive-power proxy**: `R_ratio = sum(reactive_kvarh) / sum(energy_kwh)` (baseline `0.120`)
- **Energy & Scrap Waste Index**:
  `W = 100 * (0.40*(E_unit/0.42) + 0.35*(S_rate/2.1) + 0.15*(I_share/12.0) + 0.10*(R_ratio/0.12))`
- **Robust MAD z-score**: `z = 0.6745 * |x - median(x)| / MAD(x)` (flagged if `z > 3.5`)
- **Seeded Isolation Forest**: `64` random binary trees, subsample `32`, seed `360` (flagged if score `> 0.64`)
- **Counterfactual excess energy cost**: `max(0, energy_kwh - good_units * 0.42) * RM 0.48/kWh`
