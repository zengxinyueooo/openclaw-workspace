---
name: sandbox-to-sandbox-sync
description: 从美团内网 Git 仓库（openclaw-old.git）拉取当前沙箱的最新 .openclaw 内容，并覆盖到目标沙箱的 /mnt/openclaw/.openclaw/ 目录。两端沙箱环境完全相同（路径、模型、provider 均一致），除 openclaw.json 需要做局部检查外，其余文件全部直接覆盖。
---

# sandbox-to-sandbox-sync

从 `ssh://git@git.sankuai.com/~lipengyu04/openclaw-old.git` 拉取最新代码，同步覆盖到当前沙箱的 `/mnt/openclaw/.openclaw/` 目录。

## 使用场景

- 把一个沙箱的 OpenClaw 配置/workspace/skills/cron 同步到另一个沙箱
- 两个沙箱环境完全一样：路径均为 `/mnt/openclaw/.openclaw/`，模型配置相同，provider 相同
- 不需要做路径替换，不需要做 provider 迁移，直接覆盖即可

## 执行流程

### 步骤 1：检查 SSH 可连接性

```bash
ssh -T git@git.sankuai.com -o ConnectTimeout=10 -o StrictHostKeyChecking=no 2>&1
```

如果报 `Permission denied`，需要先配置 SSH 密钥（见下方"前置：SSH 配置"）。

### 步骤 2：克隆仓库到临时目录

```bash
REPO_URL="ssh://git@git.sankuai.com/~lipengyu04/openclaw-old.git"
TMP_DIR="/tmp/sandbox-sync-$(date +%s)"
git clone --depth=1 "$REPO_URL" "$TMP_DIR"
```

### 步骤 3：备份当前 .openclaw（可选但推荐）

```bash
BACKUP_DIR="/tmp/openclaw-backup-$(date +%Y%m%d-%H%M%S)"
cp -r /mnt/openclaw/.openclaw "$BACKUP_DIR"
echo "备份在 $BACKUP_DIR"
```

### 步骤 4：执行同步

直接运行脚本：

```bash
bash <skill_dir>/scripts/sync.sh
```

脚本会自动：
1. clone 仓库
2. 备份当前目录
3. 同步所有内容（openclaw.json 单独处理）
4. 验证结果

### 步骤 5：处理 openclaw.json（见下方专节）

### 步骤 6：重启 OpenClaw 生效

```bash
openclaw gateway restart
```

---

## openclaw.json 处理规则

两端沙箱环境相同，大部分字段可以直接覆盖。但以下字段如果写错会导致 OpenClaw **启动失败或功能异常**，需要重点检查：

### ⚠️ 危险字段（必须检查，不能盲目覆盖）

| 字段路径 | 风险 | 处理方式 |
|----------|------|----------|
| `gateway.port` | 端口冲突或与系统绑定端口不一致，会导致无法启动 | **保留目标沙箱的当前值** |
| `gateway.auth.token` / `gateway.auth.secret` | 不同沙箱的 token 通常不同，覆盖会导致所有客户端断连 | **保留目标沙箱的当前值** |
| `gateway.controlUi.token` | 控制界面 token，同上 | **保留目标沙箱的当前值** |
| `models.*.apiKey` / `models.*.baseUrl` | API key 或 endpoint 与沙箱绑定，覆盖可能导致所有模型请求失败 | **保留目标沙箱的当前值** |
| `channels.*.token` / `channels.*.secret` | 各平台 bot token，沙箱间通常不同 | **保留目标沙箱的当前值** |
| `agents.*.sessionKey` | 固定 sessionKey 会导致 cron isolated session 变"不适用" | **删除或置空** |

### ✅ 可以直接覆盖的字段

- `agents.list`（agent 列表、workspace 路径、并发配置）
- `agents.defaults`（subagent 并发限制、heartbeat 间隔等）
- `cron.timezone`
- `memory.*`（记忆配置，非敏感）
- `skills.*`（skill 路径配置）
- 其他非鉴权、非端口、非路径的配置

### 自动融合逻辑

当 agent 执行此 skill 时，对 `openclaw.json`：

1. 读取仓库版本 → `/tmp/sandbox-sync-xxx/openclaw.json`
2. 读取当前沙箱版本 → `/mnt/openclaw/.openclaw/openclaw.json`
3. 用当前沙箱值**覆盖**仓库版本中的危险字段（见上表）
4. 写入融合结果到 `/mnt/openclaw/.openclaw/openclaw.json`
5. 打印 diff 供确认

如果无法判断某字段是否安全，**保留目标沙箱的当前值**，不要贸然覆盖。

---

## 前置：SSH 配置

目标沙箱需要能 SSH 访问 `git.sankuai.com`。

### 检查是否已有密钥

```bash
ls ~/.ssh/id_ed25519 2>/dev/null && echo "密钥存在" || echo "需要生成"
```

### 生成新密钥（如果没有）

```bash
ssh-keygen -t ed25519 -C 'openclaw-sandbox' -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

把公钥添加到美团 Code：https://dev.sankuai.com/code/home → 右上角 → SSH Key

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

## 可以直接覆盖的目录

以下目录/文件以仓库为准，**全部直接覆盖**：

- `workspace/`（含 MEMORY.md、AGENTS.md、SOUL.md、USER.md、skills/、memory/、tools/ 等所有子目录）
- `workspace-mcn-ant/`
- `workspace-mcn-bee/`
- `workspace-mcn-eagle/`
- `workspace-mcn-owl/`
- `workspace-mcn-squirrel/`
- `skills/`（全局 skills）
- `cron/jobs.json`

---

## 结果汇报

执行完成后必须报告：

- ✅ 同步了哪些目录
- ⚠️ openclaw.json 融合了哪些字段、保留了哪些字段
- 📁 备份目录路径
- 🔄 是否需要执行 `openclaw gateway restart`
