# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 设备连接说明

### 手机
- 用户提到的"已连接手机"是指通过 USB 连接到本电脑上的手机
- 需要通过 ADB 或其他方式进行控制和操作

### 素材采集（松鼠🐿️）
- **方案**：Playwright + CDP（连接已登录Chrome）
- **不使用 MediaCrawler**（已废弃）
- **Skill 位置**：`~/.openclaw/skills/xhs-scraper/`
- **入口**：`pipeline.py` → `XhsPipeline.collect(task_type)` 或 `run_pipeline(task_type)`
- **前提**：Chrome 带 `--remote-debugging-port=9222` 启动且已登录小红书
- **流程**：搜索 → 提取图片 → 下载 → YOLO检测 → 转jpg → 上传Venus → 入库Supabase(pending)
- **face策略**：只取封面图（不进详情页，防封控），YOLO只留单人脸
- **nail策略**：进详情页取多张，有人脸→nail-face库，无人脸→nail库
- **不在本地存图**：图片临时下载到/tmp，上传Venus后删除，素材管理全在Supabase

### 图片上传
- 公司内部图片上传（需内网）: `skills/image-upload/upload.sh <path>`
  - 返回公网 URL，可用于内部系统
- ~~Supabase Storage~~（已弃用）→ 全部走 Venus

---

### ⚠️ 铁律：所有图片必须通过 Venus 上传
- **所有素材图片的 URL 必须是美团内网 Venus 地址**（`img.meituan.net`）
- Supabase Storage、外部图床等 URL 后端生图模型无法访问
- 上传入口：`skills/image-upload/upload.sh <path>`
- 上传前必须转成 `.jpg` 格式（禁止 webp），Venus 根据上传文件格式返回对应后缀
- 入库脚本、SDK、任何涉及 image_url 的地方都必须走 Venus

### 图片上传（美团内部）
- **用途**：把本地图片上传获取公网 URL（替代 Supabase Storage）
- **Skill 位置**：`skills/image-upload/`
- **接口**：`POST https://mdz.dzu.test.sankuai.com/api/dzusergrowth/assistant/image/gen/upload`
- **Header**：`swimlane: 3792-tsgru`
- **Body**：`multipart/form-data`，字段名 `file`
- **要求**：需连接美团内网
- **快捷脚本**：`skills/image-upload/upload.sh /path/to/image.png`
- **返回**：`{"code":0,"data":{"url":"https://..."}}`
- **适用场景**：素材图片上传后存 URL 到 Supabase materials 表，国内无需 VPN 即可访问

### WebStatic（主力，美团内网）

| 页面 | URL |
|------|-----|
| 素材审核 | https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/index.html |
| 素材池 | https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/materials-pool.html |
| 生图审核 | https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/image-select.html |
| 草稿审核 | https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/draft-review.html |
| 数据看板 | https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/dashboard.html |
| 需求追踪 | https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/requirement.html |
| 生图统计 | https://mss.vip.sankuai.com/static-prod01/com.sankuai.dzfe3.opxaimanage/gen-stats.html |

- **部署命令**（在 `tasks/supabase-materials/review/` 目录下执行）：
  ```bash
  webstatic deploy --appkey=com.sankuai.dzfe3.opxaimanage --artifact=. --env=prod --token=b70bdb0e-606d-46d3-9900-1a857f9cf1a2
  ```
- **Token**：`b70bdb0e-606d-46d3-9900-1a857f9cf1a2`（Deploy Token，仅限本项目）
- **控制台**：https://webstatic.mws.sankuai.com/project/com.sankuai.dzfe3.opxaimanage
- **部署流程**：改文件（`tasks/supabase-materials/review/`）→ 跑 deploy 命令，完成
- **不再使用**：Vercel、Netlify、本地 8080 server

### Vercel / Netlify（已废弃）

- Vercel token 在 `.env.supabase` 中 `VERCEL_TOKEN`，不再使用
- Netlify 额度已满，不再使用

---

### 云真机/云测服务

- **服务名**：com.sankuai.device（美团 Conan Device Control）
- **启动命令**：`sudo sh /opt/meituan/conan-device-control/run.sh`
- **sudo 密码**：458458
- **运行在**：本机（MacBook）
- **配置**：prod 环境，provider=lipengyu04_1，STF+DC 启用
- **日志**：dc.file（在 /opt/meituan/conan-device-control/ 目录下）

---

Add whatever helps you do your job. This is your cheat sheet.

