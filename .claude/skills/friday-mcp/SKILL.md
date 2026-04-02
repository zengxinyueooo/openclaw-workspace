---
name: friday-mcp
description: 通过 Friday MCP 平台调用美团内部 MCP Server。当用户提到 Friday MCP、MCP Server、mcphub、mcphub-server.sankuai.com 接入点、或提供 friday.sankuai.com 链接时激活。也被其他依赖 MCP Server 的 skill 引用。
---

# Friday MCP 调用流程

## 概述

通过 Friday MCP 平台调用美团线上 MCP Server。完整流程：获取 clientId → 确保 MOA 登录 → 换票 → 注册到 mcporter → 调用 tool。

**重要限制：仅支持调用线上（prod）MCP Server，不支持线下 test 环境。**

## 被其他 Skill 引用

其他 skill 可以依赖 `friday-mcp` 完成 MCP Server 的认证、注册和 tool 调用。

**调用方 skill 只需在自己的 SKILL.md 中声明要用的接入点 URL 和 tool 信息**，实际的注册与调用全部交给 `friday-mcp` 执行，调用方无需自己运行 `mcporter` 命令。

典型协作流程：
1. 调用方 skill 提供**接入点 URL** 和可用的 **tool 名称 + 参数**
2. `friday-mcp` 完成：获取 clientId → MOA 登录 → 换票 → 注册到 mcporter → `mcporter call` 执行调用 → 返回结果
3. 调用方 skill 拿到结果后继续自身逻辑

## 流程

### 1. 获取 ClientId

两种输入方式：

**方式 A：Friday 页面链接**

用户提供 `https://friday.sankuai.com/mcp/mcp-server-detail?...&id=xxx` 链接时：
1. 用浏览器打开页面
2. 如果被 MOA 拦截 → 走 `moa-login` skill 完成登录后重试
3. 在页面中找到 `ClientId` 字段并记录
4. 同时记录`接入点信息`（后续 mcporter 需要）

**方式 B：接入点 URL**（推荐，可自动化）

用户提供 `http://mcphub-server.sankuai.com/mcphub-api/xxx` 格式的 URL 时：

```bash
bash <skill_dir>/scripts/get-clientid.sh "<接入点URL>"
```

输出示例：
```
CLIENT_ID=b1adb6101e
NAME=mtweather
ALIAS=美团天气
```

### 2. 确保 MOA 已登录并获取 misId

换票需要用户的 misId，必须先确保 MOA 已登录。

```bash
bash <skill_dir>/scripts/get-misid.sh
```

- 成功输出 misId → MOA 已登录，继续下一步
- 报错 `未找到 misId` → 走 `moa-login` skill 完成登录后重试

### 3. 换票

执行换票脚本（三步：CIBA 认证 → 轮询等待大象确认 → 换取 token）：

```bash
bash <skill_dir>/scripts/exchange-token.sh "<misId>" "<clientId>"
```

**交互要点：**
- 脚本执行第一步后，**用户的大象 App 会收到认证确认请求**
- **你必须立即发送一条消息明确提醒用户：「请打开大象 App，点击确认授权」**，否则用户可能不知道需要操作，导致 3 分钟后超时失败
- 不要等脚本结束再提醒，**必须在脚本开始轮询时就发消息通知用户**
- 脚本会自动轮询等待（每 5 秒一次，最多 3 分钟）
- 成功后输出 `FINAL_TOKEN=<jwt_token>`

换票接口 base URL：`https://supabase.cloud.test.sankuai.com`

### 4. 注册 MCP Server 到 mcporter

```bash
mcporter config add <server_name> <接入点URL> \
  --header "Authorization=Bearer <FINAL_TOKEN>" \
  --allow-http
```

- `server_name`：使用 MCP Server 的 name（如 `mtweather`）
- 重复 add 同名 server 会自动覆盖
- header 必须用 `Bearer` 前缀

### 5. 查看可用 Tools

**如果已明确要调用的 tool 名称和参数，跳过此步。**

仅在不清楚该 MCP Server 有哪些可用 tools 时才需要执行：

```bash
mcporter list <接入点URL> --schema
```

直接传接入点 URL 即可，**不需要先注册**。

### 6. 调用 Tool

```bash
mcporter call '<server_name>.<tool_name>(param1: "value1", param2: "value2")' --output json
```

**注意：使用 function-call 语法传参**，字符串参数用引号包裹。不要用 `key=value` 格式，可能导致类型反序列化错误。

## 输出规范

**严格控制输出内容，不要向用户暴露中间过程。** 具体要求：
- 不要输出 clientId、misId、authReqId、accessToken、FINAL_TOKEN 等中间变量的值
- 不要逐步汇报"正在获取 clientId""正在换票""正在注册"等流程细节
- 换票提醒大象确认是**唯一需要主动告知用户的中间步骤**
- 最终只需告知用户调用结果（成功/失败 + 返回数据），或在出错时给出简明的错误说明

## 注意事项

- **每次调用都重新换票**，不要复用之前的 token，直接走步骤 3→4→6
- **仅支持线上 MCP Server**（`mcphub-server.sankuai.com`），线下 test 环境不支持
- 接入点 URL 中含 `.test.` 的为线下环境，换票后无法调用
- MOA 必须处于已登录状态才能获取 misId
