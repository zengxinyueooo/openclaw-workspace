---
name: sandbox-to-sandbox-sync
description: 从用户提供的远程 Git 仓库拉取另一台沙箱的 .openclaw 内容，同步覆盖到当前沙箱的 /mnt/openclaw/.openclaw/ 目录。适用于两端路径相同、环境一致的沙箱间迁移场景。openclaw.json 及鉴权相关文件不能直接覆盖，必须先分析当前配置再融合。
---

# Sandbox to Sandbox Sync

把一个沙箱的 OpenClaw 配置（workspace、skills、cron、子 agent workspace 等）同步到另一个沙箱。

## 何时使用

- 用户要求把另一台沙箱的配置迁移到当前沙箱
- 用户要求从某个仓库拉取最新的 workspace / skills / cron 配置覆盖当前沙箱
- 两端沙箱路径均为 `/mnt/openclaw/.openclaw/`，环境一致，不需要路径替换或 provider 迁移

## 绝对铁律

1. **仓库地址由用户提供**，skill 不预设任何仓库地址
2. 只在用户明确给出仓库地址后才执行
3. 同步前必须先做备份
4. 不直接覆盖环境层文件（见下方禁止覆盖列表）
5. `openclaw.json` 必须走融合流程，不能整文件覆盖

## 可以直接覆盖的内容

以仓库版本为准，允许直接覆盖：

- `workspace/`（含 MEMORY.md、AGENTS.md、SOUL.md、USER.md、skills/、memory/、tools/ 等所有子目录）
- `workspace-mcn-ant/`
- `workspace-mcn-bee/`
- `workspace-mcn-eagle/`
- `workspace-mcn-owl/`
- `workspace-mcn-squirrel/`
- `skills/`（全局 skills 目录）
- `cron/jobs.json`

## 禁止直接覆盖的内容

以下文件或目录不能直接用仓库版本替换，必须先分析当前沙箱配置，再决定保留/局部融合/生成草稿供用户确认：

- `openclaw.json`
- `agents/*/agent/models.json`
- `agents/*/agent/auth-profiles.json`
- `identity/`
- `devices/`
- `browser/`
- `logs/`
- `media/`
- `subagents/`
- `agents/*/sessions/`
- 任意 `.env*` 文件
- 任意运行态目录

## openclaw.json 处理规则

1. 读取当前沙箱的 `/mnt/openclaw/.openclaw/openclaw.json`
2. 读取仓库里的 `openclaw.json`
3. 以当前沙箱值**覆盖**仓库版本中的以下危险字段：

| 字段路径 | 原因 |
|----------|------|
| `gateway.port` | 端口与系统绑定，覆盖会导致无法启动 |
| `gateway.auth.token` / `gateway.auth.secret` | 沙箱专有 token，覆盖会断开所有客户端 |
| `gateway.controlUi.token` | 控制界面 token，同上 |
| `models.*.apiKey` / `models.*.baseUrl` | API key 与沙箱绑定 |
| `channels.*.token` / `channels.*.secret` | 平台 bot token，沙箱间通常不同 |

4. `agents.*.sessionKey` 字段：**删除或置空**（固定 sessionKey 会导致 cron isolated session 变"不适用"）
5. 可以直接覆盖的字段（以仓库版本为准）：
   - `agents.list`（agent 列表、workspace 路径、并发配置）
   - `agents.defaults`
   - `cron.timezone`
   - `memory.*`
   - `skills.*`
   - 其他非鉴权、非端口字段
6. 如无法安全自动融合，生成建议 diff 给用户确认，不要强行写入

## 推荐执行流程

### 步骤 1：确认仓库地址

向用户确认仓库地址（SSH 或 HTTPS 格式均可），例如：

```
ssh://git@git.sankuai.com/~username/your-repo.git
```

### 步骤 2：检查 SSH 可连接性

```bash
ssh -T git@git.sankuai.com -o ConnectTimeout=10 -o StrictHostKeyChecking=no 2>&1
```

如报 `Permission denied`，先配置 SSH 密钥（见下方"SSH 配置"）。

### 步骤 3：克隆仓库到临时目录

```bash
REPO_URL="<用户提供的仓库地址>"
TMP_DIR="/tmp/sandbox-sync-$(date +%s)"
git clone --depth=1 "$REPO_URL" "$TMP_DIR"
```

### 步骤 4：检查仓库内容结构

