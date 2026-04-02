#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pack and Upload Script
Pack the entire project into a tar.gz file and upload to S3Plus.
Package name is fixed as: 9527testimageupgrade.tar.gz
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# 导入现有的上传模块
sys.path.insert(0, str(Path(__file__).parent))
from upload_to_s3plus import (
    DEFAULT_ACCESS_KEY,
    DEFAULT_ACCESS_SECRET,
    DEFAULT_BUCKET,
    DEFAULT_HOST,
    build_authorization,
    build_string_to_sign,
    calculate_content_md5,
    gmttime,
)

import requests

# 固定包名
PACKAGE_NAME = "9527testimageupgrade.tar.gz"


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.resolve()


def pack_project(project_root, output_path):
    """
    打包整个项目为 tar.gz 文件
    排除 .git、__pycache__、.pyc 等文件
    """
    # 需要排除的目录和文件
    exclude_patterns = [
        "--exclude=.git",
        "--exclude=__pycache__",
        "--exclude=*.pyc",
        "--exclude=.pytest_cache",
        "--exclude=.idea",
        "--exclude=.vscode",
        "--exclude=*.egg-info",
        "--exclude=.DS_Store",
        "--exclude=*.html",
        "--exclude=*.json",
        f"--exclude={PACKAGE_NAME}",  # 排除已有的打包文件
    ]

    # 在项目父目录创建压缩包，避免路径嵌套
    cmd = [
        "tar",
        "-czvf",
        str(output_path),
        *exclude_patterns,
        "-C",
        str(project_root.parent),
        project_root.name,
    ]

    print(f"Packing project: {project_root}")
    print(f"Output: {output_path}")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Pack failed: {result.stderr}", file=sys.stderr)
        raise RuntimeError(f"Failed to pack project: {result.stderr}")

    print(f"Pack completed: {output_path}")
    return output_path


def upload_to_s3(
    file_path,
    object_name,
    access_key,
    access_secret,
    bucket,
    host,
    timeout=300,  # 大文件上传，默认超时5分钟
):
    """上传文件到 S3Plus"""
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 构建对象名称（固定名称，不使用 UUID 前缀）
    object_name = object_name.lstrip("/")

    # 构建 URL 和资源路径
    url = f"https://{host}/{bucket}/{object_name}"
    canonicalized_resource = f"/{bucket}/{object_name}"

    # 计算 Content-MD5
    print(f"Calculating MD5 for {file_path}...", file=sys.stderr)
    content_md5 = calculate_content_md5(file_path)

    # 生成时间戳
    date = gmttime()

    # 构建待签名字符串
    string_to_sign = build_string_to_sign(
        method="PUT",
        content_md5=content_md5,
        content_type="application/gzip",
        date=date,
        canonicalized_amz_headers="",
        canonicalized_resource=canonicalized_resource,
    )

    # 生成签名
    authorization = build_authorization(
        access_key=access_key,
        access_secret=access_secret,
        string_to_sign=string_to_sign,
    )

    # 构建请求头
    headers = {
        "Authorization": authorization,
        "Date": date,
        "Host": host,
        "Content-Type": "application/gzip",
        "Content-MD5": content_md5,
    }

    # 读取文件并上传
    print(f"Uploading {file_path} to {url}...", file=sys.stderr)
    file_size = file_path.stat().st_size
    print(f"File size: {file_size / 1024 / 1024:.2f} MB", file=sys.stderr)

    with file_path.open("rb") as f:
        data = f.read()
        response = requests.put(
            url=url,
            headers=headers,
            data=data,
            timeout=timeout,
            verify=True,
        )

    return response.status_code, response.reason, response.text, dict(response.headers)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pack project and upload to S3Plus"
    )
    parser.add_argument(
        "--env",
        choices=["test", "prod-corp", "prod"],
        default="test",
        help="S3Plus environment (default: test)",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"S3Plus host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_BUCKET,
        help=f"S3Plus bucket name (default: {DEFAULT_BUCKET})",
    )
    parser.add_argument(
        "--access-key",
        default=DEFAULT_ACCESS_KEY,
        help="S3Plus access key",
    )
    parser.add_argument(
        "--access-secret",
        default=DEFAULT_ACCESS_SECRET,
        help="S3Plus access secret",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for the tar.gz file (default: temp dir, deleted after upload)",
    )
    parser.add_argument(
        "--keep-package",
        action="store_true",
        help="Keep the tar.gz file after upload",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Only pack, skip upload (useful for testing)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Upload timeout in seconds (default: 300)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    project_root = get_project_root()
    print(f"Project root: {project_root}")

    # 确定输出路径
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / PACKAGE_NAME
        cleanup = False
    else:
        output_dir = Path(tempfile.mkdtemp())
        output_path = output_dir / PACKAGE_NAME
        cleanup = not args.keep_package

    try:
        # 1. 打包项目
        try:
            pack_project(project_root, output_path)
        except Exception as e:
            print(f"Pack failed: {e}", file=sys.stderr)
            return 1

        if args.skip_upload:
            print(f"\nPackage created at: {output_path}")
            print("Skipped upload (--skip-upload)")
            return 0

        # 2. 上传到 S3
        try:
            status_code, reason, body, headers = upload_to_s3(
                file_path=output_path,
                object_name=PACKAGE_NAME,
                access_key=args.access_key,
                access_secret=args.access_secret,
                bucket=args.bucket,
                host=args.host,
                timeout=args.timeout,
            )
        except Exception as e:
            print(f"Upload failed: {e}", file=sys.stderr)
            return 1

        # 3. 检查上传结果
        if not (200 <= status_code < 300):
            print(f"HTTP {status_code} {reason}", file=sys.stderr)
            if body:
                print(body, file=sys.stderr)
            return 1

        # 4. 输出结果
        access_url = f"https://{args.host}/{args.bucket}/{PACKAGE_NAME}"
        etag = headers.get("ETag", "").strip('"')

        result = {
            "success": True,
            "package": PACKAGE_NAME,
            "url": access_url,
            "etag": etag,
            "bucket": args.bucket,
            "localPath": str(output_path) if args.keep_package else None,
        }
        print("\nUpload completed!")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        return 0

    finally:
        # 清理临时文件
        if cleanup and output_path.exists():
            print(f"\nCleaning up: {output_path}")
            output_path.unlink()
            if output_dir.exists():
                output_dir.rmdir()


if __name__ == "__main__":
    raise SystemExit(main())

