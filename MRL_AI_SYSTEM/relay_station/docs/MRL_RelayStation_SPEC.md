# MRL_Particle_Mother_RelayStation_v1

## 定位

MRL 粒子母體系統接收、重建、轉驛站。

用途：把外部資料、PDF 摘要、技術頁面、程式碼片段、網頁資料、討論材料先轉成 MRL_Particle，再重建成 MRL_MotherPacket，最後交給 MRL 母體或 AI 夥伴討論，避免上下文對不齊。

## 主流程

```text
External Input
→ MRL_Receive
→ MRL_Particleize
→ MRL_Reconstruct
→ MRL_Relay
→ MRL_Ledger
→ MRL_Discussion_Context
```

## 對應 Arm Neoverse V3 SPE 參考流程

```text
Select micro-operation
→ Mark profiled operation
→ Store in internal registers
→ Record profile data to memory after retired / aborted / flushed
```

MRL 映射：

```text
MRL_Particle_Select
→ MRL_Trace_Mark
→ MRL_RuntimeState_Register
→ MRL_MemoryLedger_Write
```

## API

### GET /health

檢查服務是否啟動。

### POST /ingest

輸入：

```json
{
  "source": "MRL_SourceName",
  "payload": {
    "title": "example",
    "content": "data"
  }
}
```

輸出：

```json
{
  "ok": true,
  "relay_state": "MRL_READY_FOR_DISCUSSION",
  "mother_packet": {}
}
```

## 目錄

```text
data/inbox    原始粒子包
data/outbox   重建後母體包
data/ledger   事件 ledger
data/state    狀態保留
```

## 使用

```bash
npm install
npm start
npm run demo
```

或直接：

```bash
node src/MRL_RelayStation.js
```
