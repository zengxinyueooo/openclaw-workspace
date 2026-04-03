# 审核页部署说明

## 两个部分

### 1. 前端文件（持久化）
- **持久化目录**：`/mnt/openclaw/mcn-review/`
- **源目录**：`/root/.openclaw/workspace/tasks/supabase-materials/review/`
- **更新方式**：修改源目录后执行同步
  ```bash
  cp -r /root/.openclaw/workspace/tasks/supabase-materials/review/. /mnt/openclaw/mcn-review/
  ```

### 2. HTTP Server（每次沙箱重启需恢复）
- **启动脚本**：`/root/.openclaw/scripts/start-review-server.sh`
- **服务端口**：8080
- **访问地址**：`http://<沙箱IP>:8080/`
- **自动恢复**：cron job `review-server-watchdog` 每天 7:00 自动检查并拉起

## 重启后恢复流程

沙箱重启后：
1. cron 每天 7:00 自动执行检查，无需手动操作
2. 如需立即恢复，手动执行：
   ```bash
   bash /root/.openclaw/scripts/start-review-server.sh
   ```

## 审核页地址

| 页面 | 地址 |
|------|------|
| 素材审核 | `http://<IP>:8080/index.html` |
| 生图审核 | `http://<IP>:8080/image-select.html` |
| 草稿审核 | `http://<IP>:8080/draft-review.html` |
| 数据看板 | `http://<IP>:8080/dashboard.html` |

> 沙箱 IP 每次重启会变，查询方式：`ip addr show eth0 | grep 'inet '`

## nginx 备用方案（当前未启用）
- 配置备份：`/mnt/openclaw/nginx-review.conf`
- 当前因无 `/etc/nginx/` 写权限，用 Python HTTP server 替代
- 如未来获得权限，可将配置 link 到 `sites-enabled/` 并 reload nginx
