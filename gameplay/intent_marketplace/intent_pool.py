"""
HKC 意图池 (intent_pool.py)
============================
用户提交意图而非具体交易——"我想把HKAIC换成稳定币，不在乎哪条链"。
意图池收集、分类、匹配意图，等待Solver竞争执行。

核心概念：
  - 意图（Intent）：用户期望的结果，而非执行路径
  - 意图状态（Intent State）：提交→匹配→执行→结算
  - 意图可交易（Tradable Intent）：意图本身可以交易

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 意图类型(Enum):
    """意图类型"""
    兑换 = "swap"
    跨链转移 = "cross_chain_transfer"
    借贷 = "lend_borrow"
    质押 = "stake"
    治理 = "governance"
    自定义 = "custom"


class 意图状态(Enum):
    """意图生命周期状态"""
    已提交 = "submitted"
    匹配中 = "matching"
    已匹配 = "matched"
    执行中 = "executing"
    已结算 = "settled"
    已过期 = "expired"
    已取消 = "cancelled"
    执行失败 = "failed"


class 优先级(Enum):
    """意图优先级"""
    低 = "low"
    中 = "medium"
    高 = "high"
    紧急 = "urgent"


@dataclass
class 意图约束:
    """意图的约束条件"""
    滑点容忍: float = 0.01       # 最大可接受滑点
    最大Gas费: float = 100.0     # 最大Gas费用
    截止时间: float = 0.0        # 过期时间戳
    最小输出量: float = 0.0      # 最小期望输出
    偏好链: List[str] = field(default_factory=list)  # 偏好执行的链

    def 是否过期(self) -> bool:
        """检查约束是否已过期"""
        if self.截止时间 == 0.0:
            return False
        return time.time() > self.截止时间


@dataclass
class 意图:
    """用户意图"""
    意图ID: str = ""
    类型: 意图类型 = 意图类型.兑换
    提交者: str = ""
    输入资产: str = ""
    输入数量: float = 0.0
    输出资产: str = ""
    最小输出: float = 0.0
    约束: 意图约束 = field(default_factory=意图约束)
    优先级: 优先级 = 优先级.中
    状态: 意图状态 = 意图状态.已提交
    匹配Solver: Optional[str] = None
    执行路径: List[Dict[str, Any]] = field(default_factory=list)
    结算结果: Optional[Dict[str, Any]] = None
    创建时间: float = 0.0
    更新时间: float = 0.0
    元数据: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.意图ID:
            # H-13修复: 使用os.urandom加密随机数，替代可预测的time.time()
            import os as _os
            self.意图ID = hashlib.sha256(
                f"{self.类型.value}{self.提交者}{_os.urandom(16).hex()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()
        if self.更新时间 == 0.0:
            self.更新时间 = self.创建时间
        if self.最小输出 == 0.0:
            self.最小输出 = self.输入数量 * (1 - self.约束.滑点容忍)

    def 更新状态(self, 新状态: 意图状态) -> None:
        """更新意图状态"""
        self.状态 = 新状态
        self.更新时间 = time.time()

    def 是否可匹配(self) -> bool:
        """检查意图是否可匹配"""
        return self.状态 == 意图状态.已提交 and not self.约束.是否过期()


class 意图池:
    """
    意图池
    
    收集、管理用户提交的意图，支持按类型、状态、优先级查询。
    """

    def __init__(self, 最大容量: int = 10000, 清理间隔秒: int = 300):
        """
        初始化意图池
        
        Args:
            最大容量: 池中最大意图数
            清理间隔秒: 过期意图清理间隔
        """
        self.最大容量 = 最大容量
        self.清理间隔秒 = 清理间隔秒

        self._意图: Dict[str, 意图] = {}
        self._按类型索引: Dict[意图类型, List[str]] = {t: [] for t in 意图类型}
        self._按提交者索引: Dict[str, List[str]] = {}
        self._上次清理时间: float = time.time()

    def 提交意图(self, 新意图: 意图) -> str:
        """提交意图到池中"""
        if len(self._意图) >= self.最大容量:
            self._清理过期()

        self._意图[新意图.意图ID] = 新意图
        self._按类型索引[新意图.类型].append(新意图.意图ID)
        if 新意图.提交者 not in self._按提交者索引:
            self._按提交者索引[新意图.提交者] = []
        self._按提交者索引[新意图.提交者].append(新意图.意图ID)
        return 新意图.意图ID

    def 获取意图(self, 意图ID: str) -> Optional[意图]:
        """获取指定意图"""
        return self._意图.get(意图ID)

    def 查询可匹配意图(
        self,
        类型过滤: Optional[意图类型] = None,
        资产过滤: Optional[str] = None,
        最多返回: int = 100,
    ) -> List[意图]:
        """查询可匹配的意图"""
        候选 = []
        if 类型过滤:
            候选IDs = self._按类型索引.get(类型过滤, [])
        else:
            候选IDs = list(self._意图.keys())

        for iid in 候选IDs:
            意图obj = self._意图.get(iid)
            if not 意图obj or not 意图obj.是否可匹配():
                continue
            if 资产过滤 and 意图obj.输入资产 != 资产过滤:
                continue
            候选.append(意图obj)

        # 按优先级排序
        优先级排序 = {优先级.紧急: 0, 优先级.高: 1, 优先级.中: 2, 优先级.低: 3}
        候选.sort(key=lambda i: (优先级排序.get(i.优先级, 2), -i.创建时间))
        return 候选[:最多返回]

    def 更新意图状态(self, 意图ID: str, 新状态: 意图状态) -> bool:
        """更新意图状态"""
        意图obj = self._意图.get(意图ID)
        if not 意图obj:
            return False
        意图obj.更新状态(新状态)
        return True

    def 取消意图(self, 意图ID: str, 提交者: str) -> bool:
        """取消意图"""
        意图obj = self._意图.get(意图ID)
        if not 意图obj:
            return False
        if 意图obj.提交者 != 提交者:
            return False
        if 意图obj.状态 not in (意图状态.已提交, 意图状态.匹配中):
            return False
        意图obj.更新状态(意图状态.已取消)
        return True

    def _清理过期(self) -> int:
        """清理过期意图"""
        清理数 = 0
        过期IDs = []
        for iid, 意图obj in self._意图.items():
            if 意图obj.约束.是否过期() or 意图obj.状态 == 意图状态.已过期:
                过期IDs.append(iid)

        for iid in 过期IDs:
            意图obj = self._意图.pop(iid)
            意图obj.状态 = 意图状态.已过期
            if 意图obj.类型 in self._按类型索引:
                try:
                    self._按类型索引[意图obj.类型].remove(iid)
                except ValueError:
                    pass
            清理数 += 1

        self._上次清理时间 = time.time()
        return 清理数

    def 获取统计(self) -> Dict[str, Any]:
        """获取池统计信息"""
        状态统计 = {}
        for 状态 in 意图状态:
            状态统计[状态.value] = 0
        for 意图obj in self._意图.values():
            状态统计[意图obj.状态.value] += 1

        return {
            "总意图数": len(self._意图),
            "容量使用率": round(len(self._意图) / self.最大容量, 4),
            "状态分布": 状态统计,
        }
