---
name: dzusergrowth-redbook-create
description: 调用opx用户增长小助手后台的小红书笔记创建接口，用于创建小红书内容资产
---

# 小红书笔记创建接口

## 默认配置

- 服务地址: https://mdz.sankuai.com
- 认证方式: 需要 access-token 和 cookie
- 必需请求头:
  - access-token: 用户认证令牌
  - Origin: https://opx-ai.sankuai.com
  - Referer: https://opx-ai.sankuai.com/
  - swimlane: 泳道标识

## 调用说明

当用户请求创建小红书笔记时，必须确保用户提供了以下4个必填参数：
1. 资产名称（assetName）
2. 标题（title）
3. 内容（content）
4. 图片（imageUrls）- 至少一张

如果缺少任何必填参数，需要提示用户提供。话题（topicList）可以为空。

## 接口详情

### 创建小红书笔记 (POST /redbook/create)

**触发词**: 创建笔记、创建小红书笔记、发布笔记、新建笔记

**路径**: /api/dzusergrowth/operation/auto-publish/redbook/create

**必填参数（用户必须提供，不能为空）**:
- assetName: 资产名称 - 必填
- title: 笔记标题 - 必填
- content: 笔记内容 - 必填
- imageUrls: 图片URL列表 - 必填，至少一张图片

**可选参数**:
- coverImageUrl: 封面图片URL（默认: 使用第一张图片）
- topicList: 话题列表（默认: []，可以为空）
- bizExtInfo: 业务扩展信息（默认: "{\"source\":\"manual\"}"）

**curl 命令模板：**

```bash
curl -X POST 'https://mdz.sankuai.com/api/dzusergrowth/operation/auto-publish/redbook/create' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://opx-ai.sankuai.com' \
  -H 'Referer: https://opx-ai.sankuai.com/' \
  -H 'access-token: {ACCESS_TOKEN}' \
  -H 'swimlane: {SWIMLANE}' \
  --data-raw '{
    "assetName": "测试笔记",
    "title": "测试标题",
    "content": "测试内容",
    "imageUrls": ["https://example.com/image.png"],
    "topicList": [],
    "coverImageUrl": "https://example.com/image.png",
    "bizExtInfo": "{\"source\":\"manual\"}"
  }'
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| assetName | String | 是 | 内容资产名称，用于在系统中标识这个笔记 |
| title | String | 是 | 小红书笔记的标题 |
| content | String | 是 | 小红书笔记的正文内容 |
| imageUrls | Array\<String\> | 是（至少一张） | 笔记图片URL列表，支持多张图片，不能为空 |
| coverImageUrl | String | 否 | 笔记封面图片URL，通常使用第一张图片作为封面 |
| topicList | Array\<String\> | 否 | 笔记话题标签列表，例如 ["美食", "探店"] |
| bizExtInfo | String (JSON) | 否 | 业务扩展信息，记录笔记来源等信息 |

## 执行步骤

1. **获取认证参数**: 调用 opx-auth skill 获取 access-token 和 cookie
2. **识别意图**: 判断用户是否要创建小红书笔记
3. **提取参数**: 从用户消息中提取笔记标题、内容、图片等信息
4. **验证必填参数**: 检查以下4个参数是否都已提供：
   - 资产名称（assetName）
   - 标题（title）
   - 内容（content）
   - 图片（imageUrls，至少一张）
5. **提示缺失参数**: 如果缺少任何必填参数，提示用户提供
6. **构建请求**: 使用认证参数和提取的参数构建 JSON 请求体
7. **执行 curl**: 使用 Bash 工具执行 curl 命令
8. **展示结果**: 解析响应，告知用户创建结果

## 响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "contentId": "2027588732543168555",
    "assetName": "测试笔记",
    "title": "测试标题"
  },
  "traceId": "xxx"
}
```

## 使用示例

### 示例1：缺少必填参数

**用户**: "帮我创建一个小红书笔记，标题是'上海探店'，内容是'发现了一家好吃的餐厅'"

**系统**: 检测到缺少图片，提示用户：
> "创建小红书笔记需要提供图片。请提供至少一张图片URL。"

### 示例2：完整参数

**用户**: "创建笔记：资产名称'上海探店'，标题'上海探店'，内容'发现了一家好吃的餐厅'，图片https://xxx.png"

**系统**: 提取参数并调用接口：
- assetName: "上海探店"
- title: "上海探店"
- content: "发现了一家好吃的餐厅"
- imageUrls: ["https://xxx.png"]
- coverImageUrl: "https://xxx.png"
- topicList: []

## 注意事项

- **必填参数验证**: 创建笔记前必须确保用户提供了资产名称、标题、内容和图片这4个参数
- **图片必填**: imageUrls 不能为空数组，至少需要一张图片
- **图片URL格式**: 必须是有效的图片链接，通常是 S3 或 CDN 地址
- **话题标签**: topicList 可以为空，如果提供话题，不需要加 # 符号
- **内容长度**: 注意小红书对标题和内容长度的限制
- **认证信息**: 使用用户提供的 access-token 和 swimlane
