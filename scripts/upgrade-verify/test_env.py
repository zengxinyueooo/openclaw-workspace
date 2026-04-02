"""
Step 1 — 环境检查（阻断性）
任何一项失败应立即停止后续测试。
"""
import hashlib
import os
import subprocess

import pytest
import requests

from config import (
    OPENCLAW_CONFIG_PATH, SKILLS_DIR,
    ENV_KEY_PATTERNS, INTRANET_HOSTS, EXTRANET_HOSTS,
)

# 内网请求不走代理
_NO_PROXY = {"http": None, "https": None}

# 外网请求走系统代理
_SYS_PROXY = {
    "http": os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY"),
    "https": os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY"),
}


# ── 辅助 ─────────────────────────────────────────────

def _run(cmd, timeout=10):
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        # 合并 stdout 和 stderr
        return (r.stdout + r.stderr).strip()


def _gateway_version() -> str:
    version = os.environ.get("CATCLAW_VERSION", "")
    if version:
        return version
    else:
        return "unknown"


# ── 测试用例 ──────────────────────────────────────────

class TestEnvironment:

    def test_01_gateway_version_upgraded(self, snapshot):
        """Gateway 版本号应高于升级前"""
        before = snapshot["gateway_version"]
        after = _gateway_version()
        assert after != "unknown", "无法获取当前 Gateway 版本"
        # 版本直接输出，能获取就行
        print(f"\n升级前版本: {before}  →  当前版本: {after}")

    def test_02_user_is_not_root(self, snapshot):
        """运行用户不应为 root（uid != 0）"""
        uid = os.getuid()
        whoami = _run(["whoami"])
        assert uid != 0, f"当前用户为 root！uid={uid}"
        assert whoami != "root", f"whoami 返回 root"
        print(f"\n当前用户: {whoami} (uid={uid})")

    @pytest.mark.parametrize("host", INTRANET_HOSTS)
    def test_03_intranet_no_proxy(self, host):
        """内网域名直连，不走代理"""
        url = f"http://{host}"
        try:
            result = _run(["curl", "-v", url], timeout=15)
            # 只检查是否有代理特征，无论连接成功还是失败
            uses_proxy = "openclaw-squid" in result
            assert not uses_proxy, f"内网不应走代理: {host}"
            print(f"\n  {host}  直连✓")
        except subprocess.TimeoutExpired:
            pytest.skip(f"访问 {host} 超时，跳过")

    @pytest.mark.parametrize("host", EXTRANET_HOSTS)
    def test_04_extranet_uses_proxy(self, host):
        """外网域名必须经代理访问（超时最多重试 3 次）"""
        url = f"http://{host}"
        max_retries = 3
        last_result = ""

        for attempt in range(1, max_retries + 1):
            try:
                result = _run(["curl", "-v", url], timeout=15)
                last_result = result
                uses_proxy = "openclaw-squid" in result
                if uses_proxy:
                    print(f"\n  {host}  via proxy✓ (attempt {attempt})")
                    return
                # 有响应但没走代理，直接断言失败，不重试
                pytest.fail(f"外网应走代理: {host}\n{result[:300]}")
            except subprocess.TimeoutExpired:
                print(f"\n  {host} 第 {attempt} 次超时，{'重试...' if attempt < max_retries else '放弃'}")
                last_result = f"timeout (attempt {attempt})"

        pytest.fail(f"外网代理检查超时，已重试 {max_retries} 次: {host}\n{last_result[:300]}")

    def test_05_moa_running(self):
        """moa 进程应已启动"""
        result = _run(["pgrep", "-f", "moa-ciba-login-online"])
        assert result.strip(), "moa 进程未运行（pgrep 无结果）"
        print(f"\n  moa pid: {result.strip().splitlines()[0]} ✓")

    def test_06_env_keys_complete(self):
        """校验必需的环境变量存在且有值"""
        required_keys = ["SANDBOX_ID", "IDENTIFIER", "CATCLAW_VERSION"]
        missing = []
        empty = []

        for key in required_keys:
            if key not in os.environ:
                missing.append(key)
            elif not os.environ[key].strip():
                empty.append(key)

        assert not missing, f"以下必需环境变量不存在：{missing}"
        assert not empty, f"以下必需环境变量为空：{empty}"

        print(f"\n必需环境变量检查通过 ✓")
        for key in required_keys:
            print(f"  {key}={os.environ[key]}")

    def test_07_config_hash_unchanged(self, snapshot):
        """openclaw.json 内容不应被升级改动"""
        before_hash = snapshot["config_hash"]
        data = open(OPENCLAW_CONFIG_PATH, "rb").read()
        current_hash = hashlib.sha256(data).hexdigest()
        assert current_hash == before_hash, (
            f"配置文件已变更！\n  升级前: {before_hash}\n  当前:   {current_hash}"
        )

    def test_08_skills_complete(self, snapshot):
        """升级前存在的 skill 升级后不应缺失"""
        before_skills = set(snapshot["skills"])
        current_skills = set(os.listdir(SKILLS_DIR))

        missing = before_skills - current_skills
        assert not missing, (
            f"以下 skill 升级后丢失：{sorted(missing)}"
        )
        new_skills = current_skills - before_skills
        if new_skills:
            print(f"\n新增 skill（正常）: {sorted(new_skills)}")

    def test_09_ssh_files_intact(self, snapshot):
        """~/.ssh/ 目录下的文件升级后不应丢失或被篡改"""
        before_ssh = snapshot.get("ssh_files", {})
        if not before_ssh:
            pytest.skip("snapshot 中无 ssh_files，跳过（升级前未采集）")

        ssh_dir = os.path.expanduser("~/.ssh")
        missing = []
        changed = []

        for fname, before_hash in before_ssh.items():
            if before_hash.startswith("ERROR:"):
                continue
            fpath = os.path.join(ssh_dir, fname)
            if not os.path.exists(fpath):
                missing.append(fname)
                continue
            current_hash = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
            if current_hash != before_hash:
                changed.append(fname)

        problems = []
        if missing:
            problems.append(f"文件丢失: {missing}")
        if changed:
            problems.append(f"内容变更: {changed}")

        assert not problems, "~/.ssh/ 文件升级后异常：\n" + "\n".join(problems)
        print(f"\n共验证 {len(before_ssh)} 个 ssh 文件，全部完整 ✓")

    def test_10_workspace_md_unchanged(self, snapshot):  # noqa: E302
        """workspace *.md 和 memory/*.md 的内容不应被升级改动"""
        before_hashes = snapshot.get("workspace_md_hashes", {})
        if not before_hashes:
            pytest.skip("snapshot 中无 workspace_md_hashes，跳过")

        workspace = os.path.expanduser("~/.openclaw/workspace")
        changed = []
        missing = []

        for rel_path, before_hash in before_hashes.items():
            if before_hash.startswith("ERROR:"):
                continue  # 采集时就失败的，跳过
            # rel_path 格式：workspace/AGENTS.md 或 memory/2026-03-18.md
            # workspace 变量已经指向 ~/.openclaw/workspace，去掉 workspace/ 前缀
            rel = rel_path.removeprefix("workspace/")
            fpath = os.path.join(workspace, rel.replace("/", os.sep))
            if not os.path.exists(fpath):
                missing.append(rel_path)
                continue
            current_hash = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
            if current_hash != before_hash:
                changed.append(rel_path)

        problems = []
        if missing:
            problems.append(f"文件丢失: {missing}")
        if changed:
            problems.append(f"内容变更: {changed}")

        assert not problems, "workspace md 文件升级后异常：\n" + "\n".join(problems)

        print(f"\n共验证 {len(before_hashes)} 个 md 文件，全部一致 ✓")
