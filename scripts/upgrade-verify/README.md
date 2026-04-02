# 镜像升级验收自动化

## 目录结构

```
upgrade-verify/
├── config.py          # 共享配置（域名列表、路径、Gateway 参数）
├── snapshot.py        # 升级前采集脚本
├── gateway_client.py  # Gateway /tools/invoke 封装
├── conftest.py        # pytest fixtures
├── test_env.py        # Step1：7 项环境检查
├── test_smoke.py      # Step2：5 项功能冒烟
├── pytest.ini         # pytest 配置（含 html report）
└── snapshot.json      # 升级前采集结果（运行时自动生成）
```

## 使用方法

### 1. 升级前采集

```bash
cd scripts/upgrade-verify
python3 snapshot.py
```

输出 `snapshot.json`，记录基线数据。

### 2. 触发镜像升级

等待 Gateway 重新上线。

### 3. 升级后验收

```bash
cd scripts/upgrade-verify
pytest
```

报告自动生成为 `report.html`（单文件，可直接发送）。

### 快捷方式：环境检查失败立即停止

```bash
pytest --failfast
```

### 只跑环境检查

```bash
pytest test_env.py
```

### 只跑冒烟

```bash
pytest test_smoke.py
```

## 配置说明

编辑 `config.py` 可调整：

- `INTRANET_HOSTS`：内网直连验证域名列表
- `EXTRANET_HOSTS`：外网代理验证域名列表
- `SMOKE_SESSION_KEY`：冒烟消息收发使用的 session
- `ENV_KEY_PATTERNS`：环境变量过滤关键词

## 判断标准

| 结果 | 含义 | 处置 |
|------|------|------|
| 全绿 (passed) | 环境 + 冒烟全过 | 升级完成 |
| 环境检查有 FAILED | 阻断性问题 | 停止，立即排查，优先回滚 |
| 环境全绿，冒烟有 FAILED | 功能问题 | 评估影响，决定是否回滚 |
| 消息收发 FAILED | 核心链路断 | 立即回滚 |
