import fs from 'node:fs';
import { MRL_process } from '../src/MRL_Core.js';

const payload = {
  name: 'MRL_acceptance_sample',
  law: 'receive -> particleize -> rebuild -> relay -> ledger',
  origin_signature: 'MrliouAI'
};
const result = MRL_process(payload, 'acceptance_test', 'MRL_Mother_Runtime');
const checks = [
  ['packet exists', Boolean(result.packet.packet_id)],
  ['particles exist', result.packet.count > 0],
  ['rebuild exists', Boolean(result.rebuild.rebuild_id)],
  ['relay file exists', fs.existsSync(result.out)]
];
let pass = 0;
for (const [name, ok] of checks) {
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}`);
  if (ok) pass++;
}
if (pass !== checks.length) process.exit(1);
console.log(`MRL_ACCEPTANCE_PASS ${pass}/${checks.length}`);
