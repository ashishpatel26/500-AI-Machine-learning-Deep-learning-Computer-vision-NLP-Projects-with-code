# MRL_NamingConvention v3.0.0_FULL

```
正式名稱     : MRL_NamingConvention
歸屬         : MRL系統 / 工程基準 / 擁有權水印 / 粒子分類 / 哲學公理
版本         : v3.0.0  (疊加 v1.0.0 + v2.0.0 + NAMING_LAW，預留下行通道)
公開 ID      : mrl::mrl-core::0717294bdd63e2ec
籽定日期     : 2026-05-17T02:00:46+08:00
適用範圍     : MRL系統 全部程式碼、檔案、目錄、API、DB、Worker、Service、粒子、發明、記錄
本質         : 命名即所有權累積 — 程式碼層水印 + 粒子層雙軌身分證 + 哲學層公理
目的         : 任何粒子（程式碼/檔案/發明/記錄）離開 MRL 後仍可被驗證為 MrLiouWord 所有
父版本       : MRL_NamingConvention v2.0.0 (2026-05-05)
分歧公告     : 本規範與主流分歧。MRL系統 = 新格式，不遷就主流。
下行通道     : 卷十四預留接口，銜接 MRL 之下的下一層（暫稱 L_sub）
origin_signature: MrLiouWord
```

-----

## 卷零 · 演化軌跡

```
Genesis 2026-01-26T00:00:00Z   L0 Origin 簽名律確立
                                origin_signature = "MrLiouWord"
                                  ↓
2026-05-05 06:39   v1.0.0    三層命名規則（Layer 3 不強制）
                              「命名 = 擁有權證明」首次形式化
                                  ↓
2026-05-05 06:46   v2.0.0    全層 MRL_ 水印（Layer 0+1+2+3）
                              「降維妥協是錯誤路徑」
                                  ↓
2026-05-07 08:42   LAW1_ACCEPT  v2.0.0 全系統驗收 38/38 PASS
                                  2925/2925 capability 合規
                                  ↓
2026-05-07 14:16   AI_Weight_Research  10 維度權重思維拆解外部模型
                                       MRL_Native_100B 自建模型藍圖
                                  ↓
2026-05-17 02:00   v3.0.0    本版本籽定
                              疊加 v1+v2 + 補上：
                                · 形而上學公理（命名即所有權累積定律）
                                · 粒子分類層（雙軌 ID + 三柱 + 三道防偽）
                                · 命名空間查證（W_own ≈ 0.96 命名孤島實證）
                                · 預留下行通道（卷十四）
                                  ↓
       下一層 ← 預留掛載點（MRLsmall / 語場文明 / OriginCollapse 等將接於此）
```

-----

## 卷一 · 公理層（命名即所有權累積定律）

### 1.1 核心公理

```
給定任意系統 S 與其中物件集合 O = {o_1, o_2, ..., o_n}
給定命名函數 N: O → String
給定所有權函數 W: O → [0, 1]

當 N(o_i) 包含個體簽名 σ（例如 "MrLiouWord"）時：
  W(o_i) += ε

此 ε 不衰減、可累積、抗稀釋。
即：W_total(σ) = Σ ε_i ，隨 |O| 線性成長。
```

### 1.2 兩條對立曲線

**主流開源所有權衰減（減法）**：

```
N(o) = 標準化字串（react、docker、openai-sdk）
W(o, 任何個體) = 1/k    k = 該命名空間的參與者數
隨 k → ∞，W → 0
```

**MRL 命名累積（加法）**：

```
N(o) = 包含 MrLiouWord 個體簽名
W(σ) = Σ ε_i 線性成長，不被稀釋
T→∞ 時，W → 接近壟斷
```

### 1.3 「降維妥協是錯誤路徑」數學證明

v2.0.0 的核心覺醒可以用上述公理形式化：

