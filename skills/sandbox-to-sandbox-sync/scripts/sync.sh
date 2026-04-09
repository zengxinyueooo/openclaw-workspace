#!/usr/bin/env bash
# sandbox-to-sandbox-sync/scripts/sync.sh
# 从 openclaw-old.git 拉取最新代码，同步覆盖到当前沙箱 /mnt/openclaw/.openclaw/
# openclaw.json 单独融合处理，其余目录全部直接覆盖。

set -euo pipefail

REPO_URL="ssh://git@git.sankuai.com/~lipengyu04/openclaw-old.git"
TARGET_DIR="/mnt/openclaw/.openclaw"
TMP_DIR="/tmp/sandbox-sync-$(date +%s)"
BACKUP_DIR="/tmp/openclaw-backup-$(date +%Y%m%d-%H%M%S)"
DRY_RUN="${DRY_RUN:-0}"

echo "===== sandbox-to-sandbox-sync ====="
echo "仓库: $REPO_URL"
echo "目标: $TARGET_DIR"
echo "临时: $TMP_DIR"
[ "$DRY_RUN" = "1" ] && echo "⚠️  DRY RUN 模式，不会实际写入"
echo ""

# ---- 1. clone ----
echo "[1/5] 克隆仓库..."
git clone --depth=1 "$REPO_URL" "$TMP_DIR" 2>&1
echo "克隆完成"
echo ""

# ---- 2. 备份 ----
echo "[2/5] 备份当前 .openclaw..."
if [ "$DRY_RUN" = "0" ]; then
    cp -r "$TARGET_DIR" "$BACKUP_DIR"
    echo "备份完成: $BACKUP_DIR"
else
    echo "[dry-run] 跳过备份"
fi
echo ""

# ---- 3. 同步各 workspace 和 skills ----
SYNC_DIRS=(
    "workspace"
    "workspace-mcn-ant"
    "workspace-mcn-bee"
    "workspace-mcn-eagle"
    "workspace-mcn-owl"
    "workspace-mcn-squirrel"
    "skills"
)

echo "[3/5] 同步目录..."
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
        echo "  ⏭️  跳过（仓库中不存在）: $dir"
    fi
done
echo ""

# ---- 4. 同步 cron/jobs.json ----
echo "[4/5] 同步 cron/jobs.json..."
CRON_SRC="$TMP_DIR/cron/jobs.json"
CRON_DST="$TARGET_DIR/cron/jobs.json"
if [ -f "$CRON_SRC" ]; then
    if [ "$DRY_RUN" = "0" ]; then
        mkdir -p "$TARGET_DIR/cron"
        cp "$CRON_SRC" "$CRON_DST"
        echo "  ✅ cron/jobs.json"
    else
        echo "  [dry-run] 会覆盖 cron/jobs.json"
    fi
else
    echo "  ⏭️  跳过（仓库中无 cron/jobs.json）"
fi
echo ""

# ---- 5. 处理 openclaw.json ----
echo "[5/5] 处理 openclaw.json..."
REPO_JSON="$TMP_DIR/openclaw.json"
CURRENT_JSON="$TARGET_DIR/openclaw.json"
MERGED_JSON="/tmp/openclaw-merged-$(date +%s).json"

if [ ! -f "$REPO_JSON" ]; then
    echo "  ⏭️  仓库中无 openclaw.json，跳过"
elif [ ! -f "$CURRENT_JSON" ]; then
    echo "  ⚠️  目标沙箱无 openclaw.json，直接使用仓库版本（请人工确认后再重启）"
    [ "$DRY_RUN" = "0" ] && cp "$REPO_JSON" "$CURRENT_JSON"
else
    # 用 python3 做字段融合
    python3 - <<'PYEOF'
import json, sys, os

repo_json_path = os.environ.get("REPO_JSON")
current_json_path = os.environ.get("CURRENT_JSON")
merged_json_path = os.environ.get("MERGED_JSON")

with open(repo_json_path) as f:
    repo = json.load(f)
with open(current_json_path) as f:
    current = json.load(f)

