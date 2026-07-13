# P0 Patch — `shengai-isp` · Move secrets to env + fix auth backdoor

`origin_signature: MrLiouWord`
`target_worker: shengai-isp` (Cloudflare)
`current_deploy: v3.1` (per source's HTML title)
`fix_type: config + one-liner auth fix`
`estimated_effort: 45 minutes + rotation + verification`

## Provenance

This patch closes the last unaddressed P0 from the CareOS 復盤品管報告 (2026-03-11) §4.1:

> shengai-isp Worker 的 ANTHROPIC_API_KEY 硬編碼在程式碼中
> → 建議：改用 wrangler secret put ANTHROPIC_API_KEY

While fetching the source to write this patch, **two additional secrets were found hardcoded in the same file** — they were not surfaced in the original CareOS report. This patch documents all three so a single `wrangler deploy` closes them together.

## Problem — three hardcoded secrets + one auth bypass

### 1. `ANTHROPIC_API_KEY` (module top, ~line 1) — **P0, CareOS-listed**

```js
const ANTHROPIC_API_KEY = "[REDACTED — literal, starts sk-ant-api03-, ~108 chars]";
```

Used only in `handleAPI` → `/api/ai/scan` handler:
```js
headers:{'Content-Type':'application/json','x-api-key':ANTHROPIC_API_KEY, ...}
```

**Impact**: any dashboard collaborator with Worker source read access can extract the key, then bill your Anthropic account and access all your prompts/completions.

### 2. JWT signing secret (~line where `mkTok` and `ckTok` are called) — **P0, newly discovered**

```js
// mkTok(user, '[REDACTED — JWT secret literal, ~24 chars, starts "sheng…"]')                           ← in /api/auth/login
// ckTok(auth.slice(7), '[REDACTED — JWT secret literal, ~24 chars, starts "sheng…"]')                  ← in top-level fetch
```

The literal string `'[REDACTED — JWT secret literal, ~24 chars, starts "sheng…"]'` is used both to sign and to verify JWTs.

**Impact**: **anyone with source read access can forge JWTs for any user** — including `role:'admin'`. Since `/api/audit`, `/api/assessments/approve`, `/api/assessments/pending` all trust `user.role`, this is a full auth bypass. Critical.

### 3. Test-bypass in login (~in `/api/auth/login` handler) — **P1, newly discovered**

```js
if(r.password_hash !== body.password &&
   r.password_hash !== '[REDACTED — magic bypass literal, ~24 chars, starts "test_h…"]') return j({...error:'密碼錯誤'}, 401);
```

Two problems in one line:
- `r.password_hash !== body.password` is a **plaintext password comparison** (not a hash check); if you ever store a real hash there, no user can log in
- The magic string `'[REDACTED — magic bypass literal, ~24 chars, starts "test_h…"]'` is a **backdoor**: any DB row whose `password_hash` column happens to equal that literal accepts ANY password

**Impact**: (a) all user passwords are stored in plaintext in D1; (b) any user record with `password_hash = '[REDACTED — magic bypass literal, ~24 chars, starts "test_h…"]'` (probably left over from seeding) is an anonymous-login target.

## Fix — source diffs

Apply all three in one edit before `wrangler deploy`.

### Diff 1 — API key

```diff
- const ANTHROPIC_API_KEY = "[REDACTED]";
+ // ANTHROPIC_API_KEY moved to secret; read from env inside handler
```

Then in the `/api/ai/scan` handler, thread `env` down:

```diff
- async function handleAPI(path, method, body, env, user){
+ async function handleAPI(path, method, body, env, user){
    ...
    if(path === '/api/ai/scan' && method === 'POST'){
      ...
-     headers:{'Content-Type':'application/json', 'x-api-key':ANTHROPIC_API_KEY, ...},
+     headers:{'Content-Type':'application/json', 'x-api-key':env.ANTHROPIC_API_KEY, ...},
```

`env` is already passed into `handleAPI` — no wiring change needed.

### Diff 2 — JWT secret

Move to env and thread through the two callers:

```diff
- async function mkTok(u, sec){ ... }
- async function ckTok(token, sec){ ... }
+ async function mkTok(u, sec){ ... }  // unchanged; caller must pass secret
+ async function ckTok(token, sec){ ... }  // unchanged; caller must pass secret

  // in /api/auth/login:
- var token = await mkTok(r, '[REDACTED — JWT secret literal, ~24 chars, starts "sheng…"]');
+ var token = await mkTok(r, env.JWT_SECRET);

  // in top-level fetch:
- if(auth && auth.startsWith('Bearer ')){ user = await ckTok(auth.slice(7), '[REDACTED — JWT secret literal, ~24 chars, starts "sheng…"]') }
+ if(auth && auth.startsWith('Bearer ')){ user = await ckTok(auth.slice(7), env.JWT_SECRET) }
```

### Diff 3 — plaintext password + test bypass

Introduce a proper hash comparison and delete the backdoor. Recommended: use WebCrypto to derive an argon2-ish salted hash. For the minimum-viable fix that removes the backdoor without a schema migration, at least gate the plaintext behind `env.ENVIRONMENT === "development"`:

```diff
- if(r.password_hash !== body.password &&
-    r.password_hash !== '[REDACTED — magic bypass literal, ~24 chars, starts "test_h…"]')
-   return j({success:false, error:'密碼錯誤'}, 401);
+ if(env.ENVIRONMENT !== 'development' &&
+    r.password_hash === '[REDACTED — magic bypass literal, ~24 chars, starts "test_h…"]')
+   return j({success:false, error:'帳號未啟用'}, 401);
+ const suppliedHash = await sha256Hex(body.password);   // helper below
+ if(r.password_hash !== suppliedHash)
+   return j({success:false, error:'密碼錯誤'}, 401);
```

Add the helper:
```js
async function sha256Hex(s){
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,'0')).join('');
}
```

**Migration for existing DB rows**: on next login for each user, if `password_hash` looks like a plaintext (length ≠ 64 or contains non-hex chars), reject with a "please reset your password" flow rather than accepting the plaintext once. Alternatively, run a one-shot D1 script that reads all rows, hashes existing plaintext values, and writes them back — but *only* if you are absolutely sure they were all plaintext to begin with.

`sha256Hex` is a minimum bar — for production, prefer PBKDF2 with per-row salt (same pattern as `particle-auth-gateway-P0.md` §Fix). Adding PBKDF2 here is a P1 follow-up.

## Rotation runbook

Rotation for the API key and JWT secret does **not** require reading the old values. Generate new ones.

### Step 1 — Prepare replacements

```bash
# On any secure host:
NEW_JWT=$(openssl rand -hex 32)
# For ANTHROPIC_API_KEY: create a NEW key in the Anthropic Console
# (Dashboard → API keys → "Create key"). Do NOT reuse the old one.
```

### Step 2 — Store new values in Cloudflare secrets

```bash
# Set both secrets on the Worker:
wrangler secret put ANTHROPIC_API_KEY --name shengai-isp
# paste NEW Anthropic key when prompted
wrangler secret put JWT_SECRET --name shengai-isp
# paste $NEW_JWT when prompted
```

### Step 3 — Apply source diffs (all three above)

Edit your local `shengai-isp` source; apply diffs 1, 2, 3. Grep once more before deploy:

```bash
grep -nE "(sk-ant-|$JWT_LITERAL|$BYPASS_LITERAL)" shengai-isp.js
# Where JWT_LITERAL and BYPASS_LITERAL are the two literals you saw
# in your local source (see §Problem 2 and 3 for the "starts with…" hints).
# Expect: 0 matches
```

### Step 4 — Deploy

```bash
wrangler deploy --name shengai-isp
```

### Step 5 — Verify

```bash
# Health probe — public, no auth needed:
curl -s https://shengai-isp.z814241.workers.dev/api/health | jq
# Expect: { "success": true, "status": "healthy", ... }

# Login flow — old JWTs must be rejected:
OLD_JWT="<paste any JWT issued before this deploy>"
curl -s -H "Authorization: Bearer $OLD_JWT" \
  https://shengai-isp.z814241.workers.dev/api/clients | jq
# Expect: { "success": false, "error": "請先登入" }

# New login must succeed:
curl -sX POST -H "Content-Type: application/json" \
  -d '{"email":"admin@shengai.org","password":"<real password>"}' \
  https://shengai-isp.z814241.workers.dev/api/auth/login | jq
# Expect: { "success": true, "data": { "token": "..." } }

# AI scan works (secret plumbing OK):
curl -sX POST -H "Content-Type: application/json" -H "Authorization: Bearer <new token>" \
  -d '{"image":"<tiny base64 test image>"}' \
  https://shengai-isp.z814241.workers.dev/api/ai/scan | jq
# Expect: 200 with some parsed result OR an AI-side error message,
# NOT an "API key" or "unauthorized" error.
```

### Step 6 — Revoke old key at Anthropic

Anthropic Console → API keys → old key → **Delete**. Confirm the deletion event appears in the audit log.

### Step 7 — Force-invalidate all outstanding user sessions

Because the JWT secret rotation makes old tokens unusable (Step 5's negative test already proves this), no extra work needed — but tell users that **all existing sessions have been signed out** so they don't get confused.

## Verification checklist

- [ ] `wrangler secret list --name shengai-isp` shows both `ANTHROPIC_API_KEY` and `JWT_SECRET`
- [ ] Deployed source (Cloudflare dashboard → Worker → View source) has **no** substring `sk-ant-`, no JWT-secret literal, no magic bypass literal
- [ ] `curl /api/health` → 200 with `success: true`
- [ ] Pre-rotation JWT → 401 on any authed endpoint
- [ ] New login → new JWT works
- [ ] Anthropic Console → old API key deleted
- [ ] D1 `users` table scanned: no row still has `password_hash = '[REDACTED — magic bypass literal, ~24 chars, starts "test_h…"]'`
- [ ] Local wrangler workspace: `git log -p -S 'sk-ant-'` and `git log -p -S '[REDACTED — JWT secret literal, ~24 chars, starts "sheng…"]'` in shengai-isp repo → 0 hits in new commits (old ones remain in history — that's why we rotated)

## Notes on git history

Same caveat as PR #3's `particle-system-hub-P0.md`: any historical value that was in git is effectively public. Rotation via the flow above is mandatory, not optional, and this patch only prevents *future* propagation to mirrors/forks/readers.

## What still needs a separate follow-up

- **PBKDF2 password hashing with per-row salt** for `users.password_hash` — same pattern as `particle-auth-gateway-P0.md` §Fix. Requires a schema migration + one-shot back-fill.
- **Login rate limiting** — currently `/api/auth/login` has no throttle; combined with plaintext comparison in the current code, credential stuffing is trivial. Prefer Cloudflare Rate Limiting rules on the route.
- **CORS `*` wildcard** — the response headers include `'Access-Control-Allow-Origin':'*'` even for authenticated endpoints. Since JWT is in a header (not a cookie), CORS `*` isn't as dangerous as with cookies, but a scoped origin is still safer.
