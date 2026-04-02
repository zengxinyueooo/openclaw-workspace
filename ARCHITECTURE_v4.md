# 小红书矩阵系统 v4.0 - Orchestrator 独立 Workspace

> 架构变更: ADR-001 (2026-03-05)

## 架构总览

```
用户(皮皮)
    │
    ├───▶ 爪爪 🦊 (~/openclaw-workspace/)
    │       - 用户交互入口
    │       - 读取Orchestrator状态
    │       - 向队列添加任务
    │
    └───▶ Orchestrator 🎛️ (~/openclaw-orchestrator/)
            - Cron定时唤醒
            - 任务调度中心
            - 管理所有Workers
```

## 组件职责

| 组件 | 位置 | 触发方式 | 职责 |
|------|------|----------|------|
| 爪爪 | ~/openclaw-workspace/ | 用户消息 | 交互入口、状态查询 |
| Orchestrator | ~/openclaw-orchestrator/ | Cron(每5分钟) | 任务调度、Worker管理 |
| Workers | ~/.openclaw/workspace/agents/ | Orchestrator调用 | 具体任务执行 |

## 通信机制

### 状态文件共享

Orchestrator写入:
- `~/openclaw-orchestrator/state/queue.json`
- `~/openclaw-orchestrator/state/system-status.json`

爪爪读取:
```bash
cat ~/openclaw-orchestrator/state/system-status.json
```

## 实施状态

- [x] Phase 1: 创建基础设施 (完成)
- [ ] Phase 2: 实现核心调度
- [ ] Phase 3: 集成爪爪读取状态

## 相关文档

- ADR-001: ~/openclaw-workspace/ADR/ADR-001-orchestrator-workspace.md
