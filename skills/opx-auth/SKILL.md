---
name: opx-auth
description: 获取 OPX AI 的 AccessToken 和 Cookie。通过 Browser Relay 或 CDP 方式获取，需要显式指定 profile: "chrome"。
metadata:
  {
    "openclaw":
      {
        "emoji": "🔑",
        "requires": { "tools": ["browser", "exec"] },
      },
  }
---

# OPX AccessToken 获取工具

自动获取 OPX AI (https://opx-ai.sankuai.com) 的 Cookie 和 accessToken。

## 原理

方案一（Browser Relay，推荐）：
1. 通过 OpenClaw Browser Relay (`profile: "chrome"`) 连接本地 Chrome
2. 打开 OPX 页面
3. 执行 JavaScript 获取 Cookie 和 Token

方案二（CDP 调试端口）：
1. Chrome 开启调试端口 (--remote-debugging-port=9222)
2. 通过 WebSocket CDP 连接
3. 监听网络请求获取 Token

## 前置条件

### 方案一（Browser Relay）
- Chrome 浏览器已安装 OpenClaw Browser Relay 扩展
- 扩展已连接（toolbar 图标显示 ON）
- 已在浏览器中登录 OPX AI

### 方案二（CDP）
- Chrome 开启调试端口：`/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`

## 使用方法

### 方式一：OpenClaw 自动执行（推荐）

告诉 Agent "获取 OPX access token"，Agent 执行：

```javascript
// 1. 打开 OPX 页面（必须指定 profile: "chrome"）
await browser.open('https://opx-ai.sankuai.com/opx-ai-manage/#/content-marketing/auto-publish', { profile: 'chrome' });

// 2. 执行 JS 获取 Cookie 和 Token（必须指定 profile: "chrome"）
await browser.act({
  profile: 'chrome',  // ⚠️ 必须显式指定，不能依赖默认值
  kind: 'evaluate',
  fn: `() => {
    return new Promise(async (resolve) => {
      try {
        const res = await fetch('https://opx-ai.sankuai.com/sso/web/auth?clientId=055da5ec53&accessEnv=product&ssoprotect=1', { credentials: 'include' });
        const data = await res.json();
        resolve({ cookie: document.cookie, accessToken: data.data?.accessToken, response: data });
      } catch (e) {
        resolve({ error: e.message, cookie: document.cookie });
      }
    });
  }`
});
```

⚠️ **重要**：必须使用 `profile: "chrome"`，不能使用默认的 `profile: "openclaw"`！

### 方式二：浏览器 Console 手动执行

在 Chrome 中打开 OPX 页面，按 F12 打开开发者工具，在 Console 执行：

```javascript
fetch('https://opx-ai.sankuai.com/sso/web/auth?clientId=055da5ec53&accessEnv=product&ssoprotect=1', { credentials: 'include' })
  .then(r => r.json())
  .then(data => {
    console.log('=== Cookie ===');
    console.log(document.cookie);
    console.log('=== AccessToken ===');
    console.log(data.data?.accessToken);
  });
```

### 方式三：命令行脚本

```bash
# 1. 启动 Chrome 调试模式
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 2. 运行脚本
cd ~/.openclaw/workspace/skills/opx-auth
node get-token.js
```

## Agent 调用指南

当其他 skill 需要 OPX 认证时：

1. 首先尝试 Browser Relay 方案（必须指定 `profile: "chrome"`）
2. 如果失败，使用 CDP 方案（运行 get-token.js）
3. 读取 `/tmp/opx-token.json` 获取 token

## 预期输出

```json
{
  "cookie": "AWPTALOS23222=; _lxsdk_cuid=...; cube_session=...",
  "accessToken": "eAGFzrtKA0EYhmGmW7QRr..."
}
```

## 文件说明

- SKILL.md — 本说明文件
- get-token.js — Node.js CDP 脚本（需要 Chrome 开启调试端口）
- get-token.sh — AppleScript 脚本（macOS 专用，目前不可用）

## 注意事项

- `/sso/web/auth` 接口需要 `clientId=055da5ec53&accessEnv=product&ssoprotect=1`
- 请求需要 `credentials: 'include'` 来携带 Cookie
- **必须显式指定 `profile: "chrome"`，不能用默认的 `profile: "openclaw"`**

## 故障排除

### 错误：Failed to start Chrome CDP on port 18800

- 原因：使用了默认的 `profile: "openclaw"`
- 解决：所有 browser 调用都显式指定 `profile: "chrome"`

### 浏览器操作超时

- 首先重试 - 网络/服务偶尔波动很正常
- 多次失败（2-3次）后再换方案
