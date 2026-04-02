#!/usr/bin/env python3
"""
用于执行完之后上传测试报告到S3
"""
import re
import subprocess
import sys
import os
import tempfile
from pathlib import Path

SKILL_SCRIPT = "./scripts/upload_to_s3plus.py"
ENV = "prod-corp"


def upload(path, object_name, content_type):
    cmd = [
        "python3", SKILL_SCRIPT,
        "--file", str(path),
        "--object-name", object_name,
        "--env", ENV,
        "--no-uuid-prefix",
        "--content-type", content_type,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Upload failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    report_path = Path(__file__).parent / "report.html"
    if not report_path.exists():
        print(f"report.html not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    html = report_path.read_text(encoding="utf-8")

    # inline <script>...</script>
    script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
    if not script_match:
        print("No inline script found, uploading as-is", file=sys.stderr)
        url = upload(report_path, f"upgrade-verify-report-{ts}.html", "text/html; charset=utf-8")
        print(url)
        return

    script_content = script_match.group(1)
    js_object_name = f"upgrade-verify-app-{ts}.js"

    with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False, encoding="utf-8") as f:
        f.write(script_content)
        js_tmp = f.name

    js_url = upload(js_tmp, js_object_name, "application/javascript; charset=utf-8")
    os.unlink(js_tmp)

    new_html = html.replace(
        script_match.group(0),
        f'<script src="{js_url}"></script>'
    )

    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False, encoding="utf-8") as f:
        f.write(new_html)
        html_tmp = f.name

    html_url = upload(html_tmp, f"upgrade-verify-report-{ts}.html", "text/html; charset=utf-8")
    os.unlink(html_tmp)

    print(html_url)


if __name__ == "__main__":
    main()
