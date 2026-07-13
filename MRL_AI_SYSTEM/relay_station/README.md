# MRL_Particle_Mother_RelayStation_v1

MRL 粒子母體接收重建轉驛站。

## 啟動

```bash
npm install
npm start
```

## 驗收

```bash
npm test
```

## 接收資料

```bash
curl -X POST http://localhost:8788/api/mrl/relay/ingest \
  -H "content-type: application/json" \
  -d '{"source":"test","content":"MRL receive rebuild relay"}'
```

## 核心用途

```text
外部資料
→ 接收
→ 粒子化
→ 重建
→ 轉驛封包
→ ledger
→ 母體 Runtime
```
