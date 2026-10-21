# Compliance & Order Hub Calculation Formulas (`packs/order/calc/`)

- **Approved PO baseline (`PO-2026-0842`)**: `12 × €180.00 = €2,160.00`
- **Billed invoice total (`INV-2026-0391`)**: `qty * unit_price + service_qty * service_unit_price`
- **Price tolerance check**: `|unit_price - 180.00| / 180.00 * 100 <= tolerance_pct` (`0%` to `5%`)
- **Unlisted service rule (`TERMS-008-v1.0-3`)**: `service_qty == 0` required unless written buyer authorization exists
- **Reserve lot reallocation (`2610-05`)**: `ORD-1041 (40) + ORD-1042 (35) + ORD-1043 (25) = 100 units <= 840 reserve units`
