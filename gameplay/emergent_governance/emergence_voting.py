"""
HKC 涌现分数投票 (emergence_voting.py)
======================================
不是"一人一票"，而是根据节点的涌现分数赋予投票权重。
涌现分数高的节点对治理提议有更大影响力——因为它们对链的涌现模式贡献更多。

核心概念：
  - 涌现分数权重（Emergence Score Weight）：投票权重与涌现分数挂钩
  - 二次方投票（Quadratic Voting）：防止巨鲸垄断，平方根衰减
  - 委托投票（Delegated Voting）：可将投票权委托给更活跃的节点

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 投票选项(Enum):
    """投票选项"""
    支持 = "yes"
    反对 = "no"
    弃权 = "abstain"


class 投票策略(Enum):
    """投票权重策略"""
    线性 = "linear"           # 权重 = 涌现分数
    二次方根 = "quadratic"     # 权重 = sqrt(涌现分数)，防止垄断
    对数 = "logarithmic"       # 权重 = log(涌现分数+1)
    阶梯 = "tiered"           # 按涌现分数区间赋予固定权重


@dataclass
class 投票记录:
    """单次投票记录"""
    投票者ID: str
    提议ID: str
    选项: 投票选项
    涌现分数: float  # 投票时的涌现分数
    投票权重: float  # 计算后的实际权重
    时间戳: float = 0.0
    委托来源: Optional[str] = None  # 如果是代投，记录来源

    def __post_init__(self):
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()


@dataclass
class 投票结果:
    """投票结果"""
    提议ID: str
    总支持权重: float = 0.0
    总反对权重: float = 0.0
    总弃权权重: float = 0.0
    支持率: float = 0.0  # 支持/(支持+反对)
    是否通过: bool = False
    通过阈值: float = 0.6  # 默认60%支持率通过
    参与率: float = 0.0
    投票详情: List[投票记录] = field(default_factory=list)

    def 计算(self) -> None:
        """计算投票结果"""
        总有效 = self.总支持权重 + self.总反对权重
        if 总有效 > 0:
            self.支持率 = round(self.总支持权重 / 总有效, 4)
        self.是否通过 = self.支持率 >= self.通过阈值


@dataclass
class 委托关系:
    """投票委托关系"""
    委托人: str
    受托人: str
    委托时间: float = 0.0
    涌现分数: float = 0.0  # 委托时的涌现分数

    def __post_init__(self):
        if self.委托时间 == 0.0:
            self.委托时间 = time.time()


class 涌现投票器:
    """
    涌现分数投票器
    
    根据节点的涌现分数分配投票权重，执行投票并统计结果。
    """

    def __init__(
        self,
        策略: 投票策略 = 投票策略.二次方根,
        通过阈值: float = 0.6,
        最小参与率: float = 0.3,
        最大委托层级: int = 3,
    ):
        """
        初始化投票器
        
        Args:
            策略: 投票权重计算策略
            通过阈值: 提议通过的最低支持率
            最小参与率: 投票生效的最低参与率
            最大委托层级: 委托链最大深度
        """
        self.策略 = 策略
        self.通过阈值 = 通过阈值
        self.最小参与率 = 最小参与率
        self.最大委托层级 = 最大委托层级

        # 投票数据
        self._投票记录: Dict[str, List[投票记录]] = {}  # 提议ID -> 投票列表
        self._委托关系: Dict[str, 委托关系] = {}  # 委托人 -> 委托关系
        self._节点涌现分数: Dict[str, float] = {}  # 节点ID -> 当前涌现分数
        self._投票结果缓存: Dict[str, 投票结果] = {}

    def 注册节点(self, 节点ID: str, 涌现分数: float) -> None:
        """注册或更新节点的涌现分数"""
        self._节点涌现分数[节点ID] = 涌现分数

    def 批量注册(self, 节点映射: Dict[str, float]) -> None:
        """批量注册节点涌现分数"""
        self._节点涌现分数.update(节点映射)

    def 委托(self, 委托人: str, 受托人: str) -> bool:
        """委托投票权"""
        # 检查委托链深度
        当前 = 受托人
        深度 = 0
        while 当前 in self._委托关系:
            当前 = self._委托关系[当前].受托人
            深度 += 1
            if 深度 >= self.最大委托层级:
                return False  # 委托链太深

        # 检查是否形成环
        if 委托人 == 受托人:
            return False

        分数 = self._节点涌现分数.get(委托人, 0.0)
        self._委托关系[委托人] = 委托关系(
            委托人=委托人,
            受托人=受托人,
            涌现分数=分数,
        )
        return True

    def 取消委托(self, 委托人: str) -> bool:
        """取消委托"""
        if 委托人 in self._委托关系:
            del self._委托关系[委托人]
            return True
        return False

    def 计算权重(self, 节点ID: str) -> float:
        """计算节点的实际投票权重（含委托权重）"""
        自身分数 = self._节点涌现分数.get(节点ID, 0.0)
        自身权重 = self._分数转权重(自身分数)

        # 加上委托来的权重
        委托权重和 = 0.0
        for 委托人, 关系 in self._委托关系.items():
            if 关系.受托人 == 节点ID:
                委托权重和 += self._分数转权重(关系.涌现分数)

        return 自身权重 + 委托权重和

    def _分数转权重(self, 涌现分数: float) -> float:
        """将涌现分数转换为投票权重"""
        if 涌现分数 <= 0:
            return 0.0

        if self.策略 == 投票策略.线性:
            return 涌现分数
        elif self.策略 == 投票策略.二次方根:
            return math.sqrt(涌现分数)
        elif self.策略 == 投票策略.对数:
            return math.log(涌现分数 + 1)
        elif self.策略 == 投票策略.阶梯:
            if 涌现分数 < 0.2:
                return 1.0
            elif 涌现分数 < 0.4:
                return 2.0
            elif 涌现分数 < 0.6:
                return 3.0
            elif 涌现分数 < 0.8:
                return 5.0
            else:
                return 8.0
        return 涌现分数

    def 投票(self, 提议ID: str, 节点ID: str, 选项: 投票选项) -> 投票记录:
        """
        执行投票
        
        Args:
            提议ID: 治理提议ID
            节点ID: 投票节点ID
            选项: 投票选项
        """
        # 检查是否已委托（已委托则不能直接投票）
        if 节点ID in self._委托关系:
            raise ValueError(f"节点{节点ID}已委托投票权给{self._委托关系[节点ID].受托人}，不能直接投票")

        涌现分数 = self._节点涌现分数.get(节点ID, 0.0)
        权重 = self.计算权重(节点ID)

        记录 = 投票记录(
            投票者ID=节点ID,
            提议ID=提议ID,
            选项=选项,
            涌现分数=涌现分数,
            投票权重=权重,
        )

        if 提议ID not in self._投票记录:
            self._投票记录[提议ID] = []
        self._投票记录[提议ID].append(记录)

        # 清除结果缓存
        if 提议ID in self._投票结果缓存:
            del self._投票结果缓存[提议ID]

        return 记录

    def 统计结果(self, 提议ID: str, 总节点数: int = 0) -> 投票结果:
        """统计投票结果"""
        if 提议ID in self._投票结果缓存:
            return self._投票结果缓存[提议ID]

        记录列表 = self._投票记录.get(提议ID, [])
        结果 = 投票结果(提议ID=提议ID, 通过阈值=self.通过阈值)

        for 记录 in 记录列表:
            结果.投票详情.append(记录)
            if 记录.选项 == 投票选项.支持:
                结果.总支持权重 += 记录.投票权重
            elif 记录.选项 == 投票选项.反对:
                结果.总反对权重 += 记录.投票权重
            else:
                结果.总弃权权重 += 记录.投票权重

        结果.计算()

        if 总节点数 > 0:
            参与节点数 = len(set(r.投票者ID for r in 记录列表))
            结果.参与率 = round(参与节点数 / 总节点数, 4)
            # 参与率不足则即使通过率够也不通过
            if 结果.参与率 < self.最小参与率:
                结果.是否通过 = False

        self._投票结果缓存[提议ID] = 结果
        return 结果

    def 获取委托链(self, 节点ID: str) -> List[str]:
        """获取委托链"""
        链 = [节点ID]
        当前 = 节点ID
        while 当前 in self._委托关系:
            当前 = self._委托关系[当前].受托人
            if 当前 in 链:
                break  # 检测到环
            链.append(当前)
        return 链

    def 获取受托权重(self, 节点ID: str) -> float:
        """获取某节点收到的委托权重总和"""
        总和 = 0.0
        for 委托人, 关系 in self._委托关系.items():
            if 关系.受托人 == 节点ID:
                总和 += self._分数转权重(关系.涌现分数)
        return 总和
