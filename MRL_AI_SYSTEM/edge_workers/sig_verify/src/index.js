// particle-sig-verify — Cloudflare Worker (Ed25519)
// origin_signature: MrliouAI
// layer: L0 (Origin — signature law)
//
// Feature parity with MRL_AI_SYSTEM/particles/sig_verify/mrl_sig_verify.py
// (the local pure-Python daemon), but using Cloudflare Workers WebCrypto.
//
// The keypair is stored in KV (binding: MRL_SIG_KEYS). On first request,
// if no keypair exists, one is generated atomically. The private key
// remains in KV in JWK-private form; the public key is served over
// GET /public_key. Sign/verify calls happen inside the Worker.
//
// Endpoints:
//   GET  /health          — liveness + origin signature
//   GET  /public_key      — public key as base64(raw) + jwk
//   POST /sign            — { message } → { signature_b64 }
//   POST /verify          — { message, signature_b64, public_key_b64? } → { ok }
//
// Compatibility notes:
//   - workerd supports Ed25519 as of ~2024. The algorithm name is "Ed25519".
//   - Older runtimes (pre-2024) may require "NODE-ED25519" — the code below
//     tries "Ed25519" first and falls back once at cold start.
//
// Security notes:
//   - Private key never leaves the Worker's KV; only the public key is exposed
//   - `/sign` requires an X-Sign-Auth header matching env.SIGN_SECRET (secret)
//   - `/verify` is public — anyone can verify (that's what signatures are for)

const ORIGIN_SIGNATURE = "MrliouAI";
const KV_KEY = "mrl_ed25519_v1"; // stable KV key name
const TE = new TextEncoder();

// ── Algorithm probe (once per isolate) ──
let ALG_NAME = null;
async function algorithm() {
  if (ALG_NAME) return ALG_NAME;
  for (const candidate of ["Ed25519", "NODE-ED25519"]) {
    try {
      await crypto.subtle.generateKey({ name: candidate }, true, ["sign", "verify"]);
      ALG_NAME = candidate;
      return candidate;
    } catch { /* try next */ }
  }
  throw new Error("sig_verify: no Ed25519 algorithm available in this runtime");
}

// ── Base64 helpers ──
function bytesToB64(bytes) {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s);
}
function b64ToBytes(b64) {
  const s = atob(b64);
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}

// ── Load or generate keypair (idempotent) ──
async function loadOrGenerate(env) {
  const stored = await env.MRL_SIG_KEYS.get(KV_KEY, { type: "json" });
  const alg = await algorithm();

  if (stored?.privateJwk && stored?.publicJwk) {
    const privateKey = await crypto.subtle.importKey(
      "jwk", stored.privateJwk, { name: alg }, false, ["sign"]
    );
    const publicKey = await crypto.subtle.importKey(
      "jwk", stored.publicJwk, { name: alg }, true, ["verify"]
    );
    return { privateKey, publicKey, publicKeyRawB64: stored.publicKeyRawB64 };
  }

  // Fresh generation (only expected on first ever deploy)
  const kp = await crypto.subtle.generateKey({ name: alg }, true, ["sign", "verify"]);
  const privateJwk = await crypto.subtle.exportKey("jwk", kp.privateKey);
  const publicJwk = await crypto.subtle.exportKey("jwk", kp.publicKey);
  const publicKeyRaw = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const publicKeyRawB64 = bytesToB64(publicKeyRaw);

  // Atomic write; if two isolates race here the second write wins — either is
  // valid because both are freshly-generated pairs. Downstream verification
  // will simply use whichever won.
  await env.MRL_SIG_KEYS.put(KV_KEY, JSON.stringify({
    privateJwk, publicJwk, publicKeyRawB64,
    createdAt: new Date().toISOString(),
    origin_signature: ORIGIN_SIGNATURE,
  }));

  return { privateKey: kp.privateKey, publicKey: kp.publicKey, publicKeyRawB64 };
}

