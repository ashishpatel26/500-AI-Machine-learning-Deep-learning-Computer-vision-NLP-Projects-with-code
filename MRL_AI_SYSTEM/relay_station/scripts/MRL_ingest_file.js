import fs from 'node:fs';
import path from 'node:path';
import { MRL_process } from '../src/MRL_Core.js';

const file = process.argv[2];
if (!file) {
  console.error('Usage: node scripts/MRL_ingest_file.js <file>');
  process.exit(1);
}
const raw = fs.readFileSync(file, 'utf8');
const result = MRL_process(raw, path.basename(file), 'MRL_Mother_Runtime');
console.log(JSON.stringify({
  ok: true,
  packet_id: result.packet.packet_id,
  particle_count: result.packet.count,
  rebuild_id: result.rebuild.rebuild_id,
  relay_id: result.relay_id,
  out: result.out
}, null, 2));
