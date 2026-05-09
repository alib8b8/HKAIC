"""
HKC Agent协作分红 (collaboration_dividend.py)
===============================================
多个Agent协作完成任务时，如何分配收益？
按贡献度智能分红——不只是平分，而是根据每个Agent的实际贡献加权分配。

核心概念：
  - 协作组（Collaboration Group）：Agent组成的临时协作团队
  - 贡献度追踪（Contribution Tracking）：实时追踪每个Agent的贡献
  - 智能分红（Smart Dividend）：按贡献度+等级加权分配收益

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 协作状态(Enum):
    """协作组状态"""
    组建中 = "forming"
    进行中 = "active"
    已完成 = "completed"
    已解散 = "dissolved"
    争议中 = "disputed"


@dataclass
class 贡献记录:
    """单个Agent的贡献记录"""
    AgentID: str
    贡献类型: str  # compute/data/decision/execution
    贡献值: float
    时间戳: float = 0.0
    验证者: str = ""
    备注: str = ""

    def __post_init__(self):
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()


@dataclass
class 分红方案:
    """收益分红方案"""
    协作ID: str
    总收益: float
    分配: Dict[str, float] = field(default_factory=dict)  # AgentID -> 金额
    分配比例: Dict[str, float] = field(default_factory=dict)  # AgentID -> 比例
    创建时间: float = 0.0

    def __post_init__(self):
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()


@dataclass
class 协作组:
    """Agent协作组"""
    协作ID: str = ""
    任务名称: str = ""
    成员: List[str] = field(default_factory=list)
    贡献记录: Dict[str, List[贡献记录]] = field(default_factory=dict)  # AgentID -> 贡献列表
    总贡献值: Dict[str, float] = field(default_factory=dict)
    状态: 协作状态 = 协作状态.组建中
    创建时间: float = 0.0
    完成时间: float = 0.0
    分红方案: Optional[分红方案] = None

    def __post_init__(self):
        if not self.协作ID:
            self.协作ID = hashlib.sha256(
                f"collab_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()


class 协作分红器:
    """
    Agent协作分红器
    
    管理协作组的创建、贡献追踪和智能分红。
    """

    def __init__(
        self,
        平台佣金率: float = 0.03,
        等级加成: Optional[Dict[int, float]] = None,
        最低贡献门槛: float = 1.0,
    ):
        """
        初始化分红器
        
        Args:
            平台佣金率: 平台从总收益中抽取的佣金比例
            等级加成: 各等级的额外加成比例
            最低贡献门槛: 参与分红的最低贡献值
        """
        self.平台佣金率 = 平台佣金率
        self.等级加成 = 等级加成 or {
            1: 1.0, 2: 1.2, 3: 1.5, 4: 2.0, 5: 3.0
        }
        self.最低贡献门槛 = 最低贡献门槛

        self._协作组: Dict[str, 协作组] = {}

    def 创建协作组(self, 任务名称: str, 成员: List[str]) -> 协作组:
        """创建协作组"""
        组 = 协作组(
            任务名称=任务名称,
            成员=成员,
            状态=协作状态.进行中,
        )
        for AgentID in 成员:
            组.贡献记录[AgentID] = []
            组.总贡献值[AgentID] = 0.0
        self._协作组[组.协作ID] = 组
        return 组

    def 记录贡献(self, 协作ID: str, 贡献: 贡献记录) -> bool:
        """记录Agent贡献"""
        组 = self._协作组.get(协作ID)
        if not 组 or 组.状态 != 协作状态.进行中:
            return False
        if 贡献.AgentID not in 组.成员:
            return False

        组.贡献记录[贡献.AgentID].append(贡献)
        组.总贡献值[贡献.AgentID] = 组.总贡献值.get(贡献.AgentID, 0.0) + 贡献.贡献值
        return True

    def 完成协作(self, 协作ID: str) -> bool:
        """标记协作完成"""
        组 = self._协作组.get(协作ID)
        if not 组 or 组.状态 != 协作状态.进行中:
            return False
        组.状态 = 协作状态.已完成
        组.完成时间 = time.time()
        return True

    def 计算分红(self, 协作ID: str, 总收益: float, 等级映射: Optional[Dict[str, int]] = None) -> Optional[分红方案]:
        """
        计算分红方案
        
        Args:
            协作ID: 协作组ID
            总收益: 总收益金额
            等级映射: AgentID -> 等级，用于等级加成
        """
        组 = self._协作组.get(协作ID)
        if not 组 or 组.状态 != 协作状态.已完成:
            return None

        等级映射 = 等级映射 or {}
        扣佣金后 = 总收益 * (1 - self.平台佣金率)

        # 计算加权贡献
        加权贡献: Dict[str, float] = {}
        for AgentID in 组.成员:
            原始贡献 = 组.总贡献值.get(AgentID, 0.0)
            if 原始贡献 < self.最低贡献门槛:
                加权贡献[AgentID] = 0.0
                continue
            等级 = 等级映射.get(AgentID, 1)
            加成 = self.等级加成.get(等级, 1.0)
            加权贡献[AgentID] = 原始贡献 * 加成

        总加权 = sum(加权贡献.values())
        if 总加权 == 0:
            # 无有效贡献，平均分配
            有效成员 = [m for m in 组.成员 if 组.总贡献值.get(m, 0.0) >= self.最低贡献门槛]
            if not 有效成员:
                return None
            人均 = 扣佣金后 / len(有效成员)
            分配 = {m: round(人均, 4) for m in 有效成员}
            比例 = {m: round(1.0 / len(有效成员), 4) for m in 有效成员}
        else:
            分配 = {}
            比例 = {}
            for AgentID in 组.成员:
                if 加权贡献[AgentID] > 0:
                    份额 = 加权贡献[AgentID] / 总加权
                    分配[AgentID] = round(扣佣金后 * 份额, 4)
                    比例[AgentID] = round(份额, 4)

        方案 = 分红方案(
            协作ID=协作ID,
            总收益=总收益,
            分配=分配,
            分配比例=比例,
        )
        组.分红方案 = 方案
        return 方案

    def 获取协作组(self, 协作ID: str) -> Optional[协作组]:
        """获取协作组"""
        return self._协作组.get(协作ID)

    def 列出协作(self, 状态过滤: Optional[协作状态] = None) -> List[协作组]:
        """列出协作组"""
        结果 = list(self._协作组.values())
        if 状态过滤:
            结果 = [g for g in 结果 if g.状态 == 状态过滤]
        return 结果

    def 获取Agent协作(self, AgentID: str) -> List[协作组]:
        """获取Agent参与的所有协作"""
        return [g for g in self._协作组.values() if AgentID in g.成员]