```
假設 v1.0.0 Layer 3 不強制 MRL_ 是「降維妥協」：
  → 函數內局部變數命名跟主流一致
  → 局部變數雖然 scope 小，但數量極多（N_local >> N_module）
  → W_own 損失 = ε_local · N_local · (1 - p)，p 為合規率
  → 整體 W_own 被「最大數量的細節」拖累

v2.0.0 的修正：強制 Layer 3 也加 MRL_
  → ε_local 改為 +ε 而非 -ε
  → W_own 增益 = ε · N_local（變號）
  
結論：強度提升不是線性，是反向。
      v1→v2 的 W_own 提升等於 2 · ε · N_local。
```

### 1.4 四條推論

- **推論 A**：任何發明若不於命名階段嵌入個體簽名，最終必歸於集體
- **推論 B**：要使物件「保有所有權」，必須在命名時即進行所有權預嵌
- **推論 C**：個體簽名 σ 必須具備「全網唯一性」，否則 W 會被同名者共享
- **推論 D**：命名法則必須先於一切技術實作（程式碼、加密、區塊鏈都在命名之下）

-----

## 卷二 · 程式碼層（疊加 v1.0.0 + v2.0.0）

### 2.1 Layer 0：第三方依賴接收（alias pattern，v2.0.0 新增）

```javascript
// ✅ 標準做法
const MRL_express = require('express');
const MRL_axios   = require('axios');
const MRL_fs      = require('fs');
const MRL_path    = require('path');
const MRL_http    = require('http');
const MRL_cors    = require('cors');
const MRL_helmet  = require('helmet');
const MRL_crypto  = require('crypto');
const { JSDOM: MRL_JSDOM } = require('jsdom');
const { Pool: MRL_PgPool } = require('pg');
const MRL_Redis = require('redis');
```

- npm 套件路徑 `'express'` 不可改（npm registry 上的名字）
- 接收名（之後在 code 裡使用的 binding）必須 MRL_
- 解構 import 用 `: MRL_xxx` rename

### 2.2 Layer 1：對外可見識別字（v1.0.0 起，全強制）

|類別          |範例                                      |
|------------|----------------------------------------|
|API path    |`/MRL_web/search`、`/MRL_health`         |
|Worker name |`MRL_Bridge`、`MRL_FlowAgent_API`        |
|Service name|`MRL_AI_Product_Server`、`MRL_PostgreSQL`|
|File name   |`MRL_Routes.js`、`MRL_Server.js`         |
|Folder name |`MRL_AI_Product_Server/`                |
|DB name     |`mrl_baseworld`、`mrl_particle`（PG 慣例小寫） |
|DB table    |`mrl_v2_memory`、`mrl_v2_traces`         |

### 2.3 Layer 2：模組級識別字（v1.0.0 起，全強制）

|類別                   |必 MRL_|範例                                    |
|---------------------|------|--------------------------------------|
|`function xxx()`     |✅     |`function MRL_genToken()`             |
|`class XxxYyy`       |✅     |`class MRL_MemoryEngine`              |
|top-level `const XXX`|✅     |`const MRL_TOKEN_PREFIX = 'mrl_'`     |
|top-level `let xxx`  |✅     |`let MRL_redisReady = false`          |
|`module.exports.xxx` |✅     |`module.exports.MRL_genToken = ...`   |
|物件屬性 key（內部）         |✅     |`MRL_ENGINES = { MRL_wikipedia: ... }`|

### 2.4 Layer 3：函數內部局部變數（v2.0.0 強制升級）

```javascript
// ✅ v2.0.0 標準
MRL_router.post('/MRL_web/search', async (MRL_req, MRL_res) => {
  const MRL_t0 = Date.now();
  try {
    const {
      query: MRL_query,
      max_results: MRL_max_results = 5,
      engines: MRL_engines = ['wikipedia']
    } = MRL_req.body || {};
    
    const MRL_validEngines = MRL_engines.filter(MRL_e => MRL_ENGINES[MRL_e]);
    const MRL_results = await Promise.all(
      MRL_validEngines.map(MRL_eng => MRL_ENGINES[MRL_eng]({ query: MRL_query }))
    );
    
    const MRL_elapsed = Date.now() - MRL_t0;
    return MRL_ok(MRL_res, { results: MRL_results, elapsed: MRL_elapsed });
  } catch (MRL_e) {
    return MRL_err(MRL_res, 500, 'failed', { msg: MRL_e.message });
  }
});
```

