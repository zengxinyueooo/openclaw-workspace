#!/usr/bin/env python3
"""
升级前采集脚本
运行：python3 snapshot.py
输出：snapshot.json（供升级后 pytest 对比使用）
"""
import hashlib
import json
import os
import subprocess
import sys
import time

import requests

# 把当前目录加入 path，方便 import config
sys.path.insert(0, os.path.dirname(__file__))
from config import (
    OPENCLAW_CONFIG_PATH, SKILLS_DIR, SNAPSHOT_PATH,
    ENV_KEY_PATTERNS, INTRANET_HOSTS, get_gateway_config,
)


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def collect_config_hash() -> str:
    try:
        data = open(OPENCLAW_CONFIG_PATH, "rb").read()
        return hashlib.sha256(data).hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def collect_skills() -> list[str]:
    try:
        return sorted(os.listdir(SKILLS_DIR))
    except Exception as e:
        return [f"ERROR: {e}"]


def collect_env_keys() -> list[str]:
    keys = []
    for k in os.environ:
        kl = k.lower()
        if any(p in kl for p in ENV_KEY_PATTERNS):
            keys.append(k)
    return sorted(keys)


def collect_user() -> dict:
    return {
        "uid": os.getuid(),
        "gid": os.getgid(),
        "whoami": _run(["whoami"]),
        "id": _run(["id"]),
    }


def collect_intranet() -> dict:
    # results = {}
    # for host in INTRANET_HOSTS:
    #     url = f"http://{host}"
    #     try:
    #         resp = requests.get(
    #             url, proxies={"http": None, "https": None},
    #             timeout=5, allow_redirects=True
    #         )
    #         results[host] = {
    #             "status": resp.status_code,
    #             "elapsed_ms": int(resp.elapsed.total_seconds() * 1000),
    #             "reachable": True,
    #         }
    #     except Exception as e:
    #         results[host] = {"reachable": False, "error": str(e)}
    ## 跳过老镜像采集
    return {}


def collect_workspace_md_hashes() -> dict:
    """采集 workspace 根目录 *.md 和 memory/*.md 的文件 hash"""
    workspace = os.path.expanduser("~/.openclaw/workspace")
    result = {}

    # workspace/*.md
    for fname in sorted(os.listdir(workspace)):
        if fname.endswith(".md"):
            fpath = os.path.join(workspace, fname)
            try:
                data = open(fpath, "rb").read()
                result[f"workspace/{fname}"] = hashlib.sha256(data).hexdigest()
            except Exception as e:
                result[f"workspace/{fname}"] = f"ERROR: {e}"

    # workspace/memory/*.md
    memory_dir = os.path.join(workspace, "memory")
    if os.path.isdir(memory_dir):
        for fname in sorted(os.listdir(memory_dir)):
            if fname.endswith(".md"):
                fpath = os.path.join(memory_dir, fname)
                try:
                    data = open(fpath, "rb").read()
                    result[f"memory/{fname}"] = hashlib.sha256(data).hexdigest()
                except Exception as e:
                    result[f"memory/{fname}"] = f"ERROR: {e}"

    return result


def collect_ssh_files() -> dict:
    """采集 ~/.ssh/ 目录下所有文件的 hash（私钥只记录 hash，不记录内容）"""
    ssh_dir = os.path.expanduser("~/.ssh")
    result = {}
    if not os.path.isdir(ssh_dir):
        return result
    for fname in sorted(os.listdir(ssh_dir)):
        fpath = os.path.join(ssh_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            data = open(fpath, "rb").read()
            result[fname] = hashlib.sha256(data).hexdigest()
        except Exception as e:
            result[fname] = f"ERROR: {e}"
    return result


def collect_gateway_version() -> str:
    version = os.environ.get("CATCLAW_VERSION", "")
    if version:
        return version
    # 降级方案：如果环境变量不存在，尝试 openclaw 命令
    try:
        out = _run(["openclaw", "--version"])
        for part in out.split():
            if part[0].isdigit():
                return part
    except Exception:
        pass
    return "unknown"


def main():
    print("📸 升级前采集开始...")

    workspace_md_hashes = collect_workspace_md_hashes()

    ssh_files = collect_ssh_files()

    snapshot = {
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "collected_ts": int(time.time()),
        "config_hash": collect_config_hash(),
        "skills": collect_skills(),
        "env_keys": collect_env_keys(),
        "user": collect_user(),
        "intranet": collect_intranet(),
        "gateway_version": collect_gateway_version(),
        "workspace_md_hashes": workspace_md_hashes,
        "ssh_files": ssh_files,
    }

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"✅ 采集完成，结果保存至：{SNAPSHOT_PATH}")
    print()
    print(f"  config_hash    : {snapshot['config_hash'][:16]}...")
    print(f"  skills 数量    : {len(snapshot['skills'])}")
    print(f"  env_keys 数量  : {len(snapshot['env_keys'])}")
    print(f"  user           : {snapshot['user']['whoami']} (uid={snapshot['user']['uid']})")
    print(f"  gateway_version: {snapshot['gateway_version']}")
    print(f"  workspace md   : {len(workspace_md_hashes)} 个文件")
    print(f"  ssh files      : {len(ssh_files)} 个文件（{', '.join(ssh_files.keys()) or '空'}）")
    print()

    reachable = sum(1 for v in snapshot["intranet"].values() if v.get("reachable"))
    print(f"  内网连通       : {reachable}/{len(snapshot['intranet'])} 可达")
    for host, info in snapshot["intranet"].items():
        if info.get("reachable"):
            print(f"    ✓ {host}  {info['status']}  {info['elapsed_ms']}ms")
        else:
            print(f"    ✗ {host}  {info.get('error','')}")

    print()
    print("升级完成后运行：")
    print("  cd scripts/upgrade-verify && pytest --html=report.html --self-contained-html -v")


if __name__ == "__main__":
    main()
