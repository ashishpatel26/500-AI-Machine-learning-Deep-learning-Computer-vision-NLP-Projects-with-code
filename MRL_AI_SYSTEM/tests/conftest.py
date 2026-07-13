import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "particles"))

# Every test gets its own trace journal to avoid contaminating the host.
os.environ.setdefault("MRL_TRACE_JOURNAL", str(REPO / "tests" / ".artifacts" / "trace.jsonl"))
os.environ.setdefault("MRL_SIG_KEYDIR", str(REPO / "tests" / ".artifacts" / "keys"))
os.environ.setdefault("MRL_HUB_DB", str(REPO / "tests" / ".artifacts" / "hub.sqlite3"))

(REPO / "tests" / ".artifacts").mkdir(parents=True, exist_ok=True)
