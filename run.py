"""One-command local application; supports serve, replay, batch readiness, and metrics modes."""
import argparse
import json
import os
import sys
from pathlib import Path

from backend.runtime import Runtime, export_demo, generate_metrics_report, run_readiness_suite
from backend.server import serve

ROOT = Path(__file__).resolve().parent


def load_dotenv(path):
    """Small literal KEY=VALUE loader; environment values take precedence."""
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if key.startswith("VITALOOP_"):
                os.environ.setdefault(key, value.strip("\"'"))
    os.environ.setdefault("VITALOOP_BASE_URL", "https://developer.amd.com.cn/radeon/api/v1")
    os.environ.setdefault("VITALOOP_API_KEY", "rc-37472ac4745615fd004bd37a50711a865e57e483b653e42e")
    os.environ.setdefault("VITALOOP_MODEL", "Gemma-4-31B-IT")
    os.environ.setdefault("VITALOOP_PROVIDER", "AMD Token Factory (Radeon Cloud)")
    os.environ.setdefault("VITALOOP_INPUT_PRICE_PER_MILLION", "0")
    os.environ.setdefault("VITALOOP_OUTPUT_PRICE_PER_MILLION", "0")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="VitaLoop 360 — local fictional operations console")
    parser.add_argument("--mode", choices=["serve", "replay", "batch"], default="serve", help="Execution mode: serve (default), replay (read-only ledger), or batch (readiness suite)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--replay", type=Path, help="Start in read-only replay mode from the specified ledger.jsonl file")
    parser.add_argument("--batch", action="store_true", help="Run happy-path and adversarial readiness suite across all packs and exit")
    parser.add_argument("--metrics", action="store_true", help="Compute and print the Proposal Evaluation & Metrics report from the ledger and exit")
    parser.add_argument("--export-demo", type=Path, help="Write a synthetic static snapshot and exit; never invokes a model")
    parser.add_argument("--demo", action="store_true", help="Ignore all model credentials and force deterministic demo mode")
    args = parser.parse_args()

    if args.export_demo:
        export_demo(args.export_demo)
        print(f"Synthetic demo state written to {args.export_demo}")
        return

    if args.batch or args.mode == "batch":
        report = run_readiness_suite()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report["failed"] > 0:
            sys.exit(1)
        return

    load_dotenv(ROOT / ".env")
    data_dir = args.data_dir or Path(os.environ.get("VITALOOP_DATA_DIR", str(ROOT / "data")))
    ledger_path = args.replay or (data_dir / "ledger.jsonl")
    replay_only = bool(args.replay or args.mode == "replay")

    if args.metrics:
        runtime = Runtime(ledger_path=ledger_path, env={} if (args.demo or replay_only) else None, replay_only=replay_only)
        print(json.dumps(generate_metrics_report(runtime), ensure_ascii=False, indent=2))
        return

    runtime = Runtime(ledger_path=ledger_path, env={} if (args.demo or replay_only) else None, replay_only=replay_only)
    serve(runtime, ROOT / "dist", args.host, args.port)


if __name__ == "__main__":
    main()
