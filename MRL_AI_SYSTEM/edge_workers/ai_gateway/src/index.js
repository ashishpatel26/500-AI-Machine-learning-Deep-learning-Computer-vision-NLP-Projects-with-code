// particle-ai-gateway — Cloudflare Worker
// origin_signature: MrliouAI
// layer: L4 World (edge boundary → hub)
//
// Terminates authenticated inbound traffic from particle-auth-gateway,
// applies rate limiting, and forwards signed requests to the local
// system-hub via Cloudflare Tunnel. Emits an event to the trace journal
// KV so the local doctor can pull it later.
//
// Required env bindings:
//   HUB_TUNNEL_URL       (var)     — https://hub.mrliouword.com
//   MRL_AI_TRACE         (KV)      — trace journal mirror
//   MRL_RATE_LIMIT       (var)     — requests / minute per subject (default 60)

async function pushTrace(env, event) {
  if (!env.MRL_AI_TRACE) return;
  const id = `${Date.now()}-${crypto.randomUUID()}`;
  await env.MRL_AI_TRACE.put(id, JSON.stringify({
    ...event,
    origin_signature: "MrliouAI",
    ts: new Date().toISOString(),
  }), { expirationTtl: 60 * 60 * 24 * 30 });
}

async function checkRate(env, subject) {
  if (!env.MRL_AI_TRACE) return true;
  const limit = parseInt(env.MRL_RATE_LIMIT || "60", 10);
  const bucket = `rl:${subject}:${Math.floor(Date.now() / 60000)}`;
  const current = parseInt((await env.MRL_AI_TRACE.get(bucket)) || "0", 10);
  if (current >= limit) return false;
  await env.MRL_AI_TRACE.put(bucket, String(current + 1), { expirationTtl: 120 });
  return true;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return Response.json({
        ok: true, particle: "ai_gateway",
        origin_signature: "MrliouAI",
        hub: env.HUB_TUNNEL_URL || "(unset)",
      });
    }
    const subject = request.headers.get("x-mrl-subject") || "anonymous";
    if (!(await checkRate(env, subject))) {
      await pushTrace(env, { event: "rate.reject", subject });
      return new Response("rate limited", { status: 429 });
    }
    if (!env.HUB_TUNNEL_URL) {
      return new Response("hub not configured", { status: 502 });
    }
    const forwarded = new Request(env.HUB_TUNNEL_URL + url.pathname + url.search, request);
    forwarded.headers.set("X-MRL-Edge", "ai_gateway");
    forwarded.headers.set("X-MRL-Origin-Signature", "MrliouAI");
    const resp = await fetch(forwarded);
    await pushTrace(env, {
      event: "forward",
      subject,
      path: url.pathname,
      status: resp.status,
    });
    return resp;
  },
};
