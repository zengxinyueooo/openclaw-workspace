# 架构决策记录 (ADR)

## ADR-001: Orchestrator 独立 Workspace 方案

**日期**: 2026-03-05  
**决策人**: 皮皮  
**状态**: ✅ 已批准，实施中

---

## 背景

### 问题
1. **爪爪不能当主管**: Session 是被动唤醒的，而调度需要主动触发
2. **Orchestrator 在规划中**: 因为 daxiang 不支持 thread 绑定，无法实现长期 Agent
3. **Cron 直接触发 Worker**: 没有集中调度，状态分散

### 考虑过的方案

| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| 爪爪当主管 | 简单 | Session 被动唤醒，无法主动调度 | ❌ 放弃 |
| 迁移到 Telegram | 原生支持 thread | 需要新账号，迁移成本 | ⏸️ 暂缓 |
| **独立 Orchestrator Workspace** | 职责清晰、状态持久、独立运行 | 需要跨 workspace 通信 | ✅ **采用** |

---

## 决策

**采用独立 Orchestrator Workspace 方案**

### 架构

```
Gateway守护进程
    │
    ├── Cron ──▶ ~/openclaw-orchestrator/scheduler.py (每5分钟)
    │                │
    │                ├── 检查任务队列
    │                ├── 调度 Worker
    │                ├── 更新状态文件
    │                └── 退出（等待下次唤醒）
    │
    └── 用户消息 ──▶ ~/openclaw-workspace/爪爪
                         │
                         └── 读取 orchestrator 状态文件
                             └── 回复用户
```

### 职责划分

| 组件 | 职责 | 触发方式 |
|------|------|----------|
| **爪爪** (~/openclaw-workspace/) | 用户交互入口、开发调试、查询状态 | 用户消息触发 |
| **Orchestrator** (~/openclaw-orchestrator/) | 任务调度、Worker管理、状态维护 | Cron定时唤醒 |
| **Workers** | 具体任务执行 | 被 Orchestrator 触发 |

### 通信机制

**状态文件共享**:
```
~/openclaw-orchestrator/state/
├── queue.json              # 任务队列
├── workers-status.json     # Worker状态
├── system-status.json      # 系统健康
└── history.log            # 执行日志

爪爪读取: ~/openclaw-orchestrator/state/*.json
```

---

## 实施计划

### Phase 1: 基础设施 (今天)
- [ ] 创建 ~/openclaw-orchestrator/ workspace
- [ ] 配置 Cron 定时任务
- [ ] 设计状态文件格式

### Phase 2: 核心调度 (本周)
- [ ] 实现 scheduler.py
- [ ] 迁移现有的 Worker 调用逻辑
- [ ] 测试跨 workspace 通信

### Phase 3: 集成 (下周)
- [ ] 更新爪爪，读取 Orchestrator 状态
- [ ] 完善错误处理和故障恢复
- [ ] 编写文档

---

## 影响

### 正面影响
- ✅ 统一调度入口
- ✅ 状态集中管理
- ✅ 故障可恢复
- ✅ 职责清晰分离

### 负面影响
- ⚠️ 增加系统复杂度
- ⚠️ 需要维护两个 workspace
- ⚠️ 跨 workspace 通信开销

### 风险
- **风险**: Orchestrator 挂了怎么办？
- **缓解**: 爪爪可以读取状态文件，必要时人工介入

---

## 相关决策

- ADR-002: Worker 状态文件格式 (待创建)
- ADR-003: 故障恢复机制 (待创建)

---

**决策记录者**: 爪爪 🦊  
**日期**: 2026-03-05