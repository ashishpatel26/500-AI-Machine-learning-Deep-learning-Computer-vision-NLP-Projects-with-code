# P0 Patch — `particle-ai-gateway` · `AUTH_BYPASS` fail-closed

`origin_signature: MrLiouWord`
`target_worker: particle-ai-gateway` (Cloudflare)
`current_deploy: 2026-05-15`
`fix_type: authentication hardening`
`estimated_effort: 15 minutes + verification`

## Problem

Current `authenticateRequest` starts with:
```js
async function authenticateRequest(request, env) {
  if (env.AUTH_BYPASS === "true") {
    return { authenticated: true, identity: "bypass", scopes: ["*"] };
  }
  // ... JWT / Bearer / X-API-Key checks below
}
```

**Impact**: setting `AUTH_BYPASS=true` in production (via wrangler dashboard, misconfiguration, restored old wrangler.toml, etc.) makes every request authenticated with `scopes: ["*"]`. There is no guard preventing this from happening in production.

## Fix — fail-closed with explicit dev flag

The bypass must require **two** environment variables set together, one of which must be **impossible to set by accident**. Any bypass attempt without both is a hard 500 refusal.

### Diff

Replace the current bypass block with:

```diff
 async function authenticateRequest(request, env) {
-  if (env.AUTH_BYPASS === "true") {
-    return { authenticated: true, identity: "bypass", scopes: ["*"] };
-  }
+  // AUTH_BYPASS is a DEV-ONLY escape hatch. Two conditions must ALL hold:
+  //   1. env.AUTH_BYPASS === "true"
+  //   2. env.ALLOW_AUTH_BYPASS === "yes_i_understand_this_disables_all_auth"
+  //   3. env.ENVIRONMENT !== "production" (default assumption if unset)
+  //
+  // Setting just AUTH_BYPASS alone in production is a bug — fail-closed.
+  if (env.AUTH_BYPASS === "true") {
+    const explicit = env.ALLOW_AUTH_BYPASS === "yes_i_understand_this_disables_all_auth";
+    const nonProd = env.ENVIRONMENT !== "production";
+    if (!explicit || !nonProd) {
+      throw new Error(
+        "particle-ai-gateway: AUTH_BYPASS is set but safeguards are missing. " +
+        "In production, unset AUTH_BYPASS. In dev, set ALLOW_AUTH_BYPASS to the " +
+        "explicit acknowledgement string and ENVIRONMENT to a non-production value."
+      );
+    }
+    return { authenticated: true, identity: "bypass", scopes: ["*"] };
+  }
   // ... JWT / Bearer / X-API-Key checks below
 }
```

The thrown error is caught by the top-level `fetch` handler's error path, returning a 500 with the message — attackers see nothing about the app internals; ops sees a clear signal in logs.

### Why not just check `ENVIRONMENT`?

A single env flag can be flipped by accident. Requiring `ALLOW_AUTH_BYPASS` to equal a **specific long acknowledgement string** ensures no one sets it while eyeballing a config UI. The string is intentionally long, unambiguous, and looks nothing like "true"/"1"/"on".

## Deployment steps

### Step 1 — Verify production is not currently bypassed

```bash
# Should return 401 for an unauthenticated request:
curl -o /dev/null -s -w "%{http_code}\n" https://particle-ai-gateway.z814241.workers.dev/v1/chat
# Expect: 401
# If it returns 200, AUTH_BYPASS is currently set — stop and investigate before deploying.
```

### Step 2 — Apply diff to source

Apply the diff above to your local `particle-ai-gateway` source.

### Step 3 — Confirm no production secrets grant bypass

```bash
wrangler secret list --name particle-ai-gateway
# Should NOT contain: AUTH_BYPASS or ALLOW_AUTH_BYPASS
```

If either is present:
```bash
wrangler secret delete AUTH_BYPASS --name particle-ai-gateway
wrangler secret delete ALLOW_AUTH_BYPASS --name particle-ai-gateway
```

Also check `wrangler.toml` `[vars]` for the same — remove.

### Step 4 — Set `ENVIRONMENT=production` as a var

```bash
# In wrangler.toml [vars] section:
#   ENVIRONMENT = "production"
# or:
wrangler kv:namespace  # not needed; just an env var
```

Actually simpler:
```toml
# wrangler.toml
[vars]
ENVIRONMENT = "production"
```

### Step 5 — Deploy

```bash
wrangler deploy --name particle-ai-gateway
```

### Step 6 — Verify fail-closed behaviour

Positive tests (should still work):

```bash
# Public endpoint — always 200:
curl -s https://particle-ai-gateway.z814241.workers.dev/monitoring/healthz
# Expect: {"status": "ok"}

# Authenticated request with valid API key:
curl -s -H "X-API-Key: $VALID_KEY" https://.../v1/models | jq
# Expect: models list
```

Negative test (the whole point):

```bash
# Try to enable bypass by setting AUTH_BYPASS in a header or query — must fail:
curl -H "X-Auth-Bypass: true" https://.../v1/chat
# Expect: 401 (headers are not env; bypass path unreachable)
```

For **dev** hosts that legitimately need bypass, set both flags:

```bash
wrangler secret put AUTH_BYPASS --name particle-ai-gateway-dev  # value: true
wrangler secret put ALLOW_AUTH_BYPASS --name particle-ai-gateway-dev
# value: yes_i_understand_this_disables_all_auth
# Set ENVIRONMENT var in dev wrangler.toml to "development"
```

## Post-deployment monitoring

Watch logs for a week for any occurrences of the thrown error:
```
particle-ai-gateway: AUTH_BYPASS is set but safeguards are missing.
```

Every occurrence is either:
- A dev config leaking into prod → investigate deployment pipeline
- An attacker probing for the bypass → good, they get 500

Either way, actionable.

## Verification checklist

- [ ] Production `wrangler secret list` has neither `AUTH_BYPASS` nor `ALLOW_AUTH_BYPASS`
- [ ] Production `wrangler.toml [vars]` has `ENVIRONMENT = "production"` and no `AUTH_BYPASS`
- [ ] `curl` to `/v1/chat` without auth returns 401 (not 200)
- [ ] Setting `AUTH_BYPASS=true` alone in a dev clone reproduces the 500 error
- [ ] Setting both env vars in dev clone restores bypass (dev use case works)
