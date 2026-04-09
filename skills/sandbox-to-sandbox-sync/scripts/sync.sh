#!/usr/bin/env bash
# sandbox-to-sandbox-sync/scripts/sync.sh
#
# 从 openclaw-old.git 拉取完整 .openclaw 快照，同步覆盖到当前沙箱。
# 仓库结构与 /mnt/openclaw/.openclaw/ 完全一致：
#   workspace/ workspace-mcn-*/ skills/ cron/ (+ openclaw.json)
#
# 用法：
#   bash sync.sh            # 正式执行
#   DRY_RUN=1 bash sync.sh  # 预览模式，不实际写入

set -euo pipefail

REPO_URL="ssh://git@git.sankuai.com/~lipengyu04/openclaw-old.git"
TARGET_DIR="/mnt/openclaw/.openclaw"
TMP_DIR="/tmp/sandbox-sync-$(date +%s)"
BACKUP_DIR="/tmp/openclaw-backup-$(date +%Y%m%d-%H%M%S)"
DRY_RUN="${DRY_RUN:-0}"

echo "===== sandbox-to-sandbox-sync ====="
echo "仓库 : $REPO_URL"
echo "目标 : $TARGET_DIR"
echo "临时 : $TMP_DIR"
[ "$DRY_RUN" = "1" ] && echo "⚠️  DRY RUN 模式，不会实际写入"
echo ""

# ────────────────────────────────────────────
# 1. 检查 SSH
# ────────────────────────────────────────────
echo "[1/5] 检查 SSH..."
if ! ssh -T git@git.sankuai.com -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o BatchMode=yes 2>&1 | grep -q ""; then
  :  # ssh -T 返回非 0 是正常的，只要能连上就行
fi
# 用 git ls-remote 验证真正可达
if ! git ls-remote "$REPO_URL" HEAD &>/dev/null; then
  echo "❌ 无法访问仓库，请先配置 SSH 密钥"
  echo "   1. ssh-keygen -t ed25519 -C 'openclaw-sandbox' -f ~/.ssh/id_ed25519 -N ''"
  echo "   2. cat ~/.ssh/id_ed25519.pub  → 添加到 https://dev.sankuai.com/code/home"
  exit 1
fi
echo "  ✅ SSH 可达"
echo ""

# ────────────────────────────────────────────
# 2. clone
# ────────────────────────────────────────────
echo "[2/5] 克隆仓库..."
git clone --depth=1 "$REPO_URL" "$TMP_DIR" 2>&1
echo "  ✅ 克隆完成"
echo ""

# ────────────────────────────────────────────
# 3. 备份
# ────────────────────────────────────────────
echo "[3/5] 备份当前 .openclaw..."
if [ "$DRY_RUN" = "0" ]; then
  cp -r "$TARGET_DIR" "$BACKUP_DIR"
  echo "  ✅ 备份完成: $BACKUP_DIR"
else
  echo "  [dry-run] 跳过备份"
fi
echo ""

# ────────────────────────────────────────────
# 4. 同步目录（直接覆盖）
# ────────────────────────────────────────────
echo "[4/5] 同步目录..."
SYNC_DIRS=(
  "workspace"
  "workspace-mcn-ant"
  "workspace-mcn-bee"
  "workspace-mcn-eagle"
  "workspace-mcn-owl"
  "workspace-mcn-squirrel"
  "skills"
  "cron"
)

for dir in "${SYNC_DIRS[@]}"; do
  src="$TMP_DIR/$dir"
  dst="$TARGET_DIR/$dir"
  if [ -d "$src" ]; then
    if [ "$DRY_RUN" = "0" ]; then
      rm -rf "$dst"
      cp -r "$src" "$dst"
      echo "  ✅ $dir"
    else
      echo "  [dry-run] 会覆盖: $dir"
    fi
  else
    echo "  ⏭️  仓库中不存在，跳过: $dir"
  fi
done
echo ""

