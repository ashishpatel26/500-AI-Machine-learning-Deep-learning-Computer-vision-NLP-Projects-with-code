# P0 Patch — `particle-auth-gateway` · XOR → PBKDF2 + AES-GCM

`origin_signature: MrLiouWord`
`target_worker: particle-auth-gateway` (Cloudflare)
`current_version: v1.1.0` (deployed 2026-03-14)
`fix_type: cryptographic upgrade with in-place migration`
`estimated_effort: 2-3 hours (dev + testing + phased deploy)`

## Problem

Current `加密()` / `解密()` use XOR + base64:

```js
function 加密(令牌, 主鑰匙) {
  const 混合 = 令牌.split("").map((字, i) =>
    String.fromCharCode(字.charCodeAt(0) ^ 主鑰匙.charCodeAt(i % 主鑰匙.length))
  ).join("");
  return btoa(混合);
}
```

Master key auth uses `SHA-256(master key)` stored in KV.

### Threat model (refined per PR #2 review)

Not universally broken — but breakable under any one of:
1. **Keystream reuse**: same master key encrypting multiple tokens of length > `masterKey.length` → attackers can XOR two ciphertexts to cancel the keystream, revealing `plaintext_a XOR plaintext_b`
2. **Known plaintext**: attacker knows any token has a well-known prefix (`ghp_`, `xoxb-`, `ntn_`, `AIza…`) → derives keystream bytes at those positions → recovers other tokens partially or fully
3. **Low-entropy master key**: user-supplied password → dictionary / rainbow-table attack on `SHA-256(masterKey)` in KV

This Worker stores GitHub / Notion / Cloudflare / Google / Vercel tokens for `/mcp/proxy`. All three conditions are plausible in practice.

## Fix — versioned envelope with real KDF and real AEAD

**Design principles:**
- Format is self-describing (version byte) so old and new envelopes coexist during migration
- Random salt **per vault** — not global, not per-token — because salt is cheap and rotation-safe
- PBKDF2-SHA256, 600k iterations (as of 2026) — OWASP baseline
- AES-256-GCM — authenticated encryption, prevents ciphertext malleability
- Master key **auth** upgrades to PBKDF2 too (so KV dump no longer allows offline brute-force of SHA-256)

### Vault schema change

```diff
 // In KV `vault_data`:
 {
   "令牌們": [...],
-  "主鑰匙雜湊": "<sha256 hex of masterKey>",
+  "主鑰匙雜湊": "<PBKDF2-SHA256(masterKey, authSalt, 600000)>",
+  "authSalt":    "<16 random bytes, base64>",
+  "vaultSalt":   "<16 random bytes, base64, used for token encryption keys>",
+  "envelopeVersion": 2,
   "建立時間": "…",
   "最後存取": "…",
   "源": "MrLiouWord"
 }
```

Envelope for each stored token becomes:

```
[ 1 byte version = 0x02 ] [ 12 bytes iv ] [ ciphertext + 16 bytes GCM tag ]  → base64
```

Version `0x00-0x01` reserved for legacy (XOR/base64) content — during migration these still decrypt via the old function.

### Replace `加密()` / `解密()` / `雜湊()`

