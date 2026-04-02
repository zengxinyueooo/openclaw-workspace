# 系统级 Cron 配置

## 配置命令

```bash
# 编辑 crontab
crontab -e

# 添加以下内容：
0 10 * * * /Users/lipengyu/.openclaw/workspace/run_daily_face.sh
0 14 * * * /Users/lipengyu/.openclaw/workspace/run_daily_nail.sh
```

## 日志位置

- Cron日志: `shared/logs/cron/`
- 审计日志: `shared/logs/audit_YYYYMMDD.log`
- 执行日志: `shared/logs/cron/face_YYYYMMDD.log`

## 审计事件

- CRON_TRIGGERED: Cron触发
- SUBAGENT_CREATED: 创建Subagent
- TASK_DELEGATED: 任务委派
- AGENT_SCHEDULED: Agent调度
- CRON_COMPLETED: 任务完成
