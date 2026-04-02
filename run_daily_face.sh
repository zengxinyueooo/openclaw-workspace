#!/bin/bash
WORKSPACE="/Users/lipengyu/.openclaw/workspace"
LOG_FILE="$WORKSPACE/shared/logs/cron/face_$(date +%Y%m%d).log"
AUDIT_FILE="$WORKSPACE/shared/logs/audit_$(date +%Y%m%d).log"

mkdir -p "$WORKSPACE/shared/logs/cron"

# 审计日志函数
audit_log() {
    echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"component\":\"system-cron\",\"event_type\":\"$1\",\"message\":\"$2\",\"data\":{}}" >> "$AUDIT_FILE"
}

# 记录Cron触发
audit_log "CRON_TRIGGERED" "颜值采集Cron触发"
echo "[$(date)] 颜值采集任务开始" >> "$LOG_FILE"

# 执行采集
cd "$WORKSPACE/skills/xhs-face-collector"
export PATH="/tmp:/Users/lipengyu/Library/Python/3.9/bin:$PATH"
./collect.sh >> "$LOG_FILE" 2>&1

# 记录完成
audit_log "CRON_COMPLETED" "颜值采集任务完成"
echo "[$(date)] 颜值采集任务完成" >> "$LOG_FILE"