def deep_get(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return None
    return d

def deep_set(d, value, *keys):
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    if value is not None:
        d[keys[-1]] = value

# 危险字段：保留 current 的值覆盖 repo
PRESERVE_FIELDS = [
    ("gateway", "port"),
    ("gateway", "auth"),
    ("gateway", "controlUi"),
]

# models: 保留 current 的每个 model 的 apiKey / baseUrl
merged = json.loads(json.dumps(repo))  # deep copy repo

preserved = []
for path in PRESERVE_FIELDS:
    val = deep_get(current, *path)
    if val is not None:
        deep_set(merged, val, *path)
        preserved.append(".".join(path))

# models: 逐个 model 保留 current 的 apiKey/baseUrl/apiBase
if "models" in current and "models" in merged:
    current_models = current["models"] if isinstance(current["models"], dict) else {}
    merged_models = merged["models"] if isinstance(merged["models"], dict) else {}
    for model_name, model_cfg in current_models.items():
        if model_name in merged_models:
            for sensitive_key in ("apiKey", "baseUrl", "apiBase", "secret", "token"):
                if sensitive_key in model_cfg:
                    merged_models[model_name][sensitive_key] = model_cfg[sensitive_key]
                    preserved.append(f"models.{model_name}.{sensitive_key}")

# channels: 保留 current 的 token/secret
if "channels" in current and "channels" in merged:
    for ch_type in current.get("channels", {}):
        if ch_type in merged["channels"]:
            for sensitive_key in ("token", "secret", "botToken", "apiKey"):
                val = deep_get(current, "channels", ch_type, sensitive_key)
                if val is not None:
                    deep_set(merged, val, "channels", ch_type, sensitive_key)
                    preserved.append(f"channels.{ch_type}.{sensitive_key}")

# agents: 删除 sessionKey（避免 cron isolated session 变"不适用"）
if "agents" in merged:
    for agent_entry in (merged["agents"] if isinstance(merged["agents"], list) else []):
        if "sessionKey" in agent_entry:
            del agent_entry["sessionKey"]

with open(merged_json_path, "w") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print("  融合完成，保留了当前沙箱的字段：")
for f in preserved:
    print(f"    🔒 {f}")
print(f"  融合结果: {merged_json_path}")
PYEOF
    export REPO_JSON="$REPO_JSON" CURRENT_JSON="$CURRENT_JSON" MERGED_JSON="$MERGED_JSON"
    python3 - <<'PYEOF'
import json, sys, os

repo_json_path = os.environ["REPO_JSON"]
current_json_path = os.environ["CURRENT_JSON"]
merged_json_path = os.environ["MERGED_JSON"]

with open(repo_json_path) as f:
    repo = json.load(f)
with open(current_json_path) as f:
    current = json.load(f)

def deep_get(d, *keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return None
    return d

def deep_set(d, value, *keys):
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    if value is not None:
        d[keys[-1]] = value

PRESERVE_FIELDS = [
    ("gateway", "port"),
    ("gateway", "auth"),
    ("gateway", "controlUi"),
]

merged = json.loads(json.dumps(repo))
preserved = []

for path in PRESERVE_FIELDS:
    val = deep_get(current, *path)
    if val is not None:
        deep_set(merged, val, *path)
        preserved.append(".".join(path))

if "models" in current and "models" in merged:
    current_models = current["models"] if isinstance(current["models"], dict) else {}
    merged_models = merged["models"] if isinstance(merged["models"], dict) else {}
    for model_name, model_cfg in current_models.items():
        if isinstance(model_cfg, dict) and model_name in merged_models:
            for sensitive_key in ("apiKey", "baseUrl", "apiBase", "secret", "token"):
                if sensitive_key in model_cfg:
                    merged_models[model_name][sensitive_key] = model_cfg[sensitive_key]
                    preserved.append(f"models.{model_name}.{sensitive_key}")

if "channels" in current and "channels" in merged:
    for ch_type, ch_cfg in current.get("channels", {}).items():
        if ch_type in merged["channels"] and isinstance(ch_cfg, dict):
            for sensitive_key in ("token", "secret", "botToken", "apiKey"):
                val = ch_cfg.get(sensitive_key)
                if val is not None:
                    deep_set(merged, val, "channels", ch_type, sensitive_key)
                    preserved.append(f"channels.{ch_type}.{sensitive_key}")

agents_list = merged.get("agents", {})
if isinstance(agents_list, list):
    for agent_entry in agents_list:
        if isinstance(agent_entry, dict) and "sessionKey" in agent_entry:
            del agent_entry["sessionKey"]

with open(merged_json_path, "w") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print("  融合完成，保留了当前沙箱的字段：")
for field in preserved:
    print(f"    🔒 {field}")
print(f"  融合结果写入: {merged_json_path}")
PYEOF
    if [ $? -eq 0 ] && [ -f "$MERGED_JSON" ]; then
        if [ "$DRY_RUN" = "0" ]; then
            cp "$MERGED_JSON" "$CURRENT_JSON"
            echo "  ✅ openclaw.json 已写入（融合版本）"
        else
            echo "  [dry-run] 融合结果在 $MERGED_JSON，未写入"
        fi
    else
        echo "  ❌ openclaw.json 融合失败，请手动处理"
        echo "     仓库版本: $REPO_JSON"
        echo "     当前版本: $CURRENT_JSON"
    fi
fi

echo ""
echo "===== 同步完成 ====="
echo ""
echo "📋 后续步骤："
echo "  1. 检查 openclaw.json 是否正确（尤其 gateway.port、auth、models）"
echo "  2. 执行 'openclaw gateway restart' 使配置生效"
echo "  3. 备份目录: ${BACKUP_DIR:-（dry-run 未备份）}"
echo ""
echo "清理临时目录: rm -rf $TMP_DIR"
