# MCN 小红书自动化矩阵 - 本周（3/16-3/20）工作回顾

> 记录时间：2026-03-16 ~ 2026-03-20
> 团队：爪爪 🦊 + 鹰眼 🦅 + 松鼠 🐿️ + 蜜蜂 🐝 + 蚂蚁 🐜 + 猫头鹰 🦉

---

## 一、架构升级：新增猫头鹰 Agent，职责重新划分

### 1.1 新建猫头鹰（mcn-owl）数据分析 Agent
- **ID**: mcn-owl
- **职责**: 数据回收 + 数据分析
- **Skill**: gui-agent-cloud（云真机 GUI Agent 自动化）
- **核心能力**: 
  - 在云真机上执行 GUI Agent 任务
  - 自动回收小红书笔记数据（曝光、观看、互动等）
  - 入库到 note_analytics 表

### 1.2 Agent 职责重新划分

| Agent | 调整前 | 调整后 |
|-------|--------|--------|
| 蚂蚁 🐜 | 发布 + 数据回收 + 评论 | **发布运营 + 评论管理** |
| 猫头鹰 🦉 | （无） | **数据回收 + 数据分析** |

---

## 二、数据库表结构新增

### 2.1 note_analytics 表
存储笔记数据快照，支持 upsert 去重：
```sql
- persona_name: 人设名称（派发时给定，不用屏幕昵称）
- note_title: 笔记标题
- collected_at: 采集时间
- impressions/views/followers_gained/likes/comments/favorites/shares: 原始数据
- 唯一约束: persona_name + note_title
```

### 2.2 requirement / sub_requirement 表
支持常态化运营需求跟踪：
- **requirement**: 运营需求（scene_type, description, status）
- **sub_requirement**: 拆分后的单账号任务（account_id, content_description, draft_id, job_id, progress）

### 2.3 字段增补
- `note_drafts.sub_requirement_id`: 关联子需求
- `generated_images.sub_requirement_id`: 关联子需求（migration_007）

---

## 三、Cron 体系全面重构

### 3.1 新增/调整 Cron 任务

| Cron 名称 | 触发时间 | 触发对象 | 功能 |
|-----------|----------|----------|------|
| `note_data_recycling` | 每天 03:00 东京 | 爪爪 → 猫头鹰 | 全账号数据回收 |
| `weekly-face-account-check` | 每天 05:00 东京 | 爪爪 → 鹰眼 | 颜值账号周度巡检 |
| `daily-note-generation` | 每天 06:00 北京 | 爪爪 → 蜜蜂 | 常态化笔记生成 |
| `daily-ant-publish-check` | 每天 11:00 东京 | 爪爪 → 蚂蚁 | 发布检查 |
| `ralph-loop-ant-10min` | 每 10 分钟 | 蚂蚁 | 静默巡检待发布草稿 |
| `ralph-loop-bee` | 每 2 小时 | 蜜蜂 | 常态化笔记生成巡检 |

### 3.2 Cron 触发模式优化
- **之前**: cron payload 写长指令
- **之后**: cron 只给一句话触发，具体规则写在对应 Agent 的 AGENTS.md
- **好处**: 规则集中管理，cron 精简，易于维护

---

## 四、各 Agent 核心优化

### 4.1 蚂蚁 🐜 - 发布运营

**问题修复**:
- 修复 `content_ready` 草稿被误处理为 `approved` 的问题
- 修复创建 OPX 资产时图片 URL 查询逻辑（必须从 generated_images 表查，不能自己编）
- 人设独立发布时间：今天有 published 则从明天选，没有则从今天剩余高峰段选

**流程优化**:
- 全量并行模式：环节1（approved→asset_created）和环节2（asset_created→published）并行 spawn subagent

### 4.2 蜜蜂 🐝 - 内容生产

**流水线改造**:
- 两环节流水线：
  - **环节1**: sub_requirement status=pending 且 draft_id 为空 → 生图
  - **环节2**: 有新的 approved 图且未被使用 → 生草稿
- 父蜜蜂集中分配素材，子蜜蜂不自己选素材（防并发冲突）

**问题修复**:
- 修复重复生图问题：AI味通过数 >= 8 则跳过
- 修复风格参考图混乱：material_ids 已有值时不重新分配
- 修复 generated_images 表漏写 face_passed=true

**架构调整**:
- ralph-loop-bee 频率从 30分钟 改为 2小时
- 蜜蜂子蜜蜂直接输出结果，统一去掉 sessions_send(label="main")

### 4.3 猫头鹰 🦉 - 数据回收

**核心流程**:
```
占用设备 → 生成 flowUuid → 设备锁 → 提交 GUI Agent 任务 → 轮询状态 → 释放设备
```

**关键铁律**:
- 无论成功失败必须释放设备
- 设备占用失败重试 3 次后立即结束
- persona_name 必须用派发时给定的名字
- 入库时间戳用 $(date) 取，不让模型自己填（防 2025 年问题）

