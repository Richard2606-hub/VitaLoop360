"""Deterministic three-way match module for Compliance & Order Hub (Track 5: Evolus)."""

PO_APPROVED_QTY = 12.0
PO_APPROVED_UNIT_PRICE = 180.0
PO_APPROVED_TOTAL = 2160.0


def compute_invoice_variance(qty, unit_price, service_qty, service_unit_price):
    goods_total = round(qty * unit_price, 2)
    service_total = round(service_qty * service_unit_price, 2)
    invoice_total = round(goods_total + service_total, 2)
    return {
        "goods_total": goods_total,
        "service_total": service_total,
        "invoice_total": invoice_total,
        "variance_eur": round(invoice_total - PO_APPROVED_TOTAL, 2),
    }
