#!/bin/bash
# 从 MOA 日志中提取当前登录用户的 misId
# 前置条件：MOA 已登录（未登录时 misId 为空）

LOG_DIR="/home/.local/share/MOA/logs"

if [ ! -d "$LOG_DIR" ]; then
  echo "ERROR: MOA 日志目录不存在: $LOG_DIR" >&2
  exit 1
fi

# 从所有日志文件中找最近的非空 misId
MIS_ID=$(grep -h -o '"misId":"[^"]*"' "$LOG_DIR"/moatray-*.txt 2>/dev/null | grep -v '""' | tail -1 | sed 's/"misId":"//;s/"//')

if [ -z "$MIS_ID" ]; then
  echo "ERROR: 未找到 misId，请确认 MOA 已登录" >&2
  exit 1
fi

echo "$MIS_ID"
