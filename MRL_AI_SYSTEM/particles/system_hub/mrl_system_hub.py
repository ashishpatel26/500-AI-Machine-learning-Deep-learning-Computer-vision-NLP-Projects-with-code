"""particle-system-hub — brain hub daemon (800AI orchestrator + MemoryVault).

origin_signature: MrliouAI
layer: L6 Cognition / L4 World

Zero external deps. Wraps the 800AI eight-role router plus a SQLite-backed
seven-layer MemoryVault stub. Endpoints:

  GET  /health              — liveness + Merkle root
  POST /brain/dispatch      — route task → assigned roles + trace anchor
  POST /brain/recall        — semantic recall from MemoryVault
  POST /brain/remember      — write item into a vault layer

Env:
  MRL_HUB_HOST=127.0.0.1
  MRL_HUB_PORT=9000
  MRL_HUB_DB=/var/lib/mrl/system_hub/memory.sqlite3
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trace_chain import emit as trace_emit, merkle_root  # noqa: E402

ORIGIN_SIGNATURE = "MrliouAI"
HOST = os.environ.get("MRL_HUB_HOST", "127.0.0.1")
PORT = int(os.environ.get("MRL_HUB_PORT", "9000"))
DB_PATH = os.environ.get("MRL_HUB_DB", "/var/lib/mrl/system_hub/memory.sqlite3")

VAULT_LAYERS = (
    "L1_sensory", "L2_working", "L3_episodic", "L4_semantic",
    "L5_procedural", "L6_reflective", "L7_soul",
)

ROLES = [
    "architect", "engineer", "reviewer", "optimizer",
    "debugger", "refactorer", "ui_builder", "physics_auditor",
]


# --- 800AI router (mirrors MRLiou_800AI orchestrator.route) ---
def route(task: str) -> list[str]:
    t = task.lower()
    roles = ["architect", "engineer", "reviewer"]
    if re.search(r"bug|debug|錯誤|除錯|故障", t):
        roles.append("debugger")
    if re.search(r"performance|optimi|效能|速度|memory", t):
        roles.append("optimizer")
    if re.search(r"refactor|clean architecture|重構", t):
        roles.append("refactorer")
    if re.search(r"ui|frontend|component|介面|元件", t):
        roles.append("ui_builder")
    if re.search(r"cfd|physics|mass|momentum|energy|守恆|物理", t):
        roles.append("physics_auditor")
    # dedupe preserving order
    return list(dict.fromkeys(roles))


# --- MemoryVault (SQLite, seven layers) ---
_db_lock = threading.Lock()


def _db() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer TEXT NOT NULL,
            key TEXT,
            content TEXT NOT NULL,
            simhash TEXT,
            written_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vault_layer ON vault(layer)")
    return conn


def _simhash(text: str, dim: int = 64) -> int:
    """Lightweight 64-bit simhash on whitespace tokens."""
    import hashlib
    weights = [0] * dim
    for tok in text.split():
        h = int.from_bytes(hashlib.sha1(tok.encode()).digest()[:8], "big")
        for i in range(dim):
            weights[i] += 1 if (h >> i) & 1 else -1
    out = 0
    for i, w in enumerate(weights):
        if w > 0:
            out |= 1 << i
    return out


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def remember(layer: str, content: str, key: str | None = None) -> dict:
    if layer not in VAULT_LAYERS:
        raise ValueError(f"unknown layer: {layer}")
    sh = _simhash(content)
    with _db_lock, _db() as conn:
        cur = conn.execute(
            "INSERT INTO vault(layer, key, content, simhash) VALUES (?,?,?,?)",
            (layer, key, content, f"{sh:016x}"),
        )
        rec_id = cur.lastrowid
    trace_emit("hub.remember", {"layer": layer, "id": rec_id, "simhash": sh}, layer="L3")
    return {"id": rec_id, "layer": layer, "simhash": sh}


def recall(query: str, layer: str | None = None, top_k: int = 5) -> list[dict]:
    target = _simhash(query)
    with _db_lock, _db() as conn:
        rows = conn.execute(
            "SELECT id, layer, key, content, simhash, written_at FROM vault"
            + (" WHERE layer=?" if layer else ""),
            (layer,) if layer else (),
        ).fetchall()
    scored = [(_hamming(target, int(r[4], 16)), r) for r in rows]
    scored.sort(key=lambda x: x[0])
    out = []
    for dist, r in scored[:top_k]:
        out.append({
            "id": r[0], "layer": r[1], "key": r[2],
            "content": r[3], "distance": dist, "written_at": r[5],
        })
    trace_emit("hub.recall", {"q_len": len(query), "hits": len(out)}, layer="L3")
    return out


# --- HTTP ---
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read(self) -> dict:
        n = int(self.headers.get("Content-Length", "0") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {
                "ok": True, "particle": "system_hub",
                "origin_signature": ORIGIN_SIGNATURE,
                "roles": ROLES, "vault_layers": VAULT_LAYERS,
                "trace_root": merkle_root(),
            })
        return self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        try:
            body = self._read()
        except Exception as exc:
            return self._send(400, {"ok": False, "error": f"bad_json: {exc}"})

        if self.path == "/brain/dispatch":
            task = body.get("task", "")
            roles = route(task)
            rec = trace_emit("hub.dispatch", {"task": task, "roles": roles}, layer="L6")
            return self._send(200, {
                "ok": True, "task": task, "assigned_roles": roles,
                "trace_anchor": rec["chain_hash"],
            })

        if self.path == "/brain/remember":
            layer = body.get("layer", "L3_episodic")
            content = body.get("content", "")
            key = body.get("key")
            try:
                out = remember(layer, content, key)
            except ValueError as exc:
                return self._send(400, {"ok": False, "error": str(exc)})
            return self._send(200, {"ok": True, **out})

        if self.path == "/brain/recall":
            q = body.get("query", "")
            layer = body.get("layer")
            top_k = int(body.get("top_k", 5))
            hits = recall(q, layer=layer, top_k=top_k)
            return self._send(200, {"ok": True, "hits": hits})

        return self._send(404, {"ok": False, "error": "not_found"})


def main() -> None:
    trace_emit("hub.daemon.start", {"host": HOST, "port": PORT}, layer="L6")
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[MRL] particle-system-hub http://{HOST}:{PORT} — origin={ORIGIN_SIGNATURE}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