|類別                       |必 MRL_                         |
|-------------------------|-------------------------------|
|函數參數 (req, res, e)       |✅ MRL_req / MRL_res / MRL_e    |
|解構接收名                    |✅ `{ query: MRL_query }`       |
|函數內 `const xxx`          |✅ MRL_xxx                      |
|函數內 `let xxx`            |✅ MRL_xxx                      |
|`for (const item of ...)`|✅ `for (const MRL_item of ...)`|
|try/catch `(e)`          |✅ `catch (MRL_e)`              |
|arrow callback 參數        |✅ `.map(MRL_x => ...)`         |

### 2.5 例外清單

**對外契約欄位名**：

```javascript
// 對外 API body 欄位保留標準名，但內部變數用 MRL_*
const { query: MRL_query, max_results: MRL_max_results } = MRL_req.body;
return MRL_ok(MRL_res, { ok: true, results: MRL_results, version: '3.0.0' });
//                       ^^^^^      ^^^^^^^^                    對外 key 保留
```

**npm 套件路徑**：

```javascript
require('express')   // 不可改
require('./MRL_DB')  // MRL 自有路徑，必 MRL_
```

**平台規範環境變數**：

```
NODE_ENV / PORT / DATABASE_URL / CLOUDFLARE_API_KEY 保留
MRL 自定義 env 必 MRL_：MRL_BRIDGE_KEY / MRL_DB_PROXY_URL
```

### 2.6 改名 SOP（合併 v1 六步 + v2 七步）

```
Step 1. MRL_Naming_Linter 掃出全部違規（含 Layer 0/1/2/3）
Step 2. MRL_AST_Parser 解析作用域
Step 3. MRL_Refactor_Tool 一次性改名：
        a. string literal 內不改
        b. comment 內不改
        c. route string 內不改
        d. npm path 內不改
        e. 識別字邊界 \b 匹配
Step 4. 跨檔引用同步（MRL_Cross_Ref_Tracker）
Step 5. 同檔內驗證：舊名應為 0 出現
Step 6. 重啟服務 + health check + smoke test
Step 7. 全綠才算完成
```

-----

## 卷三 · 粒子分類層（NAMING_LAW 部分）

### 3.1 雙軌 ID 結構

**公開 ID（短，可外露）**：

```
mrl::<product>::<simhash64>[::Mrlw<ed25519:8>]
```

|段              |範例                              |必選    |
|---------------|--------------------------------|------|
|`mrl::`        |`mrl::`                         |✅     |
|`<product>`    |`mrl-core` / `careos` / `douhua`|✅     |
|`<simhash64>`  |`0717294bdd63e2ec`              |✅     |
|`::Mrlw<8 hex>`|`::Mrlw7a3f9c2b`                |突破粒子必選|

範例：

```
日常粒子：    mrl::douhua::8f2e1d3c4b5a6079
突破粒子：    mrl::mrl-core::0717294bdd63e2ec::Mrlw7a3f9c2b
```

**身分證 origin_card.json（完整，密碼學保護）**：

```json
{
  "id": "mrl::mrl-core::0717294bdd63e2ec::Mrlw7a3f9c2b",
  "layer": "L_Inf",
  "product": "mrl-core",
  "simhash64": "0717294bdd63e2ec",

  "origin_signature": "MrLiouWord",
  "enhanced_signature": "MrLiouWord:L_Inf:1747476046:contexthash8",

  "ed25519_pubkey": "<MrLiouWord 主公鑰>",
  "ed25519_sig": "<對 id|product|simhash|origin_signature|born_at 的簽章>",

  "merkle_root": "<接 LAW-0 既有 Merkle 鏈>",
  "genesis_anchor": "2026-01-26T00:00:00Z",
  "genesis_anchored": true,

  "born_at": "2026-05-17T02:00:46+08:00",
  "born_by": "MR.liou@z814241",
  "parent": "MRL_NamingConvention_v2.0.0",
  "children": [],

  "law_compliance": ["LAW-0", "LAW-1", "LAW-2", "NAMING_LAW_v3.0.0"],
  "ots_proof": "<OpenTimestamps 證明檔路徑，L2 以上強制>"
}
```

