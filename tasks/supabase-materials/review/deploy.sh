#!/bin/bash
# 自动注入版本号并部署
# 用法：bash deploy.sh

set -e
cd "$(dirname "$0")"

TS=$(date +%Y%m%d%H%M)

echo "🔨 注入版本号 v=$TS ..."

# 要处理的 HTML 文件列表
HTML_FILES=(
  index.html
  materials-pool.html
  draft-review.html
  image-select.html
  requirement.html
  requirement-detail.html
  dashboard.html
  gen-stats.html
  command-log.html
)

# 备份并替换版本号（匹配 ?v=数字 或无版本号的 .js/.css 引用）
for f in "${HTML_FILES[@]}"; do
  [ -f "$f" ] || continue
  # 替换已有版本号
  sed -i "s/\?v=[0-9]\{8,\}/\?v=${TS}/g" "$f"
  # 给没有版本号的本地 .js/.css 引用加上版本号
  sed -i "s/\(src=\"\)\([a-zA-Z0-9._-]*\.js\)\"/\1\2?v=${TS}\"/g" "$f"
  sed -i "s/\(href=\"\)\([a-zA-Z0-9._-]*\.css\)\"/\1\2?v=${TS}\"/g" "$f"
done

echo "🚀 部署到 prod ..."
webstatic deploy \
  --appkey=com.sankuai.dzfe3.opxaimanage \
  --artifact=. \
  --env=prod \
  --token=b70bdb0e-606d-46d3-9900-1a857f9cf1a2

echo "✅ 部署完成，版本号：v=${TS}"
