---
name: repo-sync-to-openclaw
description: 从远程 Git 仓库拉取为沙箱 OpenClaw 准备好的迁移文件，并同步覆盖到当前实例的 ~/.openclaw 目录。用于主 agent 或子 agent 迁移 workspace、skills、cron/jobs.json、MEMORY.md、NOTES.md 等内容。遇到 openclaw.json、agents/*/agent/*.json、auth、identity、devices、browser、logs、sessions 这类环境相关或敏感文件时，不允许直接覆盖，必须先分析当前沙箱配置并做融合。
---

# Repo Sync To OpenClaw

用于把“迁移仓库”里的内容同步到当前沙箱实例自己的 `~/.openclaw`。

## 何时使用

- 用户要求把仓库里的 OpenClaw 文件迁移到当前沙箱
- 用户要求从远程仓库拉取最新的 workspace / skills / cron 配置
- 用户要求用 skill 完成 `.openclaw` 的内容更新

## 绝对铁律

1. 默认只同步“内容层”文件，不直接覆盖“环境层”文件
2. 在执行任何覆盖前，先检查目标 `~/.openclaw` 是否存在
3. 同步前先做备份
4. 只在用户明确给出仓库地址或本地仓库路径时执行

## 可以直接同步覆盖的内容

这些内容以仓库版本为准，允许覆盖：

- `workspace/`
- `workspace-mcn-ant/`
- `workspace-mcn-bee/`
- `workspace-mcn-eagle/`
- `workspace-mcn-owl/`
- `workspace-mcn-squirrel/`
- `skills/`
- `cron/jobs.json`

特别说明：

- `workspace/MEMORY.md`
- `workspace/NOTES.md`
- 各子 agent 的 `MEMORY.md`

都属于应优先保留的沉淀内容，可以直接按仓库版本覆盖。

## 禁止直接覆盖的内容

以下文件或目录不能直接用仓库版本替换，必须先分析当前沙箱环境，再决定“保留当前 / 局部融合 / 生成人工草稿”：

- `openclaw.json`
- `agents/*/agent/models.json`
- `agents/*/agent/auth-profiles.json`
- `identity/`
- `devices/`
- `browser/`
- `logs/`
- `media/`
- `tasks/`
- `subagents/`
- `agents/*/sessions/`
- 任意 `.env*`
- 任意 `.openclaw/` 运行态目录

原因：

- 这些文件通常包含当前沙箱特有的模型、鉴权、设备、路径、浏览器、运行状态或敏感信息
- 仓库版本可能来自另一台机器，直接覆盖容易把当前沙箱搞坏

## openclaw.json 处理规则

如果仓库里存在 `openclaw.json` 或模板文件：

1. 先读取当前沙箱的 `~/.openclaw/openclaw.json`
2. 再读取仓库里的目标配置
3. 只迁移“内容和拓扑层”的改动，例如：
   - `agents.list`
   - workspace 路径映射
   - 非敏感的并发、heartbeat、subagent 限制
4. 保留当前沙箱自己的：
   - `models`
   - `auth`
   - `browser`
   - 本地绝对路径
   - 沙箱专用 provider 配置
5. 如果无法安全自动融合，不要硬改；生成一份建议 diff 或融合草稿给用户确认

## 推荐执行流程

### 步骤 1：准备临时目录

用临时目录克隆仓库，不要直接在 `~/.openclaw` 里做 git 操作。

### 步骤 2：检查仓库内容

重点检查：

- 是否包含 `workspace/`
- 是否包含 `workspace-mcn-*`
- 是否包含 `skills/`
- 是否包含 `cron/jobs.json`
- 是否包含不应直接覆盖的环境层文件

### 步骤 3：备份当前实例

运行：

```bash
bash <skill_dir>/scripts/sync_from_repo.sh --repo <repo_url> --dry-run
```

先看计划，再执行正式同步。

### 步骤 4：执行同步

正式同步命令：

```bash
bash <skill_dir>/scripts/sync_from_repo.sh --repo <repo_url>
```

### 步骤 5：如有 openclaw.json，再单独处理

不要让脚本直接覆盖 `openclaw.json`。应由 agent 自己读取两边配置后融合。

## 脚本能力

本 skill 自带脚本：

- `scripts/sync_from_repo.sh`

用途：

- 克隆/更新远程仓库到临时目录
- 备份当前 `~/.openclaw`
- 同步允许覆盖的目录和文件
- 明确跳过环境层文件
- 支持 `--dry-run`

## 结果汇报要求

执行完成后必须明确告诉用户：

- 同步了哪些目录
- 跳过了哪些敏感文件
- 是否发现需要人工融合的 `openclaw.json` 或 agent 配置
- 备份目录在哪里

