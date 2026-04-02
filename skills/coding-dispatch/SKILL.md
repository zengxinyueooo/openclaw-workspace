---
name: coding-dispatch
description: 调度 Codex 和 Claude Code 执行编码任务，带任务追踪、卡住检测和完成回调。爪爪的专属 skill。
---

# Coding Dispatch Skill

## 何时使用
皮皮或爪爪需要让 Codex / Claude Code 执行编码任务时（优化页面、写功能、修 bug、重构等）。

## 铁律
1. 永远通过 `tools/agent-runner/run.sh` 启动，不裸跑 `codex` 或 `claude`
2. 每个任务必须有 task 记录（通过 dispatch 创建）
3. workdir 必须明确，不能在爪爪的 workspace 里跑

## 选择 Agent

| 场景 | 推荐 | 命令模式 | 理由 |
|------|------|----------|------|
| 前端页面优化 | Codex | `codex exec --full-auto` | 快速，自动审批+沙箱 |
| 复杂重构/架构 | Claude Code | `claude -p --dangerously-skip-permissions` | 更强推理 |
| 需要控制花费 | Claude Code | `claude -p --max-budget-usd 5.00` | 有预算上限 |
| 简单改动(<20行) | 不用 agent | 爪爪直接 edit | 省 token |

## CLI 核心参数速查

### Codex
```bash
# 非交互执行（推荐）
codex exec "prompt"

# 全自动模式（自动审批，沙箱内执行）
codex exec --full-auto "prompt"

# 危险模式（无沙箱，无审批 = 原来的 --yolo）
codex exec --dangerously-bypass-approvals-and-sandbox "prompt"

# 指定模型
codex exec -m o4-mini "prompt"

# 指定工作目录
codex exec -C /path/to/project "prompt"

# 静默模式（CI 用）
codex exec --quiet "prompt"

# JSONL 输出（可解析进度）
codex exec --json "prompt"
```

### Claude Code
```bash
# 非交互执行（推荐，执行完直接退出）
claude -p "prompt"

# 跳过所有权限确认
claude -p --dangerously-skip-permissions "prompt"

# 限制预算
claude -p --max-budget-usd 5.00 "prompt"

# 指定模型
claude -p --model sonnet "prompt"

# 流式 JSON 输出（实时获取进度）
claude -p --output-format stream-json "prompt"

# 追加系统提示
claude -p --append-system-prompt "完成后运行 openclaw system event" "prompt"

# 接受编辑模式（自动接受文件修改，但命令需确认）
claude --permission-mode acceptEdits "prompt"
```

### 关键区别
| | Codex | Claude Code |
|---|---|---|
| 非交互模式 | `codex exec` | `claude -p` |
| 全自动 | `--full-auto` (沙箱) | `--dangerously-skip-permissions` |
| 项目上下文 | 读 `AGENTS.md` | 读 `CLAUDE.md` |
| 预算控制 | 无 | `--max-budget-usd` |
| 实时输出 | `--json` (JSONL) | `--output-format stream-json` |
| 会追问吗 | exec 模式不会 | -p 模式不会 |

## 调度流程

### 步骤 1: 启动编码 Agent
用 PTY + 后台模式：
```bash
exec pty:true background:true \
  workdir:<项目目录> \
  command:"bash tools/agent-runner/run.sh \
    --agent codex \
    --task-id <task_id> \
    --workdir <项目目录> \
    --prompt '你的详细 prompt'"
```

### 步骤 3: 监控

run.sh 自动处理三种情况：
- ✅ 成功 → task=done + 通知爪爪
- ❌ 失败 → task=failed + 通知爪爪
- ⚠️ 卡住(2分钟无输出) → 通知爪爪

手动监控命令：
```bash
# 查看后台进程
process action:list

# 查看输出日志
process action:log sessionId:<id>

# 给 agent 发输入（卡住时）
process action:write sessionId:<id> data:"y"

# 强制终止
process action:kill sessionId:<id>
```

### 步骤 4: 部署（如涉及前端）
```bash
cd tasks/supabase-materials/review && npx vercel --yes --prod
```

## Prompt 最佳实践

基于官方文档总结：

1. **给验证标准** — 不要说"优化页面"，要说"优化后截图对比，列出差异"
2. **指定文件范围** — "修改 tasks.html 的 CSS 动画部分"
3. **一次一件事** — 大任务拆成小 prompt
4. **提供示例** — "参考 dashboard.html 的样式风格"
5. **说明约束** — "纯 HTML+CSS+JS，不引入新框架"

## 常见项目目录

| 项目 | 路径 |
|------|------|
| 审核页/看板 | tasks/supabase-materials/review |
| 素材库 | tasks/supabase-materials |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| STALL_SECONDS | 120 | 多久没输出算卡住(秒) |
| PRIORITY | 2 | 任务优先级 1-5 |
