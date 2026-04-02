#!/bin/bash
# cleanup_stale_sub_requirements.sh
# 每天 00:05 运行
# 逻辑：status=pending 的子需求，只要满足以下任一条件就标 obsolete：
#   1. created_at < 今天00:00（过了当天没完成）
#   2. deleted_at 有值（人手动删除了）
# 不管 progress 内容，不管生图是否完成

set -e

source /mnt/openclaw/.openclaw/workspace-mcn-bee/.env.supabase 2>/dev/null || source /mnt/openclaw/.openclaw/workspace-mcn-owl/.env.supabase 2>/dev/null

TODAY=$(python3 -c "from datetime import datetime,timezone,timedelta; print(datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%dT00:00:00+08:00'))")

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始检查 stale sub_requirements (截止: ${TODAY})..."

# 查找：status=pending 的子需求，分两类
# 1. created_at < 今天00:00
# 2. deleted_at 不为空（被人工删除）
curl -s -G "${SUPABASE_URL}/rest/v1/sub_requirement" \
  --data-urlencode "select=id,persona_name,status,created_at,deleted_at" \
  --data-urlencode "status=eq.pending" \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" | python3 -c "
import json, sys, urllib.request

raw = sys.stdin.read()
try:
    data = json.loads(raw)
except Exception as e:
    print(f'[ERROR] 返回不是有效 JSON: {e}')
    print(f'原始内容: {raw[:500]}')
    sys.exit(1)

if isinstance(data, dict) and 'message' in data:
    print(f'[ERROR] API 返回错误: {data[\"message\"]}')
    sys.exit(1)

if not isinstance(data, list):
    print(f'[ERROR] 期望返回数组，实际: {type(data)}')
    sys.exit(1)

today = '${TODAY}'
to_obsolete = []

for x in data:
    # 条件1：created_at < 今天00:00
    if x.get('created_at','') < today:
        to_obsolete.append(x)
        print(f'  条件1(超时): {x[\"id\"][:8]} {x[\"persona_name\"]} created={x[\"created_at\"][:10]}')
        continue
    # 条件2：deleted_at 有值
    if x.get('deleted_at') is not None:
        to_obsolete.append(x)
        print(f'  条件2(人工删): {x[\"id\"][:8]} {x[\"persona_name\"]} deleted={x[\"deleted_at\"][:10]}')

print(f'共 {len(to_obsolete)} 条待标 obsolete')

for x in to_obsolete:
    req = urllib.request.Request(
        '${SUPABASE_URL}/rest/v1/sub_requirement?id=eq.' + x['id'],
        data=json.dumps({'status': 'obsolete'}).encode(),
        method='PATCH',
        headers={
            'apikey': '${SUPABASE_ANON_KEY}',
            'Authorization': 'Bearer ${SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json'
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f'  {x[\"id\"][:8]} -> obsolete (HTTP {resp.status})')
    except Exception as e:
        print(f'  {x[\"id\"][:8]} -> 失败: {e}')
"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完成"
