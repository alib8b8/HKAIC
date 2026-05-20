"""
HKAIC SaaS - Health Check and Maintenance Tasks
定期健康检查和清理任务
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    健康检查器
    定期检查无人机连接状态并执行维护任务
    """
    
    def __init__(self, drone_manager, check_interval: int = 60):
        """
        Args:
            drone_manager: 无人机管理器实例
            check_interval: 检查间隔（秒）
        """
        self.drone_manager = drone_manager
        self.check_interval = check_interval
        self._running = False
        self._task = None
    
    async def start(self):
        """启动健康检查任务"""
        if self._running:
            logger.warning("Health checker already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._health_check_loop())
        logger.info(f"Health checker started (interval: {self.check_interval}s)")
    
    async def stop(self):
        """停止健康检查任务"""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health checker stopped")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self._running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    async def _perform_health_check(self):
        """执行健康检查"""
        from app.drone_manager import DroneConnectionStatus
        
        stale_connections = []
        
        for drone_id, connection in self.drone_manager._connections.items():
            if connection.status == DroneConnectionStatus.CONNECTED:
                # 检查遥测数据是否过时
                if connection.telemetry.last_update:
                    age = datetime.now() - connection.telemetry.last_update
                    if age > timedelta(minutes=5):
                        logger.warning(
                            f"Drone {drone_id} telemetry stale "
                            f"(last update: {age.total_seconds():.0f}s ago)"
                        )
                        stale_connections.append(drone_id)
                
                # 检查电池电量
                battery_remaining = connection.telemetry.battery.get('remaining', 100)
                if battery_remaining < 20:
                    logger.warning(
                        f"Drone {drone_id} battery low: {battery_remaining}%"
                    )
                
                # 检查无人机是否在空中但未响应
                if connection.telemetry.in_air and age > timedelta(minutes=2):
                    logger.warning(
                        f"Drone {drone_id} may be unresponsive in air "
                        f"(no commands received for {age.total_seconds():.0f}s)"
                    )
        
        # 记录统计信息
        stats = self.drone_manager.get_statistics()
        logger.info(
            f"Health check: {stats['connected_count']}/{stats['total_connections']} "
            f"drones connected, {len(stale_connections)} stale"
        )
    
    async def cleanup_stale_connections(self, max_age_minutes: int = 30):
        """
        清理过时的连接
        
        Args:
            max_age_minutes: 最大连接时长（分钟）
        """
        from app.drone_manager import DroneConnectionStatus
        
        cleaned = 0
        
        async with self.drone_manager._lock:
            for drone_id, connection in list(self.drone_manager._connections.items()):
                if connection.status != DroneConnectionStatus.CONNECTED:
                    continue
                
                if connection.last_connection_time:
                    age = datetime.now() - connection.last_connection_time
                    if age > timedelta(minutes=max_age_minutes):
                        logger.info(f"Cleaning up stale connection: {drone_id}")
                        await self.drone_manager.disconnect_drone(drone_id)
                        cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} stale connections")
        
        return cleaned


# 全局健康检查器实例
health_checker = None


def init_health_checker(drone_mgr, interval: int = 60):
    """初始化健康检查器"""
    global health_checker
    health_checker = HealthChecker(drone_mgr, interval)
    return health_checker


async def start_health_checks(drone_mgr, interval: int = 60):
    """启动健康检查任务"""
    checker = init_health_checker(drone_mgr, interval)
    await checker.start()
    return checker


async def stop_health_checks():
    """停止健康检查任务"""
    global health_checker
    if health_checker:
        await health_checker.stop()
