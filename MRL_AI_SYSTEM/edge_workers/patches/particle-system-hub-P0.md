# P0 Patch — `particle-system-hub` · Move `DL580_KEY` to secret

`origin_signature: MrLiouWord`
`target_worker: particle-system-hub` (Cloudflare)
`current_version: v2.2.0` (deployed 2026-04-14)
`fix_type: config-only (no logic change)`
`estimated_effort: 5 minutes + verification`

## Problem

Current source has:
```js
const DL580_KEY = "[REDACTED]";  // ← literal string constant at top of file
```

Which is used as:
```js
fetch(`${DL580_BRIDGE}/health`, { headers: { "x-api-key": DL580_KEY } })
```

**Impact**: any collaborator with Cloudflare dashboard read access to the Worker source can read the DL580 Bridge key.

## Fix (source diff)

Replace the module-level constant with an `env` read, and thread `env` through the two `fetch` call sites.

```diff
- const DL580_KEY = "[REDACTED]";
+ // DL580_KEY moved to secret; access via env.DL580_KEY inside fetch handler
```

Then update the two references (both inside the `fetch` handler, which already receives `env`):

**`/dl580` handler (approx. line 195):**
```diff
- headers: { "x-api-key": DL580_KEY },
+ headers: { "x-api-key": env.DL580_KEY },
```

**`/dl580/inference` handler (approx. line 225):**
```diff
- const resp = await fetch(`${DL580_BRIDGE}/MRL_run?key=${DL580_KEY}&cmd=...`, {
+ const resp = await fetch(`${DL580_BRIDGE}/MRL_run?key=${env.DL580_KEY}&cmd=...`, {
```

⚠️ `env.DL580_KEY` is only accessible **inside** the exported `fetch(request, env)`. You cannot use it at module top-level. Both current call sites are already inside the handler, so no restructuring needed.

## Rotation runbook (correct flow — do NOT read the old value)

Rotation does **not** require the old key. Generate a new one directly.

### Step 1 — Prepare the new key on DL580 Bridge

```bash
# On DL580 host
NEW_DL580_KEY=$(openssl rand -hex 24)
echo "New key generated (do not log): ${NEW_DL580_KEY:0:4}…${NEW_DL580_KEY: -4}"

# Configure Bridge to accept BOTH old and new key during transition
# (implementation-specific — depends on how Bridge validates x-api-key)
# Example if Bridge reads from ENV:
#   MRL_BRIDGE_ACCEPT_KEYS="${OLD_KEY},${NEW_DL580_KEY}"
# Reload Bridge service.
```

### Step 2 — Store new key in Cloudflare secret

```bash
# From the Worker's wrangler project directory
echo -n "$NEW_DL580_KEY" | wrangler secret put DL580_KEY --name particle-system-hub
# wrangler will prompt but read from stdin cleanly
```

### Step 3 — Deploy the env-reading Worker source

Apply the diff above to your local `particle-system-hub` source, then:

```bash
wrangler deploy --name particle-system-hub
```

### Step 4 — Verify

```bash
curl -s https://particle-system-hub.z814241.workers.dev/dl580 | jq '.dl580.status'
# Expect: "online"
```

If Step 4 returns `"unreachable"` or 503 with an auth-related error, the new key isn't reaching Bridge. Roll back with `wrangler rollback --name particle-system-hub` and debug before proceeding.

### Step 5 — Revoke old key at DL580 Bridge

```bash
# On DL580 host — remove OLD key, keep only NEW
MRL_BRIDGE_ACCEPT_KEYS="${NEW_DL580_KEY}"
# Reload Bridge service.
```

### Step 6 — Confirm hardcoded literal is gone

```bash
wrangler kv:key get "..." --binding=... 2>/dev/null  # sanity check — not applicable
grep -R 'x-api-key.*"MrLiouWord' .                    # local grep
# Cloudflare dashboard → Worker → View source: search for old value substring, expect 0 matches
```

## Post-rotation hardening (nice-to-have)

- Add a `env.DL580_KEY` presence check at the top of each fetch handler that uses it — fail-fast with a 500 explaining the misconfiguration rather than making an anonymous request to Bridge.
- Consider making `DL580_KEY` a scoped-per-endpoint token if Bridge supports it (least-privilege).

## Verification checklist

- [ ] `wrangler secret list --name particle-system-hub` shows `DL580_KEY`
- [ ] Deployed Worker source (via dashboard) contains **no** literal string starting with `MrLiou…2026`
- [ ] `curl .../dl580` returns `"status": "online"`
- [ ] `curl .../dl580/inference` returns `model_loaded: true`
- [ ] DL580 Bridge no longer accepts the old key value
