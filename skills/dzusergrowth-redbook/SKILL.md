# dzusergrowth-redbook

## description
调用opx用户增长小助手后台的小红书笔记创建接口。当用户请求创建小红书笔记时使用此skill。

## 调用说明
当用户请求创建小红书笔记时，必须确保用户提供了以下4个必填参数：
- assetName（资产名称）
- title（标题）
- content（内容）
- imageUrls（图片URL列表）

如果缺少任何必填参数，需要提示用户提供。话题（topicList）可以为空。

## 接口详情

### 创建小红书笔记 (POST /redbook/create)

**触发词**: 创建笔记、创建小红书笔记、发布笔记、新建笔记

**路径**: `/api/dzusergrowth/operation/auto-publish/redbook/create`

**必填参数**（用户必须提供，不能为空）:
- `assetName` - 资产名称
- `title` - 笔记标题
- `content` - 笔记内容
- `imageUrls` - 图片URL数组，至少一张图片

**可选参数**:
- `topicList` - 话题列表，可以为空数组
- `coverImageUrl` - 封面图片URL，默认取 imageUrls 第一张
- `bizExtInfo` - 业务扩展信息

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
    "assetName": "{ASSET_NAME}",
    "title": "{TITLE}",
    "content": "{CONTENT}",
    "imageUrls": ["{IMAGE_URL}"],
    "topicList": [],
    "coverImageUrl": "{COVER_IMAGE_URL}",
    "bizExtInfo": "{\"source\":\"manual\"}"
  }'
```

### 参数说明
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| assetName | String | ✅ | 资产名称 |
| title | String | ✅ | 笔记标题 |
| content | String | ✅ | 笔记内容 |
| imageUrls | String[] | ✅ | 图片URL列表，至少一张 |
| coverImageUrl | String | ❌ | 封面图，默认取imageUrls第一张 |
| topicList | String[] | ❌ | 话题列表，可为空 |
| bizExtInfo | String | ❌ | 业务扩展信息JSON字符串 |

### 执行步骤
1. 检查必填参数是否完整（assetName、title、content、imageUrls）
2. 缺少参数时提示用户补充
3. 参数完整后，使用 curl 调用接口
4. 返回创建结果给用户

### 响应格式
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
**系统**: 提取参数并调用接口

## 注意事项
- 用户需要先提供一次完整的 curl 命令（从浏览器开发者工具复制），以便提取 access-token、swimlane 等认证信息
- imageUrls 至少需要一张图片
- coverImageUrl 如未提供，默认使用 imageUrls 的第一张
- topicList 可以为空数组
