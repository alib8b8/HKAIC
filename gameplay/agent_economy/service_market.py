"""
HKC Agent服务市场 (service_market.py)
======================================
Agent之间的服务交易市场——提供服务的Agent赚HKAIC，
消费服务的Agent获得AI能力。让Agent经济真正运转起来。

核心概念：
  - 服务（Service）：Agent可提供的能力单元
  - 服务订单（Order）：消费方发起的服务请求
  - 服务评级（Rating）：交易后的互评系统

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 服务状态(Enum):
    """服务状态"""
    上架中 = "active"
    已下架 = "inactive"
    暂停 = "paused"


class 订单状态(Enum):
    """订单状态"""
    待接单 = "pending"
    进行中 = "in_progress"
    待确认 = "awaiting_confirmation"
    已完成 = "completed"
    已取消 = "cancelled"
    争议中 = "disputed"


@dataclass
class 服务:
    """Agent提供的服务"""
    服务ID: str = ""
    提供者ID: str = ""
    名称: str = ""
    描述: str = ""
    类别: str = "general"
    定价: float = 0.0       # 每次调用的HKAIC价格
    定价模式: str = "per_call"  # per_call/subscription
    最低等级要求: int = 1
    状态: 服务状态 = 服务状态.上架中
    评分: float = 0.0
    评价数: int = 0
    调用次数: int = 0
    创建时间: float = 0.0

    def __post_init__(self):
        if not self.服务ID:
            self.服务ID = hashlib.sha256(
                f"svc_{self.提供者ID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()

    def 更新评分(self, 新评分: float) -> None:
        """更新平均评分"""
        总分 = self.评分 * self.评价数 + 新评分
        self.评价数 += 1
        self.评分 = round(总分 / self.评价数, 2)


@dataclass
class 服务订单:
    """服务消费订单"""
    订单ID: str = ""
    服务ID: str = ""
    提供者ID: str = ""
    消费者ID: str = ""
    数量: int = 1
    总价: float = 0.0
    状态: 订单状态 = 订单状态.待接单
    消费者评分: Optional[float] = None
    提供者评分: Optional[float] = None
    创建时间: float = 0.0
    完成时间: float = 0.0
    备注: str = ""

    def __post_init__(self):
        if not self.订单ID:
            self.订单ID = hashlib.sha256(
                f"order_{self.服务ID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()


class 服务市场:
    """
    Agent服务市场
    
    管理服务的上架、搜索、下单、评价。
    """

    def __init__(self, 佣金率: float = 0.02, 争议押金率: float = 0.1):
        """
        初始化服务市场
        
        Args:
            佣金率: 平台佣金率
            争议押金率: 发起争议需缴纳的押金比例
        """
        self.佣金率 = 佣金率
        self.争议押金率 = 争议押金率

        self._服务: Dict[str, 服务] = {}
        self._订单: Dict[str, 服务订单] = {}
        self._类别索引: Dict[str, List[str]] = {}

    def 上架服务(self, 提供者ID: str, 名称: str, 描述: str, 定价: float,
                 类别: str = "general", 最低等级: int = 1) -> 服务:
        """上架新服务"""
        新服务 = 服务(
            提供者ID=提供者ID,
            名称=名称,
            描述=描述,
            定价=定价,
            类别=类别,
            最低等级要求=最低等级,
        )
        self._服务[新服务.服务ID] = 新服务
        if 类别 not in self._类别索引:
            self._类别索引[类别] = []
        self._类别索引[类别].append(新服务.服务ID)
        return 新服务

    def 下架服务(self, 服务ID: str) -> bool:
        """下架服务"""
        svc = self._服务.get(服务ID)
        if not svc:
            return False
        svc.状态 = 服务状态.已下架
        return True

    def 搜索服务(
        self, 关键词: str = "", 类别: Optional[str] = None,
        最低评分: float = 0.0, 最多返回: int = 20,
    ) -> List[服务]:
        """搜索服务"""
        候选 = []
        if 类别:
            IDs = self._类别索引.get(类别, [])
            候选 = [self._服务[i] for i in IDs if i in self._服务]
        else:
            候选 = list(self._服务.values())

        结果 = [s for s in 候选
                if s.状态 == 服务状态.上架中
                and s.评分 >= 最低评分
                and (not 关键词 or 关键词 in s.名称 or 关键词 in s.描述)]

        结果.sort(key=lambda s: s.评分, reverse=True)
        return 结果[:最多返回]

    def 下单(self, 服务ID: str, 消费者ID: str, 数量: int = 1, 备注: str = "") -> Optional[服务订单]:
        """下单购买服务"""
        svc = self._服务.get(服务ID)
        if not svc or svc.状态 != 服务状态.上架中:
            return None

        订单 = 服务订单(
            服务ID=服务ID,
            提供者ID=svc.提供者ID,
            消费者ID=消费者ID,
            数量=数量,
            总价=svc.定价 * 数量,
            备注=备注,
        )
        self._订单[订单.订单ID] = 订单
        return 订单

    def 接单(self, 订单ID: str) -> bool:
        """提供者接单"""
        订单 = self._订单.get(订单ID)
        if not 订单 or 订单.状态 != 订单状态.待接单:
            return False
        订单.状态 = 订单状态.进行中
        return True

    def 完成订单(self, 订单ID: str) -> bool:
        """完成订单"""
        订单 = self._订单.get(订单ID)
        if not 订单 or 订单.状态 != 订单状态.进行中:
            return False
        订单.状态 = 订单状态.待确认
        return True

    def 确认完成(self, 订单ID: str, 消费者评分: float = 5.0, 提供者评分: float = 5.0) -> bool:
        """消费者确认完成并评分"""
        订单 = self._订单.get(订单ID)
        if not 订单 or 订单.状态 != 订单状态.待确认:
            return False

        订单.状态 = 订单状态.已完成
        订单.消费者评分 = 消费者评分
        订单.提供者评分 = 提供者评分
        订单.完成时间 = time.time()

        # 更新服务评分
        svc = self._服务.get(订单.服务ID)
        if svc:
            svc.更新评分(消费者评分)
            svc.调用次数 += 订单.数量

        return True

    def 发起争议(self, 订单ID: str) -> bool:
        """发起争议"""
        订单 = self._订单.get(订单ID)
        if not 订单 or 订单.状态 not in (订单状态.进行中, 订单状态.待确认):
            return False
        订单.状态 = 订单状态.争议中
        return True

    def 获取服务(self, 服务ID: str) -> Optional[服务]:
        """获取服务信息"""
        return self._服务.get(服务ID)

    def 获取订单(self, 订单ID: str) -> Optional[服务订单]:
        """获取订单信息"""
        return self._订单.get(订单ID)

    def 获取Agent服务(self, 提供者ID: str) -> List[服务]:
        """获取Agent提供的所有服务"""
        return [s for s in self._服务.values() if s.提供者ID == 提供者ID]

    def 获取统计(self) -> Dict[str, Any]:
        """获取市场统计"""
        return {
            "总服务数": len(self._服务),
            "活跃服务": sum(1 for s in self._服务.values() if s.状态 == 服务状态.上架中),
            "总订单数": len(self._订单),
            "完成订单": sum(1 for o in self._订单.values() if o.状态 == 订单状态.已完成),
            "争议订单": sum(1 for o in self._订单.values() if o.状态 == 订单状态.争议中),
        }