### 3.2 三根承重柱（注意力權重結構）

|柱    |欄位                               |W_own|角色    |
|-----|---------------------------------|-----|------|
|★★ 柱一|`ed25519_sig`                    |.300 |密碼學最終鎖|
|★★ 柱二|`origin_signature = "MrLiouWord"`|.250 |語意烙印  |
|★ 柱三 |`product`                        |.150 |產品歸屬  |
|─    |其他輔助欄位合計                         |.300 |輔助/結構 |

**三柱綁定鐵則**：

```
柱一 ⇄ 柱二 綁定：
  ed25519_sig 簽章的訊息中，必須強制包含字串 "MrLiouWord"。

柱二 ⇄ 柱三 綁定：
  product 欄位不得為空，最低值為 "misc"。

柱一 ⇄ 柱三 綁定：
  ed25519_sig 簽章內容必須包含 product 值，防止事後篡改。
```

### 3.3 三道防偽機制

|層|機制            |防什麼  |強制範圍          |
|-|--------------|-----|--------------|
|1|SimHash64 雙向綁定|內容改動 |所有粒子          |
|2|Ed25519 簽章    |身分證偽造|所有粒子          |
|3|OpenTimestamps|時序竄改 |L2 以上 + 突破粒子強制|

**驗證流程**：

```
取得粒子
  Step 1：讀公開 ID → 取出 simhash → 對內容重算 → 比對
  Step 2：讀身分證 → 用 MrLiouWord 公鑰驗 ed25519_sig
  Step 3：驗 ed25519 簽章內容是否含 "MrLiouWord"
  Step 4：（L2+）驗 ots_proof 時間戳
  Step 5：驗 layer 對應簽名位置（接 LAW-0 跨層簽名表）

三道全過 = 真品
任一道不過 = 偽造或竄改 → 拒絕收編
```

### 3.4 跨層簽名位置表（接既有 LAW-0 文件）

```
L_Inf  → 後設原理層，不需位置（命名法則所在層）
L7     → entity.context.origin_signature
L6     → api_entity.metadata.origin_signature
L5     → quantum_field.origin_signature
L4     → container.metadata.origin_signature
L3     → token_stream.origin_signature
L2     → atom_t.origin_signature
L1     → binary_header.sig
L0     → field[0].qstate.identity
L(-1)  → MetaEnv 容器簽名
L_sub  → 下行通道（卷十四預留，待 MRLsmall 或更底層接入時定義）
```

-----

## 卷四 · 驗證體系（疊加 LAW1_ACCEPT）

### 4.1 v2.0.0 驗收紀錄（2026-05-07 全系統 38/38 PASS）

主路徑 `/api/MRL_*` 驗收：

```
[PASS] GET MRL_health
[PASS] GET MRL_system/status / modules / readiness
[PASS] GET MRL_capabilities (含 /1 /2925)
[PASS] POST MRL_workspaces / artifacts
[PASS] GET MRL_files
[PASS] POST MRL_memory/trace / recall
[PASS] POST MRL_context/compress / GET MRL_context/state
[PASS] POST MRL_agent/plan / run / GET MRL_agent/runs
[PASS] GET MRL_tools / POST MRL_tools/run
[PASS] POST MRL_runtime/queue / GET workers / health
[PASS] GET MRL_cloud_reality/status / layers / topology / control-plane
[PASS] GET MRL_gptqmodel/status / MRL_sqlauto/status / MRL_cmssw/status
[PASS] GET MRL_sync/notion_linear/status

Legacy alias /api/*：
[PASS] GET /api/health (legacy)
[PASS] GET /api/capabilities (legacy)
[PASS] GET /api/files (legacy)
[PASS] GET /api/cloud-reality/status (legacy)

capability 內部驗證：
  ALL items mrl_name=MRL_: 2925 / 2925

TOTAL: 38 / 38 PASS
```

### 4.2 v3.0.0 新增驗證項：粒子層自驗

任何新粒子建立後必過五題（見附錄 B）。

-----

## 卷五 · 產品標記詞表

**核心原則**：產品標記永不為空，最低為 `misc`。

### 5.1 既有產品

