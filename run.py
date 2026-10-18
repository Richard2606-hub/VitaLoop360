"""One-command local application; no third-party packages required."""
import argparse
import os
from pathlib import Path

from backend.runtime import Runtime, export_demo
from backend.server import serve

ROOT = Path(__file__).resolve().parent


def load_dotenv(path):
    """Small literal KEY=VALUE loader; environment values take precedence."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key.startswith("VITALOOP_"):
            os.environ.setdefault(key, value.strip("\"'"))


def main():
    parser = argparse.ArgumentParser(description="VitaLoop 360 — local fictional operations console")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--export-demo", type=Path, help="Write a synthetic static snapshot and exit; never invokes a model")
    parser.add_argument("--demo", action="store_true", help="Ignore all model credentials and force deterministic demo mode")
    args = parser.parse_args()
    if args.export_demo:
        export_demo(args.export_demo)
        print(f"Synthetic demo state written to {args.export_demo}")
        return
    load_dotenv(ROOT / ".env")
    data_dir = args.data_dir or Path(os.environ.get("VITALOOP_DATA_DIR", str(ROOT / "data")))
    runtime = Runtime(ledger_path=data_dir / "ledger.jsonl", env={} if args.demo else None)
    serve(runtime, ROOT / "dist", args.host, args.port)


if __name__ == "__main__":
    main()
