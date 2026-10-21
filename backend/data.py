"""Authored, fictional fixtures, configuration loader, and pack-folder discovery."""
import hashlib
import json
import math
from pathlib import Path

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
    {"id": "RETAIL-v1.0-1", "pack": "demand", "title": "Reorder and safety-stock policy", "version": "1.0", "section": "1", "text": "SYNTHETIC DEMAND POLICY. Regional pharmacy hubs maintain a 95% service-level target over a 10-day replenishment lead time. Forecasts are computed by additive Holt-Winters smoothing backtested against a seasonal naive baseline, never by a language model."},
    {"id": "RETAIL-v1.0-2", "pack": "demand", "title": "Replacement delay retention policy", "version": "1.0", "section": "2", "text": "SYNTHETIC RETENTION POLICY. Customers delayed by 7 or more days enter the high-priority retention cohort. Retention offers require positive expected net value and explicit human planner approval."},
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

ORDER_DOCUMENTS = [
    {
        "id": "CERT-2610-07",
        "kind": "Quality Certificate",
        "language": "English / Bahasa Melayu",
        "lot": "2610-07",
        "issuer": "Penang QA Lab · SMT-04",
        "status": "Hold pending thermal-profile sign-off",
        "excerpt_en": "Batch 2610-07 (1,200 units) flagged for reflow profile verification after heating-element HE-004 replacement [SOP-017-v3.2-4.2].",
        "excerpt_local": "Lot 2610-07 ditahan sementara menunggu pengesahan profil terma ketuhar aliran semula selepas penggantian elemen pemanas HE-004.",
    },
    {
        "id": "PO-2026-0842",
        "kind": "Purchase Order",
        "language": "Italiano / English",
        "supplier": "Nova Components S.r.l. · Milano",
        "currency": "EUR",
        "approved_total": 2160.00,
        "lines": [{"sku": "HE-004", "description": "Elemento riscaldante / Reflow Heating Element", "qty": 12, "unit_price": 180.00, "total": 2160.00}],
        "excerpt_en": "Approved purchase order for 12 × HE-004 heating elements at €180.00/unit (€2,160.00 total). No field calibration service ordered.",
        "excerpt_local": "Ordine d'acquisto approvato per 12 × elementi riscaldanti HE-004 a €180,00/unità (totale €2.160,00). Nessun servizio di calibrazione incluso.",
    },
    {
        "id": "INV-2026-0391",
        "kind": "Supplier Invoice",
        "language": "Italiano / English",
        "supplier": "Nova Components S.r.l. · Milano",
        "currency": "EUR",
        "billed_total": 2240.00,
        "lines": [
            {"sku": "HE-004", "description": "Elemento riscaldante / Reflow Heating Element", "qty": 12, "unit_price": 180.00, "total": 2160.00},
            {"sku": "SVC-CAL", "description": "Servizio di calibrazione / Unlisted Calibration Service", "qty": 1, "unit_price": 80.00, "total": 80.00},
        ],
        "excerpt_en": "Bills 12 × HE-004 (€2,160.00) plus 1 × unlisted calibration service (€80.00). Triggers clause [TERMS-008-v1.0-3].",
        "excerpt_local": "Fattura per 12 × HE-004 (€2.160,00) più 1 × servizio di calibrazione non autorizzato (€80,00).",
    },
    {
        "id": "GRN-2026-0218",
        "kind": "Goods Receipt Note",
        "language": "Bahasa Melayu / English",
        "location": "Penang Receiving Dock · SMT-04",
        "received_qty": 12,
        "service_received_qty": 0,
        "excerpt_en": "Physical receipt confirmed for 12 × HE-004 units. Zero external service receipts logged.",
        "excerpt_local": "Penerimaan fizikal disahkan untuk 12 unit HE-004. Tiada rekod penerimaan perkhidmatan luar.",
    },
]

# 21-day synthetic daily demand with 7-day weekly seasonality (for Holt-Winters vs Seasonal Naive backtest)
HISTORICAL_DEMAND = [
    15, 17, 20, 21, 19, 17, 15,
    14, 16, 19, 21, 18, 17, 15,
    16, 18, 21, 22, 19, 18, 16,
]

CUSTOMER_COHORTS = [
    {"id": "COH-KL-REPL", "name": "Delayed replacement customers (Kuala Lumpur)", "customers": 24, "recency_days": 9, "frequency": 2.4, "monetary_rm": 420.0, "delay_days": 7, "rfm_score": "4-4-5", "segment": "High-Value At-Risk"},
    {"id": "COH-MI-REPL", "name": "Clinic follow-up kit orders (Milan)", "customers": 18, "recency_days": 14, "frequency": 3.1, "monetary_rm": 510.0, "delay_days": 4, "rfm_score": "4-5-5", "segment": "Loyal Repeat"},
    {"id": "COH-KL-FIRST", "name": "First-time pharmacy buyers (Kuala Lumpur)", "customers": 62, "recency_days": 22, "frequency": 1.0, "monetary_rm": 260.0, "delay_days": 0, "rfm_score": "3-1-3", "segment": "Standard Onboarding"},
]

STYLE_BIBLE = {
    "version": "1.0",
    "document_id": "BRAND-v1.0-2",
    "voice": "Calm, practical, transparent, non-clinical",
    "palette": ["#d9e7de", "#31554b", "#f3ede2", "#c8b2a0"],
    "audiences": ["caregiver", "active"],
    "languages": ["en", "ms", "it"],
    "branches": ["quick", "detailed"],
    "payer": "Brand Experience & Customer Retention Budget",
    "unit_economics_note": "Deterministic template studio: $0.00 API spend in offline mode; metered per token when connected to an OpenAI-compatible endpoint.",
}


