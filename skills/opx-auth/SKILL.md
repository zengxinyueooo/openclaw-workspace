---
name: opx-auth
description: 获取 OPX AI 的 AccessToken 和 Cookie。通过 OpenClaw Browser Relay 连接本地 Chrome 浏览器，访问页面并调用 /sso/web/auth 接口获取 Cookie 和 accessToken。
metadata:
  {
    "openclaw":
      {
        "emoji": "🔑",
        "requires": { "tools": ["browser"] },
      },
  }
---

# OPX AccessToken 获取工具

自动获取 OPX AI (https://opx-ai.sankuai.com) 的 **Cookie** 和 **accessToken**。

## 原理

1. 通过 OpenClaw Browser Relay (`profile: "chrome"`) 连接你本地已登录的 Chrome 浏览器
2. 打开 `https://opx-ai.sankuai.com/opx-ai-manage/#/content-marketing/auto-publish`
3. 执行 JavaScript 调用 `/sso/web/auth` 接口
4. 提取 **document.cookie** 和响应中的 **accessToken**

## 前置条件

- Chrome 浏览器已安装 OpenClaw Browser Relay 扩展
- 扩展已连接（toolbar 图标显示 ON）
- 已在浏览器中登录 OPX AI

## 使用方法

### 方式一：OpenClaw 自动执行（推荐）

直接告诉 OpenClaw：

> "获取 OPX access token"

OpenClaw 会自动执行：

```javascript
// 1. 打开 OPX 页面
await browser.open('https://opx-ai.sankuai.com/opx-ai-manage/#/content-marketing/auto-publish', { profile: 'chrome' });

// 2. 执行 JS 获取 Cookie 和 Token
await browser.act({
  kind: 'evaluate',
  fn: `() => {
    return new Promise(async (resolve) => {
      try {
        const res = await fetch('https://opx-ai.sankuai.com/sso/web/auth?clientId=055da5ec53&accessEnv=product&ssoprotect=1', {
          credentials: 'include'
        });
        const data = await res.json();
        resolve({
          cookie: document.cookie,
          accessToken: data.data?.accessToken,
          response: data
        });
      } catch (e) {
        resolve({ error: e.message, cookie: document.cookie });
      }
    });
  }`
});
```

### 方式二：手动执行脚本

如需在命令行运行：

```bash
cd ~/.openclaw/workspace/skills/opx-auth
node get-token.js
```

**注意：** 此脚本需要 Chrome 已启用调试模式（`--remote-debugging-port=9222`）

## 预期输出

```json
{
  "cookie": "AWPTALOS23222=; _lxsdk_cuid=...; cube_session=...",
  "accessToken": "eAGFzrtKA0EYhmGmW7QRr...",
  "response": {
    "code": 200,
    "data": {
      "accessToken": "..."
    },
    "msg": "success"
  }
}
```

## 文件说明

- `get-token.js` - Node.js 脚本，通过 CDP 连接 Chrome 获取 Token（备用方案）

## 注意事项

- `/sso/web/auth` 接口需要带 `clientId` 参数，如：`clientId=055da5ec53&accessEnv=product&ssoprotect=1`
- 请求需要 `credentials: 'include'` 来携带当前页面的 Cookie
