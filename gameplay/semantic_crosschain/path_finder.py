"""
HKC 跨链路径寻找器 (path_finder.py)
====================================
自动寻找最优跨链路径——不是人去选桥，而是AI自动规划。
考虑速度、成本、安全性、流动性等多维度。

核心概念：
  - 跨链图（Cross-chain Graph）：所有链和桥的连接关系
  - 路径评分（Path Scoring）：综合多维度对路径评分
  - 动态权重（Dynamic Weight）：根据链上状态动态调整路径权重

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum


class 桥类型(Enum):
    """跨链桥类型"""
    锁铸造 = "lock_mint"       # 锁定+铸造
    流动性池 = "liquidity_pool"  # 流动性池桥
    原子交换 = "atomic_swap"    # 哈希时间锁原子交换
    消息传递 = "messaging"      # 跨链消息传递
    ETB = "etb"                # 涌信桥


@dataclass
class 跨链桥:
    """跨链桥"""
    桥ID: str
    源链: str
    目标链: str
    类型: 桥类型 = 桥类型.锁铸造
    手续费率: float = 0.001
    预计耗时秒: float = 60.0
    安全评分: float = 0.9  # 0~1
    流动性: float = 1000000.0
    支持资产: List[str] = field(default_factory=list)
    活跃: bool = True

    def 是否支持资产(self, 资产: str) -> bool:
        """检查是否支持某资产"""
        return not self.支持资产 or 资产 in self.支持资产


@dataclass
class 跨链路径:
    """跨链路径"""
    路径ID: str = ""
    源链: str = ""
    目标链: str = ""
    经过的桥: List[str] = field(default_factory=list)
    经过的链: List[str] = field(default_factory=list)
    预计耗时秒: float = 0.0
    总手续费率: float = 0.0
    综合安全分: float = 1.0
    总跳数: int = 0
    评分: float = 0.0

    def __post_init__(self):
        if not self.路径ID:
            self.路径ID = hashlib.sha256(
                f"path_{self.源链}_{self.目标链}_{time.time()}".encode()
            ).hexdigest()[:16]
        self.总跳数 = len(self.经过的桥)


class 路径寻找器:
    """
    跨链路径寻找器
    
    在跨链桥网络中寻找最优路径。
    """

    def __init__(
        self,
        速度权重: float = 0.3,
        成本权重: float = 0.3,
        安全权重: float = 0.3,
        流动性权重: float = 0.1,
        最大跳数: int = 4,
    ):
        """
        初始化路径寻找器
        
        Args:
            速度权重: 速度维度权重
            成本权重: 成本维度权重
            安全权重: 安全维度权重
            流动性权重: 流动性维度权重
            最大跳数: 最大跨链跳数
        """
        self.速度权重 = 速度权重
        self.成本权重 = 成本权重
        self.安全权重 = 安全权重
        self.流动性权重 = 流动性权重
        self.最大跳数 = 最大跳数

        self._桥: Dict[str, 跨链桥] = {}
        self._链图: Dict[str, List[Tuple[str, str]]] = {}  # 链 -> [(目标链, 桥ID)]

    def 添加桥(self, 桥: 跨链桥) -> None:
        """添加跨链桥"""
        self._桥[桥.桥ID] = 桥
        if 桥.源链 not in self._链图:
            self._链图[桥.源链] = []
        self._链图[桥.源链].append((桥.目标链, 桥.桥ID))

    def 寻找路径(
        self, 源链: str, 目标链: str, 资产: str = "", 转账量: float = 0.0
    ) -> List[跨链路径]:
        """寻找所有可行路径"""
        所有路径 = []
        self._深度搜索(
            当前链=源链,
            目标链=目标链,
            资产=资产,
            已访问=set(),
            当前路径桥=[],
            当前路径链=[源链],
            当前耗时=0.0,
            当前费率=0.0,
            当前安全分=1.0,
            结果=所有路径,
        )

        # 评分并排序
        for 路径 in 所有路径:
            路径.评分 = self._评分路径(路径, 转账量)
        所有路径.sort(key=lambda p: p.评分, reverse=True)
        return 所有路径

    def _深度搜索(
        self,
        当前链: str,
        目标链: str,
        资产: str,
        已访问: Set[str],
        当前路径桥: List[str],
        当前路径链: List[str],
        当前耗时: float,
        当前费率: float,
        当前安全分: float,
        结果: List[跨链路径],
    ) -> None:
        """深度优先搜索跨链路径"""
        if 当前链 == 目标链:
            if 当前路径桥:
                路径 = 跨链路径(
                    源链=当前路径链[0],
                    目标链=目标链,
                    经过的桥=当前路径桥.copy(),
                    经过的链=当前路径链.copy(),
                    预计耗时秒=当前耗时,
                    总手续费率=当前费率,
                    综合安全分=当前安全分,
                )
                结果.append(路径)
            return

        if len(当前路径桥) >= self.最大跳数:
            return

        连接 = self._链图.get(当前链, [])
        for 下一链, 桥ID in 连接:
            if 下一链 in 已访问:
                continue

            桥 = self._桥.get(桥ID)
            if not 桥 or not 桥.活跃:
                continue
            if 资产 and not 桥.是否支持资产(资产):
                continue

            当前路径桥.append(桥ID)
            当前路径链.append(下一链)
            新已访问 = 已访问 | {当前链}

            self._深度搜索(
                下一链, 目标链, 资产, 新已访问,
                当前路径桥, 当前路径链,
                当前耗时 + 桥.预计耗时秒,
                当前费率 + 桥.手续费率,
                min(当前安全分, 桥.安全评分),
                结果,
            )

            当前路径桥.pop()
            当前路径链.pop()

    def _评分路径(self, 路径: 跨链路径, 转账量: float) -> float:
        """对路径综合评分"""
        # 速度分（越快越好）
        速度分 = 1.0 / (1.0 + 路径.预计耗时秒 / 300.0)
        # 成本分（越低越好）
        成本分 = 1.0 / (1.0 + 路径.总手续费率 * 100)
        # 安全分
        安全分 = 路径.综合安全分
        # 流动性分（跳数越少流动性越好）
        流动性分 = 1.0 / (1.0 + 0.3 * (路径.总跳数 - 1))

        总分 = (
            self.速度权重 * 速度分 +
            self.成本权重 * 成本分 +
            self.安全权重 * 安全分 +
            self.流动性权重 * 流动性分
        )
        return round(总分, 4)

    def 最优路径(
        self, 源链: str, 目标链: str, 资产: str = "", 转账量: float = 0.0
    ) -> Optional[跨链路径]:
        """获取最优路径"""
        所有 = self.寻找路径(源链, 目标链, 资产, 转账量)
        return 所有[0] if 所有 else None

    def 获取桥信息(self, 桥ID: str) -> Optional[跨链桥]:
        """获取桥信息"""
        return self._桥.get(桥ID)

    def 列出桥(self, 活跃only: bool = True) -> List[跨链桥]:
        """列出所有桥"""
        结果 = list(self._桥.values())
        if 活跃only:
            结果 = [b for b in 结果 if b.活跃]
        return 结果
