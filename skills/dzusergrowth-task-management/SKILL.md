---
name: dzusergrowth-task-management
description: 调用opx用户增长小助手后台的自动化发布任务管理接口，包括创建任务、删除任务、获取任务详情和获取任务列表
---

# 任务管理接口调用

## 默认配置

- 服务地址: https://mdz.sankuai.com
- 认证方式: 需要 access-token 和 cookie
- 必需请求头:
  - access-token: 用户认证令牌
  - Origin: https://opx-ai.sankuai.com
  - Referer: https://opx-ai.sankuai.com/
  - swimlane: 泳道标识（从用户提供的 curl 中提取）

## 调用说明

当用户请求调用接口时，直接使用 Bash 工具执行 curl 命令，无需询问确认。根据用户的请求内容，自动判断调用哪个接口。

## 接口列表

### 1. 创建任务 (POST /task/create)

**触发词**: 创建任务、新建任务、创建发布任务

**必填参数（用户必须提供）**:
- taskName: 任务名称 - 必填

**其他必需参数（从用户消息中提取，如缺失则提示用户）**:
- startTime: 开始时间（格式：YYYY-MM-DD HH:mm:ss）
- accountIds: 账号ID列表
- contentIds: 内容ID列表

**可选参数**:
- publishInterval: 发布间隔分钟数（默认: 360，即6小时）

**执行步骤**:
1. 检查用户是否提供了任务名称，如未提供则提示
2. 检查其他必需参数（开始时间、账号ID、内容ID），如未提供则提示
3. 发布间隔如未提供，使用默认值 360 分钟（6小时）
4. 执行创建任务的 curl 命令

**curl 命令模板：**

```bash
curl -X POST 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/create' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}' \
  -d '{
    "taskName": "{TASK_NAME}",
    "startTime": "{START_TIME}",
    "accountIds": {ACCOUNT_IDS},
    "contentIds": {CONTENT_IDS},
    "publishInterval": {PUBLISH_INTERVAL}
  }'
```

### 2. 删除任务 (POST /task/delete)

**触发词**: 删除任务、删除发布任务

**必需参数**:
- taskId: 任务ID（从用户消息中提取，如 "删除任务123456"）

**执行步骤（智能删除流程）**:
1. 先调用 /task/detail 接口获取任务详情，检查任务状态
2. 如果任务状态是 PUBLISHING（发布中），则：
   - 先调用 /task/status 接口暂停任务（action: "pause"）
   - 等待暂停成功后，再调用删除接口
3. 如果任务状态不是发布中，直接调用删除接口
4. 展示删除结果

**相关接口：**

**2.1 获取任务详情（用于检查状态）**

```bash
curl -X GET 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/detail?taskId={TASK_ID}' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}'
```

**2.2 暂停任务（如果是发布中状态）**

```bash
curl -X POST 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/status' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}' \
  -d '{"taskId": "{TASK_ID}", "action": "pause"}'
```

**2.3 删除任务**

```bash
curl -X POST 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/delete' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}' \
  -d '{"taskId": "{TASK_ID}"}'
```

### 3. 获取任务详情 (GET /task/detail)

**触发词**: 查看任务详情、获取任务详情、任务详情

**必需参数**:
- taskId: 任务ID（从用户消息中提取）

**curl 命令模板：**

```bash
curl -X GET 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/detail?taskId=123456' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}' \
  -b '{COOKIE}'
```

### 4. 获取任务列表 (GET /task/list)

**触发词**: 获取任务列表、查看任务列表、任务列表、查看所有任务

**可选参数（从用户消息中提取）**:
- status: 任务状态（如 "运行中的任务" -> RUNNING）
- pageNum: 页码（默认: 1）
- pageSize: 每页条数（默认: 10）

**curl 命令模板：**

```bash
# 获取所有任务
curl -X GET 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/list?pageNum=1&pageSize=10' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}' \
  -b '{COOKIE}'

# 获取运行中的任务
curl -X GET 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/list?status=RUNNING&pageNum=1&pageSize=10' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}' \
  -b '{COOKIE}'
```

## 通用执行步骤

1. **获取认证参数**: 调用 opx-auth skill 获取 access-token 和 cookie
2. **识别意图**: 根据用户消息判断要调用哪个接口
3. **提取参数**: 从用户消息中提取业务参数
4. **构建命令**: 使用认证参数和业务参数构建 curl 命令
5. **执行 curl**: 使用 Bash 工具执行命令
6. **展示结果**: 解析响应 JSON，向用户说明操作结果

## 特殊处理逻辑

**创建任务**:
- 必须提供任务名称，否则提示用户
- 发布间隔默认为 360 分钟（6小时）

**删除任务**:
- 自动检查任务状态
- 如果是发布中状态（PUBLISHING），先暂停再删除
- 其他状态直接删除

## 使用说明

用户需要先提供一次完整的 curl 命令（从浏览器开发者工具复制），然后就可以简单地说"获取任务列表"等来调用接口。

## 响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { /* 具体数据 */ }
}
```

## 状态码映射

| 用户说法 | API状态值 |
|---------|----------|
| "运行中" / "正在运行" | RUNNING |
| "待执行" / "等待中" | PENDING |
| "已完成" / "完成" | COMPLETED |
| "已暂停" / "暂停" | PAUSED |
| "失败" | FAILED |
