#!/bin/bash
# OPX Auth - 通过 AppleScript 从已打开的 Chrome 标签页获取 Cookie 和 AccessToken
# 无需扩展、无需 CDP、无需手动操作，全自动执行

set -e

OUTPUT_FILE="/tmp/opx-token.json"
OPX_DOMAIN="opx-ai.sankuai.com"
AUTH_URL="https://opx-ai.sankuai.com/sso/web/auth?clientId=055da5ec53&accessEnv=product&ssoprotect=1"

echo "🍑 OPX Auth - AppleScript 自动获取 Token"
echo "=========================================="

# Step 1: 检查 Chrome 是否运行
if ! pgrep -x "Google Chrome" > /dev/null 2>&1; then
  echo "❌ Chrome 未运行，请先打开 Chrome 并登录 OPX"
  exit 1
fi

# Step 2: 查找 OPX 标签页并获取 Cookie
echo "🔍 查找 OPX 标签页..."

COOKIE=$(osascript << 'EOF'
tell application "Google Chrome"
  set foundTab to missing value
  repeat with w in windows
    repeat with t in tabs of w
      if URL of t contains "opx-ai.sankuai.com" then
        set foundTab to t
        exit repeat
      end if
    end repeat
    if foundTab is not missing value then exit repeat
  end repeat

  if foundTab is missing value then
    return "ERROR:NO_TAB"
  end if

  set cookieResult to execute foundTab javascript "document.cookie"
  return cookieResult
end tell
EOF
)

# 检查是否找到标签页
if [ "$COOKIE" = "ERROR:NO_TAB" ]; then
  echo "❌ 未找到 OPX 页面标签，请先在 Chrome 中打开 https://opx-ai.sankuai.com"
  exit 1
fi

if [ -z "$COOKIE" ]; then
  echo "❌ Cookie 为空，可能未登录 OPX"
  exit 1
fi

echo "✅ 获取 Cookie 成功"

# Step 3: 调用 /sso/web/auth 获取 accessToken
echo "🔑 获取 AccessToken..."

AUTH_RESULT=$(osascript << EOF
tell application "Google Chrome"
  set foundTab to missing value
  repeat with w in windows
    repeat with t in tabs of w
      if URL of t contains "opx-ai.sankuai.com" then
        set foundTab to t
        exit repeat
      end if
    end repeat
    if foundTab is not missing value then exit repeat
  end repeat

  set jsCode to "
    (async () => {
      try {
        const res = await fetch('${AUTH_URL}', { credentials: 'include' });
        const data = await res.json();
        return JSON.stringify({ code: data.code, accessToken: data.data?.accessToken || null, msg: data.msg });
      } catch (e) {
        return JSON.stringify({ error: e.message });
      }
    })()
  "

  set authResult to execute foundTab javascript jsCode
  return authResult
end tell
EOF
)

# Step 4: 解析结果并保存
ACCESS_TOKEN=$(echo "$AUTH_RESULT" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    if 'error' in data:
        print('ERROR:' + data['error'])
    elif data.get('accessToken'):
        print(data['accessToken'])
    else:
        print('ERROR:NO_TOKEN')
except:
    print('ERROR:PARSE_FAIL')
")

if [[ "$ACCESS_TOKEN" == ERROR:* ]]; then
  echo "❌ 获取 AccessToken 失败: ${ACCESS_TOKEN#ERROR:}"
  echo "   可能需要重新登录 OPX"
  exit 1
fi

echo "✅ 获取 AccessToken 成功"

# Step 5: 保存到文件
python3 -c "
import json
result = {
    'cookie': '''${COOKIE}''',
    'accessToken': '${ACCESS_TOKEN}'
}
with open('${OUTPUT_FILE}', 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(json.dumps(result, indent=2, ensure_ascii=False))
"

echo ""
echo "=========================================="
echo "💾 已保存到 ${OUTPUT_FILE}"
echo "🍑 搞定啦！"
