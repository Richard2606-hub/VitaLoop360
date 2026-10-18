"""Durable append-only SHA-256 JSONL ledger with fail-closed integrity checks."""
import hashlib
import json
import os
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
            record = {"id": f"evt-{len(self.records) + 1:05d}", "time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "pack": pack, "type": type, "lot": lot, "title": title, "detail": detail, "actor": actor, "mode": mode, "previous_hash": self.records[-1]["hash"] if self.records else "0" * 64}
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
