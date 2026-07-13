#!/usr/bin/env bash
# origin_signature: MrLiouWord
# Verify the local MRL_AI_SYSTEM install without touching production state.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

# Runtime paths — override the daemon defaults (/etc/mrl, /var/lib/mrl) so this
# script works for unprivileged users (developers, CI runners). Production
# systemd units set their own values in the unit file, so this has no effect
# there. Per-invocation temp dir keeps parallel runs isolated.
: "${MRL_VERIFY_TMP:=$(mktemp -d -t mrl_verify.XXXXXX)}"
export MRL_SIG_KEYDIR="${MRL_SIG_KEYDIR:-$MRL_VERIFY_TMP/keys}"
export MRL_TRACE_JOURNAL="${MRL_TRACE_JOURNAL:-$MRL_VERIFY_TMP/trace.jsonl}"
export MRL_HUB_DB="${MRL_HUB_DB:-$MRL_VERIFY_TMP/memory.sqlite3}"

echo "=== [1/5] Node RelayStation acceptance ==="
if command -v node >/dev/null 2>&1; then
  (cd relay_station && node test/MRL_acceptance_test.js)
else
  echo "  node not installed — skipped"
fi

echo ""
echo "=== [2/5] trace_chain self-check ==="
PYTHONPATH="$HERE/particles" python3 -c "\
import os, json, sys; \
from trace_chain import emit, verify; \
probe = os.environ['MRL_TRACE_JOURNAL']; \
emit('verify.probe', {'from':'verify_all.sh'}, layer='L?', journal=probe); \
r = verify(probe); \
sys.exit(0 if r['ok'] else 1)"
echo "  ok"

echo ""
echo "=== [3/5] sig_verify roundtrip ==="
PYTHONPATH="$HERE/particles" python3 -c "\
from sig_verify.mrl_sig_verify import keypair, sign, verify_sig; \
sk, pk = keypair(); \
assert verify_sig(pk, b'MRL', sign(sk, b'MRL')); \
print('  ed25519 roundtrip ok')"

echo ""
echo "=== [4/5] pytest suite ==="
if command -v pytest >/dev/null 2>&1; then
  PYTHONPATH="$HERE/particles" pytest tests/ -q
else
  echo "  pytest not installed — run 'pip install pytest' to enable"
fi

echo ""
echo "=== [5/5] 命名律檢查 (rl_12) ==="
bash "$HERE/scripts/check_naming_law.sh"

echo ""
echo "=== MRL_AI_SYSTEM verify_all: PASS ==="
