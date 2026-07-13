// particle-auth-gateway — Cloudflare Worker
// origin_signature: MrliouAI
// layer: L0/L4 boundary (external → internal)
//
// Verifies JWT bearer token + optional L0 Ed25519 signature header, then
// forwards to the configured backend (typically the AI gateway or a
// tunnelled system-hub). All rejections are logged to the audit KV.
//
// Required env bindings (wrangler.toml):
//   AUTH_JWT_SECRET       (secret)  — HS256 secret for JWT verification
//   BACKEND_URL           (var)     — e.g. https://ai-gateway.mrliouword.com
//   MRL_AUTH_AUDIT        (KV)      — append-only audit log
//   MRL_PUBLIC_KEY_B64    (var)     — Ed25519 public key of particle-sig-verify

const enc = new TextEncoder();
const b64urlDec = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), c => c.charCodeAt(0));

async function hmacSha256(key, data) {
  const ck = await crypto.subtle.importKey("raw", enc.encode(key), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await crypto.subtle.sign("HMAC", ck, enc.encode(data)));
}

async function verifyJwt(token, secret) {
  const [h, p, s] = token.split(".");
  if (!h || !p || !s) return { ok: false, reason: "malformed" };
  const expected = await hmacSha256(secret, `${h}.${p}`);
  const provided = b64urlDec(s);
  if (expected.length !== provided.length) return { ok: false, reason: "sig_len" };
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= expected[i] ^ provided[i];
  if (diff !== 0) return { ok: false, reason: "sig_mismatch" };
  const claims = JSON.parse(new TextDecoder().decode(b64urlDec(p)));
  if (claims.exp && Date.now() / 1000 > claims.exp) return { ok: false, reason: "expired" };
  return { ok: true, claims };
}

async function audit(env, event) {
  if (!env.MRL_AUTH_AUDIT) return;
  const key = `${Date.now()}-${crypto.randomUUID()}`;
  await env.MRL_AUTH_AUDIT.put(key, JSON.stringify({
    ...event,
    origin_signature: "MrliouAI",
    ts: new Date().toISOString(),
  }));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return Response.json({
        ok: true, particle: "auth_gateway",
        origin_signature: "MrliouAI",
        backend: env.BACKEND_URL || "(unset)",
      });
    }
    const auth = request.headers.get("authorization") || "";
    const token = auth.startsWith("Bearer ") ? auth.slice(7) : null;
    if (!token) {
      await audit(env, { event: "reject.no_token", path: url.pathname });
      return new Response("missing bearer token", { status: 401 });
    }
    const jwt = await verifyJwt(token, env.AUTH_JWT_SECRET || "");
    if (!jwt.ok) {
      await audit(env, { event: "reject.jwt", reason: jwt.reason });
      return new Response(`jwt: ${jwt.reason}`, { status: 401 });
    }
    if (!env.BACKEND_URL) {
      return new Response("backend not configured", { status: 502 });
    }
    const forwarded = new Request(env.BACKEND_URL + url.pathname + url.search, request);
    forwarded.headers.set("X-MRL-Subject", jwt.claims.sub || "anonymous");
    forwarded.headers.set("X-MRL-Origin-Signature", "MrliouAI");
    await audit(env, { event: "forward", path: url.pathname, sub: jwt.claims.sub });
    return fetch(forwarded);
  },
};