**性能优化**:
- 单账号串行 25 分钟 → 6 账号并行 6 分钟
- 爪爪调度方案：list_accounts.py → 分批 spawn 猫头鹰（每批 20 个）

### 4.4 鹰眼 🦅 - 选题策划

**新增巡检功能**:
- 颜值账号周度巡检：检查本周浏览量>100的笔记数量
- 若 <1 则标记为需要常态化运营，创建 requirement + sub_requirement

### 4.5 松鼠 🐿️ - 素材采集

**方案重构**:
- 废弃 MediaCrawler（import 失败）
- 新方案: Playwright + CDP（Chrome DevTools Protocol）
- 流程: CDP搜索 → 提取笔记图片 → 下载 → 转jpg → 上传Venus → 入库Supabase
- 新建 `pipeline.py` 完整流水线

---

## 五、图片格式统一规范

### 5.1 全面禁止 webp
- **要求**: 所有素材图片的 URL 必须是美团内网 Venus 地址（img.meituan.net）
- **上传前强制转 jpg**:
  - upload.sh: webp/png/heic → jpg
  - generate.py upload_to_venus(): 自动转 jpg
  - generate.py 取风格参考图: 加 `.like('image_url', '%.jpg')` 过滤

### 5.2 相关修复
- 乌拉拉 profile.json: styleRef 重新上传为 jpg
- task_runner.py / run_task.py: 硬编码 webp URL 已替换

---

## 六、通知机制统一

### 6.1 变更前
子 agent `sessions_send(label="main")` 主动通知爪爪

### 6.2 变更后
cron 用 main systemEvent 唤醒爪爪 → 爪爪 spawn agent → `sessions_yield` 等结果 → 结果自动回来

### 6.3 已统一去掉 sessions_send 的 Agent
- 鹰眼、蜜蜂、蚂蚁、猫头鹰
- 子 agent 只需要输出结果，不需要关心通知链路

---

## 七、前端审核页面

### 7.1 新增功能
- 草稿审核页：新增「删除草稿」功能
- 生图审核页：过滤 generated_count=0 的任务
- 话题标签：支持自定义添加

### 7.2 部署优化
- HTTP server 持久化：改用 launchctl 注册为系统服务
- 开机自启 + 挂了自动重启
- 启动目录: workspace/tasks/supabase-materials/review/

### 7.3 关键链接
- 素材审核: https://review-gold-seven.vercel.app/
- 生图审核: https://review-gold-seven.vercel.app/image-select.html
- 草稿审核: https://review-gold-seven.vercel.app/draft-review.html
- 数据看板: https://review-gold-seven.vercel.app/dashboard.html

---

## 八、sub_requirement 进度回填机制

建立了完整的需求 → 执行 → 反馈闭环：

| Agent | 回填时机 | 回填内容 |
|-------|----------|----------|
| 鹰眼 | 巡检命中 | 创建 requirement + sub_requirement |
| 蜜蜂 | 生成笔记 | 写 sub_requirement_id 到 note_drafts + 回填 progress |
| 蚂蚁 | 发布成功 | 从草稿的 sub_requirement_id 回填 progress |
| 猫头鹰 | 数据回收 | 按 persona_name 匹配 sub_requirement 回填 progress |

---

## 九、账号调整

- 账号列表从 10 个缩减为 6 个
- 删除：增增哇嘎奶、小Lin晓晓、糯糯糖要努力、一只小晚晚
- 保留：Momo不默默、一只小糕糕、乌拉拉、先叫Momo、李慢慢曼妙、沐沐木有烦恼

---

## 十、关键经验教训

1. **persona_name 一致性**：派发时给定的名字 vs 屏幕昵称（如「李慢慢曼妙」vs「李曼曼养生所」），会导致去重和匹配失败
2. **猫头鹰年份 bug**：kimi-k2.5 模型会把年份写成 2025，改用 $(date) 取时间
3. **蚂蚁图片 URL 问题**：必须从 generated_images 表查，不能自己编造
4. **cron session 生命周期**：isolated session yield 后即关闭，子 agent announce 回不到已关闭的 session
5. **并发素材选取**：limit=1 无随机排序会导致多个子蜜蜂选到同一张素材，改为父蜜蜂集中分配
6. **蜜蜂重复生图**：多 cron 触发同一 sub_requirement，需前置检查通过数量
7. **生图 API 不稳定**：3/17 起 Gemini 后端持续返回 500，全线暂停等恢复
8. **严禁修改 API 参数名**：后端报错应上报而非自行修改参数名

---

## 十一、下周待办

- [ ] 生图 API 恢复后，重新发起全部常态化笔记生成任务
- [ ] migration_007（generated_images 加 sub_requirement_id）待执行
- [ ] 素材库 165 张 webp 批量迁移为 jpg
- [ ] job_id 回填 cron 待建立
