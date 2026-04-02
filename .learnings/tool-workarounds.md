
## 2026-03-19: write 工具写长文件频繁失败

### 症状
- `write` 工具写超过 ~500 字的 markdown 文件时，content 参数经常传不过去（报 "missing required parameter: content"）
- `exec` 用 heredoc 写长文件也会截断（heredoc 内容含 markdown 代码块时容易提前匹配 EOF）

### 解决方案：分段写入法
1. 把长文件拆成 3~4 段，每段 < 500 字
2. 用 `write` 工具分别写到 `/tmp/xxx-part1.md`、`/tmp/xxx-part2.md` ...
3. 最后用 `exec` 的 `cat /tmp/xxx-part*.md > 目标文件` 拼接
4. 拼接后用 `read` 验证完整性

### 关键点
- 每段内避免 markdown 代码块嵌套（会干扰 heredoc/JSON 转义）
- 分段边界选在 `---` 分隔线处，保证语义完整
- 这个方法在 2026-03-19 实测稳定可用
