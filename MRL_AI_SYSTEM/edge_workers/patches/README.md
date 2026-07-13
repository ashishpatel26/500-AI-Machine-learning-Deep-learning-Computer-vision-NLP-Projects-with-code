# 邊緣 Worker P0 修補（Patches）

`origin_signature: MrLiouWord`

母體邊緣層 Worker 的 P0 安全發現修補 runbook 集。發現來源：
[`docs/STAGE3_WORKER_AUDIT_20260710.md`](../../docs/STAGE3_WORKER_AUDIT_20260710.md) 及後續稽核。

每份 patch 各自完整：問題敘述、diff、部署步驟、驗收 checklist。
**不重新 embed 邊緣部署源**——只列變更 hunks 與必要上下文，讓操作員能乾淨套用。

## 建議套用順序（由簡入繁）

| 順序 | Patch | 複雜度 | 預估時間 |
|---|---|---|---|
| 1 | [`particle-system-hub-P0.md`](./particle-system-hub-P0.md) | 1 行源碼 + 邊緣 secret + 6 步 rotation | 5 min |
| 2 | [`particle-ai-gateway-P0.md`](./particle-ai-gateway-P0.md) | ~10 行 auth-guard + 邊緣部署設定 var | 15 min |
| 3 | [`shengai-isp-P0.md`](./shengai-isp-P0.md) | 3 個 secret + 認證 backdoor 一份修補（API key + JWT + 密碼） | 45 min |
| 4 | [`particle-auth-gateway-P0.md`](./particle-auth-gateway-P0.md) | 密碼學重寫 + 版本化 envelope + 分階段 in-place 遷移 | 2-3 小時 |

## 共通原則

- **Rotation 不需讀舊值**：live secret 洩漏時，直接產生新值並在上游同時接受新舊過渡期；絕不從邊緣 log 或 dashboard 抓舊值重打
- **遷移期向後相容**：格式變更（patch #3）用版本化 envelope，讓新舊 payload 並存
- **Fail-closed default**：dev-only 逃生口必須雙獨立訊號，禁單一 `true`/`1`/`on` 旗標
- **Deploy → verify → revoke**：每次 rotation 都在新能力驗證後才移除舊能力，不能反向

## 尚未涵蓋（後續修補）

- `particle-doctor` — `CF_ACCOUNT` 硬編碼（P2 衛生問題；若對應憑證跨帳號則升 P0/P1）。優先級由憑證 scope 決定；見稽核 §3.5
- `particle-sig-verify` — 曾為 stub。非 P0（無漏洞邏輯），但 P1 替換：母體 daemon 邏輯 port 到邊緣層。**已完成**：見 `MRL_AI_SYSTEM/edge_workers/sig_verify/`
- `shengai-isp` 密碼雜湊升級 — P0 patch 移除明文 backdoor 並加 SHA-256 做最低門檻。P1 後續：改成 per-row salt PBKDF2（同 `particle-auth-gateway-P0.md` 的模式）+ 資料遷移
