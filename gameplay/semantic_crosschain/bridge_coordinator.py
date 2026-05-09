"""
HKC 多桥协调器 (bridge_coordinator.py)
======================================
多个跨链桥之间的协调——当一个桥拥堵或不可用时，自动切换到备选桥。
大额转账可以分片走不同的桥降低风险。

核心概念：
  - 桥健康监控（Bridge Health）：实时监控桥的状态
  - 负载均衡（Load Balancing）：跨桥分散流量
  - 分片转账（Sharded Transfer）：大额转账拆分到多个桥

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 桥状态(Enum):
    """桥健康状态"""
    健康 = "healthy"
    拥堵 = "congested"
    降级 = "degraded"
    离线 = "offline"
    维护 = "maintenance"


@dataclass
class 桥健康指标:
    """桥健康指标"""
    桥ID: str
    状态: 桥状态 = 桥状态.健康
    延迟毫秒: float = 100.0
    成功率: float = 0.99
    待处理交易: int = 0
    最大容量: int = 1000
    最后检查: float = 0.0

    def __post_init__(self):
        if self.最后检查 == 0.0:
            self.最后检查 = time.time()

    def 负载率(self) -> float:
        """计算负载率"""
        return self.待处理交易 / max(1, self.最大容量)

    def 是否可用(self) -> bool:
        """检查是否可用"""
        return self.状态 in (桥状态.健康, 桥状态.拥堵, 桥状态.降级)


@dataclass
class 分片:
    """转账分片"""
    分片ID: str = ""
    桥ID: str = ""
    金额: float = 0.0
    状态: str = "pending"  # pending/locked/transferring/completed/failed

    def __post_init__(self):
        if not self.分片ID:
            self.分片ID = hashlib.sha256(
                f"shard_{self.桥ID}_{time.time()}".encode()
            ).hexdigest()[:12]


@dataclass
class 协调转账:
    """协调的跨链转账"""
    转账ID: str = ""
    源链: str = ""
    目标链: str = ""
    资产: str = ""
    总金额: float = 0.0
    分片列表: List[分片] = field(default_factory=list)
    状态: str = "pending"
    创建时间: float = 0.0
    完成时间: float = 0.0

    def __post_init__(self):
        if not self.转账ID:
            self.转账ID = hashlib.sha256(
                f"xfer_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()

    def 已完成金额(self) -> float:
        """已完成的金额"""
        return sum(s.金额 for s in self.分片列表 if s.状态 == "completed")

    def 失败金额(self) -> float:
        """失败的金额"""
        return sum(s.金额 for s in self.分片列表 if s.状态 == "failed")


class 桥协调器:
    """
    多桥协调器
    
    管理跨链桥的健康监控、负载均衡和分片转账。
    """

    def __init__(
        self,
        分片阈值: float = 10000.0,  # 超过此金额分片
        最大分片数: int = 5,
        健康检查间隔秒: float = 60.0,
    ):
        """
        初始化协调器
        
        Args:
            分片阈值: 触发分片的金额阈值
            最大分片数: 最大分片数量
            健康检查间隔秒: 健康检查间隔
        """
        self.分片阈值 = 分片阈值
        self.最大分片数 = 最大分片数
        self.健康检查间隔秒 = 健康检查间隔秒

        self._桥健康: Dict[str, 桥健康指标] = {}
        self._转账: Dict[str, 协调转账] = {}

    def 注册桥(self, 桥ID: str, 最大容量: int = 1000) -> None:
        """注册桥到健康监控"""
        self._桥健康[桥ID] = 桥健康指标(桥ID=桥ID, 最大容量=最大容量)

    def 更新桥状态(self, 桥ID: str, 状态: 桥状态, 延迟: float = 0.0,
                    成功率: float = 0.0, 待处理: int = 0) -> None:
        """更新桥健康状态"""
        健康 = self._桥健康.get(桥ID)
        if not 健康:
            return
        健康.状态 = 状态
        if 延迟 > 0:
            健康.延迟毫秒 = 延迟
        if 成功率 > 0:
            健康.成功率 = 成功率
        健康.待处理交易 = 待处理
        健康.最后检查 = time.time()

    def 选择桥(self, 源链: str, 目标链: str, 资产: str, 可用桥IDs: List[str]) -> Optional[str]:
        """
        选择最优桥
        
        考虑健康状态、负载、延迟
        """
        候选 = []
        for 桥ID in 可用桥IDs:
            健康 = self._桥健康.get(桥ID)
            if not 健康 or not 健康.是否可用():
                continue
            # 评分：负载越低越好，延迟越低越好，成功率越高越好
            评分 = (1.0 - 健康.负载率()) * 0.4 + (1.0 / (1.0 + 健康.延迟毫秒 / 1000.0)) * 0.3 + 健康.成功率 * 0.3
            候选.append((桥ID, 评分))

        if not 候选:
            return None

        候选.sort(key=lambda x: x[1], reverse=True)
        return 候选[0][0]

    def 创建转账(
        self, 源链: str, 目标链: str, 资产: str, 金额: float,
        可用桥IDs: List[str],
    ) -> 协调转账:
        """创建协调转账（可能分片）"""
        转账 = 协调转账(
            源链=源链,
            目标链=目标链,
            资产=资产,
            总金额=金额,
        )

        if 金额 <= self.分片阈值 or len(可用桥IDs) <= 1:
            # 不分片，选一个最优桥
            选桥 = self.选择桥(源链, 目标链, 资产, 可用桥IDs) or 可用桥IDs[0]
            转账.分片列表.append(分片(桥ID=选桥, 金额=金额))
        else:
            # 分片
            分片数 = min(self.最大分片数, len(可用桥IDs))
            每片金额 = 金额 / 分片数
            可用健康桥 = [bid for bid in 可用桥IDs
                         if bid in self._桥健康 and self._桥健康[bid].是否可用()]
            if not 可用健康桥:
                可用健康桥 = 可用桥IDs[:1]

            for i in range(min(分片数, len(可用健康桥))):
                桥ID = 可用健康桥[i % len(可用健康桥)]
                片额 = 每片金额 if i < 分片数 - 1 else 金额 - 每片金额 * i
                转账.分片列表.append(分片(桥ID=桥ID, 金额=片额))

        self._转账[转账.转账ID] = 转账
        return 转账

    def 更新分片状态(self, 转账ID: str, 分片ID: str, 新状态: str) -> bool:
        """更新分片状态"""
        转账 = self._转账.get(转账ID)
        if not 转账:
            return False
        for 片 in 转账.分片列表:
            if 片.分片ID == 分片ID:
                片.状态 = 新状态
                break

        # 检查是否所有分片都完成
        全部完成 = all(s.状态 == "completed" for s in 转账.分片列表)
        全部结束 = all(s.状态 in ("completed", "failed") for s in 转账.分片列表)

        if 全部完成:
            转账.状态 = "completed"
            转账.完成时间 = time.time()
        elif 全部结束:
            转账.状态 = "partial" if 转账.已完成金额() > 0 else "failed"
            转账.完成时间 = time.time()

        return True

    def 获取转账(self, 转账ID: str) -> Optional[协调转账]:
        """获取转账信息"""
        return self._转账.get(转账ID)

    def 获取桥健康(self, 桥ID: str) -> Optional[桥健康指标]:
        """获取桥健康指标"""
        return self._桥健康.get(桥ID)

    def 获取统计(self) -> Dict[str, Any]:
        """获取协调器统计"""
        return {
            "监控桥数": len(self._桥健康),
            "健康桥数": sum(1 for h in self._桥健康.values() if h.状态 == 桥状态.健康),
            "总转账数": len(self._转账),
            "完成转账": sum(1 for t in self._转账.values() if t.状态 == "completed"),
        }