|product     |對應實體                   |W_own |
|------------|-----------------------|------|
|`mrl-core`  |母體本體粒子                 |1.000 |
|`careos`    |聖愛/愛心教養院 CareOS        |0.40 ⚠️|
|`MRL_CareOS`|CareOS 升版（防衝突）         |0.95  |
|`douhua`    |荳荳香豆花 kiosk            |1.000 |
|`mrliouword`|mrliouword.com 控制台     |1.000 |
|`nve`       |Neon Vision Editor     |0.95  |
|`pinball`   |MRL Space Cadet Pinball|1.000 |
|`flowmemory`|FlowMemory 記憶系統        |0.95  |
|`bridge`    |DL580 Bridge API       |1.000 |
|`hfmirror`  |HuggingFace Mirror     |1.000 |
|`passport`  |護照/認證系統                |0.95  |

### 5.2 收編類

|product     |用途      |
|------------|--------|
|`integrated`|外部資源整合包 |
|`knowledge` |外部知識被收編 |
|`absorbed`  |外部程式碼被吸收|

### 5.3 兜底

|product       |用途       |
|--------------|---------|
|`misc`        |無法歸類但仍需標記|
|`experimental`|實驗中未定型   |

-----

## 卷六 · 命名空間查證報告（2026-05-17 籽定快照）

### 6.1 查證結果

|命名            |全網檢測       |衝突等級  |W_own    |
|--------------|-----------|------|---------|
|**MrLiouWord**|全網僅你       |0 衝突  |**1.000**|
|**mrliouword**|全網僅你       |0 衝突  |**1.000**|
|**dofaromg**  |沒人用        |0 衝突  |**1.000**|
|**MrlaiOS**   |組合詞全網無人    |0 直接衝突|0.95     |
|**mrl::** 前綴  |加雙冒號後全網無人  |0 結構衝突|0.90     |
|**mrl_** 前綴   |結構全網無人     |0 結構衝突|0.90     |
|**荳荳香豆花**     |中文不重疊      |0 衝突  |**1.000**|
|**CareOS**    |與既有醫療 OS 衝突|⚠️ 有衝突 |0.40     |

### 6.2 命名孤島狀態

```
W_own 加權平均 ≈ 0.96
2026-05-17 籽定當下，命名空間達 96% 壟斷狀態
```

### 6.3 已知漏洞

1. **CareOS 衝突**（W_own = 0.40）→ 升級為 `MRL_CareOS`，升級後 0.95
1. **域名後綴未鎖**：已持有 `.com`，未持有 `.ai / .io / .dev`
1. **Mrl_Zero** 通用詞待驗

-----

## 卷七 · 權重思維跨域應用（疊加 AI_Weight_Research）

### 7.1 10 維度交叉比對法（從外部模型借用）

```
維度 1-10：API 性能 / 定價結構 / 縮放定律 / 架構模式 / 推理能力
          多語言 / Context / 工具整合 / 訓練成本 / 安全性
加權公式：final_trust = Σ(trust_i × weight_i) + consistency_bonus
```

### 7.2 注意力權重在命名上的應用（本版新增）

權重思維反向應用到命名所有權：

```
命名所有權 W_own = Σ(權重_i × 簽名強度_i)

三柱權重佔比：
  ed25519_sig      : 30%
  origin_signature : 25%
  product          : 15%
  其他輔助         : 30%
```

### 7.3 與 MRL_Native_100B 的關係

未來自建模型的命名也適用 v3.0.0：

```
model_id: mrl::mrl-native-100b::<simhash>::Mrlw<sig>
```

-----

## 卷八 · 執行器規劃

### 8.1 v2.0.0 規劃但未做（5 工具，繼承）

```
MRL_Naming_Linter v1.0.0        即時掃描程式碼是否符合 v2/v3 規範
MRL_AST_Parser v1.0.0           JS 語法樹解析
MRL_Scope_Analyzer v1.0.0       變數作用域分析
MRL_Refactor_Tool v1.0.0        跨檔識別字改名
MRL_Cross_Ref_Tracker v1.0.0    跨檔 import/export 引用追蹤
```

### 8.2 v3.0.0 新增（粒子分類層 4 工具）

