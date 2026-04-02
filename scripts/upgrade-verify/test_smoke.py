"""
Step 2 — 功能冒烟（环境检查全过后运行）

各用例实现方式：
  - 消息收发：Gateway WS RPC 触发 agent run，轮询 transcript JSONL 等回复
  - exec 工具：沙箱本地 subprocess（exec/write/read 在 HTTP /tools/invoke 默认 deny）
  - 内网访问：沙箱本地 requests 直连
  - 持久化读写：沙箱本地文件 I/O
  - Cron 任务：openclaw cron CLI
  - Gateway API：/tools/invoke sessions_list（只读工具，允许调用）
"""
import json
import os
import subprocess
import time
import uuid

import pytest
import requests

from config import SMOKE_SESSION_KEY, INTRANET_HOSTS, WORKSPACE_DIR, get_gateway_config
from gateway_ws_client import send_agent_message, ping_gateway

_NO_PROXY = {"http": None, "https": None}


def _gw_invoke(tool: str, args: dict = None) -> dict:
    cfg = get_gateway_config()
    r = requests.post(
        f"{cfg['base_url']}/tools/invoke",
        headers=cfg["headers"],
        json={"tool": tool, "args": args or {}},
        proxies=_NO_PROXY,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _run(cmd: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


class TestSmoke:

    def test_01_message_roundtrip(self):
        """
        消息收发：通过 Gateway WS 发消息给 agent，轮询 transcript 等待回复
        验证：大象 channel + 模型链路完整可用
        """
        # assert ping_gateway(), "Gateway WS 连接失败，无法进行消息收发测试"

        probe = f"SMOKE_{uuid.uuid4().hex[:8]}"
        print(f"\n  发送探针: {probe}")

        reply = send_agent_message(
            session_key=SMOKE_SESSION_KEY,
            message=f"[smoke test] 请直接回复以下内容，不做任何其他操作：{probe}",
            deliver=False,
            timeout=180,
            poll_interval=2.0,
        )

        assert reply is not None, f"等待 agent 回复超时（180s），探针={probe}"
        assert probe in reply, (
            f"回复中未包含探针 {probe!r}\n"
            f"实际回复（前 300 字）: {reply[:300]}"
        )
        print(f"  收到回复（含探针）✓")

    def test_02_exec_tool(self):
        """
        exec 工具：沙箱内可执行命令，且为非 root 用户
        验证：exec 工具链完整，权限变更符合预期
        """
        result = _run(["bash", "-c", "echo TEST_OK && id"])
        assert result.returncode == 0, f"命令执行失败: {result.stderr}"
        assert "TEST_OK" in result.stdout, f"输出中无 TEST_OK: {result.stdout}"
        assert "uid=0" not in result.stdout, (
            f"当前用户为 root（uid=0），预期非 root: {result.stdout}"
        )
        print(f"\n  stdout: {result.stdout.strip()}")

    # def test_03_intranet_access(self):
    #     """
    #     内网访问：沙箱内直连内网地址可达
    #     验证：新代理配置下内网请求不经代理
    #     """
    #     host = INTRANET_HOSTS[0]
    #     url = f"http://{host}"
    #     try:
    #         resp = requests.get(
    #             url, proxies=_NO_PROXY, timeout=5, allow_redirects=True
    #         )
    #         assert resp.status_code < 600, f"异常状态码: {resp.status_code}"
    #         elapsed = int(resp.elapsed.total_seconds() * 1000)
    #         print(f"\n  {url}  →  HTTP {resp.status_code}  {elapsed}ms  直连✓")
    #     except requests.exceptions.RequestException as e:
    #         pytest.fail(f"内网直连访问失败 {url}: {e}")

    def test_04_workspace_read_write(self):
        """
        持久化读写：workspace 文件读写一致
        验证：存储挂载正常，数据不丢失
        """
        content = f"SMOKE_RW_{uuid.uuid4().hex}"
        path = os.path.join(WORKSPACE_DIR, ".smoke_rw_test.txt")
        try:
            # 写入
            with open(path, "w") as f:
                f.write(content)
            # 读回
            with open(path) as f:
                read_back = f.read()
            assert read_back == content, (
                f"读写内容不一致\n  写入: {content}\n  读回: {read_back}"
            )
            print(f"\n  写入并读回一致 ✓  path={path}")
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def test_05_cron_mechanism(self):
        """
        Cron 任务：检查定时任务配置目录
        验证：调度配置正常存在
        """
        cron_dir = os.path.expanduser("~/.openclaw/cron")
        if os.path.isdir(cron_dir):
            cron_files = os.listdir(cron_dir)
            print(f"\n  cron 配置目录存在，包含 {len(cron_files)} 个文件 ✓")
        else:
            pytest.skip("cron 配置目录不存在（正常）")

    def test_06_gateway_sessions_api(self):
        """
        Gateway HTTP API：/tools/invoke 可正常调用
        验证：Gateway 启动且 API 路由正常
        """
        r = _gw_invoke("sessions_list", {"limit": 5})
        assert r.get("ok"), f"sessions_list 失败: {r}"
        details = r["result"].get("details", {})
        assert "sessions" in details, f"返回结构异常: {details}"
        count = details.get("count", "?")
        print(f"\n  sessions 数量: {count}")

    # def test_07_agent_browser_and_news(self):
    #     """
    #     浏览器工具调用：发消息给 agent，让其打开百度查询最热 3 条新闻并返回
    #     验证：agent 能调用浏览器工具、能访问外网、能正常返回结构化内容
    #     """
    #     assert ping_gateway(), "Gateway WS 连接失败，无法进行消息收发测试"
    #
    #     reply = send_agent_message(
    #         session_key=SMOKE_SESSION_KEY,
    #         message=(
    #             "[smoke test] 请用浏览器打开 https://www.baidu.com，"
    #             "查询当前最热的 3 条新闻标题，以如下格式返回，不要其他内容：\n"
    #             "1. <标题1>\n2. <标题2>\n3. <标题3>"
    #         ),
    #         deliver=False,
    #         timeout=180,
    #         poll_interval=3.0,
    #     )
    #
    #     assert reply is not None, "等待 agent 回复超时（180s）"
    #
    #     # 校验：返回内容包含至少 3 条编号条目
    #     lines = [l.strip() for l in reply.splitlines() if l.strip()]
    #     numbered = [l for l in lines if l[:2] in ("1.", "2.", "3.")]
    #     assert len(numbered) >= 3, (
    #         f"返回内容未包含 3 条新闻标题（numbered={numbered}）\n"
    #         f"实际回复（前 500 字）: {reply[:500]}"
    #     )
    #     print(f"\n  Agent 返回新闻标题：")
    #     for item in numbered:
    #         print(f"    {item}")
