---
name: mc-code-agent
description: '通过 PTY 终端驱动 mc --code（Claude Code）完成编码任务。子 Agent 自动启动 Claude Code、处理信任确认、输入任务、读取响应、判断结果并决定是否继续对话，全程无需人工干预。触发条件：需要用 Claude Code 完成编码任务、需要子 Agent 自动操作 Claude Code 时使用。'
metadata:
  { "openclaw": { "emoji": "🤖" } }
---

# mc-code-agent：自动驱动 Claude Code 完成编码任务

## 原理

`mc --code` 是一个交互式 TTY 程序，必须使用 `exec(pty=true)` 启动，然后通过 `process` 工具发送按键、读取输出来完成交互。

---

## 完整操作流程

### 第一步：启动 mc --code（后台 PTY 模式）

```
exec:
  command: "mc --code"
  pty: true
  background: true
  workdir: <目标项目目录，默认 ~>
  yieldMs: 3000   # 等待 3 秒让界面渲染
```

记录返回的 `sessionId`，后续所有操作都用这个 id。

---

### 第二步：读取初始输出，确认出现信任界面

```
process:
  action: log
  sessionId: <id>
  limit: 50
```

**判断标准：** 输出中包含 `Do you trust the files` 或 `Yes, proceed` 即为信任确认界面。

---

### 第三步：按回车确认信任（选择 "Yes, proceed"）

```
process:
  action: send-keys
  sessionId: <id>
  keys: ["Enter"]
```

然后等待 2-3 秒再读取输出：

```
process:
  action: poll
  sessionId: <id>
  timeout: 3000
```

---

### 第四步：确认已进入 Claude Code 主界面

再次读取输出：

```
process:
  action: log
  sessionId: <id>
  limit: 50
```

**判断标准：** 输出中包含 `Claude Code` 或出现输入提示符（`>`）即为成功进入主界面。

> ⚠️ 如果仍显示信任界面，再发一次 Enter。
> ⚠️ 如果出现 `No, exit` 被选中，说明方向键改变了选项，需要先按 `↑` 切换到 "Yes, proceed" 再按 Enter。

---

### 第五步：输入编码任务

使用 `paste` 发送任务（支持多行、特殊字符）：

```
process:
  action: paste
  sessionId: <id>
  text: "<你的任务描述>"
```

然后发送 Enter 提交：

```
process:
  action: send-keys
  sessionId: <id>
  keys: ["Enter"]
```

---

### 第六步：等待并轮询 Claude Code 响应

Claude Code 处理任务需要时间，使用轮询方式等待：

```
# 每隔 5 秒读取一次输出，最多等待 5 分钟
process:
  action: poll
  sessionId: <id>
  timeout: 5000
```

然后读取输出：

```
process:
  action: log
  sessionId: <id>
  limit: 100
  offset: <上次读取的行数，避免重复>
```

**判断 Claude Code 是否完成响应：**
- ✅ 完成标志：输出末尾重新出现输入提示符 `>`，或出现 `Cost:` 统计信息
- ⏳ 仍在处理：出现 `...`、`Thinking`、`Running` 等字样
- ❓ 需要确认：出现选项列表（`1.` `2.` 等），需要用 send-keys 选择

**如果 Claude Code 出现选项需要确认：**
```
# 读取选项内容，判断应该选哪个
# 通常直接按 Enter 选默认选项（通常是第1项）
process:
  action: send-keys
  sessionId: <id>
  keys: ["Enter"]
```

---

### 第七步：判断结果是否符合预期

读取完整输出后，自行判断：

- ✅ **符合预期** → 进入第八步退出
- ❌ **不符合预期 / 需要补充** → 返回第五步，继续输入新的指令

**不符合预期的情况举例：**
- 代码有语法错误
- 功能未完整实现
- 需要追加需求或修改

**继续对话时的输入方式（同第五步）：**
```
process:
  action: paste
  sessionId: <id>
  text: "请修改：<具体修改要求>"

process:
  action: send-keys
  sessionId: <id>
  keys: ["Enter"]
```

---

### 第八步：退出 Claude Code

任务完成后，发送退出命令：

```
process:
  action: send-keys
  sessionId: <id>
  keys: ["Escape"]
```

或者直接 kill session：

```
process:
  action: kill
  sessionId: <id>
```

---

## 关键注意事项

### ⚠️ PTY 必须开启
`mc --code` 是交互式 TUI 程序，没有 `pty: true` 会挂起或输出乱码。

### ⚠️ 使用 paste 而非 submit 输入长文本
- `paste` 适合输入任务描述（支持长文本、特殊字符）
- `send-keys + Enter` 用于确认/提交
- `submit` 会追加换行，对于多轮对话可能导致误触发

### ⚠️ 轮询要有耐心
Claude Code 处理复杂任务可能需要 1-5 分钟，不要过早 kill session。
每次 poll 等待 5 秒，连续无新输出超过 30 秒才判断为完成或卡住。

### ⚠️ 读取输出用 offset 避免重复
每次 `log` 记录上次读取到的行数，下次从该 offset 开始读，避免处理重复内容。

### ⚠️ 识别 ANSI 转义序列
PTY 输出包含颜色/样式的 ANSI 转义码（如 `\x1b[32m`），判断文本内容时需要忽略这些字符，只看纯文字部分。

---

## 完整示例流程

```
目标：让 Claude Code 在 ~/Projects/myapp 目录下创建一个 HelloWorld React 组件

1. exec(pty=true, background=true, workdir="~/Projects/myapp", command="mc --code", yieldMs=3000)
   → 返回 sessionId: abc123

2. process(log, abc123) → 确认看到 "Do you trust"

3. process(send-keys, abc123, ["Enter"]) → 等待 3 秒

4. process(log, abc123) → 确认看到 Claude Code 主界面

5. process(paste, abc123, "创建一个 HelloWorld React 组件，文件放在 src/components/HelloWorld.tsx")
   process(send-keys, abc123, ["Enter"])

6. 轮询等待，每 5 秒 poll + log，直到看到 ">" 提示符重新出现

7. 检查输出 → 确认文件已创建、代码正确

8. process(kill, abc123) → 结束
```

---

## 故障排查

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 输出全是乱码 | PTY 未开启 | 确保 `pty: true` |
| 停在信任界面 | Enter 没发出去 | 重试 `send-keys: ["Enter"]` |
| 长时间无响应 | Claude Code 在处理 | 继续等待，最多 5 分钟 |
| 出现 "No, exit" 被选中 | 方向键误触 | 按 `↑` 再按 Enter |
| Session 消失 | 超时被 kill | 重新启动整个流程 |
| 输入没有出现在界面 | paste 时机太早 | 等界面完全渲染后再 paste |