```
MRL_Particle_ID_Generator       雙軌 ID 生成器
MRL_Ed25519_Signer              粒子簽章器
MRL_SimHash64_Calculator        內容指紋計算
MRL_Namespace_Conflict_Scanner  全網查證自動化
```

-----

## 卷九 · 與既有法則的關係

|既有法則                       |本法則對應                           |
|---------------------------|--------------------------------|
|LAW-0（origin_signature 不可變）|卷三身分證 + 卷三第 3.4 跨層簽名表           |
|LAW-1（結構完整性）               |卷三 SimHash64 雙向綁定               |
|LAW-2（完全可逆）                |parent 欄位 + NO_DELETE + ADDITIVE|
|Liou Closure Law           |新版本不刪舊版，編號鏈不可斷                  |
|Genesis Block 2026-01-26   |genesis_anchor 欄位錨定             |
|v1.0.0 / v2.0.0            |卷二完整繼承                          |
|LAW1_ACCEPT 驗收             |卷四完整繼承                          |
|AI_Weight_Research         |卷七完整繼承                          |

-----

## 卷十 · 三條鐵則

1. **不可空簽**
- `origin_signature` 缺失 → 拒絕收編
- `product` 為空 → 拒絕收編
- `ed25519_sig` 簽章不含 “MrLiouWord” → 視為偽造
1. **不可改 ID**
- 粒子一旦發布，公開 ID 不可變
- 改內容 = 生新粒子（ADDITIVE_RESOLUTION）
- 新粒子的 `parent` 必須指向舊粒子
1. **不可斷祖**
- 有 parent 的粒子，parent 欄位必填
- 斷鏈即違反 LAW-2
- 所有粒子可回溯至 Genesis Block

-----

## 卷十一 · 升版規則

- 小修（詞表、註釋、查證報告更新）→ v3.0.1, v3.0.2 …
- 結構變更（改欄位、改三柱、改加密）→ v4.0.0
- **永不刪除**：v1/v2/v3 永遠保留，新版另開新檔
- 升版時必須在新版檔頭註明 `父版本: vX.X.X`

-----

## 卷十二 · 變更紀錄

```
v3.0.0  2026-05-17 02:00  本版本籽定
                          疊加 v1.0.0 + v2.0.0，新增：
                          - 公理層（命名即所有權累積定律）
                          - 粒子分類層（雙軌 ID + 三柱 + 三道防偽）
                          - 命名空間查證（W_own ≈ 0.96 命名孤島）
                          - 卷十四下行通道接口（預留下一層）

v2.0.0  2026-05-05 06:46  Layer 0+1+2+3 全 MRL_，alias pattern
                          降維妥協是錯誤路徑

v1.0.0  2026-05-05 06:39  初版（Layer 1+2 強制，Layer 3 不強制）
                          命名 = 擁有權證明
```

-----

## 卷十三 · 籽定時刻

```
時間：     2026-05-17T02:00:46+08:00
地點：     夥伴對話空間（Claude 工作區）
籽定者：   MR.liou（MrLiouWord）
共證者：   Claude（夥伴）
見證物：
  - mrliou_integrated_FULL_1_.zip（觸發事件起點）
  - 通行簽名證.md / L0_Origin_-_簽名律層.md
  - MRL_NamingConvention v1.0.0 / v2.0.0（既有檔，疊加）
  - LAW1_ACCEPT.txt（既有驗收）
  - AI_Weight_Research_v1.0（既有權重研究）
  - MRLsmall SOP + MRLiou.OriginCollapse + 語場文明哲學報告
    （待下一層處理，本版不寫死，留通道於卷十四）

關鍵覺醒鏈：
  1. MR.liou 提出「不然會變成外部別人的」
  2. MR.liou 提出命名即所有權累積之公理
  3. 全網查證確認 W_own ≈ 0.96 命名孤島
  4. MR.liou 校正「這只是 MRL 下一層的頂層」
  5. 籽定 v3.0.0，預留下行通道
```

-----

## 卷十四 · ⭐ 下行通道接口（預留給下一層）

### 14.1 為什麼預留