```js
// ============ Cryptographic primitives ============
const TE = new TextEncoder();
const TD = new TextDecoder();

async function _pbkdf2(masterKey, salt, iterations = 600_000, bits = 256) {
  const material = await crypto.subtle.importKey(
    "raw", TE.encode(masterKey), "PBKDF2", false, ["deriveBits", "deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations, hash: "SHA-256" },
    material,
    { name: "AES-GCM", length: bits },
    false,
    ["encrypt", "decrypt"]
  );
}

async function _pbkdf2Digest(masterKey, salt, iterations = 600_000) {
  const material = await crypto.subtle.importKey(
    "raw", TE.encode(masterKey), "PBKDF2", false, ["deriveBits"]
  );
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations, hash: "SHA-256" },
    material, 256
  );
  return btoa(String.fromCharCode(...new Uint8Array(bits)));
}

// v2 encrypt: envelope = [0x02 | iv(12) | ct+tag]
async function 加密(token, masterKey, vaultSalt) {
  const key = await _pbkdf2(masterKey, vaultSalt);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = new Uint8Array(await crypto.subtle.encrypt(
    { name: "AES-GCM", iv }, key, TE.encode(token)
  ));
  const envelope = new Uint8Array(1 + 12 + ct.length);
  envelope[0] = 0x02;
  envelope.set(iv, 1);
  envelope.set(ct, 13);
  return btoa(String.fromCharCode(...envelope));
}

// decrypt handles both v2 (new) and legacy v0/v1 (XOR/base64) transparently
async function 解密(envelopeB64, masterKey, vaultSalt) {
  const bin = Uint8Array.from(atob(envelopeB64), c => c.charCodeAt(0));

  // v2 envelope: PBKDF2 + AES-GCM
  if (bin[0] === 0x02) {
    const key = await _pbkdf2(masterKey, vaultSalt);
    const iv = bin.slice(1, 13);
    const ct = bin.slice(13);
    const pt = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv }, key, ct
    );
    return TD.decode(pt);
  }

  // Legacy fallback: raw XOR+base64 (no version prefix)
  const mixed = TD.decode(bin);
  return mixed.split("").map((c, i) =>
    String.fromCharCode(c.charCodeAt(0) ^ masterKey.charCodeAt(i % masterKey.length))
  ).join("");
}

// Auth: PBKDF2 digest for master-key verification
async function 雜湊(masterKey, authSalt) {
  return _pbkdf2Digest(masterKey, authSalt);
}
```

### `/init` — generate salts on first initialization

```diff
 if (路徑 === "/init" && request.method === "POST") {
   const 內容 = await request.json();
-  if (!內容.masterKey || 內容.masterKey.length < 16) {
+  if (!內容.masterKey || 內容.masterKey.length < 16) {
     return new Response(JSON.stringify({ 錯誤: "主鑰匙至少需要16個字符", 源 }), { status: 400, headers: 回應頭 });
   }
+  // TODO(P1): also enforce zxcvbn score >= 3 or reject common passwords
   const 現有 = await env.PARTICLE_AUTH_VAULT.get("vault_data");
   if (現有) { return new Response(JSON.stringify({ 錯誤: "已初始化，如需重置請先撤銷", 源 }), { status: 409, headers: 回應頭 }); }
+
+  const authSalt = crypto.getRandomValues(new Uint8Array(16));
+  const vaultSalt = crypto.getRandomValues(new Uint8Array(16));
+
   const 保險庫資料 = {
     令牌們: [],
-    主鑰匙雜湊: await 雜湊(內容.masterKey),
+    主鑰匙雜湊: await 雜湊(內容.masterKey, authSalt),
+    authSalt: btoa(String.fromCharCode(...authSalt)),
+    vaultSalt: btoa(String.fromCharCode(...vaultSalt)),
+    envelopeVersion: 2,
     建立時間: new Date().toISOString(),
     最後存取: new Date().toISOString(),
     源
   };
   await env.PARTICLE_AUTH_VAULT.put("vault_data", JSON.stringify(保險庫資料));
```

### `驗證()` — verify against PBKDF2 digest (old vaults still work)

