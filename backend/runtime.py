"""Shared core, manifest-validated subscriptions, approvals and lot projections."""
import copy
import json
import math
import re
import threading

from .calculations import FORMULAS, calculate
from .data import BASELINE, DOCUMENTS, LOT, LOTS, PACKS, telemetry
from .gateway import Gateway, GatewayError
from .ledger import Ledger
from .verification import care_guard, retrieve, verify


class ActionError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class Runtime:
    def __init__(self, ledger_path=None, env=None):
        self.lock = threading.RLock()
        self.ledger = Ledger(ledger_path)
        self.metrics, self.telemetry = calculate(telemetry())
        self.packs = self._load_packs(PACKS)
        self.gateway = Gateway(env=env, on_call=self._record_call)
        self.verification = None
        self.explanation = {"text": self._demo_explanation(), "citations": ["FACT:energy_per_unit", "FACT:energy_delta", "SOP-017-v3.2-4.2", "SOP-024-v1.4-2.1"], "source": "Deterministic synthetic demo"}
        self.verification = verify(self.explanation["text"], self.metrics, DOCUMENTS)
        if not self.ledger.records:
            self.ledger.append(pack="core", type="runtime.ready", lot=LOT, title="Shared core ready", detail="Fictional Lumora Wellness reference scenario. Authored telemetry; no AMD call has been made. Four packs are simulated walkthroughs.")
            self.ledger.append(pack="factory", type="telemetry.loaded", lot=LOT, title="Night-shift telemetry loaded", detail=f"{len(self.telemetry)} authored fifteen-minute windows; metrics calculated deterministically.", metrics=self.metrics)
            self.ledger.append(pack="factory", type="anomaly.flagged", lot=LOT, title="Energy and scrap anomaly detected", detail=f"{self.metrics['anomaly_count']} flagged windows; profile drift is an unconfirmed hypothesis. Supervisor review required.", metrics=self.metrics)
        else:
            for event in self.ledger.records:
                if "verification" in event:
                    self.verification = event["verification"]
                if "explanation" in event:
                    self.explanation = event["explanation"]

    @staticmethod
    def _load_packs(manifests):
        loaded = []
        seen = set()
        for original in manifests:
            pack = copy.deepcopy(original)
            required = {"id", "name", "version", "track", "status", "subscriptions", "publishes", "capabilities"}
            reason = None
            if not required.issubset(pack):
                reason = "Missing required manifest fields."
            elif pack["id"] in seen:
                reason = "Duplicate pack identifier."
            elif not all(isinstance(pack[k], list) and all(isinstance(item, str) for item in pack[k]) for k in ("subscriptions", "publishes", "capabilities")):
                reason = "Manifest event/capability lists must contain strings."
            if reason:
                pack["status"] = "quarantined"
                pack["reason"] = reason
            else:
                seen.add(pack["id"])
            loaded.append(pack)
        return loaded

    def _record_call(self, usage):
        self.ledger.append(pack="factory", type="model.called", lot=LOT, title="Model inference completed", detail="Actual configured endpoint response; hardware is operator-declared, not attested.", mode="live", usage=usage)

    def _demo_explanation(self):
        m = self.metrics
        return (f"Shift energy intensity is {m['energy_per_unit']} kWh per good unit, {m['energy_delta']}% above the authored baseline. [FACT:energy_per_unit] [FACT:energy_delta]\n"
                "An unverified thermal profile after element replacement is one possible explanation, not a confirmed root cause; request the process engineer's profile record. [SOP-017-v3.2-4.2]\n"
                "Review idle-load intervals and inspect standby equipment before proposing corrective work; savings remain unmeasured. [SOP-024-v1.4-2.1]")

    def _has(self, kind, lot=LOT):
        return any(e["type"] == kind and e["lot"] == lot for e in self.ledger.records)

    def _held(self, lot=LOT):
        held = False
        for event in self.ledger.records:
            if event["lot"] == lot and event["type"] in {"lot.held", "lot.released"}:
                held = event["type"] == "lot.held"
        return held

    def _approvals(self):
        rows = [{"id": "hold", "pack": "factory", "lot": LOT, "title": "Review and hold affected lot", "detail": "A named supervisor must approve containment and record a reason.", "status": "approved" if self._has("lot.held") else "pending"},
                {"id": "corrective", "pack": "factory", "lot": LOT, "title": "Approve profile-verification work", "detail": "Records an approved work request; does not change the oven.", "status": "approved" if self._has("corrective.approved") else "pending"}]
        event_to_action = {"lot.held": ("order", "Review invoice exception and stock reallocation"), "stock.reallocated": ("offer", "Review proposed retention offer"), "offer.proposed": ("experience", "Review two onboarding contexts"), "experience.generated": ("care", "Review lot-matched sample care instructions")}
        action_to_type = {"order": "stock.reallocated", "offer": "offer.proposed", "experience": "experience.generated", "care": "instructions.bound"}
        pack_map = {"order": "order", "offer": "demand", "experience": "experience", "care": "care"}
        for event_type, (action, title) in event_to_action.items():
            if self._has(event_type):
                rows.append({"id": action, "pack": pack_map[action], "lot": LOT, "title": title, "detail": "Simulated walkthrough. Separate named human approval; no external action occurs.", "status": "approved" if self._has(action_to_type[action]) else "pending"})
        for event in self.ledger.records:
            if event["type"] == "care.escalated":
                rows.append({"id": "nurse-" + event["id"], "pack": "care", "lot": event["lot"], "title": "Simulated nurse review requested", "detail": "No clinic has been contacted; no personal check-in text was retained.", "status": "pending"})
        return rows

    def state(self):
        with self.lock:
            lots = copy.deepcopy(LOTS)
            if self._held():
                lots[0]["status"] = "held"
            elif self._has("lot.released"):
                lots[0]["status"] = "released"
            return {"mode": "live" if self.gateway.successful else "demo", "gateway": self.gateway.status(), "lots": lots, "lot": LOT, "telemetry": self.telemetry, "baseline": BASELINE, "metrics": self.metrics, "events": copy.deepcopy(self.ledger.records), "approvals": self._approvals(), "documents": DOCUMENTS, "verification": self.verification, "packs": self.packs, "explanation": self.explanation, "ledger_valid": self.ledger.verify(), "formulas": FORMULAS, "scenario": {"company": "Lumora Wellness", "fictional": True, "data_source": "Authored synthetic fixtures; not a plant pilot or imported UCI dataset", "currency": "MYR", "timezone": "Asia/Kuala_Lumpur", "date": "2026-10-13"}}

    def _publish(self, pack, kind, title, detail, lot=LOT, actor="System", mode="demo", **payload):
        manifest = next((p for p in self.packs if p["id"] == pack), None)
        if manifest is None or manifest["status"] == "quarantined" or kind not in manifest["publishes"]:
            raise ActionError("Event is not declared by an active pack manifest.")
        subscribers = [p["id"] for p in self.packs if p["status"] != "quarantined" and kind in p["subscriptions"]]
        return self.ledger.append(pack=pack, type=kind, lot=lot, title=title, detail=detail, actor=actor, mode=mode, subscribers=subscribers, **payload)

    @staticmethod
    def _approval(payload):
        actor = payload.get("actor", "")
        notes = payload.get("notes", payload.get("reason", ""))
        if not isinstance(actor, str) or len(actor.strip()) < 2 or len(actor) > 120 or actor.strip().lower() in {"system", "ai", "agent", "anonymous", "unknown"}:
            raise ActionError("Enter the named human approver (at least two characters).")
        if not isinstance(notes, str) or len(notes.strip()) < 5 or len(notes) > 2000:
            raise ActionError("Record an approval reason or evidence note (5–2000 characters).")
        return actor.strip(), notes.strip()

    def action(self, payload):
        if not isinstance(payload, dict):
            raise ActionError("Request must be a JSON object.")
        action = payload.get("action")
        if not isinstance(action, str) or action not in {"hold", "release", "corrective", "order", "offer", "experience", "care", "verify", "analyze"}:
            raise ActionError("Unknown action.")
        lot = payload.get("lot", LOT)
        if not isinstance(lot, str) or lot not in {row["id"] for row in LOTS}:
            raise ActionError("Unknown lot.", 404)
        if action != "care" and lot != LOT:
            raise ActionError("The synthetic incident workflow applies to lot 2610-07 only.")
        request_id = payload.get("request_id")
        if request_id is not None and (not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", request_id)):
            raise ActionError("request_id must be 8–100 letters, numbers, underscores or hyphens.")
        with self.lock:
            if not self.ledger.verify():
                raise ActionError("Ledger integrity check failed; all actions are blocked.", 409)
            prior = next((e for e in self.ledger.records if request_id and e.get("request_id") == request_id), None)
            if prior:
                if prior.get("action") != action:
                    raise ActionError("That request_id was already used for a different action.", 409)
                return {"state": self.state(), "message": "This request was already recorded; no duplicate action was applied.", "result": prior.get("result", {"idempotent": True})}
            result = None
            mode = "live" if self.gateway.successful else "demo"
            common = {"lot": lot, "request_id": request_id, "action": action}
            if action in {"hold", "release", "corrective", "order", "offer", "experience"}:
                actor, notes = self._approval(payload)
                common.update(actor=actor, evidence=notes, approval={"actor": actor, "notes": notes})
            if action == "hold":
                if self._held(lot):
                    return {"state": self.state(), "message": "This lot is already held; no duplicate hold was recorded."}
                self._publish("factory", "lot.held", "Lot held by supervisor", notes, mode=mode, **common)
                message = "Lot hold recorded. Order Hub now has a separate simulated review task."
            elif action == "release":
                if not self._held(lot):
                    raise ActionError("Only a currently held lot can be released.", 409)
                holds = [e for e in self.ledger.records if e["type"] == "lot.held" and e["lot"] == lot]
                latest_hold = holds[-1]["id"]
                if not any(e["type"] == "corrective.approved" and e["lot"] == lot and e["id"] > latest_hold for e in self.ledger.records):
                    raise ActionError("Record corrective-work approval after this hold before a quality release.", 409)
                self._publish("factory", "lot.released", "Lot released by quality reviewer", notes, mode=mode, **common)
                message = "Quality release recorded with the named approver and evidence note."
            elif action == "corrective":
                if not self._held(lot):
                    raise ActionError("Hold the affected lot before approving corrective work.", 409)
                self._publish("factory", "corrective.approved", "Corrective work approved", "Profile verification and calibration review authorized. No machine parameters were changed. " + notes, mode=mode, **common)
                message = "Corrective-work approval recorded; a process engineer performs the actual work."
            elif action == "order":
                if not self._held(lot):
                    raise ActionError("Hold the incident lot before the order walkthrough.", 409)
                target = payload.get("targetLot", "2610-05")
                if target != "2610-05":
                    raise ActionError("The simulated replacement stock must come from released lot 2610-05.")
                if self._has("stock.reallocated", lot):
                    return {"state": self.state(), "message": "This simulated stock allocation is already approved."}
                orders = payload.get("orders", [{"id": "ORD-1041", "units": 40}, {"id": "ORD-1042", "units": 35}, {"id": "ORD-1043", "units": 25}])
                if not isinstance(orders, list) or len(orders) != 3 or [o.get("units") if isinstance(o, dict) else None for o in orders] != [40, 35, 25]:
                    raise ActionError("This walkthrough allocates the three documented orders: 40, 35 and 25 units.")
                allocated = sum(o["units"] for o in orders)
                reserve = next(l for l in LOTS if l["id"] == target)
                if allocated > reserve["units"]:
                    raise ActionError("The released reserve lot has insufficient units.", 409)
                invoice = payload.get("invoice", {"quantity": 12, "unitPrice": 180, "receivedQuantity": 12, "serviceQuantity": 1, "serviceUnitPrice": 80})
                keys = ("quantity", "unitPrice", "receivedQuantity", "serviceQuantity", "serviceUnitPrice")
                if not isinstance(invoice, dict) or any(isinstance(invoice.get(k), bool) or not isinstance(invoice.get(k), (int, float)) or not math.isfinite(invoice[k]) or invoice[k] < 0 for k in keys):
                    raise ActionError("Invoice inputs must be finite, nonnegative numbers.")
                tolerance = payload.get("tolerance", 1)
                if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or not 0 <= tolerance <= 5:
                    raise ActionError("Price tolerance must be between 0 and 5 percent.")
                total = round(invoice["quantity"] * invoice["unitPrice"] + invoice["serviceQuantity"] * invoice["serviceUnitPrice"], 2)
                matched = invoice["quantity"] == invoice["receivedQuantity"] == 12 and invoice["serviceQuantity"] == 0 and abs(invoice["unitPrice"] - 180) <= 180 * tolerance / 100 + 0.000001
                self._publish("order", "order.exception", "Supplier invoice match reviewed", "Simulated invoice " + ("matched the purchase order" if matched else "requires exception review") + "; no supplier was contacted or paid.", lot=lot, actor=actor, mode="walkthrough", evidence=notes, invoice_total=total, variance=round(total-2160, 2), matched=matched)
                result = {"simulated": True, "sourceLot": lot, "targetLot": target, "orders": 3, "allocated_units": allocated, "invoice_total": total, "matched": matched, "invoice": invoice, "tolerance": tolerance, "erp_posted": False}
                self._publish("order", "stock.reallocated", "Three orders reallocated in walkthrough", "Illustrative allocation from released reserve lot 2610-05. No ERP transaction or payment occurred.", mode="walkthrough", result=result, **common)
                message = "Order exception and reallocation recorded as a simulated walkthrough."
            elif action == "offer":
                if not self._has("stock.reallocated", lot):
                    raise ActionError("Complete the order reallocation walkthrough before proposing an offer.", 409)
                if self._has("offer.proposed", lot):
                    return {"state": self.state(), "message": "The simulated offer is already approved."}
                assumptions = {key: payload.get(key, default) for key, default in {"mean": 18, "std": 4.2, "lead": 10, "z": 1.65, "churn": 0.35, "ltv": 420, "uplift": 0.2, "offerCost": 15}.items()}
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 or v > 100000 for v in assumptions.values()) or assumptions["lead"] < 1 or assumptions["churn"] > 1 or assumptions["uplift"] > 1:
                    raise ActionError("Offer assumptions must be valid nonnegative numbers; probabilities are between zero and one.")
                safety = assumptions["z"] * assumptions["std"] * math.sqrt(assumptions["lead"])
                expected = assumptions["churn"] * assumptions["ltv"] * assumptions["uplift"] - assumptions["offerCost"]
                result = {"simulated": True, "sent": False, "assumptions": assumptions, "safety_stock": round(safety, 2), "reorder_point": math.ceil(assumptions["mean"] * assumptions["lead"] + safety), "expected_value": round(expected, 2), "method": "Illustrative scenario; no trained demand or survival model is claimed."}
                self._publish("demand", "offer.proposed", "Retention offer approved for walkthrough", "Human-reviewed apology offer draft for delayed replacement customers. No customer message or purchase order was sent.", mode="walkthrough", result=result, **common)
                message = "Simulated offer approved. Nothing has been sent to a customer."
            elif action == "experience":
                if not self._has("offer.proposed", lot):
                    raise ActionError("Approve the simulated retention offer before the experience walkthrough.", 409)
                if self._has("experience.generated", lot):
                    return {"state": self.state(), "message": "The sample experience was already recorded."}
                context, language, branch = payload.get("context", "caregiver"), payload.get("language", "en"), payload.get("branch", "quick")
                if context not in {"caregiver", "active"} or language not in {"en", "ms"} or branch not in {"quick", "detailed"}:
                    raise ActionError("Select one of the sample audiences, languages and story branches.")
                result = {"simulated": True, "generation": "template", "cost": 0, "currency": "USD", "model_calls": 0, "context": context, "language": language, "branch": branch, "audiences": ["Caregiver · replacement", "Active adult · first kit"], "quality": "Authored template checked against fictional style guide; no image generation or model judge."}
                self._publish("experience", "experience.generated", "Onboarding context reviewed", f"Template for {context}, language {language}, branch {branch}; zero model calls. Brand reviewer approval recorded.", mode="walkthrough", result=result, **common)
                self._publish("care", "instructions.bound", "Sample instructions bound to lot", "Synthetic IFU version 2.1 matched to the replacement kit. This is document binding, not a clinical decision.", lot=lot, mode="walkthrough", actor="Document binding rule", document="IFU-v2.1-1")
                message = "Two simulated experiences approved and sample instructions bound to the lot."
            elif action == "care":
                question = payload.get("question", "")
                if not isinstance(question, str) or not question.strip() or len(question) > 2000:
                    raise ActionError("Enter a sample question up to 2000 characters.")
                status, response = care_guard(question)
                result = {"status": status, "text": response, "citations": re.findall(r"\[([^\]]+)\]", response), "simulated": True, "stored_personal_text": False, "language": "English", "requested_language": str(payload.get("language", "English"))[:40]}
                kind = "care.escalated" if status in {"review", "urgent", "out_of_scope"} else "care.refused" if status == "refused" else "care.answered"
                event = self._publish("care", kind, "Care guard: " + status.replace("_", " "), "Deterministic guard decision. Question text is not stored or sent to a model. No clinic or emergency service has been contacted.", mode="walkthrough", result=result, **common)
                if kind == "care.escalated":
                    result["task_id"] = "nurse-" + event["id"]
                message = response
            elif action == "verify":
                draft = "The proposed oven adjustment will save 37% of energy. [SOP-017-v3.2-4.2]"
                self.verification = verify(draft, self.metrics, DOCUMENTS)
                result = {"draft": draft, **self.verification}
                self.ledger.append(pack="factory", type="verification.rejected", lot=lot, title="Fabricated savings claim blocked", detail="Planted 37% saving has no locked calculation. It is rejected before human release.", verification=self.verification, result=result, request_id=request_id, action=action)
                message = "The invented 37% saving was rejected by the numeric fact lock."
            else:
                result = self._analyze(request_id)
                message = "Cited explanation checked against calculated facts." if result["status"] == "passed" else result.get("message", "Explanation refused after verification.")
            return {"state": self.state(), "message": message, "result": result}

    def _analyze(self, request_id=None):
        passages = retrieve(DOCUMENTS, "reflow profile verification maintenance idle energy calibration", "factory")
        self.ledger.append(pack="factory", type="evidence.retrieved", lot=LOT, title="Factory procedures retrieved", detail="BM25 retrieval restricted to factory procedure passages.", passage_ids=[p["id"] for p in passages])
        text = self._demo_explanation()
        source = "Deterministic synthetic demo"
        if self.gateway.configured:
            messages = [{"role": "system", "content": "Return JSON with only a text field. Explain the operational facts; never calculate or invent numbers. Every sentence MUST cite a supplied [passage-id] or [FACT:key]. Use only numbers exactly supplied in the locked facts. Root causes are hypotheses; no confirmed savings, machine commands, medical advice or autonomous actions. Recommend named human review. Do not repeat lot or document version numbers outside citation brackets."}, {"role": "user", "content": json.dumps({"locked_facts": self.metrics, "passages": passages})}]
            for attempt in range(2):
                try:
                    text = self.gateway.complete(messages, bypass_cache=attempt > 0)
                    verdict = verify(text, self.metrics, passages)
                except GatewayError as exc:
                    if attempt == 0:
                        messages.append({"role": "user", "content": "Previous output failed. Return exactly a JSON object with one nonempty text string, with citations on every sentence."})
                        continue
                    result = {"status": "unavailable", "message": str(exc)}
                    self.ledger.append(pack="factory", type="analysis.unavailable", lot=LOT, title="Live explanation unavailable", detail=str(exc), request_id=request_id, action="analyze", result=result)
                    return result
                if verdict["status"] == "passed":
                    source = "Live configured model · " + self.gateway.model
                    break
                self.ledger.append(pack="factory", type="verification.rejected", lot=LOT, title="Model draft blocked", detail="Numeric or citation validation failed; unsupported draft not released.", mode="live", verification=verdict)
                messages.append({"role": "user", "content": "Regenerate once and fix these findings: " + json.dumps(verdict["findings"])})
            else:
                self.verification = verdict
                return {"status": "refused", "message": "Model explanation failed verification twice and was withheld."}
        verdict = verify(text, self.metrics, passages)
        self.verification = verdict
        if verdict["status"] != "passed":
            return {"status": "refused", "message": "Explanation failed deterministic verification and was withheld."}
        self.explanation = {"text": text, "citations": verdict["citations"], "source": source}
        self.ledger.append(pack="factory", type="explanation.verified", lot=LOT, title="Cited explanation verified", detail="Structural citation coverage and numeric locks passed. Hypotheses still require human review.", mode="live" if source.startswith("Live") else "demo", verification=verdict, explanation=self.explanation, request_id=request_id, action="analyze", result={"status": "passed"})
        return {"status": "passed", "explanation": self.explanation, "verification": verdict}


def export_demo(path):
    from pathlib import Path
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(Runtime(env={}).state(), ensure_ascii=False, indent=2), encoding="utf-8")
