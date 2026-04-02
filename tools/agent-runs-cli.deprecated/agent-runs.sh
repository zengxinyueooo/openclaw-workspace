#!/usr/bin/env bash
# agent-runs.sh - Agent Runs 管理 CLI
# 用法:
#   agent-runs.sh create <task_id> <parent> <child> <trigger_type>  创建 run (status=spawned)
#   agent-runs.sh start <run_id>                                    标记开始 (status=running)
#   agent-runs.sh returned <run_id> [summary]                       标记返回 (status=returned)
#   agent-runs.sh fail <run_id> [reason]                            标记失败 (status=failed)
#   agent-runs.sh timeout <run_id> [reason]                         标记超时 (status=timeout)
#   agent-runs.sh update <run_id> <field> <value>                   更新任意字段
#   agent-runs.sh get <run_id>                                      查询单条
#   agent-runs.sh list [status]                                     列出 (可选按状态)
#   agent-runs.sh check                                             巡检异常

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../../.env.supabase"

if [[ -f "$ENV_FILE" ]]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

: "${SUPABASE_URL:?SUPABASE_URL not set}"
# Prefer SERVICE_KEY, fall back to ANON_KEY
SB_KEY="${SUPABASE_SERVICE_KEY:-${SUPABASE_ANON_KEY:-}}"
: "${SB_KEY:?Neither SUPABASE_SERVICE_KEY nor SUPABASE_ANON_KEY set}"

API="${SUPABASE_URL}/rest/v1/agent_runs"
AUTH=(-H "apikey: ${SB_KEY}" -H "Authorization: Bearer ${SB_KEY}")
JSON=(-H "Content-Type: application/json" -H "Prefer: return=representation")
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

CMD="${1:-help}"
shift || true
case "$CMD" in
  create)
    TASK_ID="${1:?用法: agent-runs.sh create <task_id> <parent> <child> <trigger_type>}"
    PARENT="${2:?missing parent_agent_id}"
    CHILD="${3:?missing child_agent_id}"
    TRIGGER="${4:?missing trigger_type}"
    RUN_ID="${5:-}"
    SESSION_KEY="${6:-}"
    REQ_SESSION="${7:-}"
    METADATA="${8:-\{\}}"
    curl -s "$API" "${AUTH[@]}" "${JSON[@]}" \
      -d "{\"task_id\":\"$TASK_ID\",\"parent_agent_id\":\"$PARENT\",\"child_agent_id\":\"$CHILD\",\"trigger_type\":\"$TRIGGER\",\"run_id\":\"$RUN_ID\",\"child_session_key\":\"$SESSION_KEY\",\"requester_session_key\":\"$REQ_SESSION\",\"metadata\":$METADATA,\"status\":\"spawned\"}"
    ;;
  start)
    RUN_ID="${1:?用法: agent-runs.sh start <run_id>}"
    curl -s "$API?id=eq.${RUN_ID}" "${AUTH[@]}" "${JSON[@]}" \
      -X PATCH -d "{\"status\":\"running\",\"started_at\":\"$NOW\"}"
    ;;
  returned)
    RUN_ID="${1:?用法: agent-runs.sh returned <run_id> [summary]}"
    SUMMARY="${2:-}"
    curl -s "$API?id=eq.${RUN_ID}" "${AUTH[@]}" "${JSON[@]}" \
      -X PATCH -d "{\"status\":\"returned\",\"announce_received\":true,\"announce_received_at\":\"$NOW\",\"finished_at\":\"$NOW\",\"result_summary\":\"$SUMMARY\"}"
    ;;
  fail)
    RUN_ID="${1:?用法: agent-runs.sh fail <run_id> [reason]}"
    REASON="${2:-unknown}"
    curl -s "$API?id=eq.${RUN_ID}" "${AUTH[@]}" "${JSON[@]}" \
      -X PATCH -d "{\"status\":\"failed\",\"finished_at\":\"$NOW\",\"error_reason\":\"$REASON\"}"
    ;;
  timeout)
    RUN_ID="${1:?用法: agent-runs.sh timeout <run_id> [reason]}"
    REASON="${2:-execution timeout}"
    curl -s "$API?id=eq.${RUN_ID}" "${AUTH[@]}" "${JSON[@]}" \
      -X PATCH -d "{\"status\":\"timeout\",\"finished_at\":\"$NOW\",\"error_reason\":\"$REASON\"}"
    ;;
  update)
    RUN_ID="${1:?用法: agent-runs.sh update <run_id> <field> <value>}"
    FIELD="${2:?missing field}"
    VALUE="${3:?missing value}"
    curl -s "$API?id=eq.${RUN_ID}" "${AUTH[@]}" "${JSON[@]}" \
      -X PATCH -d "{\"$FIELD\":\"$VALUE\"}"
    ;;
  get)
    RUN_ID="${1:?用法: agent-runs.sh get <run_id>}"
    curl -s "$API?id=eq.${RUN_ID}" "${AUTH[@]}" | python3 -m json.tool
    ;;
  list)
    STATUS="${1:-}"
    if [[ -n "$STATUS" ]]; then
      curl -s "$API?status=eq.${STATUS}&order=created_at.desc" "${AUTH[@]}" | python3 -m json.tool
    else
      curl -s "$API?order=created_at.desc&limit=20" "${AUTH[@]}" | python3 -m json.tool
    fi
    ;;
  check)
    # Heartbeat 巡检：5 条规则完整实现
    # 调用 Python 脚本进行结构化检测
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    python3 "${SCRIPT_DIR}/check_agent_runs.py"
    ;;
  *)
    echo "用法: agent-runs.sh {create|start|returned|fail|timeout|update|get|list|check} [args...]"
    ;;
esac
