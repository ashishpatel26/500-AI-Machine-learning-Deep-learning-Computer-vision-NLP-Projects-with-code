import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..');
const DATA = path.join(ROOT, 'data');
const PORT = Number(process.env.MRL_RELAY_PORT || 8787);
const ORIGIN_SIGNATURE = process.env.MRL_ORIGIN_SIGNATURE || 'MrliouAI';

for (const dir of ['inbox', 'outbox', 'ledger', 'state']) fs.mkdirSync(path.join(DATA, dir), { recursive: true });

function now() { return new Date().toISOString(); }
function sha256(input) { return crypto.createHash('sha256').update(typeof input === 'string' ? input : JSON.stringify(input)).digest('hex'); }
function safeId(prefix = 'mrl') { return `${prefix}_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`; }
function readJson(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk; if (body.length > 10_000_000) req.destroy(); });
    req.on('end', () => {
      try { resolve(body ? JSON.parse(body) : {}); } catch (err) { reject(err); }
    });
    req.on('error', reject);
  });
}
function send(res, status, payload) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(payload, null, 2));
}

function atomizeValue(key, value, layer = 'MRL_InputLayer') {
  const type = Array.isArray(value) ? 'array' : value === null ? 'null' : typeof value;
  const content = type === 'object' || type === 'array' ? JSON.stringify(value) : String(value);
  return {
    particle_id: safeId('MRL_Particle'),
    key,
    layer,
    type,
    content,
    content_hash: sha256(content),
    created_at: now(),
    origin_signature: ORIGIN_SIGNATURE
  };
}

function particleize(input) {
  const source = input.source || 'MRL_External_Input';
  const raw = input.payload ?? input;
  const particles = [];

  if (typeof raw === 'string') {
    raw.split(/\n+/).map(s => s.trim()).filter(Boolean).forEach((line, i) => {
      particles.push(atomizeValue(`line_${i + 1}`, line, 'MRL_TextLayer'));
    });
  } else if (Array.isArray(raw)) {
    raw.forEach((v, i) => particles.push(atomizeValue(`item_${i + 1}`, v, 'MRL_ArrayLayer')));
  } else if (raw && typeof raw === 'object') {
    Object.entries(raw).forEach(([k, v]) => particles.push(atomizeValue(k, v, 'MRL_ObjectLayer')));
  } else {
    particles.push(atomizeValue('value', raw, 'MRL_ValueLayer'));
  }

  return {
    packet_id: safeId('MRL_InputPacket'),
    stage: 'MRL_PARTICLEIZED',
    source,
    created_at: now(),
    particle_count: particles.length,
    particles,
    origin_signature: ORIGIN_SIGNATURE
  };
}

function reconstruct(packet) {
  const links = [];
  const byLayer = {};
  for (const p of packet.particles) {
    byLayer[p.layer] ||= [];
    byLayer[p.layer].push(p.particle_id);
  }
  for (let i = 0; i < packet.particles.length - 1; i++) {
    links.push({ from: packet.particles[i].particle_id, to: packet.particles[i + 1].particle_id, relation: 'MRL_SEQUENCE_NEXT' });
  }
  const motherPacket = {
    mother_packet_id: safeId('MRL_MotherPacket'),
    input_packet_id: packet.packet_id,
    stage: 'MRL_RECONSTRUCTED',
    created_at: now(),
    source: packet.source,
    origin_signature: ORIGIN_SIGNATURE,
    topology: { byLayer, links },
    particles: packet.particles,
    merkle_root: sha256(packet.particles.map(p => p.content_hash).join('|')),
    relay_targets: ['MRL_Mother_Runtime', 'MRL_Discussion_Context', 'MRL_ReplayRestore']
  };
  return motherPacket;
}

function appendLedger(event) {
  const ledgerPath = path.join(DATA, 'ledger', 'MRL_relay_ledger.jsonl');
  const line = JSON.stringify({ ...event, ledger_at: now(), event_hash: sha256(event), origin_signature: ORIGIN_SIGNATURE });
  fs.appendFileSync(ledgerPath, line + '\n');
  return ledgerPath;
}

function persistPacket(packet, folder, idKey) {
  const file = path.join(DATA, folder, `${packet[idKey]}.json`);
  fs.writeFileSync(file, JSON.stringify(packet, null, 2));
  return file;
}

async function handleIngest(req, res) {
  const input = await readJson(req);
  const particlePacket = particleize(input);
  const motherPacket = reconstruct(particlePacket);
  const inboxFile = persistPacket(particlePacket, 'inbox', 'packet_id');
  const outboxFile = persistPacket(motherPacket, 'outbox', 'mother_packet_id');
  appendLedger({ action: 'MRL_INGEST_RECONSTRUCT_RELAY', input_hash: sha256(input), packet_id: particlePacket.packet_id, mother_packet_id: motherPacket.mother_packet_id, merkle_root: motherPacket.merkle_root, particle_count: particlePacket.particle_count, inboxFile, outboxFile });
  send(res, 200, { ok: true, relay_state: 'MRL_READY_FOR_DISCUSSION', mother_packet: motherPacket, files: { inboxFile, outboxFile } });
}

function handleHealth(res) {
  send(res, 200, { ok: true, system_name: 'MRL_Particle_Mother_RelayStation_v1', role: 'receive_particleize_reconstruct_relay', origin_signature: ORIGIN_SIGNATURE, port: PORT, time: now() });
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/health') return handleHealth(res);
    if (req.method === 'POST' && req.url === '/ingest') return await handleIngest(req, res);
    send(res, 404, { ok: false, error: 'MRL_ROUTE_NOT_FOUND', routes: ['GET /health', 'POST /ingest'] });
  } catch (err) {
    send(res, 500, { ok: false, error: 'MRL_RELAY_ERROR', message: err.message });
  }
});

server.listen(PORT, () => console.log(`MRL_Particle_Mother_RelayStation_v1 running on http://127.0.0.1:${PORT}`));
