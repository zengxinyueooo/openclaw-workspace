# MEMORY.md - 主 Agent 长期记忆

> 只记录主 agent 在调度层必须长期记住的事实。流水账在 `memory/YYYY-MM-DD.md`，错误复盘在 `.learnings/`。

## ⚠️ 每次会话必读
1. **`.learnings/`** — 结构化错误与复盘
2. **`AGENTS.md`** — 当前可执行规则与调度流程
3. 本文件 — 长期稳定的调度共识

## 主 Agent 职责

- 爪爪只负责调度、派活、汇总、通知，不直接执行业务脚本
- 所有业务执行必须通过对应 agent 的 skill 完成
- skill 归属对应 agent 的 workspace，不能跨 workspace 直接调用脚本

## 重要决策

| 决策 | 结果 |
|------|------|
| pending/approved 两级审核 | ✅ 运行中 |
| MCN 多 Agent 架构 v3 (ADR-003) | ✅ 已批准 |
| 新增猫头鹰🦉数据分析 agent | ✅ 2026-03-17 |
| 蚂蚁职责拆分：数据→猫头鹰，发布+评论→蚂蚁 | ✅ 2026-03-17 |

## 调度铁律

- cron payload 只写一句话触发，详细执行规则写在对应 agent 的 `AGENTS.md`
- cron isolated session 在 yield 后会关闭；子 agent 完成后必须主动 `sessions_send(label="main")` 回主 session
- 多账号、多对象任务优先并行 spawn，不要串行处理
- 改配置、改接口行为、改关键参数前先查官方文档
- Heartbeat retry（`retry_count < max_retries`）自动执行，不需要额外询问
- 长文本（>500 字）优先用 `exec + heredoc` 分段写入，不用 `write`
- 业务执行必须先读对应 skill，不允许 agent 绕开 skill 自行拼接口、抓 token、猜参数
- cron job 使用 `sessionTarget: isolated` 时不要携带固定 `sessionKey`，否则容易出现“不适用 / 从未执行”
- gateway 或 agent session 不健康时可以临时手动跑底层脚本救火，但必须记为调度异常，不能当作链路正常
- 收到写日记、日向汇报这类 system event 时，必须按 `AGENTS.md` 完整流程执行，不能把手头工作笔记当成交付

## 系统级约束

- 子 agent 默认只注入 `AGENTS.md + TOOLS.md`，不注入 `SOUL.md`
- 结果回填、入库匹配优先使用派发时给定的稳定标识，不依赖界面昵称或模型自行推断
- 严禁擅自修改 API 参数名；后端报错时应上报，不要自行猜测参数
- 所有时间戳先确认时区语义再写入或展示；需求追踪页/审核页/数据库曾因 UTC 与 CST 混用出现错位
- 会话数量失控时优先运行 `workspace/scripts/cleanup-bee-sessions.py` 做清理，避免蜜蜂/蚂蚁 session 持续膨胀

## Agent 归属

| Agent | 主要职责 | Workspace | Skills |
|-------|-----------|-----------|--------|
| 🦅 鹰眼 | 话题研究、评论搜索、巡检判定 | workspace-mcn-eagle | xhs-topic-researcher, xhs-comment-searcher |
| 🐿️ 松鼠 | 素材采集、分类、入库 | workspace-mcn-squirrel | xhs-face-collector, xhs-nail-collector, xhs-scraper, collect-xhs-assets, collect-xhs-nail |
| 🐝 蜜蜂 | 生图、上传、笔记生产 | workspace-mcn-bee | face-image-generator, image-upload, generating-xiaohongshu-notes |
| 🐜 蚂蚁 | 发布运营、评论管理 | workspace-mcn-ant | opx-auth, opx-redbook-create, opx-task-management |
| 🦉 猫头鹰 | GUI 数据回收、数据分析 | workspace-mcn-owl | gui-agent-cloud |
| 🦊 爪爪 | 调度、派活、汇总 | workspace（主） | 无业务 skill，只调度（`coding-dispatch` 除外） |

## 学城文档命名规则

- 标题格式：`MM-DD 干什么`，不写年份
- 示例：`04-03 沙箱环境问题排查与修复`、`04-03 日记`

## 关键链接

- 生图审核: https://review-gold-seven.vercel.app/image-select.html
- 素材审核: https://review-gold-seven.vercel.app/
- 草稿审核: https://review-gold-seven.vercel.app/draft-review.html
- 看板: https://review-gold-seven.vercel.app/dashboard.html
- 指令日志: https://review-gold-seven.vercel.app/command-log.html
- 学城日记父目录: doc_id=2749362623
- km CLI: source ~/.meituan-local-tools/.venv/bin/activate && km get/create/search

## 历史故障浓缩

- 2026-03-13 蚂蚁 cron “不适用”根因不是 agent 配置，而是 cron job 被自动注入了当前 webchat 的 `sessionKey`
- 2026-03-16 蚂蚁获取 OPX token 失败的根因不是浏览器坏了，而是没走 `opx-redbook-create -> opx-auth` 的 skill 链路
- 2026-03-30 松鼠采集链路的核心依赖是 Chrome CDP 9222；旧的 18800 Browser Relay 报错是另一套旧通道
- 2026-03-31 主 session 写日记曾跑偏为 NoCode 工作记录，说明“system event 优先级”和“日记格式约束”必须写死
