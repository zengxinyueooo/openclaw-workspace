# ADR-003: MCN 多 Agent 架构 v3

**日期**: 2026-03-04
**决策人**: 皮皮
**状态**: ✅ 已批准
**覆盖**: ADR-002

---

## 技术验证：OpenClaw 原生支持多 Agent

根据官方文档 (docs.openclaw.ai/zh-CN/concepts/multi-agent)，OpenClaw 原生支持：

1. **多个隔离 Agent**：每个 Agent 拥有独立的 workspace + agentDir + sessions
2. **统一配置**：在 openclaw.json 的 agents.list 中声明所有 Agent
3. **路由绑定**：通过 bindings 将入站消息路由到指定 Agent
4. **Agent 间通信**：通过 tools.agentToAgent 配置（默认关闭，需显式启用）
5. **独立沙箱和工具策略**：每个 Agent 可以有不同的权限

每个 Agent 是一个完全独立的"大脑"：
- 独立 workspace（SOUL.md / MEMORY.md / USER.md）
- 独立 agentDir（认证、模型配置）
- 独立 sessions（聊天历史 + 路由状态）
- 独立 skills/（每 Agent 的技能）
- 共享 skills 从 ~/.openclaw/skills 获取

## 架构设计

### 角色定义

| Agent ID | 名字 | 角色 | 性格 | 职责 | 触发方式 |
|----------|------|------|------|------|----------|
| main | 爪爪 🦊 | COO/秘书长 | 机灵、高效、偶尔皮 | 唯一用户入口，派活/汇报/审核对接 | 用户消息 |
| mcn-eagle | 鹰眼 🦅 | 策划总监 | 全局视野、精准匹配、冷静决断 | 活动策划、账号匹配、排期 | 爪爪派活 |
| mcn-squirrel | 松鼠 🐿️ | 素材总监 | 囤货狂魔、分类强迫症、嗅觉灵敏 | 日常素材积累、分类管理 | Cron + 爪爪派活 |
| mcn-bee | 蜜蜂 🐝 | 内容生产 | 勤劳高产、工艺讲究、效率至上 | 调用工作流生产内容 | 爪爪派活 |
| mcn-ant | 蚂蚁 🐜 | 运营专家 | 耐心细致、数据敏感、持续跟进 | 数据监控、评论维护、排期调整 | Cron + 爪爪派活 |
| mcn-woodpecker | 啄木鸟 🪶 | 技术运维（后期） | 找bug专家、靠谱 | 故障排查、小型开发 | 爪爪派活 |

### 目录结构

```
~/.openclaw/
  openclaw.json                          # 全局配置（agents.list + bindings）

  workspace/                             # 爪爪（main）workspace
    SOUL.md / MEMORY.md / USER.md
    shared/                              # 共享数据层
      accounts/                          # 账号数据库
        _index.json
        acc-001.json ... acc-020.json
      personas/                          # 人设库
      content-assets/                    # 素材库
      state/                             # 任务状态 + 事件队列
        task-queue.json
        events/
      config/                            # 共享配置

  workspace-mcn-eagle/                   # 鹰眼 🦅 策划总监 workspace
    SOUL.md                              # "我是鹰眼，全局视野、精准匹配..."
    MEMORY.md                            # 活动历史、匹配经验
    skills/                              # 策划专用 skills

  workspace-mcn-squirrel/                # 松鼠 🐿️ 素材总监 workspace
    SOUL.md                              # "我是松鼠，囤货狂魔、嗅觉灵敏..."
    MEMORY.md                            # 素材库存、采集经验

  workspace-mcn-bee/                     # 蜜蜂 🐝 内容生产 workspace
    SOUL.md                              # "我是蜜蜂，勤劳高产、工艺讲究..."
    MEMORY.md                            # 工作流使用经验

  workspace-mcn-ant/                     # 蚂蚁 🐜 运营专家 workspace
    SOUL.md                              # "我是蚂蚁，耐心细致、数据敏感..."
    MEMORY.md                            # 数据分析经验

  skills/                                # 全局共享 skills
    xhs-media-crawler/
    face-image-generator/
    face-redaction/
    xhs-face-collector/
    xhs-nail-collector/
    image-upload/
    xhs-topic-researcher/
    ...

  agents/
    main/agent/                          # 爪爪 🦊 agentDir
    mcn-eagle/agent/                     # 鹰眼 🦅 agentDir
    mcn-squirrel/agent/                  # 松鼠 🐿️ agentDir
    mcn-bee/agent/                       # 蜜蜂 🐝 agentDir
    mcn-ant/agent/                       # 蚂蚁 🐜 agentDir
```

## openclaw.json 配置草案

