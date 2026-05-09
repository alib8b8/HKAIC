"""
HKC AI自动提议引擎 (proposal_engine.py)
========================================
当涌现检测器发现异常模式后，AI自动生成治理提议。
不是人来写提案，而是AI根据链上数据+历史治理模式自动拟稿。

核心概念：
  - 提议模板（Proposal Template）：针对不同涌现模式的预设提议框架
  - 参数推断（Parameter Inference）：AI根据历史数据推断最优参数
  - 影响评估（Impact Assessment）：预测提议执行后的影响

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 提议类型(Enum):
    """治理提议类型"""
    参数调整 = "param_adjust"
    紧急暂停 = "emergency_pause"
    升级提案 = "upgrade_proposal"
    激励调整 = "incentive_adjust"
    安全响应 = "security_response"
    共识修改 = "consensus_modify"


class 提议状态(Enum):
    """提议状态"""
    草稿 = "draft"
    待投票 = "pending_vote"
    投票中 = "voting"
    已通过 = "passed"
    已否决 = "rejected"
    执行中 = "executing"
    已完成 = "completed"
    已回滚 = "rolled_back"


@dataclass
class 参数变更:
    """单个参数变更"""
    参数名: str
    当前值: float
    建议值: float
    变更幅度: float = 0.0
    理由: str = ""

    def __post_init__(self):
        if self.变更幅度 == 0.0 and self.当前值 != 0:
            self.变更幅度 = (self.建议值 - self.当前值) / abs(self.当前值)


@dataclass
class 影响评估:
    """提议执行的影响评估"""
    风险等级: str = "medium"  # low/medium/high/critical
    影响范围: List[str] = field(default_factory=list)
    预期收益: float = 0.0
    潜在损失: float = 0.0
    收益风险比: float = 0.0
    置信度: float = 0.0  # 0~1

    def 计算收益风险比(self) -> float:
        if self.潜在损失 == 0:
            return float('inf') if self.预期收益 > 0 else 0.0
        self.收益风险比 = round(self.预期收益 / self.潜在损失, 4)
        return self.收益风险比


@dataclass
class 治理提议:
    """治理提议"""
    提议ID: str = ""
    类型: 提议类型 = 提议类型.参数调整
    标题: str = ""
    描述: str = ""
    触发报告ID: str = ""  # 触发此提议的涌现报告ID
    参数变更列表: List[参数变更] = field(default_factory=list)
    影响评估: Optional[影响评估] = None
    状态: 提议状态 = 提议状态.草稿
    创建时间: float = 0.0
    投票截止: float = 0.0
    投票期秒: int = 86400  # 默认1天投票期
    支持票: int = 0
    反对票: int = 0
    弃权票: int = 0
    执行进度: float = 0.0  # 0~1

    def __post_init__(self):
        if not self.提议ID:
            self.提议ID = hashlib.sha256(
                f"{self.类型.value}{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()
        if self.投票截止 == 0.0:
            self.投票截止 = self.创建时间 + self.投票期秒


class 提议模板库:
    """
    提议模板库
    
    针对不同涌现信号预设的提议模板，AI根据模板框架自动填充参数。
    """

    def __init__(self):
        self._模板: Dict[信号类型映射, Dict] = {}
        self._初始化默认模板()

    def _初始化默认模板(self):
        """初始化默认模板"""
        # Gas波动模板
        self._模板["gas_volatility"] = {
            "提议类型": 提议类型.参数调整,
            "标题模板": "Gas波动异常：调整区块Gas上限",
            "参数变更": [
                {"参数名": "block_gas_limit", "调整方向": "increase"},
                {"参数名": "min_gas_price", "调整方向": "adjust"},
            ],
            "投票期": 43200,  # 12小时（紧急）
        }
        # 交易聚类模板
        self._模板["tx_clustering"] = {
            "提议类型": 提议类型.安全响应,
            "标题模板": "交易聚类异常：启动MEV防护",
            "参数变更": [
                {"参数名": "mev_protection_level", "调整方向": "increase"},
                {"参数名": "tx_ordering_delay", "调整方向": "increase"},
            ],
            "投票期": 21600,  # 6小时
        }
        # 质押异动模板
        self._模板["staking_anomaly"] = {
            "提议类型": 提议类型.安全响应,
            "标题模板": "质押异动：检查验证者集",
            "参数变更": [
                {"参数名": "validator_min_stake", "调整方向": "increase"},
                {"参数名": "unbonding_period", "调整方向": "increase"},
            ],
            "投票期": 43200,
        }
        # 共识延迟模板
        self._模板["consensus_delay"] = {
            "提议类型": 提议类型.紧急暂停,
            "标题模板": "共识延迟危急：紧急降速",
            "参数变更": [
                {"参数名": "block_interval", "调整方向": "increase"},
                {"参数名": "timeout_threshold", "调整方向": "decrease"},
            ],
            "投票期": 3600,  # 1小时（最紧急）
        }

    def 获取模板(self, 信号类型值: str) -> Optional[Dict]:
        """根据信号类型获取模板"""
        return self._模板.get(信号类型值)

    def 列出所有模板(self) -> List[str]:
        """列出所有可用模板"""
        return list(self._模板.keys())


# 信号类型字符串映射（从emergence_detector的信号类型映射）
信号类型映射 = {
    "gas_volatility": "gas_volatility",
    "tx_clustering": "tx_clustering",
    "staking_anomaly": "staking_anomaly",
    "governance_participation": "incentive_adjust",
    "crosschain_flow": "security_response",
    "consensus_delay": "consensus_delay",
}


class 提议引擎:
    """
    AI自动提议引擎
    
    接收涌现检测器的报告，自动生成治理提议。
    包含模板匹配、参数推断、影响评估三个核心流程。
    """

    def __init__(self, 模板库: Optional[提议模板库] = None):
        self.模板库 = 模板库 or 提议模板库()
        self._提议池: Dict[str, 治理提议] = {}
        self._参数历史: Dict[str, List[Tuple[float, float]]] = {}  # 参数名 -> [(时间, 值)]
        self._提议计数: int = 0

    def 根据涌现报告生成提议(self, 涌现报告: Any) -> Optional[治理提议]:
        """
        根据涌现报告自动生成治理提议
        
        Args:
            涌现报告: 涌现检测器输出的报告对象
            
        Returns:
            生成的治理提议，如果等级正常则返回None
        """
        # 只对中度及以上涌现生成提议
        等级 = 涌现报告.等级
        等级排序 = ["normal", "low", "medium", "high", "critical"]
        等级值 = 等级.value if hasattr(等级, 'value') else str(等级)
        等级索引 = 等级排序.index(等级值) if 等级值 in 等级排序 else 0
        if 等级索引 < 2:  # normal和low不生成
            return None

        # 匹配模板
        活跃信号 = 涌现报告.活跃信号
        if not 活跃信号:
            return None

        # 取最严重的信号生成提议
        主要信号 = 活跃信号[0]
        信号值 = 主要信号.value if hasattr(主要信号, 'value') else str(主要信号)
        模板 = self.模板库.获取模板(信号类型映射.get(信号值, ""))

        if not 模板:
            # 无匹配模板，生成通用提议
            return self._生成通用提议(涌现报告)

        # 根据模板生成提议
        参数变更列表 = []
        for 变更模板 in 模板["参数变更"]:
            当前值 = self._获取当前参数(变更模板["参数名"])
            建议值 = self._推断参数值(变更模板["参数名"], 当前值, 变更模板["调整方向"], 涌现报告)
            参数变更列表.append(参数变更(
                参数名=变更模板["参数名"],
                当前值=当前值,
                建议值=建议值,
                理由=f"基于{信号值}涌现信号自动推断",
            ))

        # 影响评估
        评估 = self._评估影响(参数变更列表, 涌现报告)

        提议 = 治理提议(
            类型=模板["提议类型"],
            标题=模板["标题模板"],
            描述=f"由AI提议引擎基于涌现报告{涌现报告.报告ID}自动生成",
            触发报告ID=涌现报告.报告ID,
            参数变更列表=参数变更列表,
            影响评估=评估,
            投票期秒=模板["投票期"],
        )

        self._提议池[提议.提议ID] = 提议
        self._提议计数 += 1
        return 提议

    def _生成通用提议(self, 涌现报告: Any) -> 治理提议:
        """生成通用观察提议"""
        提议 = 治理提议(
            类型=提议类型.参数调整,
            标题="链上涌现模式观察提议",
            描述=f"检测到涌现分数{涌现报告.涌现分数:.2f}，建议社区关注",
            触发报告ID=涌现报告.报告ID,
            投票期秒=86400,
        )
        self._提议池[提议.提议ID] = 提议
        self._提议计数 += 1
        return 提议

    def _获取当前参数(self, 参数名: str) -> float:
        """获取参数当前值"""
        历史 = self._参数历史.get(参数名, [])
        if 历史:
            return 历史[-1][1]
        # 默认参数值
        默认值 = {
            "block_gas_limit": 30000000,
            "min_gas_price": 1.0,
            "mev_protection_level": 1.0,
            "tx_ordering_delay": 0.5,
            "validator_min_stake": 1000.0,
            "unbonding_period": 86400.0,
            "block_interval": 5.0,
            "timeout_threshold": 30.0,
        }
        return 默认值.get(参数名, 0.0)

    def _推断参数值(self, 参数名: str, 当前值: float, 方向: str, 报告: Any) -> float:
        """根据涌现报告推断建议参数值"""
        涌现分数 = 报告.涌现分数
        # 基于涌现分数的调整幅度：分数越高，调整越大
        调整比例 = 涌现分数 * 0.3  # 最大30%调整

        if 方向 == "increase":
            return 当前值 * (1 + 调整比例)
        elif 方向 == "decrease":
            return 当前值 * (1 - 调整比例)
        else:  # adjust
            return 当前值 * (1 + 调整比例 * 0.5)

    def _评估影响(self, 参数变更列表: List[参数变更], 报告: Any) -> 影响评估:
        """评估参数变更的影响"""
        总变更幅度 = sum(abs(p.变更幅度) for p in 参数变更列表)
        风险 = "low" if 总变更幅度 < 0.1 else "medium" if 总变更幅度 < 0.3 else "high"

        评估 = 影响评估(
            风险等级=风险,
            影响范围=[p.参数名 for p in 参数变更列表],
            预期收益=1.0 - 报告.涌现分数,  # 修正后预期恢复正常
            潜在损失=报告.涌现分数 * 总变更幅度,
            置信度=max(0.5, 1.0 - 总变更幅度),
        )
        评估.计算收益风险比()
        return 评估

    def 获取提议(self, 提议ID: str) -> Optional[治理提议]:
        """获取指定提议"""
        return self._提议池.get(提议ID)

    def 列出提议(self, 状态过滤: Optional[提议状态] = None) -> List[治理提议]:
        """列出所有提议"""
        提议列表 = list(self._提议池.values())
        if 状态过滤:
            提议列表 = [p for p in 提议列表 if p.状态 == 状态过滤]
        return sorted(提议列表, key=lambda p: p.创建时间, reverse=True)

    def 更新提议状态(self, 提议ID: str, 新状态: 提议状态) -> bool:
        """更新提议状态"""
        提议 = self._提议池.get(提议ID)
        if not 提议:
            return False
        提议.状态 = 新状态
        return True