// ── HTTP response helpers ──
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "X-Particle": "sig-verify",
      "X-Layer": "L0",
      "X-Origin-Signature": ORIGIN_SIGNATURE,
    },
  });
}

// ── Route handlers ──
async function handleHealth(env) {
  const alg = await algorithm();
  return jsonResponse({
    ok: true, particle: "sig-verify", layer: "L0",
    origin_signature: ORIGIN_SIGNATURE,
    algorithm: alg,
    routes: ["GET /health", "GET /public_key", "POST /sign", "POST /verify"],
  });
}

async function handlePublicKey(env) {
  const { publicKey, publicKeyRawB64 } = await loadOrGenerate(env);
  const publicJwk = await crypto.subtle.exportKey("jwk", publicKey);
  return jsonResponse({
    public_key_b64: publicKeyRawB64,
    public_key_jwk: publicJwk,
    algorithm: await algorithm(),
    origin_signature: ORIGIN_SIGNATURE,
  });
}

async function handleSign(request, env) {
  const authHeader = request.headers.get("X-Sign-Auth");
  if (!env.SIGN_SECRET) {
    return jsonResponse({ ok: false, error: "SIGN_SECRET not configured" }, 500);
  }
  if (authHeader !== env.SIGN_SECRET) {
    return jsonResponse({ ok: false, error: "unauthorized" }, 401);
  }

  let body;
  try { body = await request.json(); }
  catch { return jsonResponse({ ok: false, error: "bad_json" }, 400); }

  const message = body.message;
  const msgBytes = typeof message === "string"
    ? TE.encode(message)
    : TE.encode(JSON.stringify(message ?? "", Object.keys(message ?? {}).sort()));

  const { privateKey } = await loadOrGenerate(env);
  const sig = new Uint8Array(await crypto.subtle.sign(
    { name: await algorithm() }, privateKey, msgBytes,
  ));
  return jsonResponse({ ok: true, signature_b64: bytesToB64(sig) });
}

async function handleVerify(request, env) {
  let body;
  try { body = await request.json(); }
  catch { return jsonResponse({ ok: false, error: "bad_json" }, 400); }

  const { message, signature_b64, public_key_b64 } = body;
  if (!signature_b64) return jsonResponse({ ok: false, error: "missing signature" }, 400);

  const msgBytes = typeof message === "string"
    ? TE.encode(message)
    : TE.encode(JSON.stringify(message ?? "", Object.keys(message ?? {}).sort()));

  let sigBytes;
  try { sigBytes = b64ToBytes(signature_b64); }
  catch { return jsonResponse({ ok: false, error: "bad_signature_b64" }, 400); }

  const alg = await algorithm();
  let publicKey;
  if (public_key_b64) {
    try {
      publicKey = await crypto.subtle.importKey(
        "raw", b64ToBytes(public_key_b64), { name: alg }, false, ["verify"],
      );
    } catch (e) {
      return jsonResponse({ ok: false, error: `bad_public_key: ${e.message}` }, 400);
    }
  } else {
    publicKey = (await loadOrGenerate(env)).publicKey;
  }

  const ok = await crypto.subtle.verify(
    { name: alg }, publicKey, sigBytes, msgBytes,
  );
  return jsonResponse({ ok });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    try {
      if (path === "/health" && request.method === "GET") return handleHealth(env);
      if (path === "/public_key" && request.method === "GET") return handlePublicKey(env);
      if (path === "/sign" && request.method === "POST") return handleSign(request, env);
      if (path === "/verify" && request.method === "POST") return handleVerify(request, env);
      return jsonResponse({
        ok: false, error: "not_found", path,
        available: ["GET /health", "GET /public_key", "POST /sign", "POST /verify"],
      }, 404);
    } catch (e) {
      return jsonResponse({ ok: false, error: "internal_error", message: e.message }, 500);
    }
  },
};