```diff
 async function 驗證() {
   if (!主鑰匙) return null;
   const 原始 = await env.PARTICLE_AUTH_VAULT.get("vault_data");
   if (!原始) return null;
   const 保險庫資料 = JSON.parse(原始);
-  if (await 雜湊(主鑰匙) !== 保險庫資料.主鑰匙雜湊) return null;
+  const authSalt = 保險庫資料.authSalt
+    ? Uint8Array.from(atob(保險庫資料.authSalt), c => c.charCodeAt(0))
+    : null;
+  const expected = authSalt
+    ? await _pbkdf2Digest(主鑰匙, authSalt)   // new PBKDF2 vault
+    : await sha256Hex(主鑰匙);                // legacy SHA-256 vault (see below)
+  if (expected !== 保險庫資料.主鑰匙雜湊) return null;
   保險庫資料.最後存取 = new Date().toISOString();
   await env.PARTICLE_AUTH_VAULT.put("vault_data", JSON.stringify(保險庫資料));
   return 保險庫資料;
 }

+// keep legacy SHA-256 helper for pre-migration vaults
+async function sha256Hex(input) {
+  const buf = TE.encode(input);
+  const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", buf));
+  return Array.from(hash).map(b => b.toString(16).padStart(2, "0")).join("");
+}
```

### `/tokens/batch` — write with new envelope

Pass `vaultSalt` (or the fallback path for legacy vaults) into `加密()`:

```diff
 if (路徑 === "/tokens/batch" && request.method === "POST") {
   const 保險庫資料 = await 驗證();
   if (!保險庫資料) { return new Response(JSON.stringify({ 錯誤: "未授權", 源 }), { status: 401, headers: 回應頭 }); }
+  const vaultSalt = 保險庫資料.vaultSalt
+    ? Uint8Array.from(atob(保險庫資料.vaultSalt), c => c.charCodeAt(0))
+    : null;   // legacy vault — will be migrated on first read
   const 內容 = await request.json();
   for (const 令牌資料 of 內容.tokens) {
-    const 加密令牌 = 加密(令牌資料.token, 主鑰匙);
+    const 加密令牌 = vaultSalt
+      ? await 加密(令牌資料.token, 主鑰匙, vaultSalt)   // v2 envelope
+      : legacyEncrypt(令牌資料.token, 主鑰匙);           // legacy XOR (writes will pause until vault is migrated — see step 4)
     ...
   }
 }
```

### `/mcp/proxy` — decrypt with format auto-detection

The `解密()` function above already handles both v2 and legacy in one call, so `/mcp/proxy` just passes `vaultSalt`:

```diff
- const 解密令牌 = 解密(平台令牌資料.令牌, 主鑰匙);
+ const vaultSalt = 保險庫資料.vaultSalt
+   ? Uint8Array.from(atob(保險庫資料.vaultSalt), c => c.charCodeAt(0))
+   : new Uint8Array(0);  // ignored by legacy fallback
+ const 解密令牌 = await 解密(平台令牌資料.令牌, 主鑰匙, vaultSalt);
```

## Rate limiting for `/mcp/proxy` (companion P0)

KV-based rate limit is **best-effort only** (eventually consistent — parallel requests can breach). For a strict per-subject quota, prefer:

- **Cloudflare Rate Limiting rules** — apply at the route, no code change, atomic
- **Durable Objects** — a `RateLimitDO` per subject, `alarm()`-based window reset

Sample Durable Object skeleton (put in a new module):

```js
export class RateLimitDO {
  constructor(state) { this.state = state; this.count = 0; this.windowStart = 0; }
  async fetch(request) {
    const now = Date.now();
    if (now - this.windowStart > 60_000) { this.count = 0; this.windowStart = now; }
    this.count++;
    return new Response(JSON.stringify({ allowed: this.count <= 60, count: this.count }));
  }
}
```

Then in `wrangler.toml`:
```toml
[[durable_objects.bindings]]
name = "RATE_LIMIT"
class_name = "RateLimitDO"

[[migrations]]
tag = "v1"
new_sqlite_classes = ["RateLimitDO"]
```

## Phased migration plan

### Phase A — Deploy dual-format Worker (backwards-compatible)

Ship the diffs above. All existing vaults continue to work via the legacy fallback in `解密()`; new tokens written go into v2 envelope.

