"""particle-sig-verify — L0 signature law daemon.

origin_signature: MrliouAI
layer: L0 (Origin — signature law)

Ed25519-backed sign / verify daemon. Zero external deps: uses stdlib
`hashlib`, `hmac`, `secrets`, and a pure-Python Ed25519 reference impl
(inlined) so it runs on any Python 3.10+ host without cryptography.

Bind:
  MRL_SIG_HOST=127.0.0.1
  MRL_SIG_PORT=8801
  MRL_SIG_KEYDIR=/etc/mrl/keys      # ed25519 private/public
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trace_chain import emit as trace_emit  # noqa: E402

ORIGIN_SIGNATURE = "MrliouAI"
HOST = os.environ.get("MRL_SIG_HOST", "127.0.0.1")
PORT = int(os.environ.get("MRL_SIG_PORT", "8801"))
KEYDIR = Path(os.environ.get("MRL_SIG_KEYDIR", "/etc/mrl/keys"))

# --- Pure-Python Ed25519 (RFC 8032 reference, stdlib-only) ---
_p = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_d = -121665 * pow(121666, -1, _p) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _sha512(m: bytes) -> bytes:
    return hashlib.sha512(m).digest()


def _bit(h: bytes, i: int) -> int:
    return (h[i // 8] >> (i % 8)) & 1


def _encode_point(P):
    x, y = P
    bits = [(y >> i) & 1 for i in range(255)] + [x & 1]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(32))


def _xrecover(y):
    xx = (y * y - 1) * pow(_d * y * y + 1, -1, _p) % _p
    x = pow(xx, (_p + 3) // 8, _p)
    if (x * x - xx) % _p != 0:
        x = (x * _I) % _p
    if x % 2 != 0:
        x = _p - x
    return x


_By = 4 * pow(5, -1, _p) % _p
_Bx = _xrecover(_By)
_B = (_Bx % _p, _By % _p)


def _edwards(P, Q):
    x1, y1 = P
    x2, y2 = Q
    x3 = (x1 * y2 + x2 * y1) * pow(1 + _d * x1 * x2 * y1 * y2, -1, _p) % _p
    y3 = (y1 * y2 + x1 * x2) * pow(1 - _d * x1 * x2 * y1 * y2, -1, _p) % _p
    return (x3, y3)


def _scalarmult(P, e):
    if e == 0:
        return (0, 1)
    Q = _scalarmult(P, e // 2)
    Q = _edwards(Q, Q)
    if e & 1:
        Q = _edwards(Q, P)
    return Q


def _hint(m: bytes) -> int:
    return int.from_bytes(_sha512(m), "little")


def keypair() -> tuple[bytes, bytes]:
    sk = secrets.token_bytes(32)
    h = bytearray(_sha512(sk))
    h[0] &= 248
    h[31] &= 127
    h[31] |= 64
    a = int.from_bytes(bytes(h[:32]), "little")
    A = _scalarmult(_B, a)
    pk = _encode_point(A)
    return sk, pk


def sign(sk: bytes, msg: bytes) -> bytes:
    h = _sha512(sk)
    a = int.from_bytes(bytes(bytearray(h)[:32])[:32], "little")
    a_bytes = bytearray(a.to_bytes(32, "little"))
    a_bytes[0] &= 248
    a_bytes[31] &= 127
    a_bytes[31] |= 64
    a = int.from_bytes(bytes(a_bytes), "little")
    A_enc = _encode_point(_scalarmult(_B, a))
    r = _hint(h[32:64] + msg) % _L
    R = _scalarmult(_B, r)
    R_enc = _encode_point(R)
    k = _hint(R_enc + A_enc + msg) % _L
    S = (r + k * a) % _L
    return R_enc + S.to_bytes(32, "little")


def _decode_point(s: bytes):
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    x = _xrecover(y)
    if x & 1 != _bit(s, 255):
        x = _p - x
    return (x, y)


def verify_sig(pk: bytes, msg: bytes, sig: bytes) -> bool:
    if len(sig) != 64 or len(pk) != 32:
        return False
    try:
        R = _decode_point(sig[:32])
        A = _decode_point(pk)
    except Exception:
        return False
    S = int.from_bytes(sig[32:], "little")
    k = _hint(sig[:32] + pk + msg) % _L
    left = _scalarmult(_B, S)
    right = _edwards(R, _scalarmult(A, k))
    return left == right


# --- Key management ---
def _load_or_gen() -> tuple[bytes, bytes]:
    KEYDIR.mkdir(parents=True, exist_ok=True)
    sk_path, pk_path = KEYDIR / "mrl_ed25519.sk", KEYDIR / "mrl_ed25519.pk"
    if sk_path.exists() and pk_path.exists():
        return sk_path.read_bytes(), pk_path.read_bytes()
    sk, pk = keypair()
    sk_path.write_bytes(sk)
    pk_path.write_bytes(pk)
    try:
        os.chmod(sk_path, 0o600)
    except OSError:
        pass
    trace_emit("sig.keys.generated", {"pk_b64": base64.b64encode(pk).decode()}, layer="L0")
    return sk, pk


SK, PK = _load_or_gen()


# --- HTTP handler ---
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quiet
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
            return self._send(200, {"ok": True, "particle": "sig_verify",
                                    "origin_signature": ORIGIN_SIGNATURE,
                                    "public_key_b64": base64.b64encode(PK).decode()})
        if self.path == "/public_key":
            return self._send(200, {"public_key_b64": base64.b64encode(PK).decode()})
        return self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        try:
            body = self._read()
        except Exception as exc:
            return self._send(400, {"ok": False, "error": f"bad_json: {exc}"})

        if self.path == "/sign":
            msg = body.get("message", "")
            if not isinstance(msg, str):
                msg = json.dumps(msg, sort_keys=True, ensure_ascii=False)
            sig = sign(SK, msg.encode())
            trace_emit("sig.signed", {"len": len(msg)}, layer="L0")
            return self._send(200, {"ok": True, "signature_b64": base64.b64encode(sig).decode()})

        if self.path == "/verify":
            msg = body.get("message", "")
            sig_b64 = body.get("signature_b64", "")
            pk_b64 = body.get("public_key_b64")
            if not isinstance(msg, str):
                msg = json.dumps(msg, sort_keys=True, ensure_ascii=False)
            try:
                sig = base64.b64decode(sig_b64)
                pk = base64.b64decode(pk_b64) if pk_b64 else PK
            except Exception as exc:
                return self._send(400, {"ok": False, "error": f"bad_b64: {exc}"})
            ok = verify_sig(pk, msg.encode(), sig)
            trace_emit("sig.verified", {"ok": ok}, layer="L0")
            return self._send(200, {"ok": ok})

        return self._send(404, {"ok": False, "error": "not_found"})


def main() -> None:
    trace_emit("sig.daemon.start", {"host": HOST, "port": PORT}, layer="L0")
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"[MRL] particle-sig-verify http://{HOST}:{PORT} — origin={ORIGIN_SIGNATURE}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
