#!/usr/bin/env python3
"""统一审计日志系统"""

import json
from datetime import datetime
from pathlib import Path

class AuditLogger:
    def __init__(self, component: str):
        self.component = component
        self.log_dir = Path("/Users/lipengyu/.openclaw/workspace/shared/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def log(self, event_type: str, message: str, **kwargs):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "component": self.component,
            "event_type": event_type,
            "message": message,
            "data": kwargs
        }
        
        # 统一审计日志
        audit_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        return entry
    
    def task_delegated(self, task_id, from_agent, to_agent, task_type):
        return self.log("TASK_DELEGATED", 
                       f"{from_agent} -> {to_agent}",
                       task_id=task_id, task_type=task_type)
    
    def subagent_created(self, parent, subagent_id, subagent_type):
        return self.log("SUBAGENT_CREATED",
                       f"{parent} created {subagent_id}",
                       subagent_type=subagent_type)
    
    def cron_triggered(self, cron_name, cron_id):
        return self.log("CRON_TRIGGERED",
                       f"Cron {cron_name} triggered",
                       cron_id=cron_id)
    
    def agent_scheduled(self, agent_id, task_id):
        return self.log("AGENT_SCHEDULED",
                       f"Agent {agent_id} scheduled for {task_id}",
                       agent_id=agent_id, task_id=task_id)

if __name__ == "__main__":
    # 测试
    logger = AuditLogger("test")
    logger.task_delegated("task-001", "Orchestrator", "Worker-1", "collect")
    print("✅ 日志系统测试成功")