Deploy:
```bash
wrangler deploy --name particle-auth-gateway
```

Verify:
```bash
# Old master key still authenticates:
curl -X POST https://particle-auth-gateway.z814241.workers.dev/status \
  -H "X-Master-Key: $OLD_MASTER_KEY" | jq
# Expect: 200 with 已初始化: true
```

### Phase B — Migrate the vault to v2 in-place

Add a one-shot `/migrate` endpoint (POST, master-key-gated) that:
1. Reads current vault
2. For each token: decrypt with legacy XOR (using master key)
3. Generate new `authSalt` and `vaultSalt` if absent
4. Re-encrypt every token with v2 envelope
5. Recompute `主鑰匙雜湊` with PBKDF2
6. Overwrite KV atomically, set `envelopeVersion: 2`

```js
if (路徑 === "/migrate" && request.method === "POST") {
  const 保險庫資料 = await 驗證();
  if (!保險庫資料) return new Response(JSON.stringify({ 錯誤: "未授權" }), { status: 401, headers: 回應頭 });
  if (保險庫資料.envelopeVersion === 2) return new Response(JSON.stringify({ ok: true, 訊息: "already migrated" }), { headers: 回應頭 });

  const authSalt = crypto.getRandomValues(new Uint8Array(16));
  const vaultSalt = crypto.getRandomValues(new Uint8Array(16));

  const newTokens = [];
  for (const t of 保險庫資料.令牌們) {
    const plaintext = await 解密(t.令牌, 主鑰匙, new Uint8Array(0));  // legacy path
    const 加密令牌 = await 加密(plaintext, 主鑰匙, vaultSalt);
    newTokens.push({ ...t, 令牌: 加密令牌 });
  }

  const migrated = {
    ...保險庫資料,
    令牌們: newTokens,
    主鑰匙雜湊: await _pbkdf2Digest(主鑰匙, authSalt),
    authSalt: btoa(String.fromCharCode(...authSalt)),
    vaultSalt: btoa(String.fromCharCode(...vaultSalt)),
    envelopeVersion: 2,
    migrated_at: new Date().toISOString(),
  };
  await env.PARTICLE_AUTH_VAULT.put("vault_data", JSON.stringify(migrated));
  return new Response(JSON.stringify({ ok: true, migrated_tokens: newTokens.length }), { headers: 回應頭 });
}
```

Run:
```bash
curl -X POST -H "X-Master-Key: $MASTER_KEY" \
  https://particle-auth-gateway.z814241.workers.dev/migrate | jq
```

### Phase C — Remove legacy code paths

Once you've confirmed `envelopeVersion: 2` in KV and all `/mcp/proxy` calls succeed, delete:
- `legacyEncrypt` function
- The legacy fallback branch in `解密()`
- The SHA-256 fallback in `驗證()`
- The `/migrate` endpoint itself

Deploy the cleaned version.

## Verification checklist

- [ ] Phase A deploy: existing tokens decrypt successfully (`/mcp/proxy` still works)
- [ ] `/migrate` returns `{ ok: true, migrated_tokens: N }` where N matches vault count
- [ ] `/status` shows `envelopeVersion: 2`
- [ ] KV `vault_data` sample envelope starts with `0x02` byte (base64 prefix `Ag==` at decode) — no bare XOR content anymore
- [ ] Phase C deploy: XOR helpers are gone from source
- [ ] Rate limit path (`/mcp/proxy`) either has Durable Object binding or CF Rate Limiting rule attached

## Notes

- **Do not increase PBKDF2 iterations casually**: 600k is the OWASP-current baseline; raising too high impacts every auth call. Revisit annually.
- **The migration is idempotent**: running `/migrate` twice is safe — it early-returns when `envelopeVersion === 2`.
- **Rollback**: keep Phase A deploy pinned as a `wrangler versions` snapshot; Phase B is fully reversible until Phase C removes the legacy path.
