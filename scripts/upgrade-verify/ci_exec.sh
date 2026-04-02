#!/bin/bash
# deploy_and_report.sh
# 运行部署脚本，输出日志到控制台，并生成 JUnit XML 测试结果文件

# ---- 记录原始目录（CI 期望报告文件在这里）----
ORIGINAL_DIR="$PWD"
REPORT_FILE="test_results.xml"

# ---- 确保工作目录名为 upgrade-verify ----
CURRENT_DIR=$(basename "$PWD")
TARGET_DIR="upgrade-verify"
RENAMED=false

if [ "$CURRENT_DIR" != "$TARGET_DIR" ]; then
    echo "当前目录为 $CURRENT_DIR，需要重命名为 $TARGET_DIR"
    cd ..
    mv "$CURRENT_DIR" "$TARGET_DIR"
    cd "$TARGET_DIR"
    RENAMED=true
    echo "已切换到目录: $PWD"
fi

TIMESTAMP=$(date '+%Y-%m-%dT%H:%M:%S')
START_TOTAL=$(date +%s%N)

declare -A CASE_STATUS
declare -A CASE_TIME
declare -A CASE_STDOUT

# ---- 自动修复 Python 脚本编码声明 ----
fix_python_encoding() {
local SCRIPT="$1"
if [ ! -f "$SCRIPT" ]; then
return
fi
# 检查文件前两行是否已包含 coding 声明
if head -2 "$SCRIPT" | grep -q "coding"; then
return
fi
# 没有 coding 声明，需要插入
local FIRST_LINE=$(head -1 "$SCRIPT")
if [[ "$FIRST_LINE" == "#!"* ]]; then
# 有 shebang，插到第二行
sed -i '1a # -*- coding: utf-8 -*-' "$SCRIPT"
else
# 没有 shebang，插到第一行
sed -i '1i # -*- coding: utf-8 -*-' "$SCRIPT"
fi
echo " [fix] 已为 $SCRIPT 添加 UTF-8 编码声明"
}

run_case() {
local CASE_NAME="$1"
local SCRIPT="$2"

echo ""
echo "=============================="
echo "▶ 开始：$CASE_NAME"
echo "=============================="

# 自动修复编码
fix_python_encoding "$SCRIPT"

local START=$(date +%s%N)

local TMPFILE=$(mktemp)
python3 "$SCRIPT" 2>&1 | tee "$TMPFILE"
local EXIT_CODE=${PIPESTATUS[0]}
local OUTPUT=$(cat "$TMPFILE")
rm -f "$TMPFILE"

local END=$(date +%s%N)
local ELAPSED=$(echo "scale=3; ($END - $START) / 1000000000" | bc)

CASE_STATUS["$CASE_NAME"]=$EXIT_CODE
CASE_TIME["$CASE_NAME"]=$ELAPSED
CASE_STDOUT["$CASE_NAME"]="$OUTPUT"

if [ $EXIT_CODE -eq 0 ]; then
echo "✅ $CASE_NAME 成功（耗时 ${ELAPSED}s）"
else
echo "❌ $CASE_NAME 失败（exit code: $EXIT_CODE，耗时 ${ELAPSED}s）"
fi
}

# ---- 执行两个 case ----

run_case "更新执行脚本" "scripts/upload_pre_upgrade.py"
run_case "更新工程包" "scripts/pack_and_upload.py"

# ---- 统计 ----

END_TOTAL=$(date +%s%N)
TOTAL_TIME=$(echo "scale=3; ($END_TOTAL - $START_TOTAL) / 1000000000" | bc)

FAILURES=0
for CASE_NAME in "更新执行脚本" "更新工程包"; do
[ "${CASE_STATUS[$CASE_NAME]}" != "0" ] && FAILURES=$((FAILURES + 1))
done

# ---- 生成 XML ----

echo ""
echo "=============================="
echo "📄 生成测试报告：$REPORT_FILE"
echo "=============================="

escape_xml() {
printf '%s' "$1" | sed \
's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&apos;/g'
}

cat > "$REPORT_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="DeployReport" tests="2" failures="$FAILURES" time="$TOTAL_TIME" timestamp="$TIMESTAMP">
<testsuite name="部署流程" tests="2" failures="$FAILURES" time="$TOTAL_TIME">
EOF

for CASE_NAME in "更新执行脚本" "更新工程包"; do
EXIT_CODE="${CASE_STATUS[$CASE_NAME]}"
ELAPSED="${CASE_TIME[$CASE_NAME]}"
OUTPUT=$(escape_xml "${CASE_STDOUT[$CASE_NAME]}")

UPLOADED_URL=$(echo "${CASE_STDOUT[$CASE_NAME]}" | grep -oE '(uploaded_url|url|地址)[：: ]+\S+' | head -1)
UPLOADED_URL=$(escape_xml "$UPLOADED_URL")

cat >> "$REPORT_FILE" <<EOF
<testcase name="$(escape_xml "$CASE_NAME")" classname="deploy" time="$ELAPSED">
<properties>
<property name="upload_result" value="$UPLOADED_URL"/>
</properties>
<system-out>$OUTPUT</system-out>
EOF

if [ "$EXIT_CODE" != "0" ]; then
FAILURE_MSG=$(escape_xml "${CASE_STDOUT[$CASE_NAME]}")
cat >> "$REPORT_FILE" <<EOF
<failure message="exit code $EXIT_CODE">$FAILURE_MSG</failure>
EOF
fi

cat >> "$REPORT_FILE" <<EOF
</testcase>
EOF
done

cat >> "$REPORT_FILE" <<EOF
</testsuite>
</testsuites>
EOF

echo "✅ 报告已生成：$REPORT_FILE"
sudo chmod 777 $REPORT_FILE

# ---- 复制报告文件到当前目录（确保 CI 能找到）----
# if [ "$REPORT_FILE" != "$PWD/test_results.xml" ]; then
#     cp "$REPORT_FILE" "$PWD/test_results.xml"
#     echo "📋 报告已复制到：$PWD/test_results.xml"
# fi


echo ""
echo "=============================="
echo "📊 汇总：共 2 个 case，失败 $FAILURES 个，总耗时 ${TOTAL_TIME}s"
echo "=============================="

if [ "$RENAMED" = "true" ]; then
cd ..
mv "$TARGET_DIR" "$CURRENT_DIR"
echo "已还原目录名: $CURRENT_DIR"
fi

[ $FAILURES -eq 0 ] && exit 0 || exit 1