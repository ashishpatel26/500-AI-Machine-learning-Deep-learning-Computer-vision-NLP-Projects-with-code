"""particle-smartbody-v2 — the body daemon (sense / act / reflex).

origin_signature: MrliouAI
layer: L4 World / L7 Execution

Upgrades v1 (which was a systemd-service shell) with real endpoints:

  Sense:
    GET  /status/system   — cpu/load/mem/disk from /proc + os.statvfs
    GET  /status/network  — /proc/net/dev counters + reachable hosts
    GET  /status/self     — pid/uptime/version

  Act:
    POST /act/http        — call an outbound URL (whitelist enforced)
    POST /act/exec        — run a whitelisted script (env MRL_ACT_WHITELIST)

  Reflex:
    POST /reflex/rules    — evaluate local rules; skip brain if a rule hits

Env:
  MRL_BODY_HOST=127.0.0.1
  MRL_BODY_PORT=8787
  MRL_BODY_HUB=http://127.0.0.1:9000
  MRL_BODY_DOCTOR=http://127.0.0.1:8788
  MRL_ACT_WHITELIST=/etc/mrl/act_whitelist.txt
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
HOST = os.environ.get("MRL_BODY_HOST", "127.0.0.1")
PORT = int(os.environ.get("MRL_BODY_PORT", "8787"))
HUB_URL = os.environ.get("MRL_BODY_HUB", "http://127.0.0.1:9000")
DOCTOR_URL = os.environ.get("MRL_BODY_DOCTOR", "http://127.0.0.1:8788")
ACT_WHITELIST = Path(os.environ.get("MRL_ACT_WHITELIST", "/etc/mrl/act_whitelist.txt"))
START_TIME = time.time()

REFLEX_RULES = [
    {"match": "ping", "response": {"reflex": "pong", "brain": False}},
    {"match": "status", "response": {"reflex": "self_status", "brain": False}},
]


def sense_system() -> dict:
    out: dict = {"origin_signature": ORIGIN_SIGNATURE}
    try:
        with open("/proc/loadavg") as f:
            out["loadavg"] = f.read().strip().split()[:3]
    except OSError:
        out["loadavg"] = None
    try:
        with open("/proc/meminfo") as f:
            mem = {}
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    mem[k.strip()] = v.strip()
                if len(mem) >= 5:
                    break
            out["meminfo"] = {k: mem.get(k) for k in
                              ("MemTotal", "MemAvailable", "MemFree", "Buffers", "Cached")}
    except OSError:
        out["meminfo"] = None
    try:
        st = os.statvfs("/")
        out["disk"] = {
            "total_gb": round(st.f_blocks * st.f_frsize / 1e9, 2),
            "free_gb": round(st.f_bavail * st.f_frsize / 1e9, 2),
        }
    except OSError:
        out["disk"] = None
    return out


def sense_network() -> dict:
    counters: dict[str, dict[str, int]] = {}
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                parts = line.split()
                if len(parts) < 10:
                    continue
                iface = parts[0].rstrip(":")
                counters[iface] = {"rx_bytes": int(parts[1]), "tx_bytes": int(parts[9])}
    except OSError:
        pass
    return {"interfaces": counters, "origin_signature": ORIGIN_SIGNATURE}


def sense_self() -> dict:
    return {
        "pid": os.getpid(),
        "uptime_sec": int(time.time() - START_TIME),
        "version": "v2.0.0",
        "hub": HUB_URL,
        "doctor": DOCTOR_URL,
        "origin_signature": ORIGIN_SIGNATURE,
    }


# --- act: whitelist enforcement ---
def _load_whitelist() -> list[str]:
    if not ACT_WHITELIST.exists():
        return []
    return [line.strip() for line in ACT_WHITELIST.read_text().splitlines()
            if line.strip() and not line.startswith("#")]


def act_http(url: str, method: str = "GET", body: dict | None = None,
             timeout: float = 5.0) -> dict:
    wl = _load_whitelist()
    if wl and not any(url.startswith(prefix) for prefix in wl):
        raise PermissionError(f"url not whitelisted: {url}")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, method=method, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            return {"status": resp.status, "body": payload}
    except urllib.error.URLError as exc:
        return {"status": None, "error": str(exc)}


def act_exec(script: str, args: list[str], timeout: float = 30.0) -> dict:
    wl = _load_whitelist()
    if wl and script not in wl:
        raise PermissionError(f"script not whitelisted: {script}")
    proc = subprocess.run(  # noqa: S603 - whitelist enforced above
        [script, *args], capture_output=True, timeout=timeout, text=True,
    )
    return {"rc": proc.returncode, "stdout": proc.stdout[-4096:],
            "stderr": proc.stderr[-4096:]}


# --- reflex ---
def evaluate_reflex(signal: str) -> dict | None:
    for rule in REFLEX_RULES:
        if rule["match"] in signal.lower():
            trace_emit("body.reflex.hit", {"signal": signal, "rule": rule["match"]}, layer="L4")
            return rule["response"]
    return None


# --- heartbeat to doctor ---
def heartbeat_loop() -> None:
    while True:
        try:
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{DOCTOR_URL}/doctor/heartbeat",
                    data=json.dumps({"particle": "smartbody_v2", "pid": os.getpid(),
                                     "uptime": int(time.time() - START_TIME)}).encode(),
                    headers={"Content-Type": "application/json"},
                ),
                timeout=2.0,
            ).read()
        except Exception:
            pass  # doctor down is OK, we're still alive
        time.sleep(15)


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
            return self._send(200, {"ok": True, "particle": "smartbody_v2",
                                    "origin_signature": ORIGIN_SIGNATURE, **sense_self()})
        if self.path == "/status/system":
            return self._send(200, sense_system())
        if self.path == "/status/network":
            return self._send(200, sense_network())
        if self.path == "/status/self":
            return self._send(200, sense_self())
        return self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        try:
            body = self._read()
        except Exception as exc:
            return self._send(400, {"ok": False, "error": f"bad_json: {exc}"})

        if self.path == "/act/http":
            try:
                out = act_http(body["url"], body.get("method", "GET"),
                               body.get("body"), float(body.get("timeout", 5)))
            except PermissionError as exc:
                return self._send(403, {"ok": False, "error": str(exc)})
            except Exception as exc:
                return self._send(500, {"ok": False, "error": str(exc)})
            trace_emit("body.act.http", {"url": body.get("url")}, layer="L7")
            return self._send(200, {"ok": True, **out})

        if self.path == "/act/exec":
            try:
                out = act_exec(body["script"], body.get("args", []),
                               float(body.get("timeout", 30)))
            except PermissionError as exc:
                return self._send(403, {"ok": False, "error": str(exc)})
            except subprocess.TimeoutExpired:
                return self._send(504, {"ok": False, "error": "timeout"})
            trace_emit("body.act.exec", {"script": body.get("script")}, layer="L7")
            return self._send(200, {"ok": True, **out})

        if self.path == "/reflex/rules":
            hit = evaluate_reflex(body.get("signal", ""))
            return self._send(200, {"ok": True, "hit": hit is not None,
                                    "response": hit,
                                    "delegated_to_brain": hit is None})

        return self._send(404, {"ok": False, "error": "not_found"})


def main() -> None:
    trace_emit("body.daemon.start", {"host": HOST, "port": PORT}, layer="L4")
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[MRL] particle-smartbody-v2 http://{HOST}:{PORT} — origin={ORIGIN_SIGNATURE}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
