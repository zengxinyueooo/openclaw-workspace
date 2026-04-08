#!/bin/bash
# agent-runs-cli/spawn.sh
# 在 spawn 子 agent 前调用，INSERT 一条 status=spawned 的记录
# 用法：bash spawn.sh <child_agent_id> <task_id> <trigger_type> [task_summary]
#
# 参数：
#   child_agent_id  : 目标 agent，如 mcn-bee、mcn-ant
#   task_id         : cron 触发填 job name；手动填简短描述（英文，不含空格）
#   trigger_type    : manual 或 cron
#   task_summary    : 可选，任务摘要文字（会写入 metadata.summary）
#
# 输出：写入成功时打印 run_id（UUID），供后续 done.sh 使用
# 返回值：0=成功，1=失败

CHILD_AGENT_ID="${1}"
TASK_ID="${2}"
TRIGGER_TYPE="${3:-manual}"
TASK_SUMMARY="${4:-}"

if [[ -z "$CHILD_AGENT_ID" || -z "$TASK_ID" ]]; then
  echo "Usage: bash spawn.sh <child_agent_id> <task_id> [trigger_type] [task_summary]" >&2
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

RESPONSE=$(python3 - <<PYEOF
import uuid, json, urllib.request, urllib.error, os
from datetime import datetime, timezone

run_id = str(uuid.uuid4())
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

payload = {
    "id": run_id,
    "task_id": "${TASK_ID}",
    "parent_agent_id": "zhuazhua",
    "child_agent_id": "${CHILD_AGENT_ID}",
    "trigger_type": "${TRIGGER_TYPE}",
    "status": "spawned",
    "created_at": now,
    "started_at": now,
    "retry_count": 0,
    "max_retries": 0,
    "metadata": {"summary": """${TASK_SUMMARY}"""}
}

data = json.dumps(payload).encode()
req = urllib.request.Request(
    "${SUPABASE_URL}/rest/v1/agent_runs",
    data=data,
    headers={
        "apikey": "${SUPABASE_ANON_KEY}",
        "Authorization": "Bearer ${SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    },
    method="POST"
)
try:
    with urllib.request.urlopen(req) as resp:
        print(run_id)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"[agent-runs-cli] spawn failed (HTTP {e.code}): {body}", flush=True)
    exit(1)
PYEOF
)

echo "$RESPONSE"