def telemetry():
    """32 deterministic fifteen-minute windows; the incident begins at 02:15."""
    rows = []
    for i in range(32):
        good = 93 + (i * 7 % 17)
        incident = 9 <= i <= 17
        energy = good * (0.425 + 0.013 * math.sin(i * 1.3) + (0.205 if incident else 0.0))
        rows.append({
            "time": f"{i // 4:02d}:{(i % 4) * 15:02d}",
            "energy": round(energy, 2),
            "good_units": good,
            "scrap": (8 + i % 3) if incident else (2 + i % 2),
            "idle_energy": round(energy * (0.27 if incident else 0.115 + 0.01 * (i % 3)), 2),
            "reactive_kvarh": round(energy * (0.22 if incident else 0.115), 2),
        })
    return rows


def load_config(config_path=None):
    """Read config.json and return (config_dict, sha256_config_hash)."""
    if config_path is None:
        config_path = Path(__file__).resolve().parents[1] / "config.json"
    else:
        config_path = Path(config_path)
    if config_path.is_file():
        raw = config_path.read_text(encoding="utf-8")
        cfg = json.loads(raw)
    else:
        cfg = {"runtime": {"mode": "serve"}, "gateway": {"mi300x_hourly_rate_usd": 1.99}}
    canonical = json.dumps(cfg, sort_keys=True, separators=(",", ":"))
    return cfg, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_restricted_calc(calc_file):
    """Load a pack's deterministic calculation module in a restricted namespace (Proposal §7)."""
    if not calc_file.is_file():
        return []
    allowed_modules = {"math": math}
    def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name in allowed_modules:
            return allowed_modules[name]
        raise ImportError(f"Pack calc module {calc_file.name} imports disallowed module: {name}")
    safe_builtins = {
        "__import__": _safe_import,
        "round": round, "min": min, "max": max, "sum": sum, "abs": abs, "len": len,
        "float": float, "int": int, "bool": bool, "str": str, "dict": dict, "list": list,
        "set": set, "tuple": tuple, "enumerate": enumerate, "range": range, "zip": zip,
        "sorted": sorted, "any": any, "all": all,
    }
    namespace = {"__builtins__": safe_builtins, "math": math}
    source = calc_file.read_text(encoding="utf-8")
    compile(source, str(calc_file), "exec")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") and stripped != "import math":
            raise ValueError(f"Pack calc module {calc_file.name} imports disallowed module: {stripped}")
    exec(source, namespace)  # noqa: S102 - trusted pack calc module in restricted namespace
    return sorted(k for k, v in namespace.items() if callable(v) and not k.startswith("_"))


def discover_pack_folders(packs_root=None):
    """Inspect installable pack folders under packs/ and return validated metadata."""
    if packs_root is None:
        packs_root = Path(__file__).resolve().parents[1] / "packs"
    else:
        packs_root = Path(packs_root)
    if not packs_root.exists():
        return []
    order = {"factory": 0, "order": 1, "demand": 2, "experience": 3, "care": 4}
    discovered = []
    for folder in sorted(packs_root.iterdir(), key=lambda p: (order.get(p.name, 99), p.name)):
        if not folder.is_dir():
            continue
        manifest_path = folder / "manifest.json"
        if not manifest_path.exists():
            discovered.append({"id": folder.name, "name": folder.name, "status": "quarantined", "reason": "Missing manifest.json in pack folder."})
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            rules_path = folder / "rules.json"
            screens_path = folder / "screens.json"
            proposal_path = folder / "PROPOSAL.md"
            calc_path = folder / "calc" / "formulas.py"
            calc_doc_path = folder / "calc" / "FORMULAS.md"
            readiness_path = folder / "readiness" / "cases.json"
            schemas_dir = folder / "schemas"
            prompts_dir = folder / "prompts"
            docs_dir = folder / "docs"
            manifest["folder"] = str(folder.name)
            manifest["has_rules"] = rules_path.is_file()
            manifest["has_readiness"] = readiness_path.is_file()
            manifest["has_calc"] = calc_path.is_file() and calc_doc_path.is_file()
            manifest["has_calc_formulas"] = manifest["has_calc"]
            manifest["has_screens"] = screens_path.is_file()
            manifest["has_proposal"] = proposal_path.is_file()
            calc_fns = _load_restricted_calc(calc_path)
            manifest["calc_functions"] = calc_fns
            manifest["calc_exports"] = calc_fns
            manifest["schemas"] = sorted(p.name for p in schemas_dir.glob("*.json")) if schemas_dir.is_dir() else []
            manifest["prompts"] = sorted(p.name for p in prompts_dir.glob("*.txt")) if prompts_dir.is_dir() else []
            manifest["doc_files"] = sorted(p.name for p in docs_dir.glob("*.md")) if docs_dir.is_dir() else []
            if screens_path.is_file():
                manifest["screens"] = json.loads(screens_path.read_text(encoding="utf-8"))
            if readiness_path.is_file():
                cases_payload = json.loads(readiness_path.read_text(encoding="utf-8"))
                manifest["readiness_cases"] = cases_payload.get("cases", [])
            if rules_path.is_file():
                manifest["rules"] = json.loads(rules_path.read_text(encoding="utf-8"))
            discovered.append(manifest)
        except (OSError, ValueError, TypeError, SyntaxError) as exc:
            discovered.append({"id": folder.name, "name": folder.name, "status": "quarantined", "reason": f"Malformed pack folder artefact: {exc}"})
    return discovered
