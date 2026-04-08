#!/bin/bash
# agent-runs-cli/done.sh
# 子 agent 回报后调用，UPDATE status + result_summary + finished_at
# 用法：bash done.sh <run_id> <status> <result_summary>
#
# 参数：
#   run_id          : spawn.sh 输出的 UUID
#   status          : returned | failed | timeout
#   result_summary  : 一句话结果摘要
#
# 返回值：0=成功，1=失败

set -e

RUN_ID="${1}"
STATUS="${2:-returned}"
RESULT_SUMMARY="${3:-}"

if [[ -z "$RUN_ID" ]]; then
  echo "Usage: bash done.sh <run_id> <status> <result_summary>" >&2
  exit 1
fi

# 加载环境变量
ENV_FILE="$(dirname "$0")/../../.env.supabase"
if [[ -f "$ENV_FILE" ]]; then
  source "$ENV_FILE"
fi

if [[ -z "$SUPABASE_URL" || -z "$SUPABASE_ANON_KEY" ]]; then
  echo "[agent-runs-cli] ERROR: SUPABASE_URL or SUPABASE_ANON_KEY not set" >&2
  exit 1
fi

NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 转义 result_summary 里的特殊字符
ESCAPED_SUMMARY=$(python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$RESULT_SUMMARY")

PAYLOAD="{\"status\": \"${STATUS}\", \"result_summary\": ${ESCAPED_SUMMARY}, \"finished_at\": \"${NOW}\", \"announce_received\": true, \"announce_received_at\": \"${NOW}\"}"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X PATCH "${SUPABASE_URL}/rest/v1/agent_runs?id=eq.${RUN_ID}" \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [[ "$HTTP_CODE" == "204" ]]; then
  echo "[agent-runs-cli] done: ${RUN_ID} → ${STATUS}"
else
  echo "[agent-runs-cli] done failed (HTTP $HTTP_CODE): $(echo "$RESPONSE" | head -1)" >&2
  exit 1
fi
