# 小红书矩阵 Skill 架构

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    XHS Skill 生态                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌─────────────┐    ┌─────────────────────────────┐   │
│   │  XHS Core   │◄───┤      MediaCrawler Core      │   │
│   │   (共享库)   │    │      (采集引擎)              │   │
│   └──────┬──────┘    └─────────────────────────────┘   │
│          │                                              │
│          ▼                                              │
│   ┌─────────────┬─────────────┬─────────────────┐      │
│   │             │             │                 │      │
│   ▼             ▼             ▼                 ▼      │
│ ┌──────┐    ┌──────┐    ┌──────────┐    ┌──────────┐ │
│ │ Face │    │ Nail │    │ Comment  │    │  Topic   │ │
│ │颜值  │    │美甲  │    │ 评论搜索  │    │ 选题研究  │ │
│ └──────┘    └──────┘    └──────────┘    └──────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Skill 列表

| Skill | 功能 | 关键词 | 输出 |
|-------|------|--------|------|
| **xhs-face-collector** | 颜值素材收集 | 甜妹、纯欲风、韩系美女 | 图片+元数据 |
| **xhs-nail-collector** | 美甲素材收集 | 美甲、穿戴甲、仙女美甲 | 图片+元数据 |
| **xhs-comment-searcher** | 评论采集分析 | 指定笔记ID | 评论+情感分析 |
| **xhs-topic-researcher** | 选题研究 | 发现低粉爆款 | 选题建议 |

## 依赖关系

```
All Skills
    └── depend on: MediaCrawler Core
                   └── config/base_config.py
                   └── data/xhs/
```

## 使用示例

### 1. 颜值素材采集
```bash
cd skills/xhs-face-collector
./collect.sh
# 输出: data/2026-03-03/{metadata.json, images/}
```

### 2. 美甲素材采集
```bash
cd skills/xhs-nail-collector
./collect.sh
# 输出: data/2026-03-03/{metadata.json, images/}
```

### 3. 评论采集（待完善）
```bash
cd skills/xhs-comment-searcher
./search_comments.sh --note-id <id>
# 输出: data/2026-03-03/comments.json
```

### 4. 选题研究（待完善）
```bash
cd skills/xhs-topic-researcher
./find_viral.sh --keyword "氛围感拍照"
# 输出: data/2026-03-03/viral_notes.json
```

## 数据隔离

每个 Skill 有自己的 data/ 目录，互不干扰：

```
skills/
├── xhs-face-collector/data/2026-03-03/
├── xhs-nail-collector/data/2026-03-03/
├── xhs-comment-searcher/data/2026-03-03/
└── xhs-topic-researcher/data/2026-03-03/
```

## 统一配置

所有 Skill 共享 MediaCrawler 的：
- 登录状态 (browser_data/)
- 采集间隔 (3秒)
- 反封策略

但各自有独立的：
- 关键词配置
- 筛选规则
- 输出目录
