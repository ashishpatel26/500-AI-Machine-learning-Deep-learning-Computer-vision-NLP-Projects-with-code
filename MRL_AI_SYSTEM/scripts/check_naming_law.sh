#!/usr/bin/env bash
# origin_signature: MrLiouWord
# rl_12 命名律檢查——掃描敘事層是否引用外部廠牌名。
# 執行層 code fence（```…```）豁免。
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

# 待檢查的敘事檔（markdown + PR 樣板 + README）
FILES=$(find . \
  -type f \
  \( -name '*.md' \) \
  -not -path './node_modules/*' \
  -not -path './.git/*' \
  -not -path './tests/.artifacts/*' \
  -not -path './mother_platform/MRL_ParticleArchive/*' \
  -not -path './mother_platform/MRL_DELIVERY_MANIFEST_*' \
  -not -path './docs/MRL_DELIVERY_MANIFEST_*' \
  -not -path './docs/MRL_Naming_Law.md' \
  -not -path './docs/STAGE3_WORKER_AUDIT_*' \
  -not -path './edge_workers/patches/*P0.md')

# 例外說明:
# - MRL_DELIVERY_MANIFEST_* 是歷史事件記錄檔,含"Cloudflare env.AI"事件本身描述,
#   改它會篡改歷史。豁免。
# - STAGE3_WORKER_AUDIT_* 是稽核歷史,含被稽核對象的原始名稱。豁免。
# - *P0.md 是外部 adapter 執行 runbook,含實際指令。豁免。
# - MRL_Naming_Law.md 是規範本身,舉反例時必須引用禁字。豁免。

# 敘事層禁字（rl_12 命名律）
BANNED='cloudflare|wrangler|anthropic|coderabbit|copilot|greptile|codex|github\.com|node\.js|systemd|sqlite'

violations=0
for f in $FILES; do
  # 抽掉 code fence 與 inline `code`,只掃敘事段
  narrative=$(awk 'BEGIN{skip=0} /^```/{skip=1-skip;next} skip==0{print}' "$f" | \
              sed 's/`[^`]*`//g')
  # 大小寫敏感:敘事層是小寫廠牌名,大寫 ALL_CAPS 是環境變數/常數識別符(豁免)
  if echo "$narrative" | grep -En "$BANNED" >/dev/null; then
    echo "── 違規 $f ──"
    echo "$narrative" | grep -En --color=always "$BANNED" | head -8
    echo ""
    violations=$((violations+1))
  fi
done

if [ "$violations" -eq 0 ]; then
  echo "✅ 命名律通過（0 個檔案違規）"
  exit 0
else
  echo "❌ $violations 個檔案的敘事段引用外部廠牌名"
  echo "   規則見 docs/MRL_Naming_Law.md"
  exit 1
fi
