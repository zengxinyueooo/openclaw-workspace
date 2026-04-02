#!/usr/bin/env bash
# tasks.sh - MCN Ralph Loop 任务管理 CLI
# 用法:
#   tasks.sh sync <agent>          拉取任务生成 TASKS.md
#   tasks.sh list <agent>          列出任务(JSON)
#   tasks.sh add <agent> <title>   添加任务
#   tasks.sh start <task_id>       标记开始执行
#   tasks.sh done <task_id> [msg]  标记完成
#   tasks.sh fail <task_id> [err]  标记失败
#   tasks.sh block <task_id> [why] 标记阻塞

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../../.env.supabase"

if [[ -f "$ENV_FILE" ]]; then
  source "$ENV_FILE"
fi

: "${SUPABASE_URL:?SUPABASE_URL not set}"
: "${SUPABASE_SERVICE_KEY:?SUPABASE_SERVICE_KEY not set}"

API="${SUPABASE_URL}/rest/v1/tasks"
AUTH=(-H "apikey: ${SUPABASE_SERVICE_KEY}" -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}")
JSON=(-H "Content-Type: application/json")

CMD="${1:-help}"
shift || true

case "$CMD" in
  list)
    AGENT="${1:?用法: tasks.sh list <agent>}"
    curl -s "$API?agent=eq.${AGENT}&order=priority.asc,created_at.asc" \
      "${AUTH[@]}" "${JSON[@]}"
    ;;

  sync)
    AGENT="${1:?用法: tasks.sh sync <agent>}"
    OUTPUT="${2:-TASKS.md}"
    DATA=$(curl -s "$API?agent=eq.${AGENT}&order=priority.asc,created_at.asc" \
      "${AUTH[@]}" "${JSON[@]}")

    # 生成 TASKS.md
    {
      echo "# TASKS.md - ${AGENT} 的待办清单"
      echo ""
      echo "> 自动从 Supabase 同步，请勿手动编辑"
      echo "> 更新时间: $(TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M')"
      echo ""

      for STATUS in running pending blocked done failed; do
        case "$STATUS" in
          running) ICON="🔵"; LABEL="进行中" ;;
          pending) ICON="⚪"; LABEL="待处理" ;;
          blocked) ICON="🟡"; LABEL="阻塞" ;;
          done)    ICON="✅"; LABEL="已完成" ;;
          failed)  ICON="❌"; LABEL="失败" ;;
        esac

        ITEMS=$(echo "$DATA" | python3 -c "
import sys, json
tasks = json.loads(sys.stdin.read())
for t in tasks:
    if t['status'] == '${STATUS}':
        p = t['priority']
        pmap = {1:'🔴P1', 2:'🟠P2', 3:'🟡P3', 4:'🟢P4', 5:'⚪P5'}
        pri = pmap.get(p, f'P{p}')
        check = 'x' if '${STATUS}' in ('done','failed') else ' '
        src = t.get('source','?')
        tid = t['id'][:8]
        title = t['title']
        line = f'- [{check}] {pri} | {title} | 来源: {src} | ID: {tid}'
        if '${STATUS}' == 'done' and t.get('completed_at'):
            ct = t['completed_at'][:16].replace('T',' ')
            line += f' | 完成于 {ct}'
        if '${STATUS}' == 'failed' and t.get('error'):
            line += f' | 原因: {t[\"error\"][:50]}'
        print(line)
" 2>/dev/null)

        if [[ -n "$ITEMS" ]]; then
          echo "## ${ICON} ${LABEL}"
          echo "$ITEMS"
          echo ""
        fi
      done
    } > "$OUTPUT"

    echo "已同步 ${AGENT} 的任务到 ${OUTPUT}"
    ;;
  add)
    AGENT="${1:?用法: tasks.sh add <agent> <title> [opts]}"
    shift
    TITLE="${1:?缺少 title}"
    shift || true
    PRIORITY="${PRIORITY:-3}"
    SOURCE="${SOURCE:-zhuazhua}"
    DESC="${DESC:-}"
    PARENT="${PARENT:-}"
    BODY="{\"title\":\"${TITLE}\",\"agent\":\"${AGENT}\",\"priority\":${PRIORITY},\"source\":\"${SOURCE}\"}"
    if [[ -n "$DESC" ]]; then
      BODY=$(echo "$BODY" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); d['description']='${DESC}'; print(json.dumps(d))")
    fi
    if [[ -n "$PARENT" ]]; then
      BODY=$(echo "$BODY" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); d['parent_task_id']='${PARENT}'; print(json.dumps(d))")
    fi
    curl -s "$API" -X POST "${AUTH[@]}" "${JSON[@]}" \
      -H "Prefer: return=representation" \
      -d "$BODY"
    ;;

  start)
    TASK_ID="${1:?用法: tasks.sh start <task_id>}"
    # 先检查重试次数
    TASK_DATA=$(curl -s "$API?id=eq.${TASK_ID}&select=retry_count,max_retries,title" \
      "${AUTH[@]}" "${JSON[@]}")
    RETRY_CHECK=$(echo "$TASK_DATA" | python3 -c "
import sys, json
tasks = json.loads(sys.stdin.read())
if not tasks:
    print('NOT_FOUND')
else:
    t = tasks[0]
    rc = t.get('retry_count', 0)
    mx = t.get('max_retries', 3)
    if rc >= mx:
        print(f'EXCEEDED|{rc}|{mx}|{t[\"title\"]}')
    else:
        print(f'OK|{rc}|{mx}')
" 2>/dev/null)

    if [[ "$RETRY_CHECK" == "NOT_FOUND" ]]; then
      echo '{"error":"task not found"}' >&2
      exit 1
    elif [[ "$RETRY_CHECK" == EXCEEDED* ]]; then
      IFS='|' read -r _ RC MX TITLE <<< "$RETRY_CHECK"
      echo "⚠️ 任务「${TITLE}」已达最大重试次数 (${RC}/${MX})，自动标记失败" >&2
      curl -s "$API?id=eq.${TASK_ID}" -X PATCH "${AUTH[@]}" "${JSON[@]}" \
        -H "Prefer: return=representation" \
        -d "{\"status\":\"failed\",\"error\":\"超过最大重试次数(${RC}/${MX})\",\"completed_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
      exit 1
    fi

    # 正常启动：status=running, retry_count+1
    IFS='|' read -r _ RC _ <<< "$RETRY_CHECK"
    NEW_RC=$((RC + 1))
    curl -s "$API?id=eq.${TASK_ID}" -X PATCH "${AUTH[@]}" "${JSON[@]}" \
      -H "Prefer: return=representation" \
      -d "{\"status\":\"running\",\"started_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"retry_count\":${NEW_RC}}"
    ;;
  done)
    TASK_ID="${1:?用法: tasks.sh done <task_id> [result_msg]}"
    shift || true
    RESULT="${1:-完成}"
    curl -s "$API?id=eq.${TASK_ID}" -X PATCH "${AUTH[@]}" "${JSON[@]}" \
      -H "Prefer: return=representation" \
      -d "{\"status\":\"done\",\"result\":\"${RESULT}\",\"completed_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
    ;;

  fail)
    TASK_ID="${1:?用法: tasks.sh fail <task_id> [error_msg]}"
    shift || true
    ERROR="${1:-未知错误}"
    curl -s "$API?id=eq.${TASK_ID}" -X PATCH "${AUTH[@]}" "${JSON[@]}" \
      -H "Prefer: return=representation" \
      -d "{\"status\":\"failed\",\"error\":\"${ERROR}\",\"completed_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
    ;;

  block)
    TASK_ID="${1:?用法: tasks.sh block <task_id> [reason]}"
    shift || true
    REASON="${1:-等待外部依赖}"
    curl -s "$API?id=eq.${TASK_ID}" -X PATCH "${AUTH[@]}" "${JSON[@]}" \
      -H "Prefer: return=representation" \
      -d "{\"status\":\"blocked\",\"error\":\"${REASON}\"}"
    ;;

  dispatch)
    # 爪爪委派任务：创建子任务 + 在 main 留委派记录
    AGENT="${1:?用法: tasks.sh dispatch <agent> <title>}"
    shift
    TITLE="${1:?缺少 title}"
    shift || true
    PRIORITY="${PRIORITY:-2}"
    SOURCE="zhuazhua"
    DESC="${DESC:-}"

    # 1. 先在爪爪(main)创建委派记录
    DISPATCH_BODY="{\"title\":\"[委派] ${TITLE} → ${AGENT}\",\"agent\":\"main\",\"priority\":${PRIORITY},\"source\":\"pipi\",\"status\":\"done\",\"result\":\"已委派给 ${AGENT}\",\"completed_at\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
    DISPATCH_RESULT=$(curl -s "$API" -X POST "${AUTH[@]}" "${JSON[@]}" \
      -H "Prefer: return=representation" \
      -d "$DISPATCH_BODY")
    DISPATCH_ID=$(echo "$DISPATCH_RESULT" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())[0]['id'])" 2>/dev/null)

    # 2. 创建子任务，关联到委派记录
    TASK_BODY="{\"title\":\"${TITLE}\",\"agent\":\"${AGENT}\",\"priority\":${PRIORITY},\"source\":\"zhuazhua\",\"parent_task_id\":\"${DISPATCH_ID}\"}"
    if [[ -n "$DESC" ]]; then
      TASK_BODY=$(echo "$TASK_BODY" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); d['description']='${DESC}'; print(json.dumps(d))")
    fi
    curl -s "$API" -X POST "${AUTH[@]}" "${JSON[@]}" \
      -H "Prefer: return=representation" \
      -d "$TASK_BODY"
    ;;

  next)
    # 获取下一个可执行任务（pending + 未超限）
    AGENT="${1:?用法: tasks.sh next <agent>}"
    RESULT=$(curl -s "$API?agent=eq.${AGENT}&status=eq.pending&order=priority.asc,created_at.asc&limit=10" \
      "${AUTH[@]}" "${JSON[@]}" | python3 -c "
import sys, json
tasks = json.loads(sys.stdin.read())
for t in tasks:
    if t.get('retry_count', 0) < t.get('max_retries', 3):
        print(json.dumps(t))
        break
else:
    print('NONE')
" 2>/dev/null)
    if [[ "$RESULT" == "NONE" ]]; then
      echo "NONE"
    else
      echo "$RESULT"
    fi
    ;;

  help|*)
    echo "tasks.sh - MCN Ralph Loop 任务管理"
    echo ""
    echo "命令:"
    echo "  sync  <agent> [file]    同步任务到 TASKS.md"
    echo "  list  <agent>           列出任务(JSON)"
    echo "  next  <agent>           获取下一个可执行任务(跳过超限)"
    echo "  add   <agent> <title>   添加任务"
    echo "  start <task_id>         标记开始(自动+1重试计数,超限自动fail)"
    echo "  done  <task_id> [msg]   标记完成"
    echo "  fail  <task_id> [err]   标记失败"
    echo "  block <task_id> [why]   标记阻塞"
    echo ""
    echo "环境变量:"
    echo "  PRIORITY=1-5  SOURCE=pipi|zhuazhua|self|agent:xxx"
    echo "  DESC=描述  PARENT=父任务ID"
    ;;
esac
