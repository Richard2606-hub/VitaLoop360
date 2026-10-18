# Factory calculation methodology

The calculation implementation is `backend/calculations.py`; authored inputs and reference baselines are in `backend/data.py`. All rows are synthetic. They cover 32 fifteen-minute windows and deliberately include an incident interval. These calculations demonstrate a workflow, not an industrial validation study.

Let `E` be total energy in kWh, `G` good units, `S` scrap units, `I` idle energy in kWh, and `R` reactive energy in kvarh, summed over the selected rows.

| Metric | Calculation | Interpretation |
| --- | --- | --- |
| Energy intensity | `E / G` | kWh per good unit. |
| Scrap rate | `100 × S / (G + S)` | Percentage of produced units classed as scrap. |
| Idle share | `100 × I / E` | Percentage of energy assigned to idle intervals in the synthetic input. |
| Reactive ratio | `R / E` | Diagnostic proxy; not a billed reactive-power penalty. |
| Waste index | `100 × (0.40 × energy_intensity / 0.42 + 0.35 × scrap_rate / 2.1 + 0.15 × idle_share / 12 + 0.10 × reactive_ratio / 0.12)` | Weighted ratio to authored baselines; `100` is the reference. Weights are design assumptions, not fitted or industry-standard coefficients. |
| Excess energy cost | `max(0, E − G × 0.42) × 0.48` | Counterfactual estimate in RM at an assumed RM0.48/kWh tariff. It is neither realized savings nor a current tariff claim. |

Energy and scrap deltas are the percentage change from their respective authored baseline values. Aggregated ratios are calculated from totals, not by averaging per-window percentages.

## Anomaly flags

The implementation evaluates two diagnostic scores:

1. Energy intensity's robust score is `0.6745 × abs(value − median) / max(MAD, 1e−9)`, where MAD is the median absolute deviation of the shift's intensities. A score greater than `3.5` triggers a flag.
2. A small dependency-free Isolation Forest uses four features: energy intensity, scrap fraction, idle fraction, and reactive ratio. It uses 64 randomly split trees, a fixed seed of `360`, and a maximum depth of `ceil(log2(number_of_rows))`. A score greater than `0.64` triggers a flag.

A window is flagged if either threshold is exceeded. The model is fit to the same synthetic shift shown in the demonstration. Scores are not probabilities of equipment failure; no separate training population, held-out benchmark, precision/recall study, or deployment calibration is supplied. A flat median distribution uses a small denominator floor, which can produce very large robust scores for small deviations.

## Evidence and verification

Factory passages are fictional procedures with stable IDs. Retrieval uses BM25-style lexical scoring within the requested pack and optional version filter. The verifier checks numeric membership in the computed fact set and resolvable citation coverage for every sentence. These are structural checks: they do not establish causal correctness, semantic entailment, or the correct association of a number with a particular unit or metric. The operator must review the proposed hypothesis against the evidence.

The application records approved local holds and corrective decisions. It does not change an oven profile, alter machinery, perform maintenance, or measure whether an intervention saved energy.
