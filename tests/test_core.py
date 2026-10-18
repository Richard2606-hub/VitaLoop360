import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from backend.calculations import calculate, isolation_scores
from backend.data import DOCUMENTS, LOT, telemetry
from backend.gateway import Gateway, GatewayError
from backend.ledger import Ledger, LedgerIntegrityError, digest
from backend.runtime import ActionError, Runtime
from backend.server import make_handler
from backend.verification import care_guard, retrieve, verify


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime(env={})

    def act(self, action, **kwargs):
        return self.runtime.action({"action": action, "actor": "Aisha Rahman", "notes": "Reviewed the fixture evidence for this demonstration.", **kwargs})

    def test_metrics_recompute_from_fixture(self):
        rows = telemetry()
        m, windows = calculate(rows)
        self.assertEqual(m["good_units"], sum(row["good_units"] for row in rows))
        self.assertEqual(m["energy_kwh"], round(sum(row["energy"] for row in rows), 2))
        self.assertEqual(m["energy_per_unit"], round(m["energy_kwh"] / m["good_units"], 3))
        self.assertEqual(m["scrap_rate"], round(100 * sum(row["scrap"] for row in rows) / sum(row["scrap"] + row["good_units"] for row in rows), 2))
        self.assertEqual(m["estimated_excess_cost"], round(max(0, m["energy_kwh"] - m["good_units"] * .42) * .48, 2))
        self.assertEqual(m["anomaly_count"], 9)
        self.assertTrue(all(windows[i]["anomaly"] for i in range(9, 18)))

    def test_anomaly_model_deterministic(self):
        rows = [[float(i), float(i * i)] for i in range(20)]
        self.assertEqual(isolation_scores(rows), isolation_scores(rows))
        self.assertNotEqual(isolation_scores(rows, seed=2), isolation_scores(rows, seed=3))

    def test_invalid_telemetry_is_rejected(self):
        for field, value in [("energy", -1), ("good_units", 0), ("scrap", float("nan")), ("idle_energy", 1e9)]:
            rows = telemetry()
            rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                calculate(rows)

    def test_default_and_analyze_are_verified(self):
        self.assertEqual(self.runtime.state()["verification"]["status"], "passed")
        response = self.act("analyze")
        self.assertEqual(response["result"]["verification"]["coverage"], 100)
        self.assertEqual(response["state"]["mode"], "demo")
        self.assertEqual(response["state"]["gateway"]["calls"], 0)

    def test_planted_saving_rejected(self):
        response = self.act("verify")
        self.assertEqual(response["result"]["status"], "rejected")
        self.assertTrue(any(f["rule"] == "unlocked_number" and f["value"] == "37" for f in response["result"]["findings"]))

    def test_verifier_handles_signed_numbers_and_citations(self):
        facts = {"cost": 98.06}
        self.assertEqual(verify("Estimated cost is 98.06. [FACT:cost]", facts, [])["status"], "passed")
        self.assertEqual(verify("Estimated cost is -98.06 [FACT:cost].", facts, [])["status"], "rejected")
        self.assertEqual(verify("Estimated cost is 98.06 [FAKE:cost].", facts, [])["status"], "rejected")
        self.assertEqual(verify("Estimated cost is 98.06.", facts, [])["status"], "rejected")
        self.assertEqual(verify("Estimated cost is 9.806e1 [FACT:cost].", facts, [])["status"], "passed")

    def test_hold_requires_named_person_and_reason(self):
        for data in ({"action": "hold"}, {"action": "hold", "actor": "System", "notes": "Reviewed evidence"}, {"action": "hold", "actor": "Aisha", "notes": "ok"}):
            with self.subTest(data=data), self.assertRaises(ActionError):
                self.runtime.action(data)
        response = self.act("hold")
        event = response["state"]["events"][-1]
        self.assertEqual(event["actor"], "Aisha Rahman")
        self.assertEqual(event["subscribers"], ["order"])
        self.assertEqual(response["state"]["lots"][0]["status"], "held")

    def test_release_requires_hold_and_new_corrective_approval(self):
        with self.assertRaises(ActionError):
            self.act("release")
        self.act("hold")
        with self.assertRaises(ActionError):
            self.act("release")
        self.act("corrective")
        self.assertEqual(self.act("release")["state"]["lots"][0]["status"], "released")
        self.act("hold")
        with self.assertRaises(ActionError):
            self.act("release")

    def test_idempotent_action(self):
        self.act("hold", request_id="hold-request-123")
        count = len(self.runtime.ledger.records)
        self.act("hold", request_id="hold-request-123")
        self.assertEqual(len(self.runtime.ledger.records), count)
        with self.assertRaises(ActionError):
            self.act("corrective", request_id="hold-request-123")

    def test_walkthrough_prerequisites_and_no_external_effect(self):
        for action in ("order", "offer", "experience"):
            with self.subTest(action=action), self.assertRaises(ActionError):
                self.act(action)
        self.act("hold")
        order = self.act("order")["result"]
        self.assertFalse(order["erp_posted"])
        self.assertFalse(self.act("offer")["result"]["sent"])
        experience = self.act("experience")["result"]
        self.assertEqual(experience["model_calls"], 0)
        self.assertEqual(experience["cost"], 0)
        self.assertEqual(self.runtime.ledger.records[-1]["type"], "instructions.bound")
        self.assertTrue(all(e["mode"] == "walkthrough" for e in self.runtime.ledger.records if e["pack"] in {"order", "demand", "experience", "care"}))

    def test_care_refusal_redflags_no_personal_text_storage(self):
        for question in ("Should I double my dose?", "Do I have an infection?", "Can I stop taking medication?", "What disease is this?"):
            with self.subTest(question=question):
                self.assertEqual(care_guard(question)[0], "refused")
        self.assertEqual(care_guard("She has chest pain")[0], "urgent")
        response = self.runtime.action({"action": "care", "question": "My mother Jane's strap causes skin irritation"})
        self.assertEqual(response["result"]["status"], "review")
        self.assertNotIn("Jane", self.runtime.ledger.jsonl())
        self.assertTrue(self.runtime.ledger.verify())
        self.act("verify")  # A care response must not mutate the prior hashed record.

    def test_malay_care_rules_and_unknown_questions(self):
        self.assertEqual(care_guard("Berapa dos ubat?")[0], "refused")
        self.assertEqual(care_guard("Kerengsaan kulit pada tali")[0], "review")
        self.assertEqual(care_guard("Sesak nafas")[0], "urgent")
        self.assertEqual(care_guard("Di mana panduan persediaan?")[0], "routine")
        self.assertEqual(care_guard("An unrelated uncovered question")[0], "out_of_scope")

    def test_invoice_calculation_and_experience_selection(self):
        self.act("hold")
        with self.assertRaises(ActionError):
            self.act("order", invoice={"quantity": -1})
        with self.assertRaises(ActionError):
            self.act("order", orders=[{"units": 900}])
        invoice = {"quantity": 12, "unitPrice": 180, "receivedQuantity": 12, "serviceQuantity": 0, "serviceUnitPrice": 80}
        result = self.act("order", invoice=invoice)["result"]
        self.assertTrue(result["matched"])
        self.assertEqual(result["invoice_total"], 2160)
        self.assertEqual(result["allocated_units"], 100)
        self.act("offer")
        selected = self.act("experience", context="active", language="ms", branch="detailed")["result"]
        self.assertEqual((selected["context"], selected["language"], selected["branch"]), ("active", "ms", "detailed"))

    def test_retrieval_respects_pack_and_version(self):
        self.assertTrue(all(d["pack"] == "factory" for d in retrieve(DOCUMENTS, "instructions skin", "factory")))
        self.assertEqual(retrieve(DOCUMENTS, "instructions", "care", version="1.0"), [])
        self.assertTrue(all(d["version"] == "2.1" for d in retrieve(DOCUMENTS, "instructions", "care", version="2.1")))

    def test_durable_ledger_restore_and_tamper_detection(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as folder:
            path = Path(folder) / "audit.jsonl"
            runtime = Runtime(path, env={})
            runtime.action({"action": "hold", "actor": "Aisha Rahman", "notes": "Reviewed incident evidence."})
            restored = Runtime(path, env={})
            self.assertEqual(restored.state()["lots"][0]["status"], "held")
            records = path.read_text(encoding="utf-8").splitlines()
            changed = json.loads(records[1])
            changed["detail"] = "changed after signing"
            records[1] = json.dumps(changed)
            path.write_text("\n".join(records) + "\n", encoding="utf-8")
            self.assertFalse(runtime.ledger.verify())
            with self.assertRaises(ActionError):
                runtime.action({"action": "analyze"})
            with self.assertRaises(LedgerIntegrityError):
                Ledger(path)

    def test_nested_ledger_payload_is_snapshotted(self):
        value = {"status": "pending"}
        ledger = Ledger()
        ledger.append(pack="test", type="test", lot=LOT, title="test", detail="test", value=value)
        value["status"] = "modified"
        self.assertTrue(ledger.verify())

    def test_schema_validation_and_quarantine(self):
        for data in ([], {}, {"action": []}, {"action": "hold", "lot": []}, {"action": "unknown"}, {"action": "care", "question": []}):
            with self.subTest(data=data), self.assertRaises(ActionError):
                self.runtime.action(data)
        invalid = Runtime._load_packs([{"id": "broken"}])
        self.assertEqual(invalid[0]["status"], "quarantined")


class GatewayTests(unittest.TestCase):
    def test_no_configuration_does_not_invent_calls(self):
        gateway = Gateway(env={})
        self.assertFalse(gateway.configured)
        self.assertIsNone(gateway.status()["cost"])
        with self.assertRaises(GatewayError):
            gateway.complete([])
        self.assertEqual(gateway.calls, 0)

    def test_mocked_provider_metering_cache_and_secret_redaction(self):
        gateway = Gateway(env={"VITALOOP_BASE_URL": "https://example.invalid/v1", "VITALOOP_MODEL": "configured-model", "VITALOOP_API_KEY": "never-show-this", "VITALOOP_INPUT_PRICE_PER_MILLION": "1", "VITALOOP_OUTPUT_PRICE_PER_MILLION": "2"})
        payload = {"choices": [{"message": {"content": json.dumps({"text": "Cited explanation [FACT:test]."})}}], "usage": {"prompt_tokens": 100, "completion_tokens": 25}}
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())) as call:
            self.assertIn("Cited", gateway.complete([]))
            gateway.complete([])
            self.assertEqual(call.call_count, 1)
        self.assertEqual(gateway.tokens, 125)
        self.assertAlmostEqual(gateway.status()["cost"], .00015)
        self.assertNotIn("never-show-this", json.dumps(gateway.status()))
        self.assertFalse(gateway.status()["hardware_verified"])

    def test_missing_usage_is_not_zero_measured_cost(self):
        gateway = Gateway(env={"VITALOOP_BASE_URL": "https://example.invalid/v1", "VITALOOP_MODEL": "test", "VITALOOP_INPUT_PRICE_PER_MILLION": "0", "VITALOOP_OUTPUT_PRICE_PER_MILLION": "0"})
        payload = {"choices": [{"message": {"content": '{"text":"Example [FACT:test]."}'}}]}
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(payload).encode())):
            gateway.complete([])
        self.assertIsNone(gateway.status()["cost"])
        self.assertIsNone(gateway.status()["tokens"])
        self.assertFalse(gateway.status()["usage_available"])


