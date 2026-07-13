// mrl-sig-verify — roundtrip test (real WebCrypto Ed25519)
// Run: node --test test/roundtrip.test.js
//
// Node's crypto.subtle supports Ed25519 as of v18.14 (behind flag) and stable
// in v20+. This test exercises the same crypto path as the Worker without
// needing wrangler or a Cloudflare account.

import { test } from "node:test";
import assert from "node:assert/strict";

const TE = new TextEncoder();

// Match the algorithm-probe from src/index.js
async function algorithm() {
  for (const candidate of ["Ed25519", "NODE-ED25519"]) {
    try {
      await crypto.subtle.generateKey({ name: candidate }, true, ["sign", "verify"]);
      return candidate;
    } catch { /* try next */ }
  }
  throw new Error("no Ed25519 algorithm available");
}

function bytesToB64(bytes) {
  return Buffer.from(bytes).toString("base64");
}
function b64ToBytes(b64) {
  return new Uint8Array(Buffer.from(b64, "base64"));
}

test("Ed25519 roundtrip: sign then verify original", async () => {
  const alg = await algorithm();
  const kp = await crypto.subtle.generateKey({ name: alg }, true, ["sign", "verify"]);
  const msg = TE.encode("MRL_AI_SYSTEM sig-verify roundtrip");
  const sig = new Uint8Array(await crypto.subtle.sign({ name: alg }, kp.privateKey, msg));
  assert.equal(sig.length, 64, "Ed25519 signatures are always 64 bytes");
  const ok = await crypto.subtle.verify({ name: alg }, kp.publicKey, sig, msg);
  assert.equal(ok, true);
});

test("Ed25519 tampered message must fail", async () => {
  const alg = await algorithm();
  const kp = await crypto.subtle.generateKey({ name: alg }, true, ["sign", "verify"]);
  const original = TE.encode("original message");
  const tampered = TE.encode("tampered message");
  const sig = new Uint8Array(await crypto.subtle.sign({ name: alg }, kp.privateKey, original));
  const ok = await crypto.subtle.verify({ name: alg }, kp.publicKey, sig, tampered);
  assert.equal(ok, false);
});

test("Ed25519 wrong public key must fail", async () => {
  const alg = await algorithm();
  const kp1 = await crypto.subtle.generateKey({ name: alg }, true, ["sign", "verify"]);
  const kp2 = await crypto.subtle.generateKey({ name: alg }, true, ["sign", "verify"]);
  const msg = TE.encode("some message");
  const sig = new Uint8Array(await crypto.subtle.sign({ name: alg }, kp1.privateKey, msg));
  const ok = await crypto.subtle.verify({ name: alg }, kp2.publicKey, sig, msg);
  assert.equal(ok, false);
});

test("Public key can be exported to raw and re-imported for verification", async () => {
  const alg = await algorithm();
  const kp = await crypto.subtle.generateKey({ name: alg }, true, ["sign", "verify"]);
  const msg = TE.encode("re-import test");
  const sig = new Uint8Array(await crypto.subtle.sign({ name: alg }, kp.privateKey, msg));

  // Export public key to raw and back — matches Worker /public_key flow
  const raw = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  assert.equal(raw.length, 32, "Ed25519 raw public key is 32 bytes");
  const pubB64 = bytesToB64(raw);
  const reimported = await crypto.subtle.importKey(
    "raw", b64ToBytes(pubB64), { name: alg }, false, ["verify"],
  );
  const ok = await crypto.subtle.verify({ name: alg }, reimported, sig, msg);
  assert.equal(ok, true);
});

test("JWK export/import cycle preserves private key sign capability", async () => {
  const alg = await algorithm();
  const kp = await crypto.subtle.generateKey({ name: alg }, true, ["sign", "verify"]);

  // Matches Worker KV storage flow: export private + public as JWK, re-import, use.
  const privateJwk = await crypto.subtle.exportKey("jwk", kp.privateKey);
  const publicJwk = await crypto.subtle.exportKey("jwk", kp.publicKey);

  const reimportedPrivate = await crypto.subtle.importKey(
    "jwk", privateJwk, { name: alg }, false, ["sign"],
  );
  const reimportedPublic = await crypto.subtle.importKey(
    "jwk", publicJwk, { name: alg }, true, ["verify"],
  );

  const msg = TE.encode("JWK cycle");
  const sig = new Uint8Array(await crypto.subtle.sign({ name: alg }, reimportedPrivate, msg));
  const ok = await crypto.subtle.verify({ name: alg }, reimportedPublic, sig, msg);
  assert.equal(ok, true);
});
