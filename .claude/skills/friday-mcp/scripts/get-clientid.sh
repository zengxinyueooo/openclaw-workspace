#!/bin/bash
# 通过接入点 URL 查询 MCP Server 的 clientId
# 用法: bash get-clientid.sh <mcp-server-url>
# 示例: bash get-clientid.sh http://mcphub-server.sankuai.com/mcphub-api/eead0e8084b54b

if [ -z "$1" ]; then
  echo "ERROR: 请提供 MCP Server 接入点 URL" >&2
  echo "用法: bash $0 <mcp-server-url>" >&2
  exit 1
fi

MCP_URL="$1"
BASE_URL="https://mcphub.sankuai.com"

RESP=$(curl -sS "${BASE_URL}/public/openapi/mcpserver/details/by-url" \
  -H 'Content-Type: application/json' \
  --data "{\"urls\":[\"${MCP_URL}\"]}" 2>/dev/null)

CODE=$(echo "$RESP" | jq -r '.code' 2>/dev/null)
if [ "$CODE" != "200" ]; then
  echo "ERROR: 接口返回异常: $RESP" >&2
  exit 1
fi

CLIENT_ID=$(echo "$RESP" | jq -r '.result.items[0].clientId' 2>/dev/null)
NAME=$(echo "$RESP" | jq -r '.result.items[0].name' 2>/dev/null)
ALIAS=$(echo "$RESP" | jq -r '.result.items[0].alias' 2>/dev/null)

if [ -z "$CLIENT_ID" ] || [ "$CLIENT_ID" = "null" ]; then
  echo "ERROR: 未找到 clientId，请检查 URL 是否正确" >&2
  exit 1
fi

echo "CLIENT_ID=${CLIENT_ID}"
echo "NAME=${NAME}"
echo "ALIAS=${ALIAS}"
