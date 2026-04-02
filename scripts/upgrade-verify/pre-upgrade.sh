#!/usr/bin/env bash
# ============================================================
# 镜像升级前采集脚本
# 用法：curl -fsSL <S3_URL> | bash
#
# 功能：
#   1. 下载 upgrade-verify 工程到 ~/.openclaw/workspace/scripts/
#   2. 安装依赖（requests, websocket-client, cryptography）
#   3. 执行升级前采集 snapshot.py
#   4. 打印 snapshot.json 路径，供升级后 pytest 使用
# ============================================================

set -euo pipefail

TARBALL_URL="https://s3plus-bj02.vip.sankuai.com/openclaw/9527testimageupgrade.tar.gz"
INSTALL_DIR="${HOME}/.openclaw/workspace/scripts"
VERIFY_DIR="${INSTALL_DIR}/upgrade-verify"


echo "=========================================="
echo "  镜像升级前采集"
echo "=========================================="
echo ""

# ── 1. 下载并解压 ─────────────────────────────
echo "[1/3] 下载并解压 upgrade-verify 工程..."
mkdir -p "${INSTALL_DIR}"
curl -fsSL --noproxy "*" "${TARBALL_URL}" | tar -xz -C "${INSTALL_DIR}"
echo "      解压到：${VERIFY_DIR}"

# ── 2. 安装 Python 依赖 ───────────────────────
echo "[2/3] 检查并安装 Python 依赖..."
python3 -m pip install --quiet --break-system-packages \
    requests websocket-client cryptography pytest pytest-html 2>/dev/null || \
python3 -m pip install --quiet \
    requests websocket-client cryptography pytest pytest-html
echo "      依赖就绪"

# ── 3. 执行升级前采集 ─────────────────────────
echo "[3/3] 执行升级前采集..."
echo ""
cd "${VERIFY_DIR}"
python3 snapshot.py

echo ""
echo "=========================================="
echo "  采集完成！"
echo "  snapshot.json 路径："
echo "  ${VERIFY_DIR}/snapshot.json"
echo ""
echo "  升级完成后，在沙箱内执行以下命令进行验收："
echo "  cd ${VERIFY_DIR} && python3 -m pytest"
echo "=========================================="