```json5
{
  agents: {
    list: [
      {
        id: "main",
        default: true,
        name: "爪爪 COO",
        workspace: "~/.openclaw/workspace",
      },
      {
        id: "mcn-eagle",
        name: "鹰眼 - 策划总监",
        workspace: "~/.openclaw/workspace-mcn-eagle",
      },
      {
        id: "mcn-squirrel",
        name: "松鼠 - 素材总监",
        workspace: "~/.openclaw/workspace-mcn-squirrel",
      },
      {
        id: "mcn-bee",
        name: "蜜蜂 - 内容生产",
        workspace: "~/.openclaw/workspace-mcn-bee",
      },
      {
        id: "mcn-ant",
        name: "蚂蚁 - 运营专家",
        workspace: "~/.openclaw/workspace-mcn-ant",
      },
    ],
  },

  // 所有用户消息路由到爪爪（唯一入口）
  bindings: [
    { agentId: "main", match: { channel: "daxiang" } },
  ],

  // Agent 间通信：爪爪可以派活给所有子 Agent
  tools: {
    agentToAgent: {
      enabled: true,
      allow: ["main", "mcn-eagle", "mcn-squirrel", "mcn-bee", "mcn-ant"],
    },
  },
}
```

## 通信机制

爪爪通过 sessions_spawn / sessions_send 与子 Agent 通信：

1. 爪爪 -> 鹰眼：sessions_spawn(agentId="mcn-eagle", task="新活动：美发美甲半价，匹配账号出排期")
2. 鹰眼完成后 -> 结果自动返回爪爪
3. 爪爪 -> 松鼠：sessions_spawn(agentId="mcn-squirrel", task="补充美甲素材20张")
4. 爪爪 -> 蜜蜂：sessions_spawn(agentId="mcn-bee", task="按排期生产5篇内容")

关键：所有子 Agent 都通过爪爪调度，不直接互相通信。

## 账号数据库设计

**决策：平铺 + tag 筛选（已确认）**

账号库合并人设库，每个账号包含完整的人设信息。平铺存放，通过 tags 灵活筛选。

shared/accounts/ 结构：
```
shared/accounts/
  _index.json              # 总索引（鹰眼查询用）
  小Lin晓晓/
    profile.json           # 账号 + 人设合并信息
    avatar/                # 头像/参考图
    content-library/       # 该账号专属素材
      face-images/
        pending/
        approved/
  上海生活圈/
    profile.json
    ...
```

```json
// shared/accounts/小Lin晓晓/profile.json
{
  "id": "xiaolinxiaoxiao",
  "name": "小Lin晓晓",
  "displayName": "小Lin",
  "businessTypes": ["颜值"],
  "categories": ["韩系", "甜美", "日常穿搭"],
  "cities": [],
  "tags": ["颜值", "韩系", "甜美", "日常穿搭"],
  "persona": {
    "style": "韩系甜美风",
    "portraitRef": "avatar/portrait.png",
    "tone": "甜美、亲和"
  },
  "device": { "binding": "phone-01", "status": "active" },
  "stats": { "followers": 1200, "totalPosts": 45, "avgLikes": 320 },
  "status": "active"
}

// shared/accounts/上海生活圈/profile.json
{
  "id": "shanghai-life",
  "name": "上海生活圈",
  "displayName": "上海生活圈",
  "businessTypes": ["清单"],
  "categories": ["洗浴", "按摩", "SPA"],
  "cities": ["上海"],
  "tags": ["清单", "上海", "洗浴", "按摩", "生活服务"],
  "persona": null,
  "device": { "binding": "phone-03", "status": "active" },
  "stats": { "followers": 800, "totalPosts": 20, "avgLikes": 150 },
  "status": "active"
}
```

鹰眼查询示例：
- "美发美甲活动" -> tags 含 美甲 OR 美发 的账号
- "上海探店" -> cities 含 上海 的账号
- "颜值韩系内容" -> tags 含 颜值 AND 韩系 的账号

## 事件驱动机制

shared/state/events/ 目录存放事件文件：

```json
// shared/state/events/evt-20260304-001.json
{
  "id": "evt-20260304-001",
  "type": "material_collected",
  "source": "mcn-material",
  "timestamp": "2026-03-04T15:00:00Z",
  "payload": {
    "taskId": "task-xxx",
    "materialCount": 25,
    "materialType": "nail"
  },
  "consumed": false
}
```

Cron 或爪爪定期扫描 events/，分发给下一个 Agent。

## 实施计划

### Phase 1: 基础搭建（本周）
1. 创建各 Agent 的 workspace 目录和 SOUL.md
2. 配置 openclaw.json 多 Agent
3. 创建 shared/accounts/ 账号数据库
4. 验证 Agent 间通信（sessions_spawn）

### Phase 2: 策划 + 素材（下周）
1. 策划总监：实现账号匹配逻辑
2. 素材总监：迁移现有采集 Skill 到共享 skills
3. 测试活动流程

### Phase 3: 内容 + 运营（第三周）
1. 内容生产：对接工作流
2. 运营专家：数据监控 + 评论维护
3. 端到端测试

### Phase 4: 优化（持续）
1. 事件驱动替代轮询
2. DevOps Agent 加入
3. Web 审核界面（可选）
