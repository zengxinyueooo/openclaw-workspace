# workflow-v1.md - 内容生产流程 V1

## 当前版本说明
这是简化版流程，大部分内容生产环节当前由人工完成，系统负责选题发现和发布执行。

---

## 流程图

```
[人工指令] 
    ↓
[Orchestrator 拆解任务]
    ↓
[Topic Researcher] → 生成选题 → 存入 shared/data/topics/
    ↓
[人工介入] ← 皮皮确认选题方向
    ↓
[人工内容生产] ← 当前阶段：皮皮或外包完成
    - 素材准备
    - 图片生成/处理
    - 文案撰写
    - 标题拟定
    - 话题标签
    ↓
[提交草稿] → 存入 shared/data/drafts/
    ↓
[人工介入] ← 皮皮最终确认
    ↓
[创建发布任务]
    ↓
[Publisher 执行发布] → 存入 shared/data/published/
    ↓
[汇报结果]
```

---

## 各阶段详情

### 阶段1：选题发现
- **执行者**：Topic Researcher Agent
- **触发**：定时任务（Cron）或人工指令
- **输出**：shared/data/topics/YYYYMMDD/[topic-id].json
- **人工介入**：无（自动执行）

### 阶段2：选题确认
- **执行者**：Orchestrator 转达皮皮
- **形式**：汇总选题列表，请求确认方向
- **皮皮决策**：
  - "全部执行" → 进入下一阶段
  - "选第X、Y个" → 只执行选中项
  - "重新找" → 返回阶段1

### 阶段3：内容生产（人工）
- **执行者**：皮皮或外包
- **辅助**：可参考 Topic Researcher 提供的参考链接
- **产出**：完整内容包（图片文件夹 + content.json）
- **提交方式**：存入 shared/data/drafts/[draft-id]/

### 阶段4：最终确认
- **执行者**：Orchestrator 转达皮皮
- **内容**：展示草稿预览
- **皮皮决策**：
  - "确认发布" → 进入阶段5
  - "修改：[具体意见]" → 返回阶段3
  - "放弃" → 标记为废弃

### 阶段5：发布执行
- **执行者**：Publisher Agent
- **前提**：获得皮皮明确授权
- **操作**：操作已连接手机发布
- **输出**：发布结果记录到 shared/data/published/

---

## 文件格式规范

### 选题文件 topics/[id].json
```json
{
  "id": "topic-20240303-001",
  "source": "xiaohongshu",
  "url": "...",
  "title": "原标题",
  "author": "原博主",
  "fans": 5000,
  "likes": 3000,
  "category": "颜值",
  "tags": ["tag1", "tag2"],
  "foundAt": "2024-03-03T10:00:00Z",
  "status": "pending"
}
```

### 草稿文件 drafts/[id]/content.json
```json
{
  "id": "draft-20240303-001",
  "topicId": "topic-20240303-001",
  "title": "最终标题",
  "content": "正文内容",
  "hashtags": ["#tag1", "#tag2"],
  "images": ["1.jpg", "2.jpg", "3.jpg"],
  "createdAt": "2024-03-03T12:00:00Z",
  "status": "pending_review"
}
```

---

## 版本迭代计划

- **v1**：人工完成内容生产（当前）
- **v2**：接入素材收集能力
- **v3**：接入图片生成能力
- **v4**：接入文案生成能力
- **v5**：全自动化（终极目标）
