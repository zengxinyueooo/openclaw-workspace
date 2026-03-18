---
name: mc-code-agent
description: '通过 PTY 终端驱动 mc --code（Claude Code）完成编码任务。子 Agent 自动启动 Claude Code、处理信任确认、输入任务、读取响应、识别并处理交互式选择菜单、验证结果、不满足预期时自动继续对话，全程无需人工干预。触发条件：需要用 Claude Code 完成编码任务、需要子 Agent 自动操作 Claude Code 时使用。'
metadata:
  { "openclaw": { "emoji": "🤖" } }
---

# mc-code-agent：自动驱动 Claude Code 完成编码任务

## 原理

`mc --code` 是一个交互式 TTY 程序，必须使用 `exec(pty=true)` 启动，然后通过 `process` 工具发送按键、读取输出来完成交互。

子 Agent 的角色是**对话驱动者 + 结果验证者**：
- Claude Code 负责直接读写文件、执行命令
- 子 Agent 负责输入任务、识别界面状态、验证结果、决定是否继续

---

## 完整操作流程

### 第一步：启动 mc --code（后台 PTY 模式）

```
exec:
  command: "mc --code"
  pty: true
  background: true
  workdir: <目标项目目录，默认 ~>
  yieldMs: 3000
```

记录返回的 `sessionId`，后续所有操作都用这个 id。

---

### 第二步：处理信任确认界面

读取输出：
```
process: action=log, sessionId=<id>, limit=50
```

**判断标准：** 输出包含 `Do you trust the files` 或 `Yes, proceed` → 发送 Enter：
```
process: action=send-keys, sessionId=<id>, keys=["Enter"]
```

等待 2 秒后再次读取，确认进入主界面（看到 `>` 提示符）。

> ⚠️ 若仍在信任界面，重试 Enter。
> ⚠️ 若 `No, exit` 被选中，先按 `↑` 切换到 Yes 再 Enter。

---

### 第三步：输入编码任务

使用 `paste` 发送任务（支持长文本、特殊字符）：
```
process: action=paste, sessionId=<id>, text="<任务描述>"
process: action=send-keys, sessionId=<id>, keys=["Enter"]
```

---

### 第四步：轮询输出 + 识别界面状态（核心循环）

每次轮询流程：
```
process: action=poll, sessionId=<id>, timeout=5000
process: action=log, sessionId=<id>, limit=100, offset=<上次行数>
```

**每次读取输出后，必须判断当前处于哪种状态：**

---

#### 状态一：交互式选择菜单（最重要！）

**识别特征（同时出现以下任意一条）：**
- 底部出现 `Enter to select · Tab/Arrow keys to navigate · Esc to cancel`
- 输出中有编号列表 `1. xxx  2. xxx  3. xxx`
- 当前行有 `›` 或 `>` 箭头指向某个选项

**处理方式：**

```
# 1. 解析选项列表，理解每个选项的含义
# 2. 根据任务需求判断应该选哪个
# 3. 用方向键导航到目标选项（当前选中的是 › 箭头指向的）

# 向下移动一项：
process: action=send-keys, sessionId=<id>, keys=["Down"]

# 向上移动一项：
process: action=send-keys, sessionId=<id>, keys=["Up"]

# 确认选择：
process: action=send-keys, sessionId=<id>, keys=["Enter"]
```

**导航策略：**
- 默认第 1 项被选中（`›` 在第 1 行）
- 每按一次 `Down`，光标下移一项
- 通过计算"目标项序号 - 当前序号"确定需要按几次方向键
- 例如：当前选中第 1 项，想选第 3 项 → 按 2 次 `Down` 再 Enter

**如果有多个菜单页（Tab 切换）：**
- 底部出现 `← □ 界面类型  □ 功能用途  ✓ Submit →` 这种 Tab 导航
- 先在当前 Tab 完成选择，再按 `Tab` 或 `→` 切换到下一个 Tab
- 所有 Tab 填完后，导航到 `Submit` 按 Enter 提交

---

#### 状态二：Claude Code 正在处理

**识别特征：**
- 出现 `...`、`Thinking`、`Running`、`Executing` 等字样
- 终端有新内容不断追加但没有提示符

**处理方式：** 继续等待，每 5 秒 poll 一次，耐心等待最多 5 分钟。

---

#### 状态三：Claude Code 完成响应

**识别特征：**
- 输出末尾重新出现 `>` 输入提示符
- 出现 `Cost:` 统计信息
- 输出了文件路径或完成摘要

**处理方式：** 进入第五步，验证结果。

