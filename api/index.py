"""Vercel Python Serverless Function entry point for VitaLoop 360 API routes."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run import load_dotenv
from backend.runtime import Runtime
from backend.server import make_handler

load_dotenv(ROOT / ".env")
LEDGER_PATH = Path(os.environ.get("VITALOOP_DATA_DIR", tempfile.gettempdir())) / "vitaloop360-ledger.jsonl"
RUNTIME = Runtime(ledger_path=LEDGER_PATH)
handler = make_handler(RUNTIME, ROOT / "dist")
