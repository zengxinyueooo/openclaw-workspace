import json
import os
import subprocess
import sys
import html as _html
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from config import SNAPSHOT_PATH

RESULT_JSON_PATH = Path(__file__).parent / "result.json"


@pytest.fixture(scope="session")
def snapshot() -> dict:
    if not os.path.exists(SNAPSHOT_PATH):
        pytest.skip(f"snapshot.json not found: {SNAPSHOT_PATH}. Run snapshot.py first.")
    with open(SNAPSHOT_PATH) as f:
        return json.load(f)


def pytest_configure(config):
    try:
        gw_ver = subprocess.check_output(
            ["openclaw", "--version"], text=True, timeout=5
        ).strip().split()[-1]
    except Exception:
        gw_ver = "unknown"
    config._metadata = getattr(config, "_metadata", {})
    config._metadata["测试时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    config._metadata["Gateway 版本（当前）"] = gw_ver
    config._metadata["运行用户"] = os.popen("id").read().strip()
    config._metadata["主机名"] = os.uname().nodename
    if os.path.exists(SNAPSHOT_PATH):
        try:
            with open(SNAPSHOT_PATH) as f:
                snap = json.load(f)
            config._metadata["Gateway 版本（升级前）"] = snap.get("gateway_version", "未知")
            config._metadata["基线采集时间"] = snap.get("collected_at", "未知")
        except Exception:
            pass


def pytest_html_report_title(report):
    report.title = "镜像升级验收测试报告"


def _block_html(title, content, color):
    # content 做 escape（防 XSS），外层 div/pre 是我们可信的 HTML 骨架
    esc = _html.escape(str(content))
    return (
        f'<div style="margin:6px 0 10px 0;font-family:monospace">'
        f'<div style="font-weight:bold;color:{color};margin-bottom:4px">{title}</div>'
        f'<pre style="background:#f8f8f8;border-left:3px solid {color};padding:8px 12px;'
        f'border-radius:3px;font-size:12px;white-space:pre-wrap;word-break:break-all;'
        f'max-height:350px;overflow:auto;margin:0">{esc}</pre></div>'
    )


# pytest-html v4 正确做法：
# - log 字段走 Jinja2 auto-escape，放 HTML 会变成 &lt;div&gt;，JS 渲染成文本 ❌
# - extras 字段由 _process_extras() 单独处理，FORMAT_HTML 不会被 escape，JS 用 innerHTML 渲染 ✅
# - plugin.py 的 pytest_runtest_makereport 是 tryfirst=True，会合并 report.extras
#   我们用 tryfirst=True + hookwrapper 在它之前把 extras 写好
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    from pytest_html import extras as html_extras
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    new_extras = []

    if report.passed:
        stdout = (getattr(report, "capstdout", "") or "").strip()
        if stdout:
            new_extras.append(html_extras.html(_block_html("✅ 执行输出", stdout, "#2e7d32")))

    if report.failed:
        longrepr = str(getattr(report, "longrepr", "") or "").strip()
        if longrepr:
            new_extras.append(html_extras.html(_block_html("❌ 失败详情", longrepr, "#c62828")))
        stdout = (getattr(report, "capstdout", "") or "").strip()
        if stdout:
            new_extras.append(html_extras.html(_block_html("📋 用例输出", stdout, "#e65100")))

    if new_extras:
        # 追加到已有 extras 前面（plugin.py 后续会再 merge，所以这里直接赋值）
        existing = getattr(report, "extras", [])
        report.extras = new_extras + existing

    # 收集结果到 item stash，供 pytest_sessionfinish 汇总
    entry = {
        "name": report.nodeid,
        "result": "passed" if report.passed else "failed" if report.failed else "skipped",
    }
    if report.failed:
        longrepr = str(getattr(report, "longrepr", "") or "").strip()
        # 只提取断言信息（AssertionError 后的内容）
        if "AssertionError" in longrepr:
            detail = longrepr.split("AssertionError:")[-1].strip()
        else:
            detail = longrepr.split("\n")[-1].strip()  # 取最后一行
        if detail:
            entry["detail"] = detail
    item.stash.setdefault("result_entry", entry)


def pytest_sessionfinish(session, exitstatus):
    """所有用例跑完后，把结果汇总写入 result.json"""
    entries = []
    for item in session.items:
        entry = item.stash.get("result_entry", None)
        if entry:
            entries.append(entry)
        else:
            # 用例被 skip 或未执行
            entries.append({"name": item.nodeid, "result": "skipped"})

    output = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(entries),
        "passed": sum(1 for e in entries if e["result"] == "passed"),
        "failed": sum(1 for e in entries if e["result"] == "failed"),
        "skipped": sum(1 for e in entries if e["result"] == "skipped"),
        "cases": entries,
    }

    with open(RESULT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n结果已写入: {RESULT_JSON_PATH}")