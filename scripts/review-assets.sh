#!/bin/bash
# 素材审核工具 - 快速审核 pending 素材
# 用法: ./review-assets.sh [类型] [日期]
# 示例: ./review-assets.sh face 2026-03-04

TYPE=${1:-face}
DATE=${2:-$(date +%Y-%m-%d)}
BASE="/Users/lipengyu/.openclaw/workspace/shared/content-assets"
PENDING="$BASE/$TYPE/pending/$DATE"
APPROVED="$BASE/$TYPE/approved/by-date/$(date +%Y-%m)"

if [ ! -d "$PENDING" ]; then
  echo "没有找到 pending 素材: $PENDING"
  echo "可用的 pending 目录:"
  ls -d "$BASE/$TYPE/pending/"*/ 2>/dev/null
  exit 1
fi

COUNT=$(find "$PENDING" -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
echo "📦 待审核: $TYPE / $DATE ($COUNT 张)"
echo ""

# 在 Finder 中打开 pending 目录
echo "打开 pending 目录..."
open "$PENDING"

echo ""
echo "审核操作:"
echo "  [a] 全部通过 → 移到 approved"
echo "  [o] 打开 approved 目录（手动挑选）"
echo "  [s] 跳过"
echo ""
read -p "选择: " choice

case $choice in
  a)
    mkdir -p "$APPROVED"
    cp "$PENDING"/*.jpg "$APPROVED/" 2>/dev/null
    cp "$PENDING"/*.png "$APPROVED/" 2>/dev/null
    MOVED=$(find "$APPROVED" -newer "$PENDING" -name "*.jpg" -o -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
    echo "✅ 已复制 $COUNT 张到 approved"
    ;;
  o)
    mkdir -p "$APPROVED"
    open "$APPROVED"
    echo "已打开 approved 目录，请手动拖入想要的图片"
    ;;
  s)
    echo "跳过"
    ;;
esac
