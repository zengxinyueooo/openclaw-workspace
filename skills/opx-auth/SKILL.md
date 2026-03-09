---
name: opx-auth
description: 获取 OPX AI 的 AccessToken 和 Cookie。通过 AppleScript 直接从已打开的 Chrome 标签页中自动获取，自动处理 OpenClaw 浏览器冲突，全自动执行。
metadata:
  {
    "openclaw":
      {
        "emoji": "🔑",
        "requires": { "tools": ["exec"] },
      },
  }
---

# OPX AccessToken 获取工具

自动获取 OPX AI (https://opx-ai.sankuai.com) 的 Cookie 和 accessToken。

## 原理

通过 macOS AppleScript (osascript) 直接操作已打开的 Chrome 标签页：

1. 检测并暂停 OpenClaw 的 Chrome 实例（避免 AppleScript 连到错误实例）
2. 查找 Chrome 中含 opx-ai.sankuai.com 的标签页
3. 在该标签页执行 JavaScript 获取 document.cookie
4. 在该标签页执行 fetch('/sso/web/auth') 获取 accessToken
5. 结果保存到 /tmp/opx-token.json
6. 自动恢复 OpenClaw 的 Chrome 实例

无需 Browser Relay 扩展，无需 CDP 远程调试端口，全自动执行。

## 前置条件

- macOS 系统
- Chrome 浏览器已运行，且已打开 OPX 页面（已登录状态）
- 首次使用时，macOS 会弹窗请求允许终端控制 Chrome 的权限（一次性授权）

## 使用方法

### Agent 自动调用（推荐）

告诉 Agent "获取 OPX access token"，Agent 执行：

```bash
bash ~/.openclaw/workspace/skills/opx-auth/get-token.sh
cat /tmp/opx-token.json
```

### 命令行手动执行

```bash
bash ~/.openclaw/workspace/skills/opx-auth/get-token.sh
```

## Agent 调用指南

当其他 skill 需要 OPX 认证时：

1. 执行 bash ~/.openclaw/workspace/skills/opx-auth/get-token.sh
2. 读取 cat /tmp/opx-token.json
3. 从 JSON 中提取 cookie 或 accessToken

### 错误处理

- Chrome 未运行 → 打开 Chrome
- 未找到 OPX 页面标签 → 打开 https://opx-ai.sankuai.com
- Cookie 为空 → 在 Chrome 中登录 OPX
- 获取 AccessToken 失败 → 在 Chrome 中重新登录 OPX

## 文件说明

- SKILL.md — 本说明文件
- get-token.sh — AppleScript 自动获取脚本（主方案，自动处理 OpenClaw 浏览器冲突）
- get-token.js — Node.js CDP 脚本（备用方案，需 --remote-debugging-port=9222）

## 注意事项

- /sso/web/auth 接口需要 clientId=055da5ec53&accessEnv=product&ssoprotect=1
- 请求需要 credentials: 'include' 来携带 Cookie
- Token 有时效性，过期后需重新获取
- 仅支持 macOS（依赖 AppleScript）
- 脚本会暂停 OpenClaw 浏览器实例，获取完成后自动恢复
