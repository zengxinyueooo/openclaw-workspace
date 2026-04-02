# LEARNINGS.md - 学习日志

> 从 CORRECTIONS.md 迁移 + 新增记录

---

## [LRN-20260307-001] correction: repeat-same-mistake

**Logged**: 2026-03-07
**Priority**: high
**Status**: promoted
**Area**: docs

### Summary
同样的问题出现两次，说明记忆机制失效

### Details
昨天已知 API 超时需要 3-5 分钟，今天蜜蜂超时又从头排查

### Suggested Action
每次被纠正后立刻写到记录文件，处理相似任务前先读

### Metadata
- Source: user_feedback
- Tags: memory, discipline
- Promoted: MEMORY.md + CORRECTIONS.md

---

## [LRN-20260308-001] correction: wrong-review-page-link

**Logged**: 2026-03-08
**Priority**: high
**Status**: promoted
**Area**: docs

### Summary
生图结果给了素材审核页链接，不是生图审核页

### Details
素材审核、生图审核、草稿审核是不同页面，不能混用：
- 生图 → image-select.html
- 素材 → 首页
- 草稿 → draft-review.html

### Suggested Action
给链接前先确认是哪种审核

### Metadata
- Source: user_feedback
- Tags: links, review-pages
- Promoted: MEMORY.md 关键链接

---

## [LRN-20260308-002] correction: style-ref-image-wrong

**Logged**: 2026-03-08
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
风格参考图不能用肖像图本身

### Details
generate.py 里风格参考图和肖像参考图用了同一张。应该从 materials 表 category=face + status=approved 随机取。

### Suggested Action
从 Supabase 素材库取已审核素材作为风格参考图

### Metadata
- Source: user_feedback
- Tags: bee, generate, style

---

## [LRN-20260308-003] best_practice: plain-links-no-markdown

**Logged**: 2026-03-08
**Priority**: high
**Status**: promoted
**Area**: frontend

### Summary
大象渠道发链接不要用 markdown 格式

### Details
大象不渲染 markdown，`**url**` 显示成 `*https://...*`。发链接就发纯文本。

### Suggested Action
发链接永远发纯文本

### Metadata
- Source: user_feedback
- Tags: daxiang, formatting
- Recurrence-Count: 2
- Promoted: MEMORY.md

---
## [LRN-20260308-004] best_practice: agent-completion-notify

**Logged**: 2026-03-08
**Priority**: high
**Status**: promoted
**Area**: infra

### Summary
Codex/Claude Code 完成后必须通知爪爪

### Details
不能依赖 agent 自觉执行通知，用包装脚本兜底。通过 coding-dispatch skill 启动。

### Suggested Action
永远通过 coding-dispatch skill 启动编码任务

### Metadata
- Source: user_feedback
- Tags: agent, notification
- Promoted: AGENTS.md

---

## [LRN-20260309-001] knowledge_gap: context-pressure-degradation

**Logged**: 2026-03-09
**Priority**: high
**Status**: promoted
**Area**: infra

### Summary
模型在高上下文压力下输出空参数导致死循环

### Details
Context window 接近满时，模型输出 `arguments: {}`，AJV 报错被 feed 回模型形成死循环。

### Suggested Action
1. 遇到第一次空参数立刻停下回复文字
2. 减少注入体积
3. 大任务拆子 agent
4. 避免单轮超 8 次连续工具调用

### Metadata
- Source: error
- Tags: context, tooling, degradation
- Promoted: MEMORY.md + CORRECTIONS.md

---

## [LRN-20260309-002] best_practice: check-docs-before-config

**Logged**: 2026-03-09
**Priority**: critical
**Status**: promoted
**Area**: config

### Summary
改配置前必须查官方文档

### Details
改 compaction mode 没查文档导致 agent 崩溃 9.5 小时

### Suggested Action
任何配置变更前先读 docs/ 或 docs.openclaw.ai

### Metadata
- Source: error
- Tags: config, docs, discipline
- Promoted: MEMORY.md 经验教训

---

## [LRN-20260317-001] correction: never-modify-api-params

**Logged**: 2026-03-17
**Priority**: critical
**Status**: promoted
**Area**: backend

### Summary
严禁修改 API 参数名

### Details
蜜蜂在 retry 中将 promptModel 改为 prompt。API 参数名由后端定义，遇到报错只报告不修改。

### Suggested Action
所有 agent 遇到 API 参数相关错误只报告不修改

### Metadata
- Source: user_feedback
- Tags: api, parameters, discipline
- Promoted: MEMORY.md 经验教训

---

## [LRN-20260317-002] best_practice: bee-must-query-image-url

**Logged**: 2026-03-17
**Priority**: high
**Status**: promoted
**Area**: backend

### Summary
蚂蚁创建 OPX 资产时必须从 generated_images 表查 image_url

### Details
不能自己拼接/猜测图片 URL，否则资产图片为空

### Suggested Action
所有需要 image_url 的地方都从 generated_images 表查

### Metadata
- Source: user_feedback
- Tags: ant, opx, image
- Promoted: MEMORY.md 经验教训

---

## [LRN-20260319-001] correction: bypass-skill-direct-execution

**Logged**: 2026-03-19T11:21:00+08:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
主 session 直接跑 MediaCrawler 绕过了松鼠 skill 流程，导致没有入库、没有审核、没有 agent_runs 记录

### Details
松鼠首次 spawn 因 cookie 过期超时后，爪爪在主 session 直接执行了 `python3 main.py` 采集命令。虽然采集成功，但跳过了 collect-xhs-assets skill 的入库和审核环节。违反了「爪爪只调度不执行业务脚本」的架构铁律。

### Suggested Action
1. 即使子 agent 失败，也应该修复问题后重新派活，不要在主 session 直接执行
2. 主 session 只能做诊断（查日志、查配置），不做业务执行
3. cookie 过期等前置问题修好后，重新 spawn 子 agent 走完整流程

### Metadata
- Source: user_feedback
- Tags: architecture, discipline, squirrel
- Pattern-Key: bypass.skill_execution
- Recurrence-Count: 1
- First-Seen: 2026-03-19

---

## [LRN-20260319-002] knowledge_gap: outdated-mediacrawler-vs-xhs-scraper

**Logged**: 2026-03-19T11:30:00+08:00
**Priority**: critical
**Status**: pending
**Area**: infra

### Summary
主 workspace 的 MediaCrawler 是旧方案，松鼠当前使用 xhs-scraper skill（Playwright+CDP），不再依赖 MediaCrawler

### Details
- 旧: MediaCrawler（在主workspace/MediaCrawler/），需要登录cookie，headless模式
- 新: xhs-scraper skill（symlink 到 ~/.openclaw/skills/xhs-scraper），基于 Playwright CDP 连接已有浏览器
- 松鼠的 collect.py 是新入口脚本，但 search_notes 函数内部仍错误引用 packages/MediaCrawler（该目录不存在）
- 旧的 skill 已全部归档到 _archived/
- MEMORY.md 里记录的 "MediaCrawler 作为采集核心" 已过时

### Suggested Action
1. 更新 MEMORY.md 将 MediaCrawler 标记为旧方案
2. 修复 collect.py 的搜索模块使用 xhs-scraper
3. 爪爪记住：采集任务只派松鼠，松鼠用 xhs-scraper + collect.py

### Metadata
- Source: user_feedback
- Tags: architecture, squirrel, xhs-scraper, mediacrawler
- Pattern-Key: knowledge.outdated_tools
- Recurrence-Count: 1
- First-Seen: 2026-03-19

---
