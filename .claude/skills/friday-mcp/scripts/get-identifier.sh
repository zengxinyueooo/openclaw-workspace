#!/bin/bash
# 获取 IDENTIFIER：优先从环境变量读取，否则从 sandbox.json 文件中提取
if [ -n "$IDENTIFIER" ]; then
  echo "$IDENTIFIER"
else
  CONFIG="/root/.openclaw/config/sandbox.json"
  if [ ! -f "$CONFIG" ]; then
    echo "ERROR: 环境变量 IDENTIFIER 未设置，且文件 $CONFIG 不存在" >&2
    exit 1
  fi
  VALUE=$(jq -r '.identifier' "$CONFIG" 2>/dev/null)
  if [ -z "$VALUE" ] || [ "$VALUE" = "null" ]; then
    echo "ERROR: 无法从 $CONFIG 中读取 identifier" >&2
    exit 1
  fi
  echo "$VALUE"
fi
