# MEMORY.md - 主 Agent 长期记忆

> 只记录主 agent 在调度层必须长期记住的事实。流水账在 `memory/YYYY-MM-DD.md`，错误复盘在 `.learnings/`。

## ⚠️ 每次会话必读
1. **`.learnings/`** - 结构化错误与复盘
2. **`AGENTS.md`** - 当前可执行规则与调度流程
3. 本文件 - 长期稳定的调度共识

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
- cron job 使用 `sessionTarget: isolated` 时不要携带固定 `sessionKey`，否则容易出现"不适用 / 从未执行"
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
| 🐜 蚂蚁 | 发布运营、评论管理、**养号** | workspace-mcn-ant | opx-auth, opx-redbook-create, opx-task-management, account-nurturing |
| 🦉 猫头鹰 | GUI 数据回收、数据分析 | workspace-mcn-owl | gui-agent-cloud |
| 🦊 爪爪 | 调度、派活、汇总 | workspace（主） | 无业务 skill，只调度（`coding-dispatch` 除外） |

### 养号委派规则
- cron `ant-account-nurturing`（每天 14:00 北京时间）→ **主 session（爪爪）** 收到「执行养号任务」
- 爪爪 spawn 蚂蚁子 agent（workspace-mcn-ant）执行
- 蚂蚁读 `skills/account-nurturing/SKILL.md`，`sessions_send(label="main")` 回报结果
- token 来自 `.env.opx`，过期由皮皮处理，爪爪不直接操作养号接口

### 养号委派规则
- cron `ant-account-nurturing`（每天 14:00 北京时间）→ 主 session（爪爪）收到「执行养号任务」
- 爪爪 spawn 蚂蚁子 agent（workspace-mcn-ant）执行
- 蚂蚁读 `skills/account-nurturing/SKILL.md`，`sessions_send(label="main")` 回报结果
- token 来自 `.env.opx`，过期由皮皮处理，爪爪不直接操作养号接口

## 学城文档命名规则

- 标题格式：`MM-DD 干什么`，不写年份
- 示例：`04-03 沙箱环境问题排查与修复`、`04-03 日记`

## 关键链接

- 生图审核: https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/image-select.html
- 素材审核: https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/index.html
- 草稿审核: https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/draft-review.html
- 看板: https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/dashboard.html
- 指令日志: https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/command-log.html
- 需求追踪: https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/requirement.html
- 部署: `webstatic deploy --appkey=com.sankuai.dzfe3.opxaimanage --artifact=. --env=prod --token=b70bdb0e-606d-46d3-9900-1a857f9cf1a2`（在 review/ 目录下）
- 学城日记父目录: doc_id=2749362623
- km CLI: source ~/.meituan-local-tools/.venv/bin/activate && km get/create/search

## 系统长期待修项（皮皮介入）

> 记录需要皮皮手动处理、非子 agent 能自行解决的系统性问题

| 问题 | 严重程度 | 首次发现 | 状态 |
|------|----------|----------|------|
| 蜜蜂 Supabase anon key 失效（03-31 起） | 🔴 阻塞生图全链路 | 2026-03-31 | **待修** |
| 小Lin晓晓 设备 `4e2ee966` 未登录小红书 | 🔴 数据回收失败 | 2026-04-05 | **待修** |
| 松鼠 nail 详情页采集逻辑失效（持续 0 产出） | 🟡 美甲素材断供 | ~2026-03-30 | **待修** |
| YOLO 未安装，face 素材无人脸过滤 | 🟡 素材质量无保障 | 2026-04-04 | **待修** |
| ZHIPU_API_KEY 未配置，AI 打标停摆 | 🟡 素材评分全为50 | 2026-04-04 | **待修** |
| 云真机 b46ba349/bb621562 GUI Agent 守护进程异常 | 🟡 影响数据回收 | 2026-04-05 | **待修** |
| 云真机多台设备持续 300404 | 🟡 数据回收成功率低 | 2026-04-04 | **持续** |
| 松鼠 CDP Runtime/Page 域不可用（Chrome `--test-type` 参数影响） | 🔴 素材采集链路完全阻塞 | 2026-04-07 | **✅ 2026-04-08 已修（nail_collector.py）** |

## 本周技术沉淀（2026-03-30 ~ 2026-04-05）

- **颜值生图切换到 V4**：从调用后端 API 改为本地跑 `ai_aesthetic_workflow`（`run_v4.py`），通过 Gemini 直接生图，耗时约 100s，smoke test 成功率高
- **素材双表架构**：`materials`（入库/审核）+ `available_materials`（已 approved，松鼠分配和蜜蜂查的唯一入口），用 `used_by TEXT[]` 做原子占用，trigger 自动同步
- **生图统计体系**：建 `image_gen_log` 表，face/nail 两条链路都接入公共 logger，审核页新增 `gen-stats.html` 统计页
- **时区铁律确立**：所有时间戳写入必须用 `Asia/Shanghai`（`+08:00`），禁止混用 UTC `Z` 结尾
- **沙箱写路径铁律**：所有写操作只走 `/mnt/openclaw/.openclaw/`，`/root/.openclaw/` 只读不写
- **doudou 美甲笔记首发**：完整走通「鹰眼创需求 → 松鼠填素材 → 蜜蜂生图 → 蚂蚁发布」全链路（taskId=197）

## 历史故障浓缩

- 2026-03-13 蚂蚁 cron "不适用"根因不是 agent 配置，而是 cron job 被自动注入了当前 webchat 的 `sessionKey`
- 2026-03-16 蚂蚁获取 OPX token 失败的根因不是浏览器坏了，而是没走 `opx-redbook-create -> opx-auth` 的 skill 链路
- 2026-03-30 松鼠采集链路的核心依赖是 Chrome CDP 9222；旧的 18800 Browser Relay 报错是另一套旧通道
- 2026-03-31 主 session 写日记曾跑偏为 NoCode 工作记录，说明"system event 优先级"和"日记格式约束"必须写死
- 2026-04-02 改 openclaw gateway 端口风险大，自动重启会覆盖配置并断 session，不要尝试
- 2026-04-03 蜜蜂 token 消耗暴涨根因：生图 API 0 图返回 + 4 轮 600s 超时重试 + 5 个 subagent 并行，需熔断机制
- 2026-04-03 `/root/.openclaw/workspace/AGENTS.md` 被爪爪误用为底稿覆盖了自定义版本；从 git 恢复，教训：改文件前先确认是 `/mnt/openclaw/` 路径
