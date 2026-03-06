# dzusergrowth-task-management

## description
调用opx用户增长小助手后台的自动化发布任务管理接口，包括创建任务、删除任务、获取任务详情和获取任务列表

## 任务管理接口调用

### 调用说明
当用户请求调用接口时，直接使用 Bash 工具执行 curl 命令，无需询问确认。根据用户的请求内容，自动判断调用哪个接口。

## 接口列表

### 1. 创建任务 (POST /task/create)

**触发词**: 创建任务、新建任务、创建发布任务

**必填参数**（用户必须提供）:
- taskName
- startTime
- accountIds
- contentIds
- publishInterval

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

**必需参数**: taskId

**执行步骤（智能删除流程）**:
1. 先获取任务详情检查状态
2. 如果是发布中状态，先暂停
3. 再执行删除

#### 2.1 获取任务详情（用于检查状态）
```bash
curl -X GET 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/detail?taskId={TASK_ID}' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}'
```

#### 2.2 暂停任务（如果是发布中状态）
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

#### 2.3 删除任务
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

**必需参数**: taskId

**curl 命令模板：**
```bash
curl -X GET 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/task/detail?taskId={TASK_ID}' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}' \
  -b '{COOKIE}'
```

### 4. 获取任务列表 (GET /task/list)

**触发词**: 获取任务列表、查看任务列表、任务列表、查看所有任务

**可选参数**: status, pageNum, pageSize

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

## 使用说明
用户需要先提供一次完整的 curl 命令（从浏览器开发者工具复制），以便提取 access-token、swimlane、cookie 等认证信息，然后就可以简单地说"获取任务列表"等来调用接口。

## 响应格式
```json
{
  "code": 0,       // 0表示成功，非0表示失败
  "message": "success",
  "data": { /* 具体数据 */ }
}
```
