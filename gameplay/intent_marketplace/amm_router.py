"""
HKC AMM路径规划 (amm_router.py)
================================
为意图寻找最优执行路径——跨多个AMM池和链的最优路由。
不是简单的A→B，而是可能经过多个中间代币和多条链。

核心概念：
  - 流动性池（Liquidity Pool）：AMM的x*y=k池
  - 路径（Route）：代币间的转换路径
  - 分割路由（Split Routing）：大额意图拆分到多条路径减少滑点

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum


class 池类型(Enum):
    """AMM池类型"""
    恒定乘积 = "constant_product"  # x*y=k
    稳定币 = "stableswap"          # 曲线稳定币池
    集中流动性 = "concentrated"     # 集中流动性


@dataclass
class 流动性池:
    """AMM流动性池"""
    池ID: str
    代币A: str
    代币B: str
    储备A: float
    储备B: float
    手续费率: float = 0.003  # 0.3%
    类型: 池类型 = 池类型.恒定乘积

    def 计算输出(self, 输入代币: str, 输入量: float) -> float:
        """计算给定输入量的输出"""
        if 输入代币 == self.代币A:
            输入储备, 输出储备 = self.储备A, self.储备B
        elif 输入代币 == self.代币B:
            输入储备, 输出储备 = self.储备B, self.储备A
        else:
            return 0.0

        if self.类型 == 池类型.恒定乘积:
            扣费输入 = 输入量 * (1 - self.手续费率)
            # x*y=k => 输出 = 输出储备 - (输入储备 * 输出储备) / (输入储备 + 扣费输入)
            输出量 = 输出储备 - (输入储备 * 输出储备) / (输入储备 + 扣费输入)
            return max(0, 输出量)
        elif self.类型 == 池类型.稳定定币:
            # 简化的稳定币池：接近1:1，小幅手续费
            return 输入量 * (1 - self.手续费率)
        return 0.0

    def 计算价格影响(self, 输入代币: str, 输入量: float) -> float:
        """计算价格影响（0~1）"""
        if 输入代币 == self.代币A:
            输入储备 = self.储备A
        elif 输入代币 == self.代币B:
            输入储备 = self.储备B
        else:
            return 1.0
        if 输入储备 == 0:
            return 1.0
        return min(1.0, 输入量 / 输入储备)


@dataclass
class 路由步骤:
    """路由的每一步"""
    池ID: str
    输入代币: str
    输出代币: str
    输入量: float
    预计输出量: float
    价格影响: float
    手续费: float
    链: str = "HKC"


@dataclass
class 路由方案:
    """完整路由方案"""
    方案ID: str = ""
    输入代币: str = ""
    输出代币: str = ""
    总输入量: float = 0.0
    总输出量: float = 0.0
    步骤: List[路由步骤] = field(default_factory=list)
    总价格影响: float = 0.0
    总手续费: float = 0.0
    路径长度: int = 0
    评分: float = 0.0

    def __post_init__(self):
        if not self.方案ID:
            self.方案ID = hashlib.sha256(
                f"route_{time.time()}".encode()
            ).hexdigest()[:16]
        self.路径长度 = len(self.步骤)
        self.总手续费 = sum(s.手续费 for s in self.步骤)
        self.总价格影响 = max((s.价格影响 for s in self.步骤), default=0)


class AMM路由器:
    """
    AMM路径规划器
    
    使用图搜索算法在流动性池网络中寻找最优路径。
    """

    def __init__(self, 最大路径长度: int = 4, 最大分割数: int = 3):
        """
        初始化路由器
        
        Args:
            最大路径长度: 最大路由跳数
            最大分割数: 分割路由的最大分割数
        """
        self.最大路径长度 = 最大路径长度
        self.最大分割数 = 最大分割数
        self._池: Dict[str, 流动性池] = {}
        self._代币图: Dict[str, List[Tuple[str, str]]] = {}  # 代币 -> [(连接代币, 池ID)]

    def 添加池(self, 池: 流动性池) -> None:
        """添加流动性池"""
        self._池[池.池ID] = 池
        # 更新代币连接图
        if 池.代币A not in self._代币图:
            self._代币图[池.代币A] = []
        if 池.代币B not in self._代币图:
            self._代币图[池.代币B] = []
        self._代币图[池.代币A].append((池.代币B, 池.池ID))
        self._代币图[池.代币B].append((池.代币A, 池.池ID))

    def 寻找路径(self, 输入代币: str, 输出代币: str, 输入量: float) -> List[路由方案]:
        """
        寻找所有可行路径
        
        Args:
            输入代币: 输入代币符号
            输出代币: 输出代币符号
            输入量: 输入数量
        """
        所有路径 = []
        self._深度搜索路径(
            当前代币=输入代币,
            目标代币=输出代币,
            剩余量=输入量,
            已访问=set(),
            当前步骤=[],
            结果列表=所有路径,
        )

        # 按总输出量排序
        所有路径.sort(key=lambda r: r.总输出量, reverse=True)
        return 所有路径

    def _深度搜索路径(
        self,
        当前代币: str,
        目标代币: str,
        剩余量: float,
        已访问: Set[str],
        当前步骤: List[路由步骤],
        结果列表: List[路由方案],
    ) -> None:
        """深度优先搜索所有可行路径"""
        if 当前代币 == 目标代币:
            if 当前步骤:
                总输出 = 当前步骤[-1].预计输出量 if 当前步骤 else 0
                方案 = 路由方案(
                    输入代币=当前步骤[0].输入代币,
                    输出代币=目标代币,
                    总输入量=当前步骤[0].输入量,
                    总输出量=总输出,
                    步骤=当前步骤.copy(),
                )
                方案.评分 = self._评分方案(方案)
                结果列表.append(方案)
            return

        if len(当前步骤) >= self.最大路径长度:
            return

        连接 = self._代币图.get(当前代币, [])
        for 下一个代币, 池ID in 连接:
            if 下一个代币 in 已访问:
                continue

            池 = self._池.get(池ID)
            if not 池:
                continue

            输出量 = 池.计算输出(当前代币, 剩余量)
            if 输出量 <= 0:
                continue

            价格影响 = 池.计算价格影响(当前代币, 剩余量)
            手续费 = 剩余量 * 池.手续费率

            步骤 = 路由步骤(
                池ID=池ID,
                输入代币=当前代币,
                输出代币=下一个代币,
                输入量=剩余量,
                预计输出量=输出量,
                价格影响=价格影响,
                手续费=手续费,
            )

            新已访问 = 已访问 | {当前代币}
            当前步骤.append(步骤)
            self._深度搜索路径(
                下一个代币, 目标代币, 输出量, 新已访问, 当前步骤, 结果列表
            )
            当前步骤.pop()

    def _评分方案(self, 方案: 路由方案) -> float:
        """对路由方案评分"""
        输出分 = 方案.总输出量
        长度惩罚 = 1.0 / (1.0 + 0.1 * (方案.路径长度 - 1))
        影响惩罚 = 1.0 - 方案.总价格影响
        return round(输出分 * 长度惩罚 * max(0.01, 影响惩罚), 4)

    def 最优路径(self, 输入代币: str, 输出代币: str, 输入量: float) -> Optional[路由方案]:
        """获取最优路径"""
        所有方案 = self.寻找路径(输入代币, 输出代币, 输入量)
        return 所有方案[0] if 所有方案 else None

    def 分割路由(
        self, 输入代币: str, 输出代币: str, 输入量: float, 分割数: int = 2
    ) -> List[路由方案]:
        """
        分割路由——将大额意图拆分到多条路径减少滑点
        
        Args:
            分割数: 分割成几份
        """
        分割数 = min(分割数, self.最大分割数)
        每份量 = 输入量 / 分割数
        结果 = []
        for i in range(分割数):
            方案 = self.最优路径(输入代币, 输出代币, 每份量)
            if 方案:
                结果.append(方案)
        return 结果

    def 获取池信息(self, 池ID: str) -> Optional[流动性池]:
        """获取池信息"""
        return self._池.get(池ID)

    def 列出池(self) -> List[流动性池]:
        """列出所有池"""
        return list(self._池.values())
