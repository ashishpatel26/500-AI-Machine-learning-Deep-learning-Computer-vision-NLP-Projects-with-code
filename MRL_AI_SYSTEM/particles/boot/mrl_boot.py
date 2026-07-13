"""particle-boot — ordered launcher for the MRL daemons.

origin_signature: MrliouAI
layer: pre-L0 (bootstrap)

Reads boot.manifest.json, launches each particle in order, waits for its health
endpoint, then continues. On failure of a critical particle, rolls back
according to policy. Writes a checkpoint after every successful start.

Usage:
  python3 mrl_boot.py                     # boot everything
  python3 mrl_boot.py --dry-run           # print plan
  python3 mrl_boot.py --stop              # send SIGTERM to tracked pids
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trace_chain import emit as trace_emit  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("boot.manifest.json")
DEFAULT_CHECKPOINT = Path(
    os.environ.get("MRL_BOOT_CHECKPOINT_DIR", "/var/lib/mrl/boot/checkpoints")
)


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def wait_ready(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(0.5)
    return False


def checkpoint(name: str, pid: int, ok: bool) -> None:
    ckpt_dir = DEFAULT_CHECKPOINT
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    (ckpt_dir / f"{name}.json").write_text(json.dumps(
        {"name": name, "pid": pid, "ok": ok, "ts": time.time()},
    ))


def start_particle(entry: dict, root: Path) -> tuple[int | None, bool]:
    script = root / entry["particle"]
    if not script.exists():
        trace_emit("boot.missing", {"name": entry["name"], "path": str(script)}, layer="L0")
        return None, False
    logfile_dir = Path(os.environ.get("MRL_BOOT_LOG_DIR", "/var/log/mrl"))
    logfile_dir.mkdir(parents=True, exist_ok=True)
    log_path = logfile_dir / f"{entry['name']}.log"
    proc = subprocess.Popen(  # noqa: S603 - script paths come from vetted manifest
        [sys.executable, str(script)],
        stdout=log_path.open("a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    trace_emit("boot.started", {"name": entry["name"], "pid": proc.pid,
                                 "log": str(log_path)}, layer="L0")
    ok = wait_ready(entry["wait_for"], timeout=float(entry.get("wait_timeout", 30)))
    checkpoint(entry["name"], proc.pid, ok)
    trace_emit("boot.ready" if ok else "boot.wait_failed",
               {"name": entry["name"], "url": entry["wait_for"], "ok": ok}, layer="L0")
    return proc.pid, ok


def stop_all() -> None:
    ckpt_dir = DEFAULT_CHECKPOINT
    if not ckpt_dir.exists():
        print("no checkpoints — nothing to stop")
        return
    for ckpt in sorted(ckpt_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(ckpt.read_text())
            pid = int(data.get("pid", 0))
            if pid <= 0:
                continue
            os.kill(pid, signal.SIGTERM)
            trace_emit("boot.stopped", {"name": data["name"], "pid": pid}, layer="L0")
            print(f"stopped {data['name']} pid={pid}")
        except (ProcessLookupError, PermissionError, ValueError, OSError) as exc:
            print(f"skip {ckpt.name}: {exc}")


def boot() -> int:
    manifest = load_manifest()
    trace_emit("boot.begin", {"manifest_version": manifest.get("manifest_version")}, layer="L0")
    for entry in manifest["boot_order"]:
        pid, ok = start_particle(entry, ROOT)
        if not ok and entry.get("critical"):
            if manifest.get("rollback_policy") == "fail_stop_on_critical":
                trace_emit("boot.aborted", {"failed": entry["name"]}, layer="L0")
                stop_all()
                return 2
        elif not ok:
            print(f"[warn] non-critical particle failed to become ready: {entry['name']}")
    trace_emit("boot.complete", {}, layer="L0")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="MRL particle-boot")
    parser.add_argument("--dry-run", action="store_true", help="print plan and exit")
    parser.add_argument("--stop", action="store_true", help="terminate tracked pids")
    args = parser.parse_args()

    if args.dry_run:
        manifest = load_manifest()
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0
    if args.stop:
        stop_all()
        return 0
    return boot()


if __name__ == "__main__":
    sys.exit(main())
