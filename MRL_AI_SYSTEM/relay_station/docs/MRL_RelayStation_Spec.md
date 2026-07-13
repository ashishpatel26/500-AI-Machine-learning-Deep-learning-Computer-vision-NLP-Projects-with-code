# MRL_Particle_Mother_RelayStation_v1

## 定位

MRL_粒子母體接收重建轉驛站。

用途：把外部資料、文件、API 回傳、文字、JSON、系統事件，轉成 MRL 母體可接收的粒子封包，並完成重建、驗證、轉驛、ledger 寫入。

## 主流程

```text
MRL_Receive
→ MRL_Particleize
→ MRL_Rebuild
→ MRL_Relay
→ MRL_Ledger
→ MRL_Mother_Runtime
```

## 對應 Arm SPE 參考頁

Arm Neoverse V3 SPE 的流程為：選取 micro-operation、標記、核內暫存追蹤、在 retired / aborted / flushed 後寫入 memory。

MRL 映射：

```text
micro-operation → MRL_Particle / MRL_Runtime_Event
profile mark → MRL_Trace_Mark
internal registers → MRL_Internal_Profile_Register
record to memory → MRL_MemoryLedger
retired / aborted / flushed → completed / failed / cancelled / flushed lifecycle state
```

## API

### Health

```bash
curl http://localhost:8788/api/health
```

### Ingest

```bash
curl -X POST http://localhost:8788/api/mrl/relay/ingest \
  -H "content-type: application/json" \
  -d '{"hello":"MRL"}'
```

## File ingest

```bash
node scripts/MRL_ingest_file.js ./data/inbox/sample.txt
```

## 輸出

- `data/outbox/*.json`：可轉交母體的 relay packet
- `data/ledger/MRL_relay_ledger.jsonl`：事件紀錄

## MRL 命名限制

正式主體只使用 MRL_。外部技術只作 Adapter / Reference，不作母體主名。
