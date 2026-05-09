"""
HKC 灰度执行器 (gradual_executor.py)
=====================================
治理提议通过后，不立即全量执行，而是灰度推进——先小范围试点，观察效果，
逐步扩大范围。如果出现异常，自动回滚。

核心概念：
  - 灰度阶段（Gradual Phase）：10%→30%→60%→100%逐步推进
  - 效果监控（Effect Monitoring）：每个阶段持续监控链上指标
  - 自动回滚（Auto Rollback）：监控到异常自动回退到上一个稳定状态

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum


class 执行阶段(Enum):
    """灰度执行阶段"""
    未开始 = "not_started"
    阶段一_10 = "phase_10"   # 10% 节点
    阶段二_30 = "phase_30"   # 30% 节点
    阶段三_60 = "phase_60"   # 60% 节点
    阶段四_100 = "phase_100" # 100% 节点
    已完成 = "completed"
    已回滚 = "rolled_back"


class 回滚原因(Enum):
    """回滚原因"""
    指标恶化 = "metrics_degradation"
    错误率超限 = "error_rate_exceeded"
    共识异常 = "consensus_anomaly"
    手动触发 = "manual_trigger"
    超时 = "timeout"


@dataclass
class 阶段快照:
    """执行阶段快照（用于回滚）"""
    阶段: 执行阶段
    参数值: Dict[str, float]
    时间戳: float = 0.0
    节点列表: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()


@dataclass
class 监控指标:
    """灰度执行期间的监控指标"""
    阶段: 执行阶段
    Gas均值: float = 0.0
    交易成功率: float = 1.0
    共识延迟毫秒: float = 0.0
    错误率: float = 0.0
    节点在线率: float = 1.0
    时间戳: float = 0.0

    def __post_init__(self):
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()

    def 是否异常(self, 阈值: Optional[Dict[str, float]] = None) -> Tuple[bool, str]:
        """检查指标是否异常"""
        默认阈值 = {
            "交易成功率下限": 0.95,
            "错误率上限": 0.05,
            "共识延迟上限": 5000.0,
            "节点在线率下限": 0.9,
        }
        阈值 = 阈值 or 默认阈值

        if self.交易成功率 < 阈值["交易成功率下限"]:
            return True, f"交易成功率{self.交易成功率:.2%}低于阈值{阈值['交易成功率下限']:.2%}"
        if self.错误率 > 阈值["错误率上限"]:
            return True, f"错误率{self.错误率:.2%}超过上限{阈值['错误率上限']:.2%}"
        if self.共识延迟毫秒 > 阈值["共识延迟上限"]:
            return True, f"共识延迟{self.共识延迟毫秒}ms超过上限{阈值['共识延迟上限']}ms"
        if self.节点在线率 < 阈值["节点在线率下限"]:
            return True, f"节点在线率{self.节点在线率:.2%}低于阈值{阈值['节点在线率下限']:.2%}"
        return False, ""


@dataclass
class 执行记录:
    """灰度执行记录"""
    提议ID: str
    当前阶段: 执行阶段 = 执行阶段.未开始
    阶段历史: List[执行阶段] = field(default_factory=list)
    快照栈: List[阶段快照] = field(default_factory=list)
    监控历史: List[监控指标] = field(default_factory=list)
    回滚次数: int = 0
    最后回滚原因: Optional[回滚原因] = None
    开始时间: float = 0.0
    结束时间: float = 0.0

    def __post_init__(self):
        if self.开始时间 == 0.0:
            self.开始时间 = time.time()


class 灰度执行器:
    """
    灰度执行器
    
    治理提议通过后的分阶段执行引擎，支持灰度推进和自动回滚。
    """

    # 阶段顺序和对应节点比例
    阶段进度 = [
        (执行阶段.阶段一_10, 0.10),
        (执行阶段.阶段二_30, 0.30),
        (执行阶段.阶段三_60, 0.60),
        (执行阶段.阶段四_100, 1.00),
    ]

    def __init__(
        self,
        阶段持续区块: int = 100,
        最大回滚次数: int = 3,
        监控阈值: Optional[Dict[str, float]] = None,
    ):
        """
        初始化执行器
        
        Args:
            阶段持续区块: 每个灰度阶段持续的区块数
            最大回滚次数: 最多回滚几次后放弃执行
            监控阈值: 监控指标异常阈值
        """
        self.阶段持续区块 = 阶段持续区块
        self.最大回滚次数 = 最大回滚次数
        self.监控阈值 = 监控阈值

        self._执行记录: Dict[str, 执行记录] = {}
        self._当前参数: Dict[str, float] = {}  # 当前生效的参数

    def 开始执行(self, 提议ID: str, 参数变更: Dict[str, Tuple[float, float]]) -> 执行记录:
        """
        开始灰度执行
        
        Args:
            提议ID: 治理提议ID
            参数变更: {参数名: (当前值, 目标值)}
        """
        记录 = 执行记录(提议ID=提议ID)
        self._执行记录[提议ID] = 记录
        # 保存初始快照
        初始快照 = 阶段快照(
            阶段=执行阶段.未开始,
            参数值={k: v[0] for k, v in 参数变更.items()},
        )
        记录.快照栈.append(初始快照)
        return 记录

    def 推进阶段(self, 提议ID: str, 节点列表: List[str]) -> Tuple[执行阶段, List[str]]:
        """
        推进到下一个灰度阶段
        
        Args:
            提议ID: 治理提议ID
            节点列表: 所有节点ID列表
            
        Returns:
            (新阶段, 本阶段涉及的节点列表)
        """
        记录 = self._执行记录.get(提议ID)
        if not 记录:
            raise ValueError(f"未找到提议{提议ID}的执行记录")

        # 确定下一阶段
        当前索引 = -1
        for i, (阶段, _) in enumerate(self.阶段进度):
            if 记录.当前阶段 == 阶段:
                当前索引 = i
                break

        下一索引 = 当前索引 + 1
        if 下一索引 >= len(self.阶段进度):
            # 已到最后阶段，标记完成
            记录.当前阶段 = 执行阶段.已完成
            记录.结束时间 = time.time()
            return 执行阶段.已完成, []

        新阶段, 比例 = self.阶段进度[下一索引]
        记录.当前阶段 = 新阶段
        记录.阶段历史.append(新阶段)

        # 选择参与本阶段的节点
        参与数 = max(1, int(len(节点列表) * 比例))
        参与节点 = 节点列表[:参与数]

        # 保存快照
        快照 = 阶段快照(
            阶段=新阶段,
            参数值=copy.deepcopy(self._当前参数),
            节点列表=参与节点,
        )
        记录.快照栈.append(快照)

        return 新阶段, 参与节点

    def 报告指标(self, 提议ID: str, 指标: 监控指标) -> Tuple[bool, Optional[回滚原因]]:
        """
        报告当前阶段的监控指标
        
        Returns:
            (是否正常, 回滚原因如果异常)
        """
        记录 = self._执行记录.get(提议ID)
        if not 记录:
            return False, None

        记录.监控历史.append(指标)
        异常, 原因描述 = 指标.是否异常(self.监控阈值)

        if 异常:
            回滚原因 = self._判断回滚原因(原因描述)
            return False, 回滚原因

        return True, None

    def _判断回滚原因(self, 原因描述: str) -> 回滚原因:
        """根据异常描述判断回滚原因"""
        if "交易成功率" in 原因描述:
            return 回滚原因.指标恶化
        elif "错误率" in 原因描述:
            return 回滚原因.错误率超限
        elif "共识延迟" in 原因描述:
            return 回滚原因.共识异常
        else:
            return 回滚原因.指标恶化

    def 回滚(self, 提议ID: str, 原因: 回滚原因 = 回滚原因.手动触发) -> bool:
        """
        回滚到上一个稳定阶段
        
        Args:
            提议ID: 治理提议ID
            原因: 回滚原因
        """
        记录 = self._执行记录.get(提议ID)
        if not 记录:
            return False

        if 记录.回滚次数 >= self.最大回滚次数:
            # 超过最大回滚次数，彻底回滚到初始状态
            if len(记录.快照栈) > 0:
                初始快照 = 记录.快照栈[0]
                self._当前参数 = copy.deepcopy(初始快照.参数值)
            记录.当前阶段 = 执行阶段.已回滚
            记录.最后回滚原因 = 原因
            记录.结束时间 = time.time()
            return True

        # 回滚到上一个快照
        if len(记录.快照栈) > 1:
            记录.快照栈.pop()  # 弹出当前阶段快照
            上一快照 = 记录.快照栈[-1]
            self._当前参数 = copy.deepcopy(上一快照.参数值)
            # 回退到上一个阶段
            阶段索引 = None
            for i, (阶段, _) in enumerate(self.阶段进度):
                if 阶段 == 上一快照.阶段:
                    阶段索引 = i
                    break
            if 阶段索引 is not None and 阶段索引 > 0:
                记录.当前阶段 = self.阶段进度[阶段索引 - 1][0] if 阶段索引 > 0 else 执行阶段.未开始
            else:
                记录.当前阶段 = 执行阶段.未开始

        记录.回滚次数 += 1
        记录.最后回滚原因 = 原因
        return True

    def 获取执行进度(self, 提议ID: str) -> float:
        """获取执行进度（0~1）"""
        记录 = self._执行记录.get(提议ID)
        if not 记录:
            return 0.0
        for i, (阶段, 比例) in enumerate(self.阶段进度):
            if 记录.当前阶段 == 阶段:
                return 比例
        if 记录.当前阶段 == 执行阶段.已完成:
            return 1.0
        return 0.0

    def 获取记录(self, 提议ID: str) -> Optional[执行记录]:
        """获取执行记录"""
        return self._执行记录.get(提议ID)

    def 列出执行中(self) -> List[str]:
        """列出正在执行中的提议ID"""
        return [
            pid for pid, 记录 in self._执行记录.items()
            if 记录.当前阶段 not in (执行阶段.已完成, 执行阶段.已回滚, 执行阶段.未开始)
        ]