# ────────────────────────────────────────────
# 5. 处理 openclaw.json（融合危险字段）
# ────────────────────────────────────────────
echo "[5/5] 处理 openclaw.json..."
REPO_JSON="$TMP_DIR/openclaw.json"
CURRENT_JSON="$TARGET_DIR/openclaw.json"
MERGED_JSON="/tmp/openclaw-merged-$(date +%s).json"

if [ ! -f "$REPO_JSON" ]; then
  echo "  ⏭️  仓库中无 openclaw.json，跳过"
elif [ ! -f "$CURRENT_JSON" ]; then
  echo "  ⚠️  目标沙箱无 openclaw.json，直接使用仓库版本"
  [ "$DRY_RUN" = "0" ] && cp "$REPO_JSON" "$CURRENT_JSON"
else
  REPO_JSON="$REPO_JSON" \
  CURRENT_JSON="$CURRENT_JSON" \
  MERGED_JSON="$MERGED_JSON" \
  python3 - <<'PYEOF'
import json, os, sys

repo_path    = os.environ["REPO_JSON"]
current_path = os.environ["CURRENT_JSON"]
merged_path  = os.environ["MERGED_JSON"]

with open(repo_path)    as f: repo    = json.load(f)
with open(current_path) as f: current = json.load(f)

def deep_get(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d: d = d[k]
        else: return None
    return d

def deep_set(d, value, *keys):
    for k in keys[:-1]: d = d.setdefault(k, {})
    if value is not None: d[keys[-1]] = value

merged    = json.loads(json.dumps(repo))   # deep copy
preserved = []

# 顶级危险字段：直接保留 current 的值
for path in [("gateway","port"), ("gateway","auth"), ("gateway","controlUi")]:
    val = deep_get(current, *path)
    if val is not None:
        deep_set(merged, val, *path)
        preserved.append(".".join(path))

# models：保留每个 model 的鉴权字段
for model_name, model_cfg in current.get("models", {}).items():
    if not isinstance(model_cfg, dict): continue
    if model_name not in merged.get("models", {}): continue
    for key in ("apiKey", "baseUrl", "apiBase", "secret", "token"):
        if key in model_cfg:
            merged["models"][model_name][key] = model_cfg[key]
            preserved.append(f"models.{model_name}.{key}")

# channels：保留 token/secret
for ch, ch_cfg in current.get("channels", {}).items():
    if not isinstance(ch_cfg, dict): continue
    if ch not in merged.get("channels", {}): continue
    for key in ("token", "secret", "botToken", "apiKey"):
        if key in ch_cfg:
            deep_set(merged, ch_cfg[key], "channels", ch, key)
            preserved.append(f"channels.{ch}.{key}")

# agents：删除 sessionKey（防 cron isolated session 变"不适用"）
for entry in (merged.get("agents", []) if isinstance(merged.get("agents"), list) else []):
    if isinstance(entry, dict) and "sessionKey" in entry:
        del entry["sessionKey"]

with open(merged_path, "w") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print("  融合完成，以下字段保留了当前沙箱的值：")
for field in preserved:
    print(f"    🔒 {field}")
print(f"  融合结果: {merged_path}")
PYEOF

  if [ $? -eq 0 ] && [ -f "$MERGED_JSON" ]; then
    if [ "$DRY_RUN" = "0" ]; then
      cp "$MERGED_JSON" "$CURRENT_JSON"
      echo "  ✅ openclaw.json 已写入（融合版）"
    else
      echo "  [dry-run] 融合结果在 $MERGED_JSON，未写入"
    fi
  else
    echo "  ❌ openclaw.json 融合失败，请手动处理"
    echo "     仓库版本: $REPO_JSON"
    echo "     当前版本: $CURRENT_JSON"
  fi
fi

# ────────────────────────────────────────────
# 完成
# ────────────────────────────────────────────
echo ""
echo "===== 同步完成 ====="
[ "$DRY_RUN" = "0" ] && echo "📁 备份目录: $BACKUP_DIR" || echo "📁 备份目录: （dry-run 未备份）"
echo ""
echo "⚡ 下一步：openclaw gateway restart"
echo ""
echo "🧹 清理临时目录: rm -rf $TMP_DIR"
