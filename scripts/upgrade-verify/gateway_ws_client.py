"""
Gateway WebSocket 客户端
负责：握手认证、触发 agent run、轮询 transcript 等回复
"""
import base64
import json
import os
import time
import uuid
from typing import Optional

import websocket
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
    Encoding,
    PublicFormat,
)

_OPENCLAW_BASE = os.path.expanduser("~/.openclaw")
IDENTITY_PATH = os.path.join(_OPENCLAW_BASE, "identity/device.json")
SESSIONS_JSON = os.path.join(_OPENCLAW_BASE, "agents/main/sessions/sessions.json")
WS_URL = "ws://127.0.0.1:18789"
TOKEN = "catpaw"


# ── 工具函数 ──────────────────────────────────────────

def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _pub_b64(pem: bytes) -> str:
    pub = load_pem_public_key(pem)
    return _b64u(pub.public_bytes(Encoding.Raw, PublicFormat.Raw))


def _sign(pem: bytes, payload: str) -> str:
    key = load_pem_private_key(pem, password=None)
    return _b64u(key.sign(payload.encode()))


def _load_identity() -> dict:
    with open(IDENTITY_PATH) as f:
        return json.load(f)


def _connect_ws(timeout: int = 15) -> websocket.WebSocket:
    """完成 Gateway WS 握手，返回已认证连接"""
    identity = _load_identity()
    device_id = identity["deviceId"]
    private_pem = identity["privateKeyPem"].encode()
    public_pem = identity["publicKeyPem"].encode()

    ws = websocket.create_connection(WS_URL, timeout=timeout)
    challenge = json.loads(ws.recv())
    nonce = challenge["payload"]["nonce"]
    ts = challenge["payload"]["ts"]

    scopes = ["operator.read", "operator.write"]
    sig_payload = "|".join([
        "v3", device_id, "cli", "cli", "operator",
        ",".join(scopes), str(ts), TOKEN, nonce, "linux", "",
    ])
    signature = _sign(private_pem, sig_payload)

    ws.send(json.dumps({
        "type": "req",
        "id": str(uuid.uuid4()),
        "method": "connect",
        "params": {
            "minProtocol": 3, "maxProtocol": 3,
            "client": {"id": "cli", "version": "2026.2.26",
                       "platform": "linux", "mode": "cli"},
            "role": "operator",
            "scopes": scopes,
            "caps": [], "commands": [], "permissions": {},
            "auth": {"token": TOKEN},
            "locale": "zh-CN",
            "userAgent": "openclaw-smoke/1.0",
            "device": {
                "id": device_id,
                "publicKey": _pub_b64(public_pem),
                "signature": signature,
                "signedAt": ts,
                "nonce": nonce,
            },
        },
    }))
    resp = json.loads(ws.recv())
    assert resp.get("ok"), f"Gateway WS 握手失败: {resp}"
    return ws


def _normalize_path(path: str) -> str:
    """将 /mnt/openclaw/.openclaw/... 修正为实际的 ~/.openclaw/... 路径"""
    if path and "/mnt/openclaw/.openclaw/" in path:
        path = path.replace("/mnt/openclaw/.openclaw/", _OPENCLAW_BASE + "/")
    return path


def _get_transcript_path(session_key: str) -> Optional[str]:
    """从 sessions.json 解析 transcript 文件路径"""
    try:
        with open(SESSIONS_JSON) as f:
            sessions = json.load(f)
        entry = sessions.get(session_key, {})
        raw = entry.get("sessionFile")
        return _normalize_path(raw) if raw else None
    except Exception:
        return None


def _parse_ts(raw) -> float:
    """把 timestamp 统一转成 unix 秒（支持 ms int 和 ISO 字符串两种格式）"""
    if isinstance(raw, (int, float)):
        # 毫秒级整数
        return raw / 1000 if raw > 1e10 else float(raw)
    if isinstance(raw, str):
        from datetime import datetime, timezone
        try:
            # 兼容 "2026-03-18T13:19:12.569Z" 格式
            s = raw.replace("Z", "+00:00")
            return datetime.fromisoformat(s).timestamp()
        except Exception:
            pass
    return 0.0


def _read_latest_assistant_text(path: str, after_ts: float) -> Optional[str]:
    """
    读取 transcript JSONL，返回 after_ts 之后最新的 assistant 纯文本回复。
    transcript 格式：{type:"message", timestamp, message:{role, content:[...]}}
    """
    try:
        with open(path) as f:
            lines = f.readlines()
    except Exception:
        return None

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        # 支持两种格式：包装结构 和 裸 message
        if obj.get("type") == "message":
            ts = _parse_ts(obj.get("timestamp", 0))
            msg = obj.get("message", {})
        else:
            ts = _parse_ts(obj.get("timestamp", 0))
            msg = obj

        if msg.get("role") != "assistant":
            continue
        if ts <= after_ts:
            continue

        # 提取纯文本内容（跳过纯 toolCall 消息）
        content = msg.get("content", [])
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    return c["text"]
        elif isinstance(content, str):
            return content
    return None


# ── 公开接口 ─────────────────────────────────────────

def send_agent_message(
    session_key: str,
    message: str,
    deliver: bool = False,
    timeout: int = 60,
    poll_interval: float = 3.0,
) -> Optional[str]:
    """
    通过 Gateway WS 发送消息给 agent，轮询 transcript 等待回复。
    返回 agent 回复文本，超时返回 None。
    """
    transcript_path = _get_transcript_path(session_key)
    assert transcript_path, f"找不到 session {session_key!r} 的 transcript 路径"
    assert os.path.exists(transcript_path), f"transcript 文件不存在: {transcript_path}"

    sent_at = time.time()

    # 通过 WS 触发 agent run
    ws = _connect_ws(timeout=15)
    try:
        req_id = str(uuid.uuid4())
        ws.send(json.dumps({
            "type": "req",
            "id": req_id,
            "method": "agent",
            "params": {
                "message": message,
                "sessionKey": session_key,
                "deliver": deliver,
                "idempotencyKey": str(uuid.uuid4()),
            },
        }))
        # 等待 RPC accepted（跳过 Gateway 主动推送的 event）
        ws.settimeout(10)
        deadline_ack = time.time() + 10
        while time.time() < deadline_ack:
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                raise RuntimeError("等待 agent RPC ack 超时")
            resp = json.loads(raw)
            if resp.get("type") == "event":
                continue  # 跳过 health/presence 等主动推送
            if resp.get("type") == "res" and resp.get("id") == req_id:
                if not resp.get("ok"):
                    raise RuntimeError(f"agent RPC 被拒绝: {resp}")
                break
    finally:
        try:
            ws.close()
        except Exception:
            pass

    # 轮询 transcript 等待 agent 回复
    deadline = time.time() + timeout
    while time.time() < deadline:
        reply = _read_latest_assistant_text(transcript_path, sent_at)
        if reply:
            return reply
        time.sleep(poll_interval)

    return None


def ping_gateway() -> bool:
    """测试 Gateway WS 连通性，返回是否成功"""
    try:
        ws = _connect_ws(timeout=10)
        ws.close()
        return True
    except Exception:
        return False