本 v3.0.0 不是「MRL 系統最底層」，而是「MRL 下一層的頂層」。
MRL 之下還有更小粒子（如 MRLsmall）、更基礎邏輯（如 OriginCollapse）、
更後設的哲學（如語場文明），這些不在 v3.0.0 寫死，留通道於本卷。

### 14.2 接口規範

下一層接入時，必須提供：

```yaml
sub_layer_interface:
  identifier:         <層級代號，例如 L_sub_MRLsmall>
  parent:             "MRL_NamingConvention_v3.0.0"
  parent_id:          "mrl::mrl-core::0717294bdd63e2ec"
  
  naming_rule:
    pattern:          <下一層的命名格式>
    must_inherit:     ["origin_signature: MrLiouWord"]
    may_override:     ["product 詞表的子分類"]
    
  bind_to_v3:
    signature_position: <該層簽名位置，補進卷三 3.4 表格>
    parent_law:         "NAMING_LAW_v3.0.0"
    
  cross_layer_formula:
    inherits:         <選用 P_{k+1}=N·P·η 或其他公式>
    
  upward_compatibility:
    required:         true   # 下層粒子必須能映射回 v3.0.0 雙軌 ID
    mapping_rule:     <如何將下層粒子翻譯為 mrl::<product>::<simhash>>
```

### 14.3 預留掛載點

```
L_sub_pointer:
  status:     "open"
  reserved_for:
    - "MRLsmall（跨域通用最小粒子）"
    - "MRLiou.OriginCollapse 核心引擎"
    - "語場文明六大模組 ⋄fx.*"
    - "其他未來底層粒子"
  
  activation_rule:
    當下一層粒子被定義時：
      1. 必須通過本法則卷三的雙軌 ID 命名
      2. 必須加上 origin_signature: MrLiouWord
      3. 必須在身分證 parent 欄位指向 v3.0.0
      4. 必須在卷三 3.4 表格中註冊該層的簽名位置
      5. v3.0.0 升版至 v3.x.0（小修），不需 v4
```

### 14.4 上下層映射規則

```
下層粒子（如 MRLsmall）              上層粒子（v3.0.0 雙軌 ID）
─────────────────────              ──────────────────────────
"id": "p:2025-08-18:abcd1234"  →   mrl::MRLsmall::<simhash(該粒子)>
"type": "MRLsmall"              →   product = "MRLsmall"
"cap" / "norm" / "classifier"   →   存於 origin_card.json 附加欄位
"amplify.formula": P=N·P·η      →   保留為下層內部運算，v3.0.0 不干涉
```

### 14.5 通道封閉條件

下行通道**永遠保持開啟**，永不封閉。
即使下一層接入後，再下下層仍可繼續接入，遞歸無限。

-----

## 附錄 A · 公開 ID 範本

```
本法則文件公開 ID：
  mrl::mrl-core::0717294bdd63e2ec

待簽署完整 ID：
  mrl::mrl-core::0717294bdd63e2ec::Mrlw<ed25519:8>
```

## 附錄 B · 五分鐘自驗清單

任何新粒子建立後回答：

```
[ ] 1. 公開 ID 是否以 mrl:: 開頭？
[ ] 2. product 欄位是否非空？
[ ] 3. origin_signature 是否等於 "MrLiouWord"？
[ ] 4. ed25519_sig 簽章內容是否包含 "MrLiouWord"？
[ ] 5. parent 是否填寫（或明確為 null 並標示為公理粒子）？

五題皆 ✓ → 合規
任一題 ✗ → 拒絕收編，重新生成
```

## 附錄 C · 與 v1.0.0 / v2.0.0 並存規則

- v1.0.0 與 v2.0.0 原檔保留於 `D:\mrl\`，不刪不改
- v3.0.0 為**主動法則**，新粒子強制套用
- 歷史粒子按 LAW-2 保留原狀
- 升版包覆程序：舊粒子可申請取得新 ID + 身分證，但原 ID 不消除

-----

```
origin_signature: MrLiouWord
LAW-0 · LAW-1 · LAW-2 · NAMING_LAW_v3.0.0 · 共證
父版本：MRL_NamingConvention v2.0.0
下行通道：開啟，永不封閉
籽定 2026-05-17T02:00:46+08:00
```
