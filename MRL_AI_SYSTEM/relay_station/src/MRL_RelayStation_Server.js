import http from 'node:http';
import { MRL_CONFIG, MRL_process, MRL_ensure_dirs } from './MRL_Core.js';

MRL_ensure_dirs();
const PORT = Number(process.env.MRL_RELAY_PORT || 8788);

function send(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(body, null, 2));
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return Buffer.concat(chunks).toString('utf8');
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/api/health') {
      return send(res, 200, {
        ok: true,
        system_name: MRL_CONFIG.system_name,
        origin_signature: MRL_CONFIG.origin_signature,
        capabilities: ['receive', 'particleize', 'rebuild', 'relay', 'ledger']
      });
    }

    if (req.method === 'POST' && req.url === '/api/mrl/relay/ingest') {
      const raw = await readBody(req);
      const contentType = req.headers['content-type'] || '';
      let payload = raw;
      if (contentType.includes('application/json')) {
        try { payload = JSON.parse(raw); } catch { payload = raw; }
      }
      const result = MRL_process(payload, 'api', 'MRL_Mother_Runtime');
      return send(res, 200, {
        ok: true,
        packet_id: result.packet.packet_id,
        particle_count: result.packet.count,
        rebuild_id: result.rebuild.rebuild_id,
        coherence: result.rebuild.coherence,
        relay_id: result.relay_id,
        out: result.out
      });
    }

    return send(res, 404, { ok: false, error: 'MRL_ROUTE_NOT_FOUND' });
  } catch (error) {
    return send(res, 500, { ok: false, error: error.message });
  }
});

server.listen(PORT, () => {
  console.log(`[MRL] ${MRL_CONFIG.system_name} listening on ${PORT}`);
});
