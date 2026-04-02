#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
S3Plus Upload Script
Upload files to Meituan S3Plus (MSS) storage service.
Based on: https://km.sankuai.com/collabpage/58102733
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests

# 环境配置
ENV_HOSTS = {
    "test": "msstest.vip.sankuai.com",
    "prod-corp": "s3plus-corp.sankuai.com",
    "prod": "s3plus.sankuai.com",
}

# 默认配置
DEFAULT_ACCESS_KEY = os.getenv("S3PLUS_ACCESS_KEY", "SRV_TWf8pAm28iVVnYAjazSLqn4L8CkKyhZB")
DEFAULT_ACCESS_SECRET = os.getenv("S3PLUS_ACCESS_SECRET", "Zj97qdzjCMXy8wnJ372n1z1aY7AkKsvM")
DEFAULT_BUCKET = os.getenv("S3PLUS_BUCKET", "openclaw")
DEFAULT_HOST = "s3plus-bj02.vip.sankuai.com"


def gmttime(offset_seconds=0):
    """生成 GMT 格式的时间字符串"""
    now = time.time() + offset_seconds
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now))


def calculate_content_md5(file_path):
    """计算文件的 Content-MD5（base64 编码的 MD5 值）"""
    md5_hash = hashlib.md5()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return base64.b64encode(md5_hash.digest()).decode("utf-8")


def build_string_to_sign(
    method,
    content_md5,
    content_type,
    date,
    canonicalized_amz_headers,
    canonicalized_resource,
):
    """
    构建待签名字符串
    StringToSign = HTTP-Verb + "\n"
                 + Content-MD5 + "\n"
                 + Content-Type + "\n"
                 + Date + "\n"
                 + CanonicalizedAmzHeaders
                 + CanonicalizedResource
    """
    return f"{method}\n{content_md5}\n{content_type}\n{date}\n{canonicalized_amz_headers}{canonicalized_resource}"


def build_authorization(
    access_key,
    access_secret,
    string_to_sign,
):
    """
    生成 Authorization header
    Authorization = "AWS" + " " + AccessKey + ":" + Signature
    Signature = Base64(HMAC-SHA1(AccessSecret, UTF-8-Encoding-Of(StringToSign)))
    """
    signature = base64.b64encode(
        hmac.new(
            access_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")
    return f"AWS {access_key}:{signature}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upload file to Meituan S3Plus and return URL"
    )
    parser.add_argument(
        "--env",
        choices=sorted(ENV_HOSTS.keys()),
        default="test",
        help="S3Plus environment (default: test)",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Override S3Plus host (default: s3plus-bj02.vip.sankuai.com)",
    )
    parser.add_argument(
        "--bucket",
        default=DEFAULT_BUCKET,
        help="S3Plus bucket name",
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
        "--file",
        required=True,
        help="Local file path to upload",
    )
    parser.add_argument(
        "--object-name",
        help="Object name in bucket (default: use filename)",
    )
    parser.add_argument(
        "--content-type",
        default="",
        help="Content-Type header (optional)",
    )
    parser.add_argument(
        "--skip-md5",
        action="store_true",
        help="Skip Content-MD5 calculation (faster but less safe)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification",
    )
    parser.add_argument(
        "--output",
        choices=("url", "json"),
        default="url",
        help="Output format: url only or full json response",
    )
    parser.add_argument(
        "--date-skew-seconds",
        type=int,
        default=0,
        help="Date header offset in seconds (for clock skew)",
    )
    parser.add_argument(
        "--no-uuid-prefix",
        action="store_true",
        help="Disable auto-generated UUID directory prefix (by default a UUID dir is prepended to prevent filename collisions)",
    )
    return parser


def require_auth_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """验证必需的认证参数"""
    missing = []
    if not args.bucket:
        missing.append("--bucket or S3PLUS_BUCKET")
    if not args.access_key:
        missing.append("--access-key or S3PLUS_ACCESS_KEY")
    if not args.access_secret:
        missing.append("--access-secret or S3PLUS_ACCESS_SECRET")
    if missing:
        parser.error("Missing required auth args: " + ", ".join(missing))


def upload(args: argparse.Namespace) -> tuple[int, str, str, dict]:
    """执行上传操作"""
    # 1. 确定主机和 URL
    host = args.host or ENV_HOSTS[args.env]
    file_path = Path(args.file)

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 2. 确定对象名称
    base_name = args.object_name or file_path.name
    base_name = base_name.lstrip("/")  # 移除开头的斜杠

    # 生成 UUID 目录前缀，防止文件重名覆盖
    if args.no_uuid_prefix:
        object_name = base_name
    else:
        uuid_dir = uuid.uuid4().hex
        object_name = f"{uuid_dir}/{base_name}"

    # 3. 构建 URL 和资源路径
    url = f"https://{host}/{args.bucket}/{object_name}"
    canonicalized_resource = f"/{args.bucket}/{object_name}"

    # 4. 计算 Content-MD5（可选）
    content_md5 = ""
    if not args.skip_md5:
        print(f"Calculating MD5 for {file_path}...", file=sys.stderr)
        content_md5 = calculate_content_md5(file_path)

    # 5. 生成时间戳
    date = gmttime(args.date_skew_seconds)

    # 6. 构建待签名字符串
    string_to_sign = build_string_to_sign(
        method="PUT",
        content_md5=content_md5,
        content_type=args.content_type,
        date=date,
        canonicalized_amz_headers="",  # 暂不支持自定义 x-amz- headers
        canonicalized_resource=canonicalized_resource,
    )

    # 7. 生成签名
    authorization = build_authorization(
        access_key=args.access_key,
        access_secret=args.access_secret,
        string_to_sign=string_to_sign,
    )

    # 8. 构建请求头
    headers = {
        "Authorization": authorization,
        "Date": date,
        "Host": host,
    }

    if content_md5:
        headers["Content-MD5"] = content_md5

    if args.content_type:
        headers["Content-Type"] = args.content_type

    # 9. 读取文件并上传
    print(f"Uploading {file_path} to {url}...", file=sys.stderr)

    with file_path.open("rb") as f:
        data = f.read()
        response = requests.put(
            url=url,
            headers=headers,
            data=data,
            timeout=args.timeout,
            verify=not args.insecure,
        )

    # 10. 解析响应
    response_headers = dict(response.headers)

    return response.status_code, response.reason, response.text, response_headers


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    require_auth_args(args, parser)

    try:
        status_code, reason, body, headers = upload(args)
    except Exception as exc:
        print(f"Upload request failed: {exc}", file=sys.stderr)
        return 1

    # 检查 HTTP 状态码
    if not (200 <= status_code < 300):
        print(f"HTTP {status_code} {reason}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        return 1

    # 提取 ETag
    etag = headers.get("ETag", "").strip('"')

    # 构建访问 URL
    host = args.host or ENV_HOSTS[args.env]
    object_name = args.object_name or Path(args.file).name
    object_name = object_name.lstrip("/")
    access_url = f"https://{host}/{args.bucket}/{object_name}"

    # 输出结果
    if args.output == "json":
        result = {
            "success": True,
            "url": access_url,
            "etag": etag,
            "bucket": args.bucket,
            "objectName": object_name,
            "headers": headers,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 仅输出 URL（便于脚本集成）
        print(access_url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())