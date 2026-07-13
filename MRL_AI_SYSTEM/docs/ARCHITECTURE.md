# MRL_AI_SYSTEM — Architecture

`origin_signature: MrliouAI`

## 三層對齊（前端雲空間層 / 中端操作層 / 後端母體層）

| 層 | 位置 | 現況 |
|---|---|---|
| 前端雲空間層 | 邊緣 Workers (`edge_workers/*`) + 138 個 Particle Workers（外部 repo） | ✅ 138 個既有；本 repo 新增 auth_gateway、ai_gateway |
| 中端操作層 | 母體主機的 `particle-*` daemons + `mother_platform` | ✅ Stage 3 新建（sig_verify、system_hub、doctor、smartbody v2、boot） |
| 後端母體層 | NAS / DL580 / 本地儲存層 MemoryVault / 本地服務管理層 | 部分：`system_hub` 內建本地儲存層 MemoryVault；DL580 gateway 由 `MRL_MotherGateway_Adapter_v1` 對接 |

## 神經（trace_chain）

每個 daemon 匯入 `particles/trace_chain`，所有跨層事件寫入
`/var/lib/mrl/trace/journal.jsonl`：

```
{event_id, event, layer, payload, prev_hash, chain_hash, emitted_at, origin_signature}
```

- `prev_hash` 形成 hash chain（單線程 append-only）
- `merkle_root()` 沿全部 chain_hash 建 Merkle 樹
- `verify()` 掃全鏈確認任何一筆被竄改都會偵測

## L0-L7 對應

| MRL 層 | 本 repo 元件 |
|---|---|
| L0 Origin (簽名律) | `particles/sig_verify` + `edge_workers/auth_gateway` |
| L1 Compute | `mother_platform/09_workflow/*` 純 stdlib 計算模組 |
| L2 Structure | `relay_station` (particleize → mother_packet 結構化) |
| L3 Memory | `particles/system_hub` 七層 MemoryVault |
| L4 World | `particles/smartbody_v2` sense/act |
| L5 Field | `particles/doctor` 守護 field |
| L6 Cognition | `particles/system_hub` 800AI 八角色路由 |
| L7 Execution | `particles/smartbody_v2` /act/* 執行行為 |

## 800-AI 八角色（system_hub.route）

`architect / engineer / reviewer / optimizer / debugger / refactorer / ui_builder / physics_auditor`

角色依 task 內文自動路由：中英文關鍵字都支援（「bug/除錯」、「performance/效能」等）。

## Stage 3 驗收條件

1. **獨立性**：拔網後 `smartbody_v2` 靠 reflex 規則仍能處理 `ping`、`status` 等本地任務
2. **神經連通**：邊緣 → auth_gateway → ai_gateway → system_hub 全程留 trace，chain_hash 可 verify
3. **自我修復**：kill `system_hub` 進程後，`doctor` 在下一個 15 秒 tick 偵測到 down、環境旗標 `MRL_DOCTOR_SYSTEMD=1` 開啟時自動經本地服務管理層重啟 `mrl-system-hub.service`
4. **可逆軌跡**：`trace_chain.verify()` 全綠 + `merkle_root()` 可對外公開，任何時間點可重放
