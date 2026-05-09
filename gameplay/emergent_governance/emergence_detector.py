"""
HKC 涌现模式检测器 (emergence_detector.py)
============================================
AI实时观测链上行为的涌现模式——Gas波动、交易聚类、质押异动等。
使用滑动窗口+统计异常检测，当检测到涌现模式时自动触发治理提议。

核心概念：
  - 涌现信号（Emergence Signal）：链上指标偏离基线的程度
  - 滑动窗口（Sliding Window）：只看最近N个区块/时段的数据
  - 异常阈值（Anomaly Threshold）：偏离均值几倍标准差视为异常
  - 涌现分数（Emergence Score）：综合多个信号的涌现强度

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
import copy
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 信号类型(Enum):
    """涌现信号类型"""
    GAS波动 = "gas_volatility"
    交易聚类 = "tx_clustering"
    质押异动 = "staking_anomaly"
    治理参与 = "governance_participation"
    跨链流量 = "crosschain_flow"
    共识延迟 = "consensus_delay"


class 涌现等级(Enum):
    """涌现强度等级"""
    正常 = "normal"
    低度 = "low"
    中度 = "medium"
    高度 = "high"
    危急 = "critical"


@dataclass
class 信号数据:
    """单个信号的数据点"""
    类型: 信号类型
    值: float
    时间戳: float = 0.0
    区块高度: int = 0
    元数据: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()


@dataclass
class 涌现报告:
    """涌现检测报告"""
    报告ID: str = ""
    时间戳: float = 0.0
    等级: 涌现等级 = 涌现等级.正常
    活跃信号: List[信号类型] = field(default_factory=list)
    涌现分数: float = 0.0
    详情: Dict[str, Any] = field(default_factory=dict)
    建议行动: str = ""

    def __post_init__(self):
        if not self.报告ID:
            self.报告ID = hashlib.sha256(
                f"{self.时间戳}{self.涌现分数}".encode()
            ).hexdigest()[:16]
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()


class 涌现检测器:
    """
    涌现模式检测器
    
    使用滑动窗口统计方法，实时检测链上行为的涌现模式。
    每种信号类型独立维护窗口，综合计算涌现分数。
    """

    def __init__(
        self,
        窗口大小: int = 100,
        异常倍数: float = 2.0,
        高度倍数: float = 3.0,
        危急倍数: float = 4.0,
        检测间隔: int = 10,
    ):
        """
        初始化检测器
        
        Args:
            窗口大小: 滑动窗口数据点数
            异常倍数: 偏离均值几倍标准差视为低度异常
            高度倍数: 高度涌现阈值
            危急倍数: 危急涌现阈值
            检测间隔: 每隔多少区块检测一次
        """
        self.窗口大小 = 窗口大小
        self.异常倍数 = 异常倍数
        self.高度倍数 = 高度倍数
        self.危急倍数 = 危急倍数
        self.检测间隔 = 检测间隔

        # 每种信号的滑动窗口
        self._窗口: Dict[信号类型, deque] = {
            t: deque(maxlen=窗口大小) for t in 信号类型
        }
        # 基线参数（可自适应更新）
        self._基线: Dict[信号类型, Tuple[float, float]] = {
            t: (0.0, 1.0) for t in 信号类型
        }
        # 检测历史
        self._历史报告: List[涌现报告] = []
        self._上次检测高度: int = 0

    def 添加信号(self, 数据: 信号数据) -> None:
        """添加一个信号数据点到窗口"""
        self._窗口[数据.类型].append(数据.值)
        # 更新基线（指数移动平均）
        当前均值, 当前标准差 = self._基线[数据.类型]
        alpha = 2.0 / (self.窗口大小 + 1)
        新均值 = alpha * 数据.值 + (1 - alpha) * 当前均值
        diff = 数据.值 - 新均值
        新方差 = alpha * (diff ** 2) + (1 - alpha) * (当前标准差 ** 2)
        self._基线[数据.类型] = (新均值, math.sqrt(max(0, 新方差)))

    def 批量添加(self, 数据列表: List[信号数据]) -> None:
        """批量添加信号数据"""
        for 数据 in 数据列表:
            self.添加信号(数据)

    def 计算信号偏差(self, 类型: 信号类型) -> float:
        """
        计算某类型信号的最新偏差（z-score）
        返回偏离均值几倍标准差
        """
        窗口 = self._窗口[类型]
        if len(窗口) == 0:
            return 0.0
        最新值 = 窗口[-1]
        均值, 标准差 = self._基线[类型]
        if 标准差 < 1e-10:
            return 0.0
        return abs(最新值 - 均值) / 标准差

    def 计算涌现分数(self) -> float:
        """
        计算综合涌现分数（0~1）
        所有信号偏差的加权平均，归一化到[0,1]
        """
        总偏差 = 0.0
        权重 = {
            信号类型.GAS波动: 1.0,
            信号类型.交易聚类: 1.2,
            信号类型.质押异动: 1.5,
            信号类型.治理参与: 0.8,
            信号类型.跨链流量: 1.0,
            信号类型.共识延迟: 2.0,
        }
        加权偏差和 = 0.0
        权重和 = 0.0
        for 类型 in 信号类型:
            偏差 = self.计算信号偏差(类型)
            w = 权重.get(类型, 1.0)
            加权偏差和 += 偏差 * w
            权重和 += w

        if 权重和 == 0:
            return 0.0
        平均偏差 = 加权偏差和 / 权重和
        # 用sigmoid归一化到[0,1]，中点在2倍标准差
        分数 = 1.0 / (1.0 + math.exp(-1.5 * (平均偏差 - 2.0)))
        return round(分数, 4)

    def 判断涌现等级(self, 涌现分数: float) -> 涌现等级:
        """根据涌现分数判断等级"""
        if 涌现分数 < 0.2:
            return 涌现等级.正常
        elif 涌现分数 < 0.4:
            return 涌现等级.低度
        elif 涌现分数 < 0.6:
            return 涌现等级.中度
        elif 涌现分数 < 0.8:
            return 涌现等级.高度
        else:
            return 涌现等级.危急

    def 检测(self, 当前区块高度: int = 0) -> 涌现报告:
        """
        执行一次涌现检测，返回报告
        
        Args:
            当前区块高度: 当前区块高度（用于判断检测间隔）
        """
        # 检查检测间隔
        if 当前区块高度 > 0:
            if 当前区块高度 - self._上次检测高度 < self.检测间隔:
                return 涌现报告(等级=涌现等级.正常, 涌现分数=0.0)
            self._上次检测高度 = 当前区块高度

        # 计算涌现分数
        分数 = self.计算涌现分数()
        等级 = self.判断涌现等级(分数)

        # 收集活跃信号
        活跃信号 = []
        信号详情 = {}
        for 类型 in 信号类型:
            偏差 = self.计算信号偏差(类型)
            if 偏差 >= self.异常倍数:
                活跃信号.append(类型)
                均值, 标准差 = self._基线[类型]
                窗口 = self._窗口[类型]
                当前值 = list(窗口)[-1] if len(窗口) > 0 else 0.0
                信号详情[类型.value] = {
                    "偏差": round(偏差, 2),
                    "当前值": round(当前值, 4),
                    "基线均值": round(均值, 4),
                    "基线标准差": round(标准差, 4),
                }

        # 生成建议行动
        建议 = self._生成建议(等级, 活跃信号)

        报告 = 涌现报告(
            等级=等级,
            活跃信号=活跃信号,
            涌现分数=分数,
            详情=信号详情,
            建议行动=建议,
        )

        if 等级 != 涌现等级.正常:
            self._历史报告.append(报告)

        return 报告

    def _生成建议(self, 等级: 涌现等级, 活跃信号: List[信号类型]) -> str:
        """根据涌现等级和活跃信号生成建议"""
        if 等级 == 涌现等级.正常:
            return "系统运行正常，无需行动"

        建议 = []
        if 信号类型.GAS波动 in 活跃信号:
            建议.append("考虑调整区块Gas上限")
        if 信号类型.交易聚类 in 活跃信号:
            建议.append("检测到交易聚类，可能存在MEV攻击")
        if 信号类型.质押异动 in 活跃信号:
            建议.append("质押异动显著，建议检查验证者健康度")
        if 信号类型.治理参与 in 活跃信号:
            建议.append("治理参与率异常，可能需要调整激励")
        if 信号类型.跨链流量 in 活跃信号:
            建议.append("跨链流量异动，检查桥安全性")
        if 信号类型.共识延迟 in 活跃信号:
            建议.append("共识延迟升高，检查节点网络状况")

        前缀 = {
            涌现等级.低度: "【低度涌现】观察中：",
            涌现等级.中度: "【中度涌现】建议行动：",
            涌现等级.高度: "【高度涌现】强烈建议：",
            涌现等级.危急: "【危急涌现】立即处理：",
        }
        return 前缀.get(等级, "") + "；".join(建议) if 建议 else "无具体建议"

    def 获取历史(self, 最低等级: 涌现等级 = 涌现等级.低度) -> List[涌现报告]:
        """获取历史涌现报告"""
        等级排序 = list(涌现等级)
        最低索引 = 等级排序.index(最低等级)
        return [r for r in self._历史报告 if 等级排序.index(r.等级) >= 最低索引]

    def 重置基线(self, 类型: Optional[信号类型] = None) -> None:
        """重置基线参数（用于大范围参数调整后重新校准）"""
        if 类型:
            self._基线[类型] = (0.0, 1.0)
            self._窗口[类型].clear()
        else:
            for t in 信号类型:
                self._基线[t] = (0.0, 1.0)
                self._窗口[t].clear()

    def 获取窗口统计(self, 类型: 信号类型) -> Dict[str, float]:
        """获取某信号类型的窗口统计信息"""
        窗口 = list(self._窗口[类型])
        if not 窗口:
            return {"数据量": 0, "均值": 0.0, "标准差": 0.0, "最新值": 0.0}
        均值 = sum(窗口) / len(窗口)
        方差 = sum((x - 均值) ** 2 for x in 窗口) / len(窗口)
        return {
            "数据量": len(窗口),
            "均值": round(均值, 4),
            "标准差": round(math.sqrt(方差), 4),
            "最新值": round(窗口[-1], 4),
        }
