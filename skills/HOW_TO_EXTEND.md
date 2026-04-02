# 如何扩展新的采集 Skill

## 快速创建步骤

### 1. 创建 Skill 目录
```bash
mkdir skills/xhs-{类型}-collector
cd skills/xhs-{类型}-collector
```

### 2. 创建 SKILL.md
```bash
cat > SKILL.md << 'SKILL'
# XHS {类型} Collector Skill

## 功能
{类型}素材收集

## 关键词
{关键词1},{关键词2},{关键词3}

## 使用
./collect.sh

## 输出
shared/content-assets/{类型}/pending/
SKILL
```

### 3. 创建 collect.sh (复制模板修改)
```bash
cp ../xhs-face-collector/collect.sh ./collect.sh
```

修改以下部分：
```bash
# 第1处: 输出目录
OUTPUT_DIR="$SCRIPT_DIR/../../shared/content-assets/{类型}/pending"

# 第2处: 关键词
KEYWORDS="关键词1,关键词2,关键词3"

# 第3处: 日志标识
echo "🎯 XHS {类型} Collector"
audit_log "CRON_TRIGGERED" "{类型}采集Cron触发"
echo "✅ {类型}素材: {filtered} 条"
```

### 4. 添加执行权限
```bash
chmod +x collect.sh
```

### 5. 创建 OpenClaw Cron 任务
```bash
openclaw cron add \
  --name "daily-{类型}-workflow" \
  --cron "0 {时间} * * *" \
  --message "执行每日{类型}素材采集" \
  --timeout-seconds 1800
```

### 6. 添加到每日工作流 (可选)
在 `orchestrator_tasks/daily_workflow.sh` 中添加:
```bash
# 步骤X: {类型}采集
echo "[$(date)] 步骤X: 采集{类型}素材"
cd "$WORKSPACE/skills/xhs-{类型}-collector"
./collect.sh
```

## 完整示例

### 示例: 创建穿搭素材采集 Skill

```bash
# 1. 创建目录
mkdir -p ~/.openclaw/workspace/skills/xhs-fashion-collector
cd ~/.openclaw/workspace/skills/xhs-fashion-collector

# 2. 复制并修改 collect.sh
cp ../xhs-face-collector/collect.sh ./collect.sh

# 修改 collect.sh:
# OUTPUT_DIR=".../fashion/pending"
# KEYWORDS="穿搭,ootd,韩系穿搭,日常穿搭,纯欲穿搭"
# echo "👗 XHS Fashion Collector"

# 3. 创建 SKILL.md
cat > SKILL.md << 'SKILL'
# XHS Fashion Collector
## 功能
穿搭素材收集
## 关键词
穿搭,ootd,韩系穿搭,日常穿搭
## 使用
./collect.sh
SKILL

# 4. 添加权限
chmod +x collect.sh

# 5. 创建 Cron (可选)
# openclaw cron add ...
```

## 输出规范

所有采集 Skill 统一输出到:
```
shared/content-assets/
├── face/pending/      # 颜值
├── nail/pending/      # 美甲
├── fashion/pending/   # 穿搭 (新)
├── food/pending/      # 美食 (新)
└── {类型}/pending/    # 其他类型
```

## 命名规范

| 类型 | Skill目录名 | 关键词示例 |
|------|------------|-----------|
| 颜值 | xhs-face-collector | 甜妹,纯欲,自拍 |
| 美甲 | xhs-nail-collector | 美甲,穿戴甲 |
| 穿搭 | xhs-fashion-collector | 穿搭,ootd,韩系 |
| 美食 | xhs-food-collector | 美食,探店,甜品 |
| 风景 | xhs-scenery-collector | 风景,旅行,摄影 |
| 家居 | xhs-home-collector | 家居,装修,收纳 |

## 关键词选择建议

1. **核心词**: 直接描述类型 (美甲/穿搭/美食)
2. **风格词**: 纯欲/韩系/ins风
3.场景词: 日常/约会/通勤
4. **动作词**: 分享/推荐/合集

## 后处理流程

采集完成后可接入的后处理 (OpenClaw调度):

```
collect.sh (采集)
    ↓
[可选后处理] (通过OpenClaw Agent)
    ↓
yolo_filter.py (YOLO人脸/物体过滤)
    ↓
llm_evaluate.py (大模型质量评分)
    ↓
duplicate_check.py (重复检测)
    ↓
save_to_pending/ (保存到待审核)
```

## 调试技巧

```bash
# 1. 测试采集
./collect.sh

# 2. 检查输出
ls shared/content-assets/{类型}/pending/$(date +%Y-%m-%d)/

# 3. 查看日志
tail -f shared/logs/cron/{类型}_$(date +%Y%m%d).log

# 4. 检查元数据
cat shared/content-assets/{类型}/pending/.../metadata.json | jq
```

## 常见问题

**Q: 采集失败怎么办?**
- 检查 MediaCrawler 是否已登录
- 查看日志文件
- 检查网络连接

**Q: 如何修改筛选条件?**
- 编辑 collect.sh 中的筛选参数
- MIN_LIKES: 最小点赞数
- TIME_RANGE: 时间范围(天)

**Q: 如何添加去重?**
- 参考 xhs-face-collector 的实现
- 使用 collected_ids.txt 记录已采集

## 扩展清单

- [x] 颜值采集 (xhs-face-collector)
- [x] 美甲采集 (xhs-nail-collector)
- [ ] 穿搭采集 (待创建)
- [ ] 美食采集 (待创建)
- [ ] 风景采集 (待创建)
- [ ] 家居采集 (待创建)
