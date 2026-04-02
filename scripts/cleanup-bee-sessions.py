#!/usr/bin/env python3
"""清理蜜蜂的 orphan session 条目。

按状态删除：
- failed: 删（失败记录留着没意义）
- null (孤儿): 删（进程被kill或没启动成功）
- done: 删（已完成记录不需要在列表里占位）
- running: 不删（活跃的）
"""

import json
import sys

AGENTS = ["mcn-bee", "mcn-ant", "mcn-eagle", "mcn-squirrel", "mcn-owl"]

def cleanup_agent(agent_id: str) -> dict:
    store_path = f"/Users/lipengyu/.openclaw/agents/{agent_id}/sessions/sessions.json"
    try:
        with open(store_path) as f:
            d = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"agent": agent_id, "removed": 0, "remaining": 0, "error": "file not found or invalid"}

    original_count = len(d)
    removed_by_status = {}

    for k, v in list(d.items()):
        status = v.get("status")

        if status in ("failed", "done", None):
            # null = orphan (process was killed before registering status)
            # done = completed (no need to keep in list)
            # failed = failed task (can be cleaned up)
            if status not in removed_by_status:
                removed_by_status[status] = 0
            removed_by_status[status] += 1
            del d[k]

    with open(store_path, "w") as f:
        json.dump(d, f, indent=2)

    return {
        "agent": agent_id,
        "removed": original_count - len(d),
        "remaining": len(d),
        "by_status": removed_by_status,
    }


if __name__ == "__main__":
    results = [cleanup_agent(a) for a in AGENTS]
    total_removed = sum(r["removed"] for r in results)
    print(f"[cleanup-bee-sessions] Removed {total_removed} sessions:")
    for r in results:
        if r["removed"] > 0:
            print(f"  {r['agent']}: removed={r['removed']} ({r.get('by_status',{})}), remaining={r['remaining']}")
