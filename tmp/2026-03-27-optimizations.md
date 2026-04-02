# 📋 MCN Agent 日记与记忆体系优化记录

**日期：2026-03-27**
**作者：爪爪**

---

## 背景

今天（2026-03-27）和皮皮进行了一次系统性的梳理，针对日记体系、记忆沉淀、cron 职责等方面做了多项优化。以下是完整记录。

---

## 一、日记体系分层（新增设计）

之前只有爪爪主 cron 写成长日记，各 sub-agent 的汇报是纯清单式汇报，没有反思。今天确立了三层结构：

| 层级 | 写入者 | 文件位置 | 触发频率 | 内容要求 |
|------|--------|----------|----------|----------|
| 原始日志 | 各 sub-agent | `workspace-<agent>/memory/YYYY-MM-DD.md` | 每天 | 完整记录，有产出/异常/反思 |
| 成长日记 | 爪爪 | `memory/YYYY-MM-DD.md` | 每天凌晨 | 有主题句、分条目、根因分析、教训 |
| 精华沉淀 | 各 agent + 爪爪 | `MEMORY.md` | 每周一凌晨 | 回顾7天日志后筛选，只写真正重要的 |

---

## 二、各 sub-agent 日报格式更新（2026-03-27 执行）

**涉及文件：** `workspace-mcn-<ant/bee/eagle/owl/squirrel>/AGENTS.md`

每个 sub-agent 的「日向汇报」格式从原来三节（今日完成/异常/备注）升级为四节：

```
## YYYY-MM-DD 日记

### 今日完成
- <具体产出>

### 异常/问题
- <如果有>

### 反思
- <今天哪里做得不好、哪里可以改进、自己的判断和思考，不只是罗列现象>

### 备注
- <如果有>
```

汇报给爪爪的格式也同步更新，加入了「反思」节。

---

## 三、爪爪成长日记格式固化

**涉及文件：** `workspace/AGENTS.md`、`memory/2026-03-18-diary.md`（格式参考）

格式要求（详见 `memory/2026-03-18-diary.md`）：

```
# 🦊 爪爪成长日记 — YYYY年MM月DD日

## 今天的主题：（一句话概括今天的主线）

---

### （小标题：今天主要事件或重要问题）
具体内容：做了什么、怎么发生的、结果如何

---

## 今天学到的
- **（具体教训1）**
- **（具体教训2）**

---

*（一句话收尾）
```

**写作要求：**
- 有主题句，不是流水账
- 问题类事件要写根因，不只是描述现象
- 学到的教训要具体，能落地
- 爪爪反思要有自己的判断，不只是收集各 agent 汇报
- 可以有情绪和态度，但要有根据

---

## 四、每天必须写，不能断（新增铁律）

**铁律：** 即使所有 sub-agent 都回复"无产出"或根本没有回复，爪爪也必须根据 MEMORY.md、memory/、.learnings/ 进行反思和总结，写出当天的成长日记。日记是爪爪对系统的判断，不取决于子 agent 有没有给信息。

---

## 五、每周精华沉淀机制（新增）

**涉及文件：** `workspace/AGENTS.md`
**Cron：** `weekly-memory-consolidation`（ID: bc955f9d-dbc5-41bd-822d-1e6485064e44）
**时间：** 每周一 02:05（东京时区）

### 触发流程

1. 主 session 收到 systemEvent
2. 并行 spawn 5 个 sub-agent 执行「本周精华沉淀」
3. 爪爪自身同步执行沉淀
4. 各 agent 汇报完成后写 cron_runs

### 各 agent 沉淀动作

收到「执行本周精华沉淀」后：
1. 读 `memory/` 下过去 7 天的日志
2. 识别值得固化的内容：
   - 新确立的铁律或重要决策（立即写，标注日期）
   - 重复出现的问题且已找到根因
   - 被验证有效的流程或判断
   - 值得长期记住的事实
3. 融入各自 `MEMORY.md` 的合适位置（不是简单追加，是整合进已有结构）
4. 汇报给爪爪「✅ <agent> 本周沉淀已完成」

### MEMORY.md vs 日志的定位

| 文件 | 定位 | 写入频率 |
|------|------|----------|
| `memory/YYYY-MM-DD.md` | 完整日志，不过滤 | 每天 |
| `MEMORY.md` | 精华筛选，经过判断 | weekly + 重要决策立即写 |

---

## 六、cron_runs 表（新建）

**用途：** 记录所有 cron 的执行历史，用于追溯和问题排查。

**表结构：**
- `cron_name`：cron 名称
- `agent_id`：执行者
- `triggered_by`：触发方式
  - `cron`：由 cron 调度器自动触发
  - `manual`：由皮皮手动触发（如从控制面板点"立即执行"）
- `finished_at`：完成时间
- `status`：执行结果（ok / failed / error）
- `summary`：简短摘要

**已有 cron 列表：**

| Cron | 时间 | 任务 |
|------|------|------|
| session-cleanup | 每30分钟 | 清理 bee sessions |
| ralph-loop-ant | 每30分钟 | 检查笔记常态化运营 |
| ant-publish-status-sync | 每小时 | 发布状态同步 |
| ralph-loop-bee | 每小时 | 检查常态化笔记需求 |
| ralph-loop-eagle | 每天01:00 JST | 检查需求闭环状态 |
| daily-stale-subreq-cleanup | 每天00:05 CST | 废弃子需求清理 |
| daily-journal | 每天02:00 JST | 写成长日记 |
| daily-owl-data-recycling | 每天03:00 JST | 笔记数据回收 |
| daily-eagle-daily-check | 每天05:00 JST | 颜值账号日巡检 |
| daily-bee-note-generation | 每天06:00 JST | 检查并生成笔记 |
| daily-ant-publish-check | 每天11:00 JST | 检查待发布草稿 |
| daily-squirrel-dispatch | 每天12:00 JST | 素材采集任务 |
| **weekly-memory-consolidation** | **每周一02:05 JST** | **精华沉淀** |

---

## 七、今天发现并记录的问题

1. **发布链路卡单**：OPX 接口层异常导致 taskId 190/191 卡在 PENDING_SUBMIT，需要皮皮登录 OPX 后台检查
2. **松鼠采集未真正触发**：daily-squirrel-dispatch cron 触发了，但松鼠没有昨日入库记录，需要排查调度链路

---

*文档ID：待补充*
*最后更新：2026-03-27 18:08*
