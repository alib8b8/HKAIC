"""
HKC 涌现治理模块 (emergent_governance/)
========================================
传统链：提案→投票→执行，人来决策
HKC玩法：AI实时观测链上行为涌现出什么模式，自动提议调整参数。
节点用涌现分数投票权决定。人定方向，AI定细节。

子模块：
  - emergence_detector: 涌现模式检测器
  - proposal_engine: AI自动提议引擎
  - emergence_voting: 涌现分数投票
  - gradual_executor: 灰度执行器
  - governance_coordinator: 治理协调器
"""

from .emergence_detector import 涌现检测器, 涌现报告, 涌现等级, 信号数据, 信号类型
from .proposal_engine import 提议引擎, 治理提议, 提议状态, 提议类型, 影响评估
from .emergence_voting import 涌现投票器, 投票选项, 投票策略, 投票结果
from .gradual_executor import 灰度执行器, 执行阶段, 监控指标, 回滚原因
from .governance_coordinator import 治理协调器, 治理流程, 治理阶段
