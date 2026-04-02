---
name: km-doc-tools
description: Comprehensive toolkit for Meituan Knowledge Management (学城) operations using the km CLI. Supports searching, reading, creating, copying, moving, deleting, and restoring KM documents, as well as reading embedded files and exploring document hierarchies. Use when users need to interact with km.sankuai.com pages in any way — searching docs, fetching content, creating new documents, restructuring spaces, or managing the document lifecycle. Triggers on: "在学城搜索", "获取学城文档", "创建学城文档", "复制文档", "移动文档", "删除文档", "恢复文档", "文档结构", or any task involving km.sankuai.com.
---

# KM Document Tools

> **参考文档**：[美团本地 MCP & Skills 依赖问题及安装说明](https://km.sankuai.com/collabpage/2708424384)

Full-featured CLI toolkit for Meituan Knowledge Management (学城) using the `km` command.

## Prerequisites & Setup

```bash
# Install (if not present)
git clone ssh://git@git.sankuai.com/waimb/waimai-ai-tools.git ~/.meituan-local-tools
cd ~/.meituan-local-tools && bash setup.sh

# Activate before EVERY session
source ~/.meituan-local-tools/.venv/bin/activate
```

> **git clone 遇到 SSH Key 报错？
安装支持前请先在Code平台设置好SSH Key：
https://km.sankuai.com/collabpage/1465033066**

Keep browser logged into https://km.sankuai.com for SSO auth.

---

## Parsing Doc IDs from URLs

| URL | Doc ID |
|-----|--------|
| `km.sankuai.com/collabpage/2747985261` | `2747985261` |
| `km.sankuai.com/page/12345678` | `12345678` |

---

## Commands

### search — 搜索文档

```bash
km search "关键词" [--limit 20] [--page 1]
```

- `--limit`: 返回数量（默认 20）
- `--page`: 页码（默认 1）

**示例：**
```bash
km search "API 设计规范" --limit 10
km search "项目文档" --limit 5 --page 2
```

---

### get — 获取文档内容

自动转换为 Markdown 格式返回。doc_id 为位置参数。

```bash
km get DOC_ID [--json]
```

- `--json`: 返回完整 ProseMirror JSON（原始结构，通常比 Markdown 大很多）

**示例：**
```bash
km get 2747985261
```

---

### read-file — 读取嵌入文件/图片

从文档内嵌文件 URL 读取内容（图片、附件等）。URL 为位置参数，从 `km get` 返回的 Markdown 中提取。

```bash
km read-file KM_FILE_URL [--compression 3]
```

- `--compression`: 0（无压缩）~ 3（最高压缩，默认 3）

---

### create — 创建文档

```bash
# 内联内容
km create --title "文档标题" --content "# 标题\n\n正文" --parent PARENT_ID

# 从文件读取（适合长内容）
cat > /tmp/km_content.md << 'KMEOF'
# 文档标题

正文内容...
KMEOF
km create --title "文档标题" --file /tmp/km_content.md --parent PARENT_ID
rm -f /tmp/km_content.md
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `--title` | 标题（最多 100 字符） | 是 |
| `--content` | 内联 Markdown 内容 | 二选一 |
| `--file` | Markdown 文件路径 | 二选一 |
| `--parent` | 父文档 ID | 推荐 |
| `--space` | 空间 ID（根级文档时用） | 与 parent 二选一 |

**支持的 Markdown 元素：** 标题、列表、表格、代码块、加粗/斜体、任务列表、数学公式 `$$...$$`、图片 `![alt](file://path.png)`

---

### copy — 复制文档

from_id 为位置参数（源文档 ID）。

```bash
km copy FROM_ID [--title "新标题"] [--parent TARGET_PARENT_ID] [--space TARGET_SPACE_ID]
```

- `--title` / `-t`: 副本标题（默认 "Copy of Document"）
- `--parent`: 目标父文档 ID
- `--space`: 目标空间 ID（跨空间复制时使用）

---

### hierarchy-info — 文档结构信息

获取指定文档的同级文档和子文档，以及空间结构。

```bash
km hierarchy-info --doc-id DOC_ID   # 查看某文档的邻近树
km hierarchy-info --space-id SPACE_ID  # 查看整个空间树
km hierarchy-info                    # 默认显示个人空间树
```

常用于：确认访问权限、了解文档树结构、获取子文档 ID 列表。

---

### move — 移动文档

doc_id 为位置参数。

```bash
km move DOC_ID --parent TARGET_PARENT_ID [--space TARGET_SPACE_ID]
```

- `--parent`: 目标父文档 ID
- `--space`: 目标空间 ID（跨空间移动时使用）

---

### delete — 删除文档（软删除）

文档移入回收站，可恢复。doc_id 为位置参数。

```bash
km delete DOC_ID
```

---

### restore — 从回收站恢复文档

doc_id 为位置参数。

```bash
km restore DOC_ID
```

---

## Common Workflows

### 查找并读取文档

```bash
# 1. 搜索
km search "需求文档" --limit 5
# 2. 获取内容（用搜索结果中的 doc_id）
km get FOUND_ID
```

### 创建文档层级

```bash
# 创建父目录
km create --title "项目文档" --content "" --parent 2747985261
# 用返回的 ID 创建子文档
km create --title "需求文档" --content "# 需求文档" --parent NEW_ID
km create --title "技术方案" --content "# 技术方案" --parent NEW_ID
```

### 复制并移动到新位置

```bash
# 复制文档
km copy 123456 --title "文档副本" --parent TARGET_PARENT_ID
# 或直接移动
km move 123456 --parent TARGET_PARENT_ID
```

### 查看空间结构再操作

```bash
# 先查看结构
km hierarchy-info --doc-id SPACE_ROOT_ID
# 确认结构后再创建/移动
```

---

## Troubleshooting

For auth errors (401), permission errors (403), or other issues, see [references/TROUBLESHOOTING.md](references/TROUBLESHOOTING.md).

**Quick fixes:**
- Auth error → open https://km.sankuai.com in Chrome and log in
- Permission error → verify "添加" permission on parent doc
- `km` not found → `source ~/.meituan-local-tools/.venv/bin/activate`

