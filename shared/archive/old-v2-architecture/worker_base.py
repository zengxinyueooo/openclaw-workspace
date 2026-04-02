#!/usr/bin/env python3
"""
Worker 基础类 - 包含监控、重试、状态上报
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path

class WorkerBase:
    """Worker 基类，提供监控、重试、状态管理"""
    
    def __init__(self, worker_id, config=None):
        self.worker_id = worker_id
        self.workspace = Path("/Users/lipengyu/.openclaw/workspace")
        self.state_file = self.workspace / "shared/state/system-state.json"
        self.config = config or {}
        
        # 默认配置
        self.max_retries = self.config.get("max_retries", 3)
        self.base_delay = self.config.get("base_delay", 5)
        self.max_delay = self.config.get("max_delay", 60)
        self.timeout = self.config.get("timeout", 1800)
        
        self.current_task = None
        self.task_start_time = None
        self.consecutive_failures = 0
    
    def load_state(self):
        """加载全局状态"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"workers": {}}
    
    def save_state(self, state):
        """保存全局状态"""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
    
    def send_heartbeat(self, status="idle", progress=None, message=None):
        """发送心跳到监控系统"""
        heartbeat = {
            "worker_id": self.worker_id,
            "status": status,
            "current_task": self.current_task,
            "task_start_time": self.task_start_time,
            "progress": progress or {},
            "consecutive_failures": self.consecutive_failures,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        # 更新全局状态
        state = self.load_state()
        if "workers" not in state:
            state["workers"] = {}
        
        state["workers"][self.worker_id] = heartbeat
        self.save_state(state)
        
        return heartbeat
    
    def exponential_backoff_retry(self, func, *args, **kwargs):
        """指数退避重试"""
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                # 成功，重置失败计数
                self.consecutive_failures = 0
                return result
            except Exception as e:
                self.consecutive_failures += 1
                
                if attempt < self.max_retries - 1:
                    # 计算退避时间
                    delay = min(
                        self.base_delay * (2 ** attempt) + random.uniform(0, 1),
                        self.max_delay
                    )
                    print(f"   ⚠️  尝试 {attempt+1}/{self.max_retries} 失败: {e}")
                    print(f"   ⏳ 等待 {delay:.1f} 秒后重试...")
                    time.sleep(delay)
                else:
                    # 最终失败
                    print(f"   ❌ 最终失败 (已重试{self.max_retries}次): {e}")
                    raise
        
        return None
    
    def checkpoint(self, data):
        """保存断点，支持任务恢复"""
        checkpoint_file = self.workspace / f"workers/{self.worker_id}/checkpoint.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            "worker_id": self.worker_id,
            "current_task": self.current_task,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint, f, indent=2)
        
        # 同时更新全局状态
        self.send_heartbeat(status="running", progress=data)
    
    def load_checkpoint(self):
        """加载断点"""
        checkpoint_file = self.workspace / f"workers/{self.worker_id}/checkpoint.json"
        
        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                return json.load(f)
        return None
    
    def request_human_review(self, reason, data=None):
        """请求人工审核"""
        review_request = {
            "worker_id": self.worker_id,
            "task": self.current_task,
            "reason": reason,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "status": "pending_review"
        }
        
        # 保存到审核队列
        state = self.load_state()
        if "review_queue" not in state:
            state["review_queue"] = []
        
        state["review_queue"].append(review_request)
        self.save_state(state)
        
        print(f"\n🔔 [人工审核] {reason}")
        print(f"   Worker: {self.worker_id}")
        print(f"   Task: {self.current_task}")
        
        return review_request
    
    def check_quality(self, metrics):
        """质量检查，决定是否触发人工审核"""
        threshold_file = self.workspace / "shared/config/quality-threshold.json"
        
        with open(threshold_file) as f:
            thresholds = json.load(f)
        
        triggers = []
        
        # YOLO 置信度检查
        if "yolo_confidence" in metrics:
            conf = metrics["yolo_confidence"]
            if conf < thresholds["thresholds"]["yolo_face_confidence"]["human_review_below"]:
                triggers.append(f"YOLO置信度 {conf:.2f} 低于阈值")
        
        # 连续失败检查
        if self.consecutive_failures >= thresholds["triggers"]["consecutive_failures"]:
            triggers.append(f"连续失败 {self.consecutive_failures} 次")
        
        # 超时检查
        if self.task_start_time:
            start = datetime.fromisoformat(self.task_start_time)
            elapsed = (datetime.now() - start).total_seconds()
            if elapsed > thresholds["triggers"]["timeout_seconds"]:
                triggers.append(f"任务超时 ({elapsed/60:.0f}分钟)")
        
        if triggers:
            self.request_human_review(
                reason="; ".join(triggers),
                data=metrics
            )
            return False
        
        return True
    
    def start_task(self, task_name):
        """开始任务"""
        self.current_task = task_name
        self.task_start_time = datetime.now().isoformat()
        self.send_heartbeat(status="running", message=f"Starting {task_name}")
    
    def complete_task(self, result):
        """完成任务"""
        self.send_heartbeat(
            status="completed",
            message=f"Completed {self.current_task}",
            progress={"result": result}
        )
        self.current_task = None
        self.task_start_time = None
    
    def fail_task(self, error):
        """任务失败"""
        self.send_heartbeat(
            status="failed",
            message=f"Failed {self.current_task}: {error}",
        )
        
        # 检查是否需要人工介入
        if self.consecutive_failures >= 3:
            self.request_human_review(
                reason=f"任务连续失败 {self.consecutive_failures} 次: {error}"
            )
