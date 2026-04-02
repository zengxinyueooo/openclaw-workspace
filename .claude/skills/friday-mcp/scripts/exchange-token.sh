#!/bin/bash
# Friday MCP 换票脚本：CIBA 认证 → 获取 accessToken → 换取 MCP Server token
# 用法: bash exchange-token.sh <misId> <clientId> [base_url]
# 示例: bash exchange-token.sh liuyiwei06 9ade809a7f
#
# 输出: 成功时输出 FINAL_TOKEN=<jwt_token>
# 注意: 第一步发起认证后用户的大象会收到确认提示，需要用户点击确认

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "ERROR: 请提供 misId 和 clientId" >&2
  echo "用法: bash $0 <misId> <clientId> [base_url]" >&2
  exit 1
fi

MIS_ID="$1"
CLIENT_ID="$2"
BASE_URL="${3:-https://supabase.cloud.test.sankuai.com}"

# 获取 identifier
IDENTIFIER=$(bash "${SCRIPT_DIR}/get-identifier.sh")
if [ $? -ne 0 ]; then
  echo "ERROR: 获取 identifier 失败: $IDENTIFIER" >&2
  exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 开始 Friday MCP 换票"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "misId: $MIS_ID"
echo "clientId: $CLIENT_ID"
echo "baseUrl: $BASE_URL"
echo ""

# ===== 步骤 1：发起 CIBA 认证 =====
echo "📌 步骤 1：发起 CIBA 认证..."
BC_RESPONSE=$(curl --noproxy "*" -s -X POST "${BASE_URL}/api/sandbox/sso/ciba-auth" \
  -H 'Content-Type: application/json' \
  -d "{\"identifier\":\"${IDENTIFIER}\",\"misId\":\"${MIS_ID}\"}")

AUTH_REQ_ID=$(echo "$BC_RESPONSE" | python3 -c "
import json,sys
data=json.load(sys.stdin)
d=data.get('data',{}) if data.get('code')==0 else {}
print(d.get('authReqId','') or d.get('existingAuthReqId',''))
" 2>/dev/null)

if [ -z "$AUTH_REQ_ID" ]; then
  echo "ERROR: 获取 authReqId 失败: $BC_RESPONSE" >&2
  exit 1
fi

echo "✅ authReqId: $AUTH_REQ_ID"
echo ""
echo "⏳ 请在大象 App 中确认认证请求..."
echo ""

# ===== 步骤 2：轮询获取 accessToken =====
echo "📌 步骤 2：轮询获取 accessToken（每 5s 一次，最多 3 分钟）..."
MAX_RETRY=36
RETRY=0
ACCESS_TOKEN=""

while [ $RETRY -lt $MAX_RETRY ]; do
  RETRY=$((RETRY + 1))
  echo "  第 ${RETRY}/${MAX_RETRY} 次轮询..."

  TOKEN_RESPONSE=$(curl --noproxy "*" -s -X POST "${BASE_URL}/api/sandbox/sso/ciba-token" \
    -H 'Content-Type: application/json' \
    -d "{\"authReqId\":\"${AUTH_REQ_ID}\"}")

  ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "
import json,sys
data=json.load(sys.stdin)
print(data.get('data',{}).get('accessToken','') if data.get('code')==0 else '')
" 2>/dev/null)

  if [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ accessToken 获取成功"
    break
  fi

  sleep 5
done

if [ -z "$ACCESS_TOKEN" ]; then
  echo "ERROR: 轮询超时，未获取到 accessToken（用户未在大象确认？）" >&2
  exit 1
fi
echo ""

# ===== 步骤 3：换取 MCP Server token =====
echo "📌 步骤 3：换取 MCP Server token..."
EXCHANGE_RESPONSE=$(curl --noproxy "*" -s -X POST "${BASE_URL}/api/sandbox/sso/exchange-token-by-client-ids" \
  -H 'Content-Type: application/json' \
  -d "{\"accessToken\":\"${ACCESS_TOKEN}\",\"clientIds\":[\"${CLIENT_ID}\"]}")

FINAL_TOKEN=$(echo "$EXCHANGE_RESPONSE" | python3 -c "
import json,sys
data=json.load(sys.stdin)
print(data.get('data','') if data.get('code')==0 else '')
" 2>/dev/null)

if [ -z "$FINAL_TOKEN" ]; then
  echo "ERROR: 换票失败: $EXCHANGE_RESPONSE" >&2
  exit 1
fi

echo "✅ 换票成功"
echo ""
echo "FINAL_TOKEN=${FINAL_TOKEN}"