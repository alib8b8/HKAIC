"""
HKC Solver竞争 (solver_competition.py)
======================================
Solver竞争执行用户意图——谁给出的执行路径最优，谁就赢得执行权。
竞争维度：价格最优、速度最快、可靠性最高。

核心概念：
  - Solver（求解器）：意图的执行者，竞争提供最优路径
  - 竞标（Bid）：Solver提交的执行方案
  - 评分（Scoring）：综合多维度对竞标打分

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 竞标状态(Enum):
    """竞标状态"""
    已提交 = "submitted"
    验证中 = "validating"
    有效 = "valid"
    无效 = "invalid"
    中标 = "won"
    未中标 = "lost"
    执行中 = "executing"
    已完成 = "completed"
    已惩罚 = "slashed"


@dataclass
class Solver信息:
    """Solver注册信息"""
    SolverID: str
    名称: str = ""
    ATH验证: bool = False         # 是否通过ATH身份验证
    历史成功率: float = 0.0      # 0~1
    累计执行量: float = 0.0
    信誉分数: float = 1.0        # 0~10
    资金锁定: float = 0.0        # 质押的资金量
    注册时间: float = 0.0
    惩罚次数: int = 0

    def __post_init__(self):
        if self.注册时间 == 0.0:
            self.注册时间 = time.time()


@dataclass
class 执行路径:
    """Solver提供的执行路径"""
    步骤: List[Dict[str, Any]] = field(default_factory=list)
    预计输出量: float = 0.0
    预计Gas费: float = 0.0
    预计耗时秒: float = 0.0
    经过链: List[str] = field(default_factory=list)
    风险评分: float = 0.0  # 0~1, 越低越安全

    def 计算综合评分(self, 价格权重: float = 0.5, 速度权重: float = 0.2, 安全权重: float = 0.3) -> float:
        """计算路径综合评分"""
        价格分 = self.预计输出量  # 越高越好
        速度分 = 1.0 / (1.0 + self.预计耗时秒 / 60.0)  # 越快越好
        安全分 = 1.0 - self.风险评分  # 越安全越好
        return 价格权重 * 价格分 + 速度权重 * 速度分 + 安全权重 * 安全分


@dataclass
class 竞标:
    """Solver竞标"""
    竞标ID: str = ""
    意图ID: str = ""
    SolverID: str = ""
    路径: 执行路径 = field(default_factory=执行路径)
    报价输出量: float = 0.0
    服务费: float = 0.0
    状态: 竞标状态 = 竞标状态.已提交
    综合评分: float = 0.0
    创建时间: float = 0.0

    def __post_init__(self):
        if not self.竞标ID:
            self.竞标ID = hashlib.sha256(
                f"bid_{self.SolverID}_{self.意图ID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()


class Solver竞争器:
    """
    Solver竞争器
    
    管理Solver注册、竞标提交、竞标评分和中标选择。
    """

    def __init__(
        self,
        竞标窗口秒: float = 30.0,
        最少Solver数: int = 2,
        信誉阈值: float = 3.0,
        价格权重: float = 0.5,
        速度权重: float = 0.2,
        安全权重: float = 0.3,
    ):
        """
        初始化竞争器
        
        Args:
            竞标窗口秒: 意图发布后Solver竞标的时间窗口
            最少Solver数: 最少需要几个Solver竞标
            信誉阈值: Solver最低信誉分
            价格权重: 评分中价格维度权重
            速度权重: 评分中速度维度权重
            安全权重: 评分中安全维度权重
        """
        self.竞标窗口秒 = 竞标窗口秒
        self.最少Solver数 = 最少Solver数
        self.信誉阈值 = 信誉阈值
        self.价格权重 = 价格权重
        self.速度权重 = 速度权重
        self.安全权重 = 安全权重

        self._Solvers: Dict[str, Solver信息] = {}
        self._竞标: Dict[str, List[竞标]] = {}  # 意图ID -> 竞标列表
        self._中标记录: Dict[str, 竞标] = {}  # 意图ID -> 中标竞标

    def 注册Solver(self, Solver: Solver信息) -> bool:
        """注册Solver"""
        if Solver.信誉分数 < self.信誉阈值:
            return False
        self._Solvers[Solver.SolverID] = Solver
        return True

    def 注销Solver(self, SolverID: str) -> bool:
        """注销Solver"""
        if SolverID in self._Solvers:
            del self._Solvers[SolverID]
            return True
        return False

    def 提交竞标(self, 竞标对象: 竞标) -> Tuple[bool, str]:
        """
        提交竞标
        
        Returns:
            (是否成功, 原因)
        """
        # 检查Solver是否已注册
        Solver = self._Solvers.get(竞标对象.SolverID)
        if not Solver:
            return False, "Solver未注册"

        # 检查ATH验证
        if not Solver.ATH验证:
            return False, "Solver未通过ATH验证"

        # 检查资金是否充足
        if Solver.资金锁定 < 竞标对象.报价输出量 * 0.1:
            return False, "Solver资金锁定不足"

        # 验证竞标路径
        if not self._验证路径(竞标对象.路径):
            return False, "执行路径验证失败"

        # 计算综合评分
        竞标对象.综合评分 = self._计算竞标评分(竞标对象, Solver)
        竞标对象.状态 = 竞标状态.有效

        # 加入竞标池
        if 竞标对象.意图ID not in self._竞标:
            self._竞标[竞标对象.意图ID] = []
        self._竞标[竞标对象.意图ID].append(竞标对象)
        return True, "竞标提交成功"

    def _验证路径(self, 路径: 执行路径) -> bool:
        """验证执行路径是否合法"""
        if 路径.预计输出量 <= 0:
            return False
        if 路径.预计Gas费 < 0:
            return False
        if 路径.风险评分 < 0 or 路径.风险评分 > 1:
            return False
        return True

    def _计算竞标评分(self, 竞标对象: 竞标, Solver: Solver信息) -> float:
        """计算竞标综合评分"""
        路径分 = 竞标对象.路径.计算综合评分(
            self.价格权重, self.速度权重, self.安全权重
        )
        信誉加成 = 1.0 + Solver.信誉分数 * 0.05  # 信誉越高加成越大
        成功率加成 = 1.0 + Solver.历史成功率 * 0.1
        return round(路径分 * 信誉加成 * 成功率加成, 4)

    def 选择中标(self, 意图ID: str) -> Optional[竞标]:
        """选择最优竞标"""
        竞标列表 = self._竞标.get(意图ID, [])
        有效竞标 = [b for b in 竞标列表 if b.状态 == 竞标状态.有效]

        if len(有效竞标) < self.最少Solver数:
            # Solver不足，选择唯一的（如果有）
            if len(有效竞标) == 1:
                中标 = 有效竞标[0]
            else:
                return None
        else:
            # 选评分最高的
            有效竞标.sort(key=lambda b: b.综合评分, reverse=True)
            中标 = 有效竞标[0]

        中标.状态 = 竞标状态.中标
        # 其余标记未中标
        for b in 有效竞标:
            if b.竞标ID != 中标.竞标ID and b.状态 == 竞标状态.有效:
                b.状态 = 竞标状态.未中标

        self._中标记录[意图ID] = 中标
        return 中标

    def 获取中标(self, 意图ID: str) -> Optional[竞标]:
        """获取意图的中标结果"""
        return self._中标记录.get(意图ID)

    def 报告执行结果(self, 意图ID: str, 成功: bool) -> None:
        """报告执行结果，更新Solver信誉"""
        中标 = self._中标记录.get(意图ID)
        if not 中标:
            return

        Solver = self._Solvers.get(中标.SolverID)
        if not Solver:
            return

        if 成功:
            中标.状态 = 竞标状态.已完成
            Solver.历史成功率 = Solver.历史成功率 * 0.95 + 1.0 * 0.05
            Solver.累计执行量 += 中标.报价输出量
            Solver.信誉分数 = min(10.0, Solver.信誉分数 + 0.1)
        else:
            中标.状态 = 竞标状态.已惩罚
            Solver.历史成功率 *= 0.9
            Solver.信誉分数 = max(0.0, Solver.信誉分数 - 0.5)
            Solver.惩罚次数 += 1

    def 获取Solver信息(self, SolverID: str) -> Optional[Solver信息]:
        """获取Solver信息"""
        return self._Solvers.get(SolverID)

    def 列出Solvers(self) -> List[Solver信息]:
        """列出所有注册的Solver"""
        return sorted(self._Solvers.values(), key=lambda s: s.信誉分数, reverse=True)

    def 获取竞标列表(self, 意图ID: str) -> List[竞标]:
        """获取某意图的所有竞标"""
        return self._竞标.get(意图ID, [])