重点确认仓库里包含哪些目录：

```bash
ls "$TMP_DIR"
```

预期结构（以 `.openclaw/` 为根的拍平形式）：

```
workspace/
workspace-mcn-ant/
workspace-mcn-bee/
workspace-mcn-eagle/
workspace-mcn-owl/
workspace-mcn-squirrel/
skills/
cron/
openclaw.json      ← 单独处理，不直接覆盖
```

如果仓库结构不符合预期，先和用户确认后再继续。

### 步骤 5：备份当前沙箱

```bash
BACKUP_DIR="/tmp/openclaw-backup-$(date +%Y%m%d-%H%M%S)"
cp -r /mnt/openclaw/.openclaw "$BACKUP_DIR"
echo "备份完成：$BACKUP_DIR"
```

### 步骤 6：同步允许覆盖的目录

逐目录覆盖：

```bash
DEST="/mnt/openclaw/.openclaw"
for DIR in workspace workspace-mcn-ant workspace-mcn-bee workspace-mcn-eagle workspace-mcn-owl workspace-mcn-squirrel skills; do
  if [ -d "$TMP_DIR/$DIR" ]; then
    rm -rf "$DEST/$DIR"
    cp -r "$TMP_DIR/$DIR" "$DEST/$DIR"
    echo "✅ 已同步：$DIR"
  fi
done

# cron/jobs.json 单独处理
if [ -f "$TMP_DIR/cron/jobs.json" ]; then
  cp "$TMP_DIR/cron/jobs.json" "$DEST/cron/jobs.json"
  echo "✅ 已同步：cron/jobs.json"
fi
```

### 步骤 7：处理 openclaw.json

使用 Python 融合（保留当前沙箱危险字段，覆盖其余配置）：

```python
import json

with open("/mnt/openclaw/.openclaw/openclaw.json") as f:
    current = json.load(f)
with open(f"{TMP_DIR}/openclaw.json") as f:
    source = json.load(f)

# 保留危险字段
for key in ["port", "auth", "controlUi"]:
    if key in current.get("gateway", {}):
        source.setdefault("gateway", {})[key] = current["gateway"][key]

for model_key, model_val in source.get("models", {}).items():
    if model_key in current.get("models", {}):
        for field in ["apiKey", "baseUrl"]:
            if field in current["models"][model_key]:
                model_val[field] = current["models"][model_key][field]

for ch_key, ch_val in source.get("channels", {}).items():
    if ch_key in current.get("channels", {}):
        for field in ["token", "secret"]:
            if field in current["channels"][ch_key]:
                ch_val[field] = current["channels"][ch_key][field]

# 删除 agents.*.sessionKey
for agent in source.get("agents", {}).get("list", []):
    agent.pop("sessionKey", None)

with open("/mnt/openclaw/.openclaw/openclaw.json", "w") as f:
    json.dump(source, f, indent=2, ensure_ascii=False)

print("✅ openclaw.json 融合完成")
```

融合后打印 diff 确认：

```bash
diff <(python3 -c "import json,sys; print(json.dumps(json.load(open('$BACKUP_DIR/openclaw.json')), indent=2))") \
     <(python3 -c "import json,sys; print(json.dumps(json.load(open('/mnt/openclaw/.openclaw/openclaw.json')), indent=2))")
```

### 步骤 8：重启 OpenClaw 生效

```bash
openclaw gateway restart
```

---

## SSH 配置（如未配置）

### 检查是否已有密钥

```bash
ls ~/.ssh/id_ed25519 2>/dev/null && echo "密钥已存在" || echo "需要生成"
```

### 生成新密钥

```bash
ssh-keygen -t ed25519 -C 'openclaw-sandbox' -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

将公钥添加到代码托管平台（如美团 Code：https://dev.sankuai.com/code/home → 右上角 → SSH Key）。

### 配置 ~/.ssh/config

```
Host git.sankuai.com
    HostName git.sankuai.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    HostkeyAlgorithms +ssh-ed25519
    PubkeyAcceptedKeyTypes +ssh-ed25519
```

---

## 结果汇报要求

执行完成后必须明确报告：

- ✅ 同步了哪些目录
- ⚠️ openclaw.json 保留了哪些字段、覆盖了哪些字段
- ⏭️ 跳过了哪些敏感文件
- 📁 备份目录路径
- 🔄 是否已执行 `openclaw gateway restart`
