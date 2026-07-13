import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

export const MRL_CONFIG = {
  system_name: 'MRL_Particle_Mother_RelayStation_v1',
  origin_signature: 'MrliouAI',
  namespace: 'MRL_',
  ledger_dir: path.resolve('data/ledger'),
  outbox_dir: path.resolve('data/outbox')
};

export function MRL_sha256(input) {
  return crypto.createHash('sha256').update(input).digest('hex');
}

export function MRL_now() {
  return new Date().toISOString();
}

export function MRL_ensure_dirs() {
  for (const dir of [MRL_CONFIG.ledger_dir, MRL_CONFIG.outbox_dir, path.resolve('data/inbox')]) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

export function MRL_safe_json_parse(raw) {
  try { return JSON.parse(raw); } catch { return null; }
}

export function MRL_extract_atoms(raw) {
  const text = typeof raw === 'string' ? raw : JSON.stringify(raw, null, 2);
  const lines = text.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
  const chunks = [];
  let buffer = [];
  for (const line of lines) {
    buffer.push(line);
    if (buffer.join(' ').length >= 360) {
      chunks.push(buffer.join('\n'));
      buffer = [];
    }
  }
  if (buffer.length) chunks.push(buffer.join('\n'));
  return chunks.length ? chunks : [text];
}

export function MRL_particleize(payload, source = 'unknown') {
  const received_at = MRL_now();
  const raw = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
  const source_hash = MRL_sha256(raw);
  const atoms = MRL_extract_atoms(payload);
  const particles = atoms.map((atom, index) => {
    const content_hash = MRL_sha256(atom);
    return {
      particle_id: `MRL_PARTICLE_${source_hash.slice(0, 12)}_${String(index).padStart(4, '0')}`,
      index,
      type: 'MRL_TextAtom',
      source,
      content: atom,
      content_hash,
      origin_signature: MRL_CONFIG.origin_signature,
      received_at
    };
  });
  return {
    packet_id: `MRL_PACKET_${source_hash.slice(0, 16)}`,
    source,
    source_hash,
    received_at,
    count: particles.length,
    particles
  };
}

export function MRL_rebuild(packet) {
  const ordered = [...packet.particles].sort((a, b) => a.index - b.index);
  const rebuilt_text = ordered.map(p => p.content).join('\n');
  const rebuilt_hash = MRL_sha256(rebuilt_text);
  return {
    rebuild_id: `MRL_REBUILD_${rebuilt_hash.slice(0, 16)}`,
    packet_id: packet.packet_id,
    source: packet.source,
    rebuilt_text,
    rebuilt_hash,
    particle_count: ordered.length,
    coherence: packet.source_hash === rebuilt_hash ? 'EXACT' : 'STRUCTURAL',
    rebuilt_at: MRL_now(),
    origin_signature: MRL_CONFIG.origin_signature
  };
}

export function MRL_write_ledger(event) {
  MRL_ensure_dirs();
  const line = JSON.stringify({ ...event, ledger_at: MRL_now() }) + '\n';
  const file = path.join(MRL_CONFIG.ledger_dir, 'MRL_relay_ledger.jsonl');
  fs.appendFileSync(file, line);
  return file;
}

export function MRL_relay(packet, rebuild, target = 'MRL_Mother_Runtime') {
  MRL_ensure_dirs();
  const relay_packet = {
    relay_id: `MRL_RELAY_${MRL_sha256(packet.packet_id + rebuild.rebuilt_hash + target).slice(0, 16)}`,
    target,
    status: 'READY_FOR_MOTHERBODY_INGEST',
    packet,
    rebuild,
    relay_at: MRL_now(),
    origin_signature: MRL_CONFIG.origin_signature
  };
  const out = path.join(MRL_CONFIG.outbox_dir, `${relay_packet.relay_id}.json`);
  fs.writeFileSync(out, JSON.stringify(relay_packet, null, 2));
  MRL_write_ledger({
    event: 'MRL_RELAY_CREATED',
    relay_id: relay_packet.relay_id,
    packet_id: packet.packet_id,
    rebuild_id: rebuild.rebuild_id,
    target,
    particle_count: packet.count,
    rebuilt_hash: rebuild.rebuilt_hash,
    origin_signature: MRL_CONFIG.origin_signature
  });
  return { relay_packet, out };
}

export function MRL_process(payload, source = 'api', target = 'MRL_Mother_Runtime') {
  const packet = MRL_particleize(payload, source);
  const rebuild = MRL_rebuild(packet);
  const relay = MRL_relay(packet, rebuild, target);
  return { packet, rebuild, relay_id: relay.relay_packet.relay_id, out: relay.out };
}
