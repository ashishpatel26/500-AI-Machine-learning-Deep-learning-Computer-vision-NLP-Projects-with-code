"""particle-trace_chain — cross-layer append-only Merkle trace.

origin_signature: MrliouAI
layer: shared (used by sig_verify, system_hub, doctor, smartbody, boot)

Zero-dependency Python stdlib. Every particle emits events here; a Merkle root
is computed lazily so any subsequent tampering is detectable.

Journal file: /var/lib/mrl/trace/journal.jsonl  (env: MRL_TRACE_JOURNAL)
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from pathlib import Path

DEFAULT_JOURNAL = os.environ.get(
    "MRL_TRACE_JOURNAL", "/var/lib/mrl/trace/journal.jsonl"
)
ORIGIN_SIGNATURE = os.environ.get("MRL_ORIGIN_SIGNATURE", "MrliouAI")

_lock = threading.Lock()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def emit(event: str, payload: dict, *, layer: str = "L?", journal: str | None = None) -> dict:
    """Append an event, return the event record with its chained hash."""
    journal = journal or DEFAULT_JOURNAL
    _ensure_parent(journal)
    with _lock:
        prev = _tail_hash(journal)
        record = {
            "event_id": str(uuid.uuid4()),
            "event": event,
            "layer": layer,
            "payload": payload,
            "prev_hash": prev,
            "emitted_at": now_iso(),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        canonical = json.dumps(record, sort_keys=True, ensure_ascii=False).encode()
        record["chain_hash"] = _sha256(canonical)
        with open(journal, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def _tail_hash(journal: str) -> str:
    if not os.path.exists(journal):
        return "GENESIS"
    with open(journal, "rb") as f:
        try:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                return "GENESIS"
            f.seek(max(0, size - 4096))
            tail = f.read().splitlines()
        except OSError:
            return "GENESIS"
    for line in reversed(tail):
        try:
            return json.loads(line)["chain_hash"]
        except Exception:
            continue
    return "GENESIS"


def merkle_root(journal: str | None = None) -> str:
    """Compute a Merkle root over all chain_hashes in the journal."""
    journal = journal or DEFAULT_JOURNAL
    if not os.path.exists(journal):
        return "EMPTY"
    hashes: list[str] = []
    with open(journal, "r", encoding="utf-8") as f:
        for line in f:
            try:
                hashes.append(json.loads(line)["chain_hash"])
            except Exception:
                continue
    if not hashes:
        return "EMPTY"
    while len(hashes) > 1:
        if len(hashes) % 2 == 1:
            hashes.append(hashes[-1])
        hashes = [
            _sha256((hashes[i] + hashes[i + 1]).encode())
            for i in range(0, len(hashes), 2)
        ]
    return hashes[0]


def verify(journal: str | None = None) -> dict:
    """Walk the chain and confirm every record's chain_hash + prev_hash link."""
    journal = journal or DEFAULT_JOURNAL
    if not os.path.exists(journal):
        return {"ok": True, "records": 0, "root": "EMPTY"}
    prev = "GENESIS"
    count = 0
    with open(journal, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            try:
                rec = json.loads(line)
            except Exception as exc:
                return {"ok": False, "reason": f"line {lineno} parse: {exc}"}
            claimed = rec.pop("chain_hash", None)
            if rec.get("prev_hash") != prev:
                return {"ok": False, "reason": f"line {lineno} broken prev_hash"}
            canonical = json.dumps(rec, sort_keys=True, ensure_ascii=False).encode()
            actual = _sha256(canonical)
            if actual != claimed:
                return {"ok": False, "reason": f"line {lineno} chain_hash mismatch"}
            prev = claimed
            count += 1
    return {"ok": True, "records": count, "root": merkle_root(journal)}


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "emit":
        rec = emit("cli.test", {"argv": sys.argv[2:]}, layer="L?")
        print(json.dumps(rec, ensure_ascii=False, indent=2))
    elif cmd == "root":
        print(merkle_root())
    else:
        print(json.dumps(verify(), ensure_ascii=False, indent=2))
