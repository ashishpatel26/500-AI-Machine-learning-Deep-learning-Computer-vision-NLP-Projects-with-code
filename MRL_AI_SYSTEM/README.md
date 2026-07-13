# MRL_AI_SYSTEM

`origin_signature: MrliouAI`

MRL AI 母體整合系統。把三段既有交付物（母體 relay、母體平台、800AI 組織）
與 Stage 3 新建的四個核心 daemon（sig-verify、system-hub、doctor、smartbody v2）
接成一個可部署、可觀測、可自我修復的完整拓撲。

> 本目錄目前作為 monorepo 子樹存在於這個 500-AI repo 底下。之後可整體遷出到獨立
> `MRL_AI_SYSTEM` repo，不需要改任何相對路徑。

## 拓撲

```
外界流量  ─── HTTPS ───►  edge_workers/auth_gateway   (Cloudflare Worker)
                              │
                              ▼
                       edge_workers/ai_gateway        (Cloudflare Worker, 限流 + 追蹤)
                              │  Tunnel
                              ▼
        ┌──────────────────  母體端  ──────────────────┐
        │                                              │
        │   particle-boot  ─►  boot.manifest.json      │
        │        │                                     │
        │        ├─ particles/sig_verify   (L0, 8801)  │
        │        ├─ particles/system_hub   (L6, 9000)  │
        │        ├─ particles/doctor       (L5, 8788)  │
        │        └─ particles/smartbody_v2 (L4, 8787)  │
        │                                              │
        │   共享神經：particles/trace_chain             │
        │                                              │
        │   高階應用：                                  │
        │     • mother_platform  (母體對外平台)         │
        │     • relay_station    (Node.js 粒子中繼)     │
        └──────────────────────────────────────────────┘
```

## 目錄

| 路徑 | 用途 |
|---|---|
| `particles/trace_chain/`   | L0-L7 共用的 append-only Merkle 神經 |
| `particles/sig_verify/`    | Ed25519 簽名驗證 daemon（L0 簽名律） |
| `particles/system_hub/`    | 大腦中樞：800AI 路由 + 七層 MemoryVault |
| `particles/doctor/`        | 健康監控 + 自動重啟守護 |
| `particles/smartbody_v2/`  | 感知/動作/反射身體 daemon |
| `particles/boot/`          | 有序啟動器 + 本地服務單元 + boot.manifest |
| `edge_workers/auth_gateway/` | 邊緣 Worker：JWT 驗證 |
| `edge_workers/ai_gateway/`   | 邊緣 Worker：限流 + 追蹤鏡像 |
| `relay_station/`           | 母體粒子中繼站 |
| `mother_platform/`         | Python 母體平台（含 09_workflow 模組、AbsorbedArtifacts） |
| `scripts/`                 | 本機開發/驗證/煙霧測試 |
| `tests/`                   | 跨粒子 pytest |
| `docs/`                    | ARCHITECTURE、部署指南、DELIVERY_MANIFEST |

## 快速啟動（本機開發）

```bash
# 一鍵：先本機起 sig-verify、system-hub、doctor、smartbody
cd MRL_AI_SYSTEM
python3 -m pip install -U pytest  # 唯一「開發」需求；runtime 零依賴
python3 particles/boot/mrl_boot.py --dry-run
python3 particles/boot/mrl_boot.py
```

停止：`python3 particles/boot/mrl_boot.py --stop`

## 生產部署（本地服務管理層）

```bash
sudo cp particles/boot/systemd/*.service /etc/systemd/system/
sudo cp particles/boot/systemd/mrl.target /etc/systemd/system/
sudo useradd --system --home-dir /var/lib/mrl mrl || true
sudo mkdir -p /opt/mrl/ai-system /etc/mrl /var/lib/mrl /var/log/mrl
sudo cp -r . /opt/mrl/ai-system/MRL_AI_SYSTEM/
sudo systemctl daemon-reload
sudo systemctl enable --now mrl.target
```

## 驗收

```bash
bash scripts/verify_all.sh          # 各 daemon 健康 + trace 鏈完整性
python3 -m pytest tests/            # 跨粒子端到端測試
```

## 命名律

所有母體主體只使用 `MRL_` 前綴 / `origin_signature: MrliouAI`。外部產物只作
adapter/reference，不作母體主名（依 `mother_platform/MRL_DELIVERY_MANIFEST_20260531.md`
中的 rl_12 命名回收原則）。

## Audit history

- **2026-07-10** — [Stage 3 系統級 Workers 補查稽核報告](docs/STAGE3_WORKER_AUDIT_20260710.md)
  - 追查 CareOS 復盤報告 (2026-03-11) 中 5 個「待確認」系統級 Workers
  - 發現：`particle-sig-verify` 為 stub；`particle-system-hub` 有 `DL580_KEY` 硬編碼；`particle-auth-gateway` 用 XOR 弱加密
  - 建議動作：3 個 P0 安全問題需在 24 小時內完成 rotation（與報告七章對齊）
