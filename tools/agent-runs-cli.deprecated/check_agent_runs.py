#!/usr/bin/env python3
# check_agent_runs.py - Heartbeat 巡检实现

import json, subprocess, os, sys
from datetime import datetime, timedelta

url = os.environ.get('SUPABASE_URL', '')
key = os.environ.get('SUPABASE_SERVICE_KEY', '') or os.environ.get('SUPABASE_ANON_KEY', '')
if not url or not key:
    print(json.dumps({"error": "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY/SUPABASE_ANON_KEY"}, ensure_ascii=False))
    sys.exit(1)

API = f"{url}/rest/v1/agent_runs"
AUTH = ["-H", f"apikey: {key}", "-H", f"Authorization: Bearer {key}"]

def curl_get(params):
    cmd = ["curl", "-s", f"{API}?{params}"] + AUTH
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout or "[]")
        return data if isinstance(data, list) else []
    except:
        return []

now = datetime.utcnow()
ts5 = (now - timedelta(minutes=5)).isoformat()
ts30 = (now - timedelta(minutes=30)).isoformat()

actions = []

spawned_stuck = curl_get(f"status=eq.spawned&created_at=lt.{ts5}")
for r in spawned_stuck:
    actions.append({"rule": 1, "action": "respawn", "run_id": r["id"], "task_id": r["task_id"], "child_agent_id": r["child_agent_id"], "reason": "spawned > 5min"})

running_stuck = curl_get(f"status=eq.running&started_at=lt.{ts30}")
for r in running_stuck:
    actions.append({"rule": 2, "action": "timeout", "run_id": r["id"], "task_id": r["task_id"], "child_agent_id": r["child_agent_id"], "reason": "running > 30min"})

failed_runs = curl_get("or=(status.eq.failed,status.eq.timeout)&order=created_at.desc&limit=20")
for r in failed_runs:
    rc = r.get("retry_count", 0)
    mr = r.get("max_retries", 3)
    if rc < mr:
        actions.append({"rule": 4, "action": "retry", "run_id": r["id"], "task_id": r["task_id"], "child_agent_id": r["child_agent_id"], "retry_count": rc, "reason": "auto_retry"})
    else:
        actions.append({"rule": 5, "action": "manual", "run_id": r["id"], "task_id": r["task_id"], "child_agent_id": r["child_agent_id"], "retry_count": rc, "reason": "max_retries exceeded"})

report = {"checked_at": now.isoformat(), "thresholds": {"spawned": 5, "running": 30}, "total_actions": len(actions), "actions": actions}
print(json.dumps(report, indent=2, ensure_ascii=False))