---

#### 状态四：Claude Code 需要文字输入

**识别特征：**
- 出现问号 `?` 提示
- 等待用户输入文字（非选择菜单）

**处理方式：**
```
process: action=paste, sessionId=<id>, text="<回答内容>"
process: action=send-keys, sessionId=<id>, keys=["Enter"]
```

---

### 第五步：验证结果

Claude Code 完成后，**主动验证**，不能只看终端输出就结束：

```
# 验证文件是否存在
exec: command="ls -la <workdir>/<预期文件路径>"

# 验证文件内容是否正确
exec: command="cat <文件路径>"

# 如果是代码，可以尝试运行验证
exec: command="cd <workdir> && node <文件> 2>&1" （根据语言选择）
```

**验证判断标准（根据任务类型自行判断）：**
- 文件是否存在 ✅
- 文件内容是否包含预期的关键逻辑 ✅
- 代码语法是否正确（能否运行） ✅
- 功能是否满足任务描述的要求 ✅

---

### 第六步：结果不符合预期 → 自动继续对话

**如果验证不通过，不要退出，继续和 Claude Code 对话：**

```
# 直接在同一个 session 里继续输入修改指令
process: action=paste, sessionId=<id>, text="<具体的修改要求，说明哪里不对>"
process: action=send-keys, sessionId=<id>, keys=["Enter"]
```

然后回到**第四步**，继续轮询等待新的响应，再次验证。

**重试次数建议：** 最多重试 3 次，3 次后仍不符合预期，汇报给主 Agent 处理。

**修改指令要具体，举例：**
- ❌ 模糊："改一下这个代码"
- ✅ 具体："刚才生成的 HelloWorld.tsx 缺少 props 类型定义，请补充 name: string 和 age: number 两个 props"

---

### 第七步：退出 Claude Code

任务完成且验证通过后：

```
process: action=kill, sessionId=<id>
```

---

## 完整状态机（子 Agent 执行逻辑）

```
启动 mc --code
    ↓
处理信任确认（Enter）
    ↓
输入任务
    ↓
┌─→ 轮询输出
│       ↓
│   判断状态：
│   ├── 选择菜单 → 分析选项 → 方向键导航 → Enter 确认 → 继续轮询
│   ├── 正在处理 → 继续等待
│   ├── 需要文字输入 → paste 回答 → 继续轮询
│   └── 完成响应
│           ↓
│       验证结果（exec 检查文件）
│           ↓
│       符合预期？
│       ├── ✅ 是 → kill session → 结束，汇报结果
└───────└── ❌ 否（重试<3次）→ paste 修改指令 → Enter → 继续轮询
                ↓（重试≥3次）
            汇报失败，等待主 Agent 指示
```

---

## 关键注意事项

### ⚠️ PTY 必须开启
`mc --code` 是交互式 TUI 程序，没有 `pty: true` 会挂起或输出乱码。

### ⚠️ 使用 paste 输入文字，send-keys 操作按键
- `paste`：输入任务描述、文字回答
- `send-keys`：Enter 提交、方向键导航、Esc 取消

### ⚠️ 读取输出用 offset 避免重复
每次 `log` 记录当前总行数，下次从该 offset 开始读，避免重复处理旧内容。

### ⚠️ ANSI 转义序列过滤
PTY 输出包含颜色码（如 `\x1b[32m`、`\x1b[0m`），判断文本内容时忽略这些字符。

### ⚠️ 选择菜单不能用 paste 输入数字
选择菜单必须用方向键导航，不能直接输入数字序号，那样会被当成文字输入。

### ⚠️ 多 Tab 表单要逐个填完再 Submit
如图所示的多 Tab 界面（界面类型 / 功能用途 / Submit），每个 Tab 独立选择，最后 Tab 到 Submit 回车。

---

## 故障排查

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 输出全是乱码 | PTY 未开启 | 确保 `pty: true` |
| 停在信任界面 | Enter 没发出去 | 重试 `send-keys: ["Enter"]` |
| 选择菜单没有响应 | paste 了文字而非方向键 | 改用 `send-keys: ["Down"/"Up"]` |
| 方向键选错了选项 | 按键次数计算错误 | 重新 log 读取当前 `›` 位置再重算 |
| 长时间无响应 | Claude Code 在处理 | 继续等待，最多 5 分钟 |
| 文件没有生成 | workdir 设置错误 | 检查 workdir 路径是否正确 |
| 输入没出现在界面 | paste 时机太早 | 等界面完全渲染后再 paste |
