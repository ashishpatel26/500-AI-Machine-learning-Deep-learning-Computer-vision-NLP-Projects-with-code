import http from 'node:http';

function get(path) {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:8787${path}`, res => {
      let body = '';
      res.on('data', d => body += d);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(body) }));
    }).on('error', reject);
  });
}

const health = await get('/health');
if (!health.body.ok || health.body.system_name !== 'MRL_Particle_Mother_RelayStation_v1') {
  console.error('FAIL', health);
  process.exit(1);
}
console.log('PASS MRL_RelayStation health');
