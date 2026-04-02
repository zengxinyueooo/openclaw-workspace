#!/usr/bin/env bash
# run.sh - 带完成回调的 coding agent 包装器
# 用法: run.sh --agent codex|claude --task-id <id> --workdir <dir> --prompt "..."
# 
# 不管 agent 成功还是失败，都会：
# 1. 更新 Supabase task 状态
# 2. 通知爪爪主 session

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

AGENT_TYPE=""
TASK_ID=""
WORKDIR="."
PROMPT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent) AGENT_TYPE="$2"; shift 2 ;;
    --task-id) TASK_ID="$2"; shift 2 ;;
    --workdir) WORKDIR="$2"; shift 2 ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

: "${AGENT_TYPE:?需要 --agent codex|claude}"
: "${PROMPT:?需要 --prompt}"

# agent_runs 已停用 (2026-03-30)，RUN_ID 相关逻辑已移除

LOG_FILE=$(mktemp /tmp/agent-runner-XXXXXX.log)
STALL_SECONDS=${STALL_SECONDS:-120}  # 多久没输出算卡住，默认2分钟

# 后台监控：检测 agent 是否卡住
monitor_agent() {
  local PID=$1
  local LAST_SIZE=0
  local STALL=0

  while kill -0 "$PID" 2>/dev/null; do
    sleep 30
    local NOW_SIZE
    NOW_SIZE=$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)
    if [[ "$NOW_SIZE" -eq "$LAST_SIZE" ]]; then
      STALL=$((STALL + 30))
      if [[ $STALL -ge $STALL_SECONDS ]]; then
        local TAIL
        TAIL=$(tail -3 "$LOG_FILE" 2>/dev/null | head -c 200)
        openclaw system event \
          --text "⚠️ ${AGENT_TYPE} 可能卡住了(${STALL}s无新输出) | 任务: ${PROMPT:0:60} | 最后输出: ${TAIL}" \
          --mode now 2>/dev/null || true
        STALL=0
      fi
    else
      STALL=0
      LAST_SIZE=$NOW_SIZE
    fi
  done
}

echo "🚀 启动 ${AGENT_TYPE}..."
echo "📂 工作目录: ${WORKDIR}"
echo "📝 任务: ${PROMPT:0:100}..."
echo "📊 卡住检测: ${STALL_SECONDS}s"

# 执行 agent（输出同时到终端和 log 文件）
EXIT_CODE=0
cd "$WORKDIR"

case "$AGENT_TYPE" in
  codex)
    codex exec --full-auto "$PROMPT" 2>&1 | tee "$LOG_FILE" &
    AGENT_PID=$!
    ;;
  codex-yolo)
    codex exec --dangerously-bypass-approvals-and-sandbox "$PROMPT" 2>&1 | tee "$LOG_FILE" &
    AGENT_PID=$!
    ;;
  claude)
    claude -p --dangerously-skip-permissions "$PROMPT" 2>&1 | tee "$LOG_FILE" &
    AGENT_PID=$!
    ;;
  claude-safe)
    claude -p --permission-mode acceptEdits "$PROMPT" 2>&1 | tee "$LOG_FILE" &
    AGENT_PID=$!
    ;;
  *)
    echo "未知 agent: $AGENT_TYPE" >&2
    EXIT_CODE=1
    AGENT_PID=""
    ;;
esac

if [[ -n "${AGENT_PID:-}" ]]; then
  # 启动后台监控
  monitor_agent "$AGENT_PID" &
  MONITOR_PID=$!

  # 等待 agent 完成
  wait "$AGENT_PID" 2>/dev/null
  EXIT_CODE=$?

  # 停止监控
  kill "$MONITOR_PID" 2>/dev/null || true
fi

# 清理 log
rm -f "$LOG_FILE" 2>/dev/null

echo ""
echo "=========================================="
echo "Agent 退出码: $EXIT_CODE"
echo "=========================================="

# 构造通知消息
if [[ $EXIT_CODE -eq 0 ]]; then
  NOTIFY_MSG="✅ ${AGENT_TYPE} 完成: ${PROMPT:0:80}"
else
  NOTIFY_MSG="❌ ${AGENT_TYPE} 失败(exit=${EXIT_CODE}): ${PROMPT:0:80}"
fi

# agent_runs 已停用 (2026-03-30)，完成回调已移除

# 通知爪爪
echo ""
echo "📢 通知爪爪..."
openclaw system event --text "$NOTIFY_MSG" --mode now 2>/dev/null || true

echo "🏁 完成"
exit $EXIT_CODE
