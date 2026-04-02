#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload pre-upgrade.sh to S3Plus
"""

import argparse
import json
import sys
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

# 固定对象名
OBJECT_NAME = "pre-upgrade.sh"


def get_script_path() -> Path:
    """获取 pre-upgrade.sh 的路径"""
    return Path(__file__).parent.parent / "pre-upgrade.sh"


def upload_to_s3(
    file_path,
    object_name,
    access_key,
    access_secret,
    bucket,
    host,
    timeout=60,
):
    """上传文件到 S3Plus"""
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 构建对象名称
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
        content_type="text/x-shellscript",
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
        "Content-Type": "text/x-shellscript",
        "Content-MD5": content_md5,
    }

    # 读取文件并上传
    print(f"Uploading {file_path} to {url}...", file=sys.stderr)

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
        description="Upload pre-upgrade.sh to S3Plus"
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
        "--timeout",
        type=int,
        default=60,
        help="Upload timeout in seconds (default: 60)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    file_path = get_script_path()
    print(f"Script path: {file_path}")

    if not file_path.exists():
        print(f"Error: {file_path} not found", file=sys.stderr)
        return 1

    # 上传到 S3
    try:
        status_code, reason, body, headers = upload_to_s3(
            file_path=file_path,
            object_name=OBJECT_NAME,
            access_key=args.access_key,
            access_secret=args.access_secret,
            bucket=args.bucket,
            host=args.host,
            timeout=args.timeout,
        )
    except Exception as e:
        print(f"Upload failed: {e}", file=sys.stderr)
        return 1

    # 检查上传结果
    if not (200 <= status_code < 300):
        print(f"HTTP {status_code} {reason}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        return 1

    # 输出结果
    access_url = f"https://{args.host}/{args.bucket}/{OBJECT_NAME}"
    etag = headers.get("ETag", "").strip('"')

    result = {
        "success": True,
        "file": str(file_path),
        "objectName": OBJECT_NAME,
        "url": access_url,
        "etag": etag,
        "bucket": args.bucket,
    }
    print("\nUpload completed!")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

