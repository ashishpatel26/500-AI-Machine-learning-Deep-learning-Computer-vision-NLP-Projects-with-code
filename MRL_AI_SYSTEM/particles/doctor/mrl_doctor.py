"""particle-doctor — health monitor + auto-restart supervisor.

origin_signature: MrliouAI
layer: L5 Field (guardian)

Polls sig_verify / system_hub / smartbody_v2 health endpoints, records incidents
to trace_chain, and (when configured) restarts a systemd unit via `systemctl`.

Endpoints:
  GET  /health                    — doctor itself
  GET  /doctor/status             — last known status of every watched particle
  POST /doctor/heartbeat          — particles push heartbeats here
  POST /doctor/restart/<name>     — force-attempt a restart

Env:
  MRL_DOCTOR_HOST=127.0.0.1
  MRL_DOCTOR_PORT=8788
  MRL_DOCTOR_INTERVAL=15
  MRL_DOCTOR_TARGETS='{"sig_verify":"http://127.0.0.1:8801/health",...}'  (JSON)
  MRL_DOCTOR_SYSTEMD=1           — call `systemctl --user restart mrl-<name>.service`
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trace_chain import emit as trace_emit  # noqa: E402

ORIGIN_SIGNATURE = "MrliouAI"
HOST = os.environ.get("MRL_DOCTOR_HOST", "127.0.0.1")
PORT = int(os.environ.get("MRL_DOCTOR_PORT", "8788"))
INTERVAL = int(os.environ.get("MRL_DOCTOR_INTERVAL", "15"))
USE_SYSTEMD = os.environ.get("MRL_DOCTOR_SYSTEMD", "0") == "1"

DEFAULT_TARGETS = {
    "sig_verify": "http://127.0.0.1:8801/health",
    "system_hub": "http://127.0.0.1:9000/health",
    "smartbody_v2": "http://127.0.0.1:8787/health",
}
try:
    TARGETS = json.loads(os.environ.get("MRL_DOCTOR_TARGETS", "")) or DEFAULT_TARGETS
except json.JSONDecodeError:
    TARGETS = DEFAULT_TARGETS

STATUS: dict[str, dict] = {}
HEARTBEATS: dict[str, dict] = {}
_lock = threading.Lock()


def probe(name: str, url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            body = json.loads(resp.read().decode())
            ok = bool(body.get("ok"))
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        return {"ok": False, "error": str(exc), "checked_at": time.time()}
    return {"ok": ok, "body": body, "checked_at": time.time()}


def restart(name: str) -> dict:
    if not USE_SYSTEMD:
        trace_emit("doctor.restart.skipped", {"name": name, "reason": "systemd_disabled"}, layer="L5")
        return {"ok": False, "reason": "systemd_disabled"}
    unit = f"mrl-{name}.service"
    trace_emit("doctor.restart.begin", {"unit": unit}, layer="L5")
    proc = subprocess.run(  # noqa: S603
        ["systemctl", "--user", "restart", unit],
        capture_output=True, text=True, timeout=15,
    )
    ok = proc.returncode == 0
    trace_emit("doctor.restart.done", {"unit": unit, "ok": ok,
                                        "stderr": proc.stderr[-512:]}, layer="L5")
    return {"ok": ok, "unit": unit, "rc": proc.returncode,
            "stderr": proc.stderr[-2048:]}


def monitor_loop() -> None:
    while True:
        for name, url in TARGETS.items():
            result = probe(name, url)
            with _lock:
                prev = STATUS.get(name, {}).get("ok")
                STATUS[name] = result
            if prev is True and not result["ok"]:
                trace_emit("doctor.down_detected", {"name": name, "url": url,
                                                    "error": result.get("error")},
                           layer="L5")
                restart(name)
            elif prev is False and result["ok"]:
                trace_emit("doctor.recovered", {"name": name}, layer="L5")
        time.sleep(INTERVAL)


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
            return self._send(200, {"ok": True, "particle": "doctor",
                                    "origin_signature": ORIGIN_SIGNATURE,
                                    "watching": list(TARGETS.keys()),
                                    "interval": INTERVAL,
                                    "systemd": USE_SYSTEMD})
        if self.path == "/doctor/status":
            with _lock:
                snapshot = {"status": dict(STATUS), "heartbeats": dict(HEARTBEATS)}
            return self._send(200, snapshot)
        return self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        try:
            body = self._read()
        except Exception as exc:
            return self._send(400, {"ok": False, "error": f"bad_json: {exc}"})

        if self.path == "/doctor/heartbeat":
            name = body.get("particle", "unknown")
            with _lock:
                HEARTBEATS[name] = {**body, "received_at": time.time()}
            return self._send(200, {"ok": True})

        if self.path.startswith("/doctor/restart/"):
            name = self.path.rsplit("/", 1)[-1]
            if name not in TARGETS:
                return self._send(404, {"ok": False, "error": f"unknown target: {name}"})
            return self._send(200, restart(name))

        return self._send(404, {"ok": False, "error": "not_found"})


def main() -> None:
    trace_emit("doctor.daemon.start", {"host": HOST, "port": PORT,
                                        "targets": list(TARGETS.keys())}, layer="L5")
    threading.Thread(target=monitor_loop, daemon=True).start()
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[MRL] particle-doctor http://{HOST}:{PORT} — origin={ORIGIN_SIGNATURE}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
