"""Authored, fictional fixtures. These are not imported public or plant data."""
import math

LOT = "2610-07"
BASELINE = {"energy_per_unit": 0.42, "scrap_rate": 2.1, "idle_share": 12.0, "reactive_ratio": 0.12}
LOTS = [
    {"id": LOT, "product": "LumaBand Recovery Kit", "units": 1200, "status": "review", "line": "Penang · SMT-04", "destination": "Milan / Kuala Lumpur", "ifu": "2.1"},
    {"id": "2610-05", "product": "LumaBand Recovery Kit", "units": 840, "status": "released", "line": "Penang · SMT-02", "destination": "Reserve inventory", "ifu": "2.1"},
]
DOCUMENTS = [
    {"id": "SOP-017-v3.2-4.2", "pack": "factory", "title": "Reflow oven profile verification", "version": "3.2", "section": "4.2", "text": "SYNTHETIC PROCEDURE — fictional demonstration only. After heating-element replacement, a process engineer must verify the thermal profile against the approved recipe before the next production release. Record the profile and engineer sign-off. An energy anomaly is a hypothesis trigger, not proof of a faulty profile."},
    {"id": "SOP-017-v3.2-4.3", "pack": "factory", "title": "Containment and quality release", "version": "3.2", "section": "4.3", "text": "SYNTHETIC PROCEDURE — fictional demonstration only. The supervisor may place the affected lot on hold pending profile verification and calibration review. Only a named quality reviewer may release a held lot after corrective work and evidence are recorded. No machine parameter changes are made by VitaLoop."},
    {"id": "SOP-024-v1.4-2.1", "pack": "factory", "title": "Idle-load and compressed-air inspection", "version": "1.4", "section": "2.1", "text": "SYNTHETIC PROCEDURE — fictional demonstration only. Review idle-load intervals and inspect for air leaks, standby equipment and incomplete shutdown. A supervisor must approve the work order. Do not claim a confirmed root cause or realized savings before a measured follow-up."},
    {"id": "TERMS-008-v1.0-3", "pack": "order", "title": "Supplier service authorization", "version": "1.0", "section": "3", "text": "SYNTHETIC TERMS. Services not listed on the purchase order require written buyer approval before invoice payment. Disputed invoice lines are referred to the supplier; payment is never autonomous."},
    {"id": "BRAND-v1.0-2", "pack": "experience", "title": "Lumora style and claims guide", "version": "1.0", "section": "2", "text": "SYNTHETIC BRAND GUIDE. Use calm, practical language. Acknowledge replacement delays. Never promise healing, treatment or a clinical outcome. Include a link to the lot-matched instructions. A brand reviewer approves each experience."},
    {"id": "IFU-v2.1-1", "pack": "care", "title": "LumaBand kit instructions — sample", "version": "2.1", "section": "1", "text": "SYNTHETIC INSTRUCTIONS, not clinical guidance. For the fictional kit: confirm that the lot on the box matches the supplied instructions; keep the instruction leaflet and clinic contact information accessible. Follow the instructions supplied by your actual care team."},
    {"id": "IFU-v2.1-4", "pack": "care", "title": "When to contact the care team — sample", "version": "2.1", "section": "4", "text": "SYNTHETIC INSTRUCTIONS, not clinical guidance. In this fictional workflow, reported skin irritation, persistent discomfort or a damaged strap is routed for nurse review. This application cannot diagnose a symptom or decide treatment. No nurse or emergency service is contacted by this demonstration."},
]
PACKS = [
    {"id": "factory", "name": "Factory Sentinel", "status": "ready", "version": "0.1.0", "track": "Intelligent Industry", "subscriptions": [], "publishes": ["anomaly.flagged", "lot.held", "lot.released", "corrective.approved"], "capabilities": ["telemetry.read", "procedure.retrieve", "approval.request"]},
    {"id": "order", "name": "Compliance & Order Hub", "status": "walkthrough", "version": "0.1.0", "track": "Evolus Business Agents", "subscriptions": ["lot.held"], "publishes": ["order.exception", "stock.reallocated"], "capabilities": ["simulation"]},
    {"id": "demand", "name": "Demand & Retention Brain", "status": "walkthrough", "version": "0.1.0", "track": "Reinvent Commerce", "subscriptions": ["stock.reallocated"], "publishes": ["offer.proposed"], "capabilities": ["simulation"]},
    {"id": "experience", "name": "Adaptive Unboxing Studio", "status": "walkthrough", "version": "0.1.0", "track": "Create a New Kind of Experience", "subscriptions": ["offer.proposed"], "publishes": ["experience.generated"], "capabilities": ["simulation"]},
    {"id": "care", "name": "SafeCare Navigator", "status": "walkthrough", "version": "0.1.0", "track": "Health and Wellbeing", "subscriptions": ["experience.generated"], "publishes": ["instructions.bound", "care.escalated", "care.refused", "care.answered"], "capabilities": ["simulation"]},
]


def telemetry():
    """32 deterministic fifteen-minute windows; the incident begins at 02:15."""
    rows = []
    for i in range(32):
        good = 93 + (i * 7 % 17)
        incident = 9 <= i <= 17
        energy = good * (0.425 + 0.013 * math.sin(i * 1.3) + (0.205 if incident else 0.0))
        rows.append({"time": f"{i // 4:02d}:{(i % 4) * 15:02d}", "energy": round(energy, 2), "good_units": good, "scrap": (8 + i % 3) if incident else (2 + i % 2), "idle_energy": round(energy * (0.27 if incident else 0.115 + 0.01 * (i % 3)), 2), "reactive_kvarh": round(energy * (0.22 if incident else 0.115), 2)})
    return rows
