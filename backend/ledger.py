"""Durable append-only SHA-256 JSONL ledger with fail-closed integrity checks and materialised views."""
import hashlib
import json
import math
import os
import statistics
import threading
from datetime import datetime, timezone
from pathlib import Path


class LedgerIntegrityError(ValueError):
    pass


def digest(record):
    payload = {key: value for key, value in record.items() if key != "hash"}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class Ledger:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.lock = threading.RLock()
        self.records = []
        if self.path and self.path.exists():
            self.records = self._read()
            if not self.verify():
                raise LedgerIntegrityError("Ledger hash chain is invalid; refusing to append.")

    def _read(self):
        try:
            return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, ValueError) as exc:
            raise LedgerIntegrityError("Ledger contains an unreadable record.") from exc

    def verify(self):
        with self.lock:
            try:
                records = self._read() if self.path and self.path.exists() else self.records
                previous = "0" * 64
                for i, record in enumerate(records, 1):
                    if record.get("id") != f"evt-{i:05d}" or record.get("previous_hash") != previous or record.get("hash") != digest(record):
                        return False
                    previous = record["hash"]
                return True
            except (LedgerIntegrityError, TypeError, KeyError):
                return False

    def append(self, *, pack, type, lot, title, detail, actor="System", mode="demo", **payload):
        with self.lock:
            if not self.verify():
                raise LedgerIntegrityError("Ledger changed on disk; action refused.")
            if self.path and self.path.exists():
                self.records = self._read()
            record = {
                "id": f"evt-{len(self.records) + 1:05d}",
                "time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "pack": pack,
                "type": type,
                "lot": lot,
                "title": title,
                "detail": detail,
                "actor": actor,
                "mode": mode,
                "previous_hash": self.records[-1]["hash"] if self.records else "0" * 64,
            }
            reserved = set(record) | {"hash"}
            if reserved.intersection(payload):
                raise ValueError("Payload cannot replace ledger metadata.")
            # Snapshot nested values so callers cannot mutate already hashed rows.
            record.update(json.loads(json.dumps(payload, ensure_ascii=False)))
            record["hash"] = digest(record)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
            self.records.append(record)
            return record

    def jsonl(self):
        return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in self.records)

    def reset(self, records=None):
        with self.lock:
            self.records = [json.loads(json.dumps(r, ensure_ascii=False)) for r in (records or [])]
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                content = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in self.records)
                self.path.write_text(content, encoding="utf-8")
            if self.records and not self.verify():
                raise LedgerIntegrityError("Reset ledger records failed hash-chain verification.")

    def views(self):
        """Materialise the four Proposal Module 6 views: cost_view, verification_view, approvals_view, lot_view."""
        with self.lock:
            records = list(self.records)
            valid = self.verify()
            model_calls = [r for r in records if r.get("type") == "model.called" and isinstance(r.get("usage"), dict)]
            latencies = sorted(r["usage"]["latency_ms"] for r in model_calls if isinstance(r["usage"].get("latency_ms"), (int, float)))
            prompt_tokens = sum(r["usage"].get("prompt_tokens") or 0 for r in model_calls)
            completion_tokens = sum(r["usage"].get("completion_tokens") or 0 for r in model_calls)
            median_ms = round(statistics.median(latencies), 1) if latencies else None
            p95_ms = latencies[min(len(latencies) - 1, max(0, math.ceil(0.95 * len(latencies)) - 1))] if latencies else None

            verifications = [r for r in records if isinstance(r.get("verification"), dict)]
            passed_count = sum(1 for r in verifications if r["verification"].get("status") == "passed")
            rejected_count = sum(1 for r in verifications if r["verification"].get("status") == "rejected")
            rule_counts = {"unlocked_number": 0, "unresolved_citation": 0, "citation_coverage": 0, "unlocked_identifier": 0}
            coverages = []
            for r in verifications:
                v = r["verification"]
                if isinstance(v.get("coverage"), (int, float)):
                    coverages.append(float(v["coverage"]))
                for f in v.get("findings", []):
                    rule = f.get("rule")
                    if rule in rule_counts:
                        rule_counts[rule] += 1

            approvals = [
                {
                    "id": r["id"],
                    "time": r["time"],
                    "pack": r["pack"],
                    "type": r["type"],
                    "lot": r["lot"],
                    "actor": r["actor"],
                    "title": r["title"],
                    "evidence": r.get("evidence") or (r.get("approval") or {}).get("notes") or r["detail"],
                    "mode": r.get("mode", "demo"),
                    "hash": r["hash"],
                }
                for r in records
                if r.get("actor") and r.get("actor") not in {"System", "Document binding rule", "Demo system", "Demo caregiver"}
            ]

            lots_map = {}
            for r in records:
                lot_id = r.get("lot", "unknown")
                lots_map.setdefault(lot_id, []).append({
                    "id": r["id"],
                    "time": r["time"],
                    "pack": r["pack"],
                    "type": r["type"],
                    "title": r["title"],
                    "actor": r["actor"],
                    "mode": r.get("mode", "demo"),
                    "subscribers": r.get("subscribers", []),
                    "hash": r["hash"],
                })

            guard_events = [r for r in records if r.get("pack") == "care" and r.get("type") in {"care.refused", "care.escalated", "care.answered", "nurse.resolved"}]
            redaction_totals = {"EMAIL": 0, "PHONE": 0, "ID": 0, "ADDRESS": 0, "PERSON": 0}
            for r in guard_events:
                entities = ((r.get("result") or {}).get("redaction") or {}).get("entities") or {}
                for k in redaction_totals:
                    redaction_totals[k] += int(entities.get(k, 0))

            return {
                "chain_intact": valid,
                "total_records": len(records),
                "cost_view": {
                    "model_calls": len(model_calls),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "median_latency_ms": median_ms,
                    "p95_latency_ms": p95_ms,
                },
                "verification_view": {
                    "checked": len(verifications),
                    "passed": passed_count,
                    "rejected": rejected_count,
                    "findings_by_rule": rule_counts,
                    "mean_coverage_pct": round(sum(coverages) / len(coverages), 1) if coverages else 100.0,
                },
                "guard_view": {
                    "events": len(guard_events),
                    "refused": sum(1 for r in guard_events if r["type"] == "care.refused"),
                    "escalated": sum(1 for r in guard_events if r["type"] == "care.escalated"),
                    "answered": sum(1 for r in guard_events if r["type"] == "care.answered"),
                    "resolved_by_nurse": sum(1 for r in guard_events if r["type"] == "nurse.resolved" or r.get("action") == "nurse_resolve" or r.get("task_id")),
                    "redactions_by_entity": redaction_totals,
                },
                "approvals_view": approvals,
                "lot_view": lots_map,
            }