class HTTPTests(unittest.TestCase):
    def test_json_errors_static_isolation_and_state(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as folder:
            root = Path(folder)
            (root / "index.html").write_text("VitaLoop", encoding="utf-8")
            runtime = Runtime(env={})
            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(runtime, root))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urllib.request.urlopen(base + "/api/state") as response:
                    self.assertEqual(json.load(response)["mode"], "demo")
                for path, body, content_type, expected in [("/api/action", b'{"action":"hold"}', "application/json", 400), ("/api/action", b"{", "application/json", 400), ("/api/action", b"{}", "text/plain", 415), ("/api/missing", b"{}", "application/json", 404)]:
                    request = urllib.request.Request(base + path, data=body, headers={"Content-Type": content_type})
                    with self.subTest(path=path, body=body), self.assertRaises(urllib.error.HTTPError) as caught:
                        urllib.request.urlopen(request)
                    self.assertEqual(caught.exception.code, expected)
                    self.assertIn("error", json.load(caught.exception))
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(base + "/%2e%2e/run.py")
                self.assertEqual(caught.exception.code, 403)
                request = urllib.request.Request(base + "/api/action", data=b'{"action":"verify"}', headers={"Content-Type": "application/json", "Origin": "https://foreign.example"})
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(request)
                self.assertEqual(caught.exception.code, 403)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
