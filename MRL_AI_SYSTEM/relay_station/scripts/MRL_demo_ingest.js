const payload = {
  source: 'MRL_Demo_Input',
  payload: {
    title: 'Arm Neoverse V3 SPE 映射',
    flow: ['select micro-operation', 'mark', 'internal register', 'record to memory'],
    mrl_mapping: ['MRL_Perception_Select', 'MRL_Trace_Mark', 'MRL_RuntimeState', 'MRL_MemoryLedger']
  }
};

const res = await fetch('http://127.0.0.1:8787/ingest', {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify(payload)
});
console.log(JSON.stringify(await res.json(), null, 2));
