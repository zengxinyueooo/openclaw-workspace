# ERRORS.md - 错误日志

> 从 CORRECTIONS.md 迁移 + 新增记录

---

## [ERR-20260306-001] agent-timeout-misdiagnosis

**Logged**: 2026-03-06
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
误判子 Agent 超时为失败，实际是生图 API 正常耗时

### Error
蜜蜂超时，以为出错了，实际是 API 需要 3-5 分钟

### Context
- 生图 API 本身需要较长时间
- 默认超时设置太短（15分钟）

### Suggested Fix
给子 Agent 设 30 分钟超时

### Resolution
- **Resolved**: 2026-03-06
- **Notes**: timeout 调整为 30 分钟

### Metadata
- Reproducible: yes
- Source: user_feedback
- Tags: timeout, api, bee

---

## [ERR-20260307-001] api-empty-url-retry-loop

**Logged**: 2026-03-07
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
API 返回空 URL 时反复重试浪费资源

### Error
生图 API 返回 `url: ""` + `batchId`，误以为需要重试

### Context
- 后端异步问题，不是参数错误
- 昨天已出现过同样问题

### Suggested Fix
看到 `url: ""` 立刻问皮皮，不要自己反复试

### Resolution
- **Resolved**: 2026-03-07
- **Notes**: 后端异步查询机制确认

### Metadata
- Reproducible: yes
- Source: user_feedback
- Tags: api, retry, async

---

## [ERR-20260308-001] image-quality-2k-crash

**Logged**: 2026-03-08
**Priority**: critical
**Status**: resolved
**Area**: backend

### Summary
imageQuality=2k 导致后端报 "prompt is not defined"

### Error
V3 重构时擅自把 quality 从 1k 改成 2k，后端报错

### Context
- 原始参数: picNum=8, imageQuality=1k
- 2k 质量触发后端未处理的分支

### Suggested Fix
默认参数必须是 picNum=8, imageQuality=1k, timeout>=600秒

### Resolution
- **Resolved**: 2026-03-08
- **Notes**: 恢复原始参数

### Metadata
- Reproducible: yes
- Source: user_feedback
- Tags: api, parameters, bee
- See Also: ERR-20260317-001

---
## [ERR-20260308-002] write-tool-long-text-loss

**Logged**: 2026-03-08
**Priority**: critical
**Status**: resolved
**Area**: infra

### Summary
write/exec 工具长文本参数被吞，反复空转

### Error
写学城日记时 content 参数丢失，validation 报 "must have required property 'content'"

### Context
- 3/7 出现 5 次，3/8 出现 4 次，3/9 出现 14 次
- 模型在高上下文压力下输出空参数 → 死循环
- 不是 OpenClaw bug，是模型长上下文退化

### Suggested Fix
1. 长文本(>500字)用 exec+heredoc 分段写
2. 每段控制 300 字以内
3. 第一次失败立刻换方案，不重试 write
4. 遇到空参数立刻停下回复文字，中断死循环
5. 避免单轮超过 8 次连续工具调用

### Resolution
- **Resolved**: 2026-03-09
- **Notes**: 采用 heredoc 分段方案

### Metadata
- Reproducible: yes
- Source: error
- Tags: tooling, context-pressure, write
- Recurrence-Count: 3
- First-Seen: 2026-03-07
- Last-Seen: 2026-03-09

---

## [ERR-20260309-001] config-change-without-docs

**Logged**: 2026-03-09
**Priority**: critical
**Status**: resolved
**Area**: config

### Summary
改 compaction mode 没查官方文档导致 agent 崩溃

### Error
把 safeguard → auto，agent 从下午 3:47 到次日凌晨 1:10 无响应

### Context
- 评估报告建议改，直接改了没查文档
- auto 模式有前置条件

### Suggested Fix
任何配置变更前必须先读官方文档

### Resolution
- **Resolved**: 2026-03-10
- **Notes**: 恢复配置，建立铁律

### Metadata
- Reproducible: yes
- Source: error
- Tags: config, crash, critical

---

## [ERR-20260317-001] api-param-name-modified

**Logged**: 2026-03-17
**Priority**: critical
**Status**: resolved
**Area**: backend

### Summary
蜜蜂擅自将 promptModel 改为 prompt 导致 API 报错

### Error
retry 任务中修改了 API 参数名试图修复报错

### Context
- API 参数名由后端定义，不得擅自修改
- 后端报错应上报人工处理

### Suggested Fix
所有 agent 遇到 API 参数相关错误只报告不修改

### Resolution
- **Resolved**: 2026-03-17
- **Notes**: 撤回为 promptModel，写入 MEMORY.md 铁律

### Metadata
- Reproducible: yes
- Source: user_feedback
- Tags: api, parameters, bee
- See Also: ERR-20260308-001

---

## [ERR-20260319-001] bee-face-validation-failed-and-missing-column

**Logged**: 2026-03-19T11:21:00+08:00
**Priority**: high
**Status**: pending
**Area**: backend

### Summary
蜜蜂生图任务：API生成7张但人脸验证全部失败 + generated_images 表缺少 scene 列

### Error
- 任务：先叫Momo 颜值生图 (8张)
- API 返回 7 张图，人脸验证全部失败
- 数据库 `generated_images` 表缺少 `scene` 列

### Context
- 需要检查参考图质量
- 需要修复数据库表结构

### Suggested Fix
1. 检查参考图是否清晰、正脸
2. 给 generated_images 表加 scene 列
3. 重新跑生图任务

### Metadata
- Reproducible: unknown
- Source: error
- Tags: bee, face-validation, database, schema

---
