# mrl-sig-verify (邊緣 Worker)

`origin_signature: MrliouAI`
`layer: L0 (Origin — signature law)`
`replaces: particle-sig-verify（30 行 stub，見稽核報告 §3.2）`

母體 `MRL_AI_SYSTEM/particles/sig_verify/mrl_sig_verify.py` 對應的邊緣層 Worker。
使用邊緣密碼學 runtime 的 Ed25519 (`crypto.subtle`) 做真簽名/驗證——沒有 pure-JS crypto，
零外部相依。

## 與母體 daemon 的能力對齊

| Endpoint | 母體 daemon (`:8801`) | 邊緣 Worker | 說明 |
|---|---|---|---|
| `GET /health` | ✅ | ✅ | 相同 JSON 結構（多一個 `algorithm` 除錯欄位） |
| `GET /public_key` | ✅ | ✅ | 回傳 `raw` base64 + `jwk` 兩種格式 |
| `POST /sign` | ✅ | ✅ + auth | 邊緣版加 `X-Sign-Auth` header 需求 |
| `POST /verify` | ✅ | ✅ | 兩者皆 public——驗證簽名本就該開放 |

`/sign` 加驗證是因為邊緣 Worker 對外，母體 daemon 綁 `127.0.0.1` 靠 OS 存取控制。

## 設計決策

- **金鑰放邊緣儲存層**：`MRL_SIG_KEYS[mrl_ed25519_v1] = {privateJwk, publicJwk, publicKeyRawB64, createdAt}`
- **首發生成**：冷啟動時邊緣儲存層為空則產生新 keypair。兩個 isolate race 時皆為有效對，後續驗證都能通
- **JSON 訊息 canonicalize**：object 訊息以排序鍵 `JSON.stringify`，結構相等的 payload 產生相同簽名
- **私鑰不出邊緣**：`privateJwk` 只存在 Worker 記憶體與邊緣儲存層——不會出線
- **runtime 偵測**：邊緣 runtime 自 2024 起接 `Ed25519` 標準名，冷啟動 probe 一次，舊 runtime fallback 到 `NODE-ED25519`

## 邊緣部署 adapter 設定

```bash
# 1. Create the KV namespace
wrangler kv:namespace create MRL_SIG_KEYS
# → paste the returned id into wrangler.toml's [[kv_namespaces]].id

# 2. Set the sign-auth secret (any high-entropy string)
openssl rand -hex 32 | wrangler secret put SIGN_SECRET --name mrl-sig-verify

# 3. Deploy
wrangler deploy --name mrl-sig-verify
```

## 兩條部署路徑（稽核報告 §3.2 建議）

### Path A — 覆蓋 stub 命名

改邊緣部署設定的 `name` 直接覆蓋既有 stub：

```diff
- name = "mrl-sig-verify"
+ name = "particle-sig-verify"
```

好處：既有指向 `particle-sig-verify` 子域路由的 consumer 自動升級到真簽名。
代價：一次性遷移；port 有 bug stub 就消失。

### Path B — 雙軌並存

以 `mrl-sig-verify` 部署，保留 stub。consumer 逐一遷移。

好處：遷移安全。
代價：遷移期間兩個 Worker 都要維護。

## Smoke test after deploy

```bash
# 1. Health
curl -s https://mrl-sig-verify.z814241.workers.dev/health | jq
# Expect: algorithm = "Ed25519" (or "NODE-ED25519" on older runtimes)

# 2. Fetch public key
PUBKEY=$(curl -s https://mrl-sig-verify.z814241.workers.dev/public_key | jq -r .public_key_b64)
echo "$PUBKEY" | wc -c  # 44 chars (32 bytes base64 + padding)

# 3. Sign a message
SIG=$(curl -sX POST https://mrl-sig-verify.z814241.workers.dev/sign \
  -H "Content-Type: application/json" \
  -H "X-Sign-Auth: $SIGN_SECRET" \
  -d '{"message": "MRL hello"}' | jq -r .signature_b64)

# 4. Verify — should succeed
curl -sX POST https://mrl-sig-verify.z814241.workers.dev/verify \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"MRL hello\", \"signature_b64\": \"$SIG\"}" | jq
# Expect: { "ok": true }

# 5. Verify with tampered message — should fail
curl -sX POST https://mrl-sig-verify.z814241.workers.dev/verify \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"MRL tampered\", \"signature_b64\": \"$SIG\"}" | jq
# Expect: { "ok": false }
```

## 本機測試（母體 runtime）

母體 runtime v18+ 內建 WebCrypto Ed25519（`--experimental-webcrypto` 或穩定支援）。
`test/roundtrip.test.js` 走同一組 code path，不需邊緣部署 adapter：

```bash
npm test
```

## 邊緣層 vs 母體 daemon 取捨

| | 邊緣 Worker | 母體 daemon (particles/sig_verify) |
|---|---|---|
| 延遲 | ~10-30ms 全球邊緣 | <1ms localhost |
| 金鑰隔離 | 邊緣儲存層（需邊緣端存取控制） | 母體 OS 使用者、`/etc/mrl/keys/`、0600 權限 |
| 可用性 | 邊緣 SLA 99.99% | 綁母體主機 uptime |
| 認證範圍 | 對外，需 SIGN_SECRET | localhost，走 OS ACL |
| 成本 | 邊緣免費額度 100k req/day | $0（用母體 CPU） |

兩者**互補**：邊緣 Worker 服務無法回母體的邊緣元件；母體 daemon 走母體平台內部熱路徑。
