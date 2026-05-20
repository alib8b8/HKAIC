"""
HKAIC SaaS - Audit Logger
记录所有无人机操作的安全审计日志
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    审计日志记录器
    记录所有飞行控制操作，用于安全审计和问题排查
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.audit_file = self.log_dir / "drone_audit.log"
    
    def log_action(
        self,
        action: str,
        user_id: Optional[int],
        drone_id: str,
        result: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        记录操作到审计日志
        
        Args:
            action: 操作类型 (connect, disconnect, arm, disarm, takeoff, land, etc.)
            user_id: 用户ID
            drone_id: 无人机ID
            result: 操作结果 (success, failure, denied)
            details: 额外的详细信息
            ip_address: 用户IP地址
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "user_id": user_id,
            "drone_id": drone_id,
            "result": result,
            "details": details or {},
            "ip_address": ip_address
        }
        
        # 写入日志文件
        try:
            with open(self.audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
        
        # 同时记录到标准日志
        log_msg = (
            f"AUDIT | {log_entry['timestamp']} | "
            f"User: {user_id} | "
            f"Drone: {drone_id} | "
            f"Action: {action} | "
            f"Result: {result}"
        )
        
        if result == "success":
            logger.info(log_msg)
        elif result == "denied":
            logger.warning(log_msg)
        else:
            logger.error(log_msg)
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        drone_id: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        查询审计日志
        
        Args:
            user_id: 按用户ID过滤
            drone_id: 按无人机ID过滤
            action: 按操作类型过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回的最大记录数
        
        Returns:
            匹配的日志记录列表
        """
        logs = []
        
        try:
            if not self.audit_file.exists():
                return logs
            
            with open(self.audit_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # 应用过滤条件
                        if user_id is not None and log_entry.get("user_id") != user_id:
                            continue
                        
                        if drone_id is not None and log_entry.get("drone_id") != drone_id:
                            continue
                        
                        if action is not None and log_entry.get("action") != action:
                            continue
                        
                        # 时间过滤
                        log_time = datetime.fromisoformat(log_entry["timestamp"].replace("Z", "+00:00"))
                        
                        if start_time and log_time < start_time:
                            continue
                        
                        if end_time and log_time > end_time:
                            continue
                        
                        logs.append(log_entry)
                        
                        if len(logs) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to read audit logs: {str(e)}")
        
        return logs


# 单例实例
audit_logger = AuditLogger()


# 便捷函数
def log_drone_action(
    action: str,
    user_id: Optional[int],
    drone_id: str,
    result: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> None:
    """
    便捷函数：记录无人机操作
    
    示例:
        log_drone_action("takeoff", user_id=1, drone_id="drone-001", result="success")
        log_drone_action("arm", user_id=2, drone_id="drone-002", result="denied", 
                         details={"reason": "Permission denied"})
    """
    audit_logger.log_action(action, user_id, drone_id, result, details, ip_address)
