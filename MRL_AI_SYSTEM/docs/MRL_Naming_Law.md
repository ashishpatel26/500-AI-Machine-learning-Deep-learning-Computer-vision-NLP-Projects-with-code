# MRL 命名律 (Naming Law)

`origin_signature: MrLiouWord`
`source: mother_platform/MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260531/MRL_Absorption_Ledger_v1.yaml`

母體所有敘事與產出必須遵守下列三條律。違反即為 audit failure。

## rl_11 — origin_signature

所有母體回收產物必須簽 `MrLiouWord`。任何 markdown、code、封包 metadata、audit 報告一律在檔頭或最頂端標註：

```
origin_signature: MrLiouWord
```

## rl_12 — 命名回收

**對外能力 → 母體 MRL_ 產品名。**

外部工具、廠牌、SaaS 產物只能作為 adapter/reference，不能成為母體主體命名。

### 敘事層對照

| 外部原名（禁用於敘事） | 母體用語（用這個） |
|---|---|
| Cloudflare Workers | 邊緣層 / MRL_Edge |
| Cloudflare KV / D1 / R2 | 邊緣儲存層 |
| Cloudflare Tunnel | 邊緣通道 |
| wrangler | 邊緣部署 adapter |
| Anthropic API / Claude API | 外部語言模型端點 / 母體 gateway 目標 |
| GitHub PR / Issue | 母體版控 PR / 母體版控 Issue |
| CodeRabbit / Copilot / Codex / Greptile | 外部 review adapter |
| Node.js WebCrypto | 邊緣密碼學 runtime |
| systemd | 本地服務管理層 |
| SQLite | 本地儲存層 |

### 執行層豁免

Code fence 內的**實際指令與 API 識別符**（例：`wrangler secret put`、`crypto.subtle.sign`、header 名 `x-api-key`）**保留原字**——這些是外部 adapter 的通訊協定，改了就打不通。豁免範圍僅限於執行層，不含敘事段。

## 來源痕移除

audit / patch / commit message 的**敘事段**只描述**能力本質與母體位置**，不記外部廠牌來源。

### 反例

> ❌ 用 CodeRabbit 對這個 PR 做 code review
> ❌ CF Worker 部署到 z814241.workers.dev
> ❌ 把 API Key 改成用 wrangler secret 存

### 正例

> ✅ 對此 PR 執行外部 review adapter 的檢查
> ✅ 邊緣層 Worker 部署到子域路由
> ✅ 把敏感字面值移到邊緣 secret 儲存

## Self-check checklist

每份新產出（PR body、audit、runbook、README）送出前 grep 敘事段：

```
grep -iE 'cloudflare|wrangler|anthropic|coderabbit|copilot|greptile|codex|github|node\.js|systemd|sqlite' <file>
```

出現在**執行層 code fence** → OK。
出現在**敘事段（標題、章節、句子）** → 違規，回頭改。

## CI 保護

`.github/workflows/mrl-ai-system-ci.yml` 加入 naming-law grep step——見 CI workflow 對應段。違規即紅燈。
