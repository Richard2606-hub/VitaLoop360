# ThermoYield — Factory Sentinel Standalone Pack Proposal

- **Track**: Track 1 — Intelligent Industry
- **Pack ID**: `factory` (`v0.1.0`, Live in submission)
- **Primary User**: Line Shift Supervisor (Penang SMT-04) & Process Engineer
- **Operational Problem**: Shift-level energy excursions and calibration scrap spikes on SMT reflow lines are discovered weeks later in monthly finance variance reports rather than during the shift when containment is possible.
- **Deterministic Calculations**: `packs/factory/calc/formulas.py` & `backend/calculations.py` compute `energy_per_unit`, `scrap_rate`, `idle_share`, `reactive_ratio`, the composite **Energy & Scrap Waste Index**, robust MAD z-scores, and a seeded 64-tree Isolation Forest (`seed=360`).
- **Resident Model Stage**: `Gemma-4-31B-IT` on AMD Token Factory explains the flagged anomaly using only locked numeric facts and BM25-retrieved SOP passages (`SOP-017-v3.2-4.2`, `SOP-017-v3.2-4.3`, `SOP-024-v1.4-2.1`).
- **Verification & Human Gate**: 100% citation coverage floor; fabricated numbers (such as the planted 37% savings claim) are deterministically blocked. Holding a lot, approving profile verification, and releasing a lot require named human approvals recorded in the SHA-256 ledger.
