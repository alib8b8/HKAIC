"""
HKC Agent纪律系统 (discipline_system.py)
=========================================
Agent经济的"免疫系统"——惩罚违规、奖励合规、防止作恶。
没有纪律的经济不是自由，是丛林。

核心概念：
  - 违规记录（Violation Record）：Agent的违规行为记录
  - 惩罚机制（Penalty）：从扣款到降级到封禁的递进惩罚
  - 信用修复（Credit Repair）：违规后的信用恢复路径

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 违规类型(Enum):
    """违规类型"""
    交易欺诈 = "fraud"
    服务违约 = "service_breach"
    恶意竞标 = "malicious_bidding"
    合谋操纵 = "collusion"
    Gas滥用 = "gas_abuse"
    身份冒用 = "identity_fraud"
    重复结算 = "double_settlement"
    拒绝执行 = "refusal_execute"


class 惩罚等级(Enum):
    """惩罚等级"""
    警告 = "warning"
    轻微罚款 = "minor_fine"        # 扣款5%
    中度罚款 = "moderate_fine"      # 扣款20%
    重度罚款 = "heavy_fine"         # 扣款50%
    降级 = "demotion"               # 身份等级降1级
    临时封禁 = "temp_ban"           # 封禁7天
    永久封禁 = "permanent_ban"      # 永久封禁


@dataclass
class 违规记录:
    """违规行为记录"""
    记录ID: str = ""
    AgentID: str = ""
    类型: 违规类型 = 违规类型.交易欺诈
    严重程度: float = 0.5  # 0~1
    描述: str = ""
    证据哈希: str = ""
    时间戳: float = 0.0
    已处理: bool = False

    def __post_init__(self):
        if not self.记录ID:
            self.记录ID = hashlib.sha256(
                f"violation_{self.AgentID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()


@dataclass
class 惩罚执行:
    """惩罚执行记录"""
    惩罚ID: str = ""
    AgentID: str = ""
    违规ID: str = ""
    惩罚: 惩罚等级 = 惩罚等级.警告
    罚款金额: float = 0.0
    封禁截止: float = 0.0
    降级数量: int = 0
    执行时间: float = 0.0
    已执行: bool = False

    def __post_init__(self):
        if not self.惩罚ID:
            self.惩罚ID = hashlib.sha256(
                f"penalty_{self.AgentID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.执行时间 == 0.0:
            self.执行时间 = time.time()


# 违规类型到惩罚等级的映射
违规惩罚映射 = {
    违规类型.交易欺诈: [惩罚等级.中度罚款, 惩罚等级.重度罚款, 惩罚等级.临时封禁],
    违规类型.服务违约: [惩罚等级.警告, 惩罚等级.轻微罚款, 惩罚等级.中度罚款],
    违规类型.恶意竞标: [惩罚等级.轻微罚款, 惩罚等级.中度罚款, 惩罚等级.降级],
    违规类型.合谋操纵: [惩罚等级.重度罚款, 惩罚等级.临时封禁, 惩罚等级.永久封禁],
    违规类型.Gas滥用: [惩罚等级.警告, 惩罚等级.轻微罚款, 惩罚等级.中度罚款],
    违规类型.身份冒用: [惩罚等级.临时封禁, 惩罚等级.永久封禁],
    违规类型.重复结算: [惩罚等级.中度罚款, 惩罚等级.重度罚款, 惩罚等级.降级],
    违规类型.拒绝执行: [惩罚等级.警告, 惩罚等级.轻微罚款, 惩罚等级.降级],
}


class 纪律系统:
    """
    Agent纪律系统
    
    管理违规记录、惩罚执行和信用修复。
    """

    def __init__(self, 修复期天数: int = 30, 修复衰减率: float = 0.1):
        """
        初始化纪律系统
        
        Args:
            修复期天数: 信用修复的基础天数
            修复衰减率: 每天的信誉恢复率
        """
        self.修复期天数 = 修复期天数
        self.修复衰减率 = 修复衰减率

        self._违规记录: Dict[str, List[违规记录]] = {}  # AgentID -> 违规列表
        self._惩罚记录: Dict[str, List[惩罚执行]] = {}  # AgentID -> 惩罚列表
        self._封禁状态: Dict[str, float] = {}  # AgentID -> 封禁截止时间
        self._违规计数: Dict[str, Dict[违规类型, int]] = {}  # AgentID -> {类型: 次数}

    def 报告违规(self, AgentID: str, 类型: 违规类型, 严重程度: float = 0.5, 描述: str = "", 证据哈希: str = "") -> 违规记录:
        """报告违规行为"""
        记录 = 违规记录(
            AgentID=AgentID,
            类型=类型,
            严重程度=max(0, min(1, 严重程度)),
            描述=描述,
            证据哈希=证据哈希,
        )

        if AgentID not in self._违规记录:
            self._违规记录[AgentID] = []
            self._违规计数[AgentID] = {}
        self._违规记录[AgentID].append(记录)

        # 更新违规计数
        当前计数 = self._违规计数[AgentID].get(类型, 0)
        self._违规计数[AgentID][类型] = 当前计数 + 1

        # 自动执行惩罚
        self._自动惩罚(AgentID, 类型, 严重程度, 记录.记录ID)
        记录.已处理 = True

        return 记录

    def _自动惩罚(self, AgentID: str, 类型: 违规类型, 严重程度: float, 违规ID: str) -> None:
        """根据违规类型和严重程度自动执行惩罚"""
        惩罚阶梯 = 违规惩罚映射.get(类型, [惩罚等级.警告])
        违规次数 = self._违规计数.get(AgentID, {}).get(类型, 1)

        # 根据违规次数选择惩罚等级
        阶梯索引 = min(违规次数 - 1, len(惩罚阶梯) - 1)
        选中惩罚 = 惩罚阶梯[阶梯索引]

        # 严重程度加成
        if 严重程度 >= 0.8 and 阶梯索引 < len(惩罚阶梯) - 1:
            选中惩罚 = 惩罚阶梯[阶梯索引 + 1]

        执行 = 惩罚执行(
            AgentID=AgentID,
            违规ID=违规ID,
            惩罚=选中惩罚,
        )

        # 根据惩罚等级设置具体参数
        if 选中惩罚 == 惩罚等级.轻微罚款:
            执行.罚款金额 = 50.0
        elif 选中惩罚 == 惩罚等级.中度罚款:
            执行.罚款金额 = 200.0
        elif 选中惩罚 == 惩罚等级.重度罚款:
            执行.罚款金额 = 1000.0
        elif 选中惩罚 == 惩罚等级.降级:
            执行.降级数量 = 1
        elif 选中惩罚 == 惩罚等级.临时封禁:
            执行.封禁截止 = time.time() + 86400 * 7
            self._封禁状态[AgentID] = 执行.封禁截止
        elif 选中惩罚 == 惩罚等级.永久封禁:
            执行.封禁截止 = float('inf')
            self._封禁状态[AgentID] = 执行.封禁截止

        执行.已执行 = True
        if AgentID not in self._惩罚记录:
            self._惩罚记录[AgentID] = []
        self._惩罚记录[AgentID].append(执行)

    def 是否被封禁(self, AgentID: str) -> Tuple[bool, float]:
        """检查Agent是否被封禁"""
        截止 = self._封禁状态.get(AgentID, 0)
        if 截止 == float('inf'):
            return True, float('inf')
        if time.time() < 截止:
            return True, 截止 - time.time()
        return False, 0

    def 解除封禁(self, AgentID: str) -> bool:
        """手动解除封禁"""
        if AgentID in self._封禁状态:
            del self._封禁状态[AgentID]
            return True
        return False

    def 计算信用修复(self, AgentID: str) -> float:
        """计算Agent当前的信用修复进度（0~1）"""
        惩罚列表 = self._惩罚记录.get(AgentID, [])
        if not 惩罚列表:
            return 1.0

        最后惩罚时间 = max(p.执行时间 for p in 惩罚列表)
        已过天数 = (time.time() - 最后惩罚时间) / 86400
        修复进度 = 1.0 - math.exp(-self.修复衰减率 * 已过天数)
        return round(min(1.0, 修复进度), 4)

    def 获取违规历史(self, AgentID: str) -> List[违规记录]:
        """获取违规历史"""
        return self._违规记录.get(AgentID, [])

    def 获取惩罚历史(self, AgentID: str) -> List[惩罚执行]:
        """获取惩罚历史"""
        return self._惩罚记录.get(AgentID, [])

    def 获取Agent风险等级(self, AgentID: str) -> str:
        """评估Agent风险等级"""
        违规数 = len(self._违规记录.get(AgentID, []))
        封禁, _ = self.是否被封禁(AgentID)
        if 封禁:
            return "prohibited"
        elif 违规数 == 0:
            return "safe"
        elif 违规数 <= 2:
            return "low_risk"
        elif 违规数 <= 5:
            return "medium_risk"
        else:
            return "high_risk"

    def 获取统计(self) -> Dict[str, Any]:
        """获取纪律系统统计"""
        return {
            "总违规数": sum(len(v) for v in self._违规记录.values()),
            "总惩罚数": sum(len(v) for v in self._惩罚记录.values()),
            "当前封禁数": sum(1 for t in self._封禁状态.values() if time.time() < t),
        }
