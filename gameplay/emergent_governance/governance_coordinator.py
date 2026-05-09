"""
HKC 涌现治理协调器 (governance_coordinator.py)
===============================================
协调涌现检测→提议生成→投票→灰度执行的完整治理流程。
这是涌现治理模块的"大脑"，串联所有子模块。

核心概念：
  - 治理流程（Governance Flow）：检测→提议→投票→执行→监控
  - 紧急通道（Emergency Channel）：危急涌现可跳过投票直接执行
  - 治理审计（Governance Audit）：所有治理操作有审计轨迹

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from .emergence_detector import 涌现检测器, 涌现报告, 涌现等级, 信号数据, 信号类型
from .proposal_engine import 提议引擎, 治理提议, 提议状态, 提议类型
from .emergence_voting import 涌现投票器, 投票选项, 投票策略, 投票结果
from .gradual_executor import 灰度执行器, 执行阶段, 监控指标, 回滚原因


class 治理阶段(Enum):
    """治理流程阶段"""
    检测中 = "detecting"
    提议中 = "proposing"
    投票中 = "voting"
    执行中 = "executing"
    监控中 = "monitoring"
    完成 = "completed"
    回滚中 = "rolling_back"
    紧急执行 = "emergency"


@dataclass
class 治理流程:
    """一次完整的治理流程"""
    流程ID: str = ""
    当前阶段: 治理阶段 = 治理阶段.检测中
    涌现报告: Optional[涌现报告] = None
    治理提议: Optional[治理提议] = None
    投票结果: Optional[投票结果] = None
    执行记录ID: Optional[str] = None
    开始时间: float = 0.0
    结束时间: float = 0.0
    紧急模式: bool = False
    审计日志: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if not self.流程ID:
            self.流程ID = hashlib.sha256(
                f"governance_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.开始时间 == 0.0:
            self.开始时间 = time.time()

    def 记录审计(self, 动作: str, 详情: str) -> None:
        """记录审计日志"""
        self.审计日志.append({
            "时间": time.time(),
            "阶段": self.当前阶段.value,
            "动作": 动作,
            "详情": 详情,
        })


class 治理协调器:
    """
    涌现治理协调器
    
    串联涌现检测、提议生成、投票、灰度执行的完整流程。
    """

    def __init__(
        self,
        检测器: Optional[涌现检测器] = None,
        提议引擎实例: Optional[提议引擎] = None,
        投票器: Optional[涌现投票器] = None,
        执行器: Optional[灰度执行器] = None,
        紧急阈值: 涌现等级 = 涌现等级.危急,
        自动执行: bool = True,
    ):
        """
        初始化协调器
        
        Args:
            检测器: 涌现检测器实例
            提议引擎实例: 提议引擎实例
            投票器: 涌现投票器实例
            执行器: 灰度执行器实例
            紧急阈值: 触发紧急通道的涌现等级
            自动执行: 投票通过后是否自动启动灰度执行
        """
        self.检测器 = 检测器 or 涌现检测器()
        self.提议引擎实例 = 提议引擎实例 or 提议引擎()
        self.投票器 = 投票器 or 涌现投票器()
        self.执行器 = 执行器 or 灰度执行器()
        self.紧急阈值 = 紧急阈值
        self.自动执行 = 自动执行

        self._活跃流程: Dict[str, 治理流程] = {}
        self._历史流程: List[治理流程] = []
        self._治理统计 = {
            "总流程数": 0,
            "成功数": 0,
            "回滚数": 0,
            "紧急执行数": 0,
        }

    def 注入信号(self, 信号: 信号数据) -> Optional[治理流程]:
        """
        注入链上信号，触发检测→提议流程
        
        Args:
            信号: 链上信号数据
            
        Returns:
            如果触发了治理流程则返回流程对象，否则None
        """
        self.检测器.添加信号(信号)
        报告 = self.检测器.检测()

        if 报告.等级 == 涌现等级.正常:
            return None

        # 创建治理流程
        流程 = 治理流程(
            当前阶段=治理阶段.检测中,
            涌现报告=报告,
        )
        流程.记录审计("涌现检测", f"等级={报告.等级.value}, 分数={报告.涌现分数}")

        # 检查是否需要紧急执行
        等级排序 = list(涌现等级)
        if 等级排序.index(报告.等级) >= 等级排序.index(self.紧急阈值):
            流程.紧急模式 = True
            流程.当前阶段 = 治理阶段.紧急执行
            流程.记录审计("紧急通道", "跳过投票直接执行")
            self._治理统计["紧急执行数"] += 1

        self._活跃流程[流程.流程ID] = 流程
        self._治理统计["总流程数"] += 1
        return 流程

    def 推进提议(self, 流程ID: str) -> Optional[治理提议]:
        """将流程推进到提议阶段"""
        流程 = self._活跃流程.get(流程ID)
        if not 流程 or not 流程.涌现报告:
            return None

        提议 = self.提议引擎实例.根据涌现报告生成提议(流程.涌现报告)
        if 提议:
            流程.治理提议 = 提议
            流程.当前阶段 = 治理阶段.提议中
            提议.状态 = 提议状态.待投票
            流程.记录审计("生成提议", f"提议ID={提议.提议ID}, 类型={提议.类型.value}")
        return 提议

    def 推进投票(self, 流程ID: str) -> bool:
        """将流程推进到投票阶段"""
        流程 = self._活跃流程.get(流程ID)
        if not 流程 or not 流程.治理提议:
            return False

        流程.当前阶段 = 治理阶段.投票中
        流程.治理提议.状态 = 提议状态.投票中
        流程.记录审计("开始投票", f"提议ID={流程.治理提议.提议ID}")
        return True

    def 执行投票(self, 流程ID: str, 节点ID: str, 选项: 投票选项) -> bool:
        """在指定流程中执行投票"""
        流程 = self._活跃流程.get(流程ID)
        if not 流程 or not 流程.治理提议:
            return False

        try:
            self.投票器.投票(流程.治理提议.提议ID, 节点ID, 选项)
            流程.记录审计("投票", f"节点={节点ID}, 选项={选项.value}")
            return True
        except ValueError:
            return False

    def 统计投票(self, 流程ID: str, 总节点数: int = 0) -> Optional[投票结果]:
        """统计投票结果"""
        流程 = self._活跃流程.get(流程ID)
        if not 流程 or not 流程.治理提议:
            return None

        结果 = self.投票器.统计结果(流程.治理提议.提议ID, 总节点数)
        流程.投票结果 = 结果

        if 结果.是否通过:
            流程.当前阶段 = 治理阶段.执行中
            流程.治理提议.状态 = 提议状态.执行中
            流程.记录审计("投票通过", f"支持率={结果.支持率:.2%}")

            if self.自动执行:
                self.启动执行(流程ID)
        else:
            流程.当前阶段 = 治理阶段.完成
            流程.治理提议.状态 = 提议状态.已否决
            流程.记录审计("投票否决", f"支持率={结果.支持率:.2%}")
            self._归档流程(流程ID)

        return 结果

    def 启动执行(self, 流程ID: str) -> bool:
        """启动灰度执行"""
        流程 = self._活跃流程.get(流程ID)
        if not 流程 or not 流程.治理提议:
            return False

        参数变更 = {}
        for 变更 in 流程.治理提议.参数变更列表:
            参数变更[变更.参数名] = (变更.当前值, 变更建议值)

        记录 = self.执行器.开始执行(流程.治理提议.提议ID, 参数变更)
        流程.执行记录ID = 流程.治理提议.提议ID
        流程.当前阶段 = 治理阶段.执行中
        流程.记录审计("启动执行", f"参数变更数={len(参数变更)}")
        return True

    def 推进执行(self, 流程ID: str, 节点列表: List[str]) -> Optional[执行阶段]:
        """推进灰度执行"""
        流程 = self._活跃流程.get(流程ID)
        if not 流程 or not 流程.执行记录ID:
            return None

        新阶段, 参与节点 = self.执行器.推进阶段(流程.执行记录ID, 节点列表)
        流程.记录审计("推进执行", f"阶段={新阶段.value}, 参与节点={len(参与节点)}")

        if 新阶段 == 执行阶段.已完成:
            流程.当前阶段 = 治理阶段.完成
            if 流程.治理提议:
                流程.治理提议.状态 = 提议状态.已完成
            self._治理统计["成功数"] += 1
            self._归档流程(流程ID)

        return 新阶段

    def 报告执行指标(self, 流程ID: str, 指标: 监控指标) -> Tuple[bool, Optional[回滚原因]]:
        """报告执行期间的监控指标"""
        流程 = self._活跃流程.get(流程ID)
        if not 流程 or not 流程.执行记录ID:
            return True, None

        正常, 原因 = self.执行器.报告指标(流程.执行记录ID, 指标)
        if not 正常 and 原因:
            流程.记录审计("异常检测", f"原因={原因.value}")
            self.执行器.回滚(流程.执行记录ID, 原因)
            流程.当前阶段 = 治理阶段.回滚中
            记录 = self.执行器.获取记录(流程.执行记录ID)
            if 记录 and 记录.当前阶段 == 执行阶段.已回滚:
                流程.当前阶段 = 治理阶段.完成
                if 流程.治理提议:
                    流程.治理提议.状态 = 提议状态.已回滚
                self._治理统计["回滚数"] += 1
                self._归档流程(流程ID)

        return 正常, 原因

    def _归档流程(self, 流程ID: str) -> None:
        """归档已完成的流程"""
        流程 = self._活跃流程.pop(流程ID, None)
        if 流程:
            流程.结束时间 = time.time()
            self._历史流程.append(流程)

    def 获取流程(self, 流程ID: str) -> Optional[治理流程]:
        """获取治理流程"""
        return self._活跃流程.get(流程ID) or next(
            (f for f in self._历史流程 if f.流程ID == 流程ID), None
        )

    def 获取统计(self) -> Dict[str, int]:
        """获取治理统计"""
        return copy.deepcopy(self._治理统计)

    def 列出活跃流程(self) -> List[治理流程]:
        """列出所有活跃流程"""
        return list(self._活跃流程.values())


import copy
