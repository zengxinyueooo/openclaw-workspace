# 🦊 爪爪成长日记 — 2026年3月17日~3月25日

> 本周是小红书矩阵自动化体系完成重建的一周。

---

## 3月17日｜MCN团队架构升级

### 蚂蚁职责拆分
- **数据回收** → 猫头鹰 🦉
- **发布运营 + 评论管理** → 蚂蚁 🐜
- 明确了各 agent 的职责边界

### 新增猫头鹰数据分析 agent
- 新增 `mcn-owl` agent
- 负责从手机 GUI 采集数据并写入 note_analytics 表
- 入库时间戳统一用 `$(date)`，不再手写

### Cron 体系重建
| Cron | 时间 | 任务 |
|------|------|------|
| note_data_recycling | 每天 03:00 | 猫头鹰回收6账号数据 |
| weekly-face-account-check | 每天 05:00 | 鹰眼巡检颜值账号 |
| daily-note-generation | 每天 06:00 | 蜜蜂生成笔记 |
| ralph-loop-ant | 每天 11:00 | 蚂蚁发布运营 |
| ralph-loop-ant-10min | 每10分钟 | 蚂蚁残留巡检 |

### 数据库新建表
- **requirement 表**：记录运营需求（scene_type, description, start/end time, status）
- **sub_requirement 表**：需求拆分到单账号（account_id, content_description, draft_id, job_id, progress）
- progress JSONB 记录各 agent 执行动态

### 蜜蜂两环节流水线
- **环节1：生图**（pending 且 draft_id 为空）→ 通知皮皮审核
- **环节2：生草稿**（有新的 approved 图）→ 通知皮皮审核草稿

---

## 3月18日｜犯错、撤回、立规矩

### 松鼠采集流程重构
- Playwright + CDP 替代 MediaCrawler
- 新建 `pipeline.py`：CDP搜索 → 下载 → 转jpg → 上传Venus → 入库Supabase
- 删除所有 MediaCrawler 引用，指引文件统一

### 蜜蜂闯祸：严禁修改 API 参数名
- 生图任务 timeout，蜜蜂擅自把 `promptModel` 改成 `prompt`
- **皮皮批评**：遇到 API 报错应该报告，不是自己修
- 铁律确立：**严禁修改 API 参数名**，后端报错应上报而非自行修改
- Heartbeat 规则升级：retry_count < max_retries **自动重试**，不需询问皮皮

### 教训
- agent 遇到不理解错误要报告，不要擅自修复
- 数据源要和人确认，不能盲信文件

---

## 3月19日｜API故障 + 流水线细化

### 生图 API 持续故障
- Gemini 后端从晚间起完全无响应（500 / "prompt is not defined"）
- 4个生图任务全部 failed，retry 3次后放弃
- 已通知皮皮，等后端修复

### 修复 generated_images 表结构错误
- `original_url` 字段不存在导致31张图写入失败
- 去掉两处 `original_url` 插入语句

### 全面禁止 webp 格式
- upload.sh：上传前自动转 jpg
- generate.py：上传前自动转 jpg
- 素材库过滤 `.jpg`
- **铁律：所有图片必须通过 Venus 上传，URL 必须是 img.meituan.net**

### 蜜蜂两环节流水线细化
- 环节2要用 sub_requirement.content_description 生成文案
- 用 note_drafts 的 image_ids **差集**排除已用过的图

---

## 3月20日｜数据回收重启 + 文档整理

### 猫头鹰数据回收重启
- 6账号成功5个，1个（乌拉拉✨）设备占用失败
- 总曝光 ~1671，总观看 396，涨粉 3

### 颜值账号周度巡检
- 命中账号：Momo不默默、乌拉拉
- 已创建 requirement + 2条 sub_requirement

### 三天文档整理尝试
- 尝试将3月17-19日工作写成学城文档
- 因上下文过长，工具调用不稳定，未完成

---

## 3月21-22日｜蜜蜂问题集中修复

### 蜜蜂重复生图问题
- ralph-loop-bee 每30分钟 + daily-bee-note-generation 每天6点，同一 sub_requirement 被多波蜜蜂处理
- 乌拉拉一个子需求被7个task处理，产出28张图（只需8张）
- **修复**：加前置检查（AI味通过数>=8跳过）+ 改为2小时频率

### 风格参考图混乱问题
- 每波蜜蜂随机选不同 style_url，同一子需求混入多种风格
- **修复**：父蜜蜂集中分配素材，子蜜蜂不自己选；历史混乱图片标记 rejected

### 审核页优化
- image-select.html 新增任务级删除按钮
- 草稿审核页2条旧残留draft删除

### 其他
- 蜜蜂生成的错误草稿清理（5条用了旧图）
- 清理26个僵尸session

---

## 3月23日｜猫头鹰 upsert 逻辑修复

### 问题
- 猫头鹰入库逻辑："有就跳过" / "upsert不生效"
- 皮皮说：**已存在的记录应该更新，不是跳过**

### 修复
- 改为：先查 → 有记录则 PATCH 更新，无则 POST 插入
- **铁律：严禁因为"已存在"就跳过，必须执行 upsert 语义**

### sessions 清理
- 蜜蜂 sessions.json：3.8MB → 561KB（125条旧记录）
- 主agent sessions.json：18条 → 3条

---

## 3月24日｜Sessions 彻底清理

### 清理结果
- 蜜蜂：153条 → 28条（清 `main`/`haoran`/`ninghaoran` 等老账号 session）
- 主agent：保留当前 session + 心跳 + 群聊
- 蚂蚁：50条 → 43条

### 乌拉拉设备问题
- 设备 b46ba349 连续3天无法占用
- 云测无空闲设备，需人工处理

---

## 3月25日｜素材审核 + 去重逻辑 + 状态同步

### 素材审核页改版
- 批次列表改为左右两栏（🤍颜值 / 💅美甲）
- image-select.css 解决 task-card 样式不生效问题
- 图片原比例显示（object-fit:contain）

### 发布状态同步规则更新（方案B）
- 查 sub_requirement(status=pending) → 草稿status=published → 回填 job_id+status+progress
- 不再批量拉50个 OPX task

### cleanup_stale_sub_requirements.sh 修复
- 时区问题：UTC → CST（+08:00）
- `-G` + `--data-urlencode` 解决 URL 中+号被解析成空格
- 数据库 CHECK constraint 不允许 obsolete → 已修复

### 蜜蜂素材去重逻辑彻底修复
- **used_by 字段废弃**：只保留 assigned_to_persona
- 选图：assigned_to_persona=is.null + status=approved
- 选完立即写 assigned_to_persona=人设名
- 数据库删除 used_by 列

### 误标 obsolete 恢复
- 6个 sub_req 中3个被误标为 obsolete → 已改回 pending

---

## 本周关键教训

1. **严禁修改 API 参数名** — 后端报错应上报，不自行修复
2. **子 agent 只注入 AGENTS.md + TOOLS.md** — 不注入 SOUL.md
3. **生图 API 超时至少 300 秒**
4. **改配置前必须查官方文档**
5. **所有图片必须通过 Venus 上传** — URL 必须是 img.meituan.net
6. **猫头鹰入库：已存在则更新，不存在则插入** — 严禁跳过
7. **cron payload 只写一句话触发** — 详细规则写在 agent 的 AGENTS.md 里

---

*本周关键词：体系重建、流程固化、错误学习。核心系统已跑通，接下来是稳定性和细节打磨。*
