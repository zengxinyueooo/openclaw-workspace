# Heartbeat 检查清单

Heartbeat 每半小时执行一次，通过 `sessions_list` 检查子 agent 会话的异常状态。

> ⚠️ agent_runs 表已停用（2026-03-30），调度追踪全面迁移到 OpenClaw 原生 sessions 管理。

## 巡检规则

| 规则 | 条件 | 判定 | 动作 |
|------|------|------|------|
| 1 | spawned > 5min | 派发可能失败 | 记录，人工介入 |
| 2 | running > 60min | 执行过长 | 记录，人工介入 |
| 3 | sessions_list 异常 | 无法获取状态 | 告警 |

## 执行方式

通过 `sessions_list` API 主动查询，不再依赖数据库表。

## Git 自动提交

如果距离上次 commit > 4 小时，自动 commit workspace 变更。

```bash
cd /Users/lipengyu/.openclaw/workspace && git diff --quiet || git add -A && git commit -m "heartbeat auto-commit"
```
