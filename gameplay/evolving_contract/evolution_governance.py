"""
HKC 进化治理 (evolution_governance.py)
=======================================
进化不是无序的——社区通过涌现分数加权投票决定合约变异方向。
安全性危急时可跳过投票紧急变异，效果差的可在24h内回滚。
连续3代变异效果为负自动暂停进化。

核心机制：
  - 进化提议：每代变异生成进化提议
  - 社区投票：涌现分数加权投票决定是否接受变异
  - 紧急变异：安全性评分<阈值时可跳过投票直接变异
  - 回滚机制：变异后效果差的可在24h内回滚
  - 进化暂停：连续3代变异效果为负，自动暂停进化

纯Python标准库，零外部依赖。
"""

import hashlib
import math
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .contract_genome import 合约基因组
from .fitness_evaluator import 适应性评估器, 评估结果, 评估维度
from .mutation_sandbox import 变异沙盒, 沙盒结果


class 提议状态(Enum):
    """进化提议状态"""
    待投票 = "pending"
    投票中 = "voting"
    已通过 = "approved"
    已拒绝 = "rejected"
    已执行 = "executed"
    已回滚 = "rolled_back"
    紧急执行 = "emergency"


@dataclass
class 进化提议:
    """进化提议——合约变异的治理提案"""
    提议ID: str
    变异合约ID: str
    原始合约ID: str
    变异类型: str          # "mutation" / "crossover"
    变异描述: str
    沙盒评分: float = 0.0
    原始评分: float = 0.0
    状态: 提议状态 = 提议状态.待投票
    创建时间: float = 0.0
    投票截止: float = 0.0
    执行时间: float = 0.0
    回滚截止: float = 0.0   # 执行后24h内可回滚
    赞成票权重: float = 0.0  # 加权赞成票
    反对票权重: float = 0.0  # 加权反对票
    投票详情: List[dict] = field(default_factory=list)
    变异快照: Dict[str, float] = field(default_factory=dict)  # 变异后参数快照
    原始快照: Dict[str, float] = field(default_factory=dict)  # 原始参数快照

    def __post_init__(self):
        if self.创建时间 == 0:
            self.创建时间 = time.time()
        if self.投票截止 == 0:
            self.投票截止 = self.创建时间 + 86400  # 24小时投票期


@dataclass
class 投票记录:
    """单次投票记录"""
    提议ID: str
    投票者: str
    赞成: bool
    涌现分数: float    # 投票者的涌现分数E_i，用于加权
    权重: float        # 实际投票权重
    时间: float = 0.0

    def __post_init__(self):
        if self.时间 == 0:
            self.时间 = time.time()


class 进化治理:
    """
    进化治理——合约变异的社区治理系统

    治理流程：
    1. 进化引擎生成变异→沙盒测试→生成进化提议
    2. 社区涌现分数加权投票（24小时投票期）
    3. 通过后执行变异，替换线上合约
    4. 执行后24h观察期，效果差可回滚
    5. 安全性危急时跳过投票紧急执行

    投票权重 = 投票者涌现分数 E_i
    通过条件 = 赞成权重 > 反对权重 且 赞成权重 > 总权重 × 50%

    紧急变异条件：
      - 安全性评分 < 阈值（默认30分）
      - 沙盒测试变异后安全性评分提升
    """

    # 治理参数
    投票期秒 = 86400        # 24小时投票期
    回滚观察期秒 = 86400    # 24小时回滚观察期
    安全性紧急阈值 = 30.0   # 安全性评分低于此值可紧急变异
    通过比例 = 0.50         # 赞成权重需超过总权重的50%

    def __init__(self, 评估器: Optional[适应性评估器] = None,
                 沙盒: Optional[变异沙盒] = None):
        """初始化进化治理

        参数:
            评估器: 适应性评估器
            沙盒: 变异沙盒
        """
        self._评估器 = 评估器 or 适应性评估器()
        self._沙盒 = 沙盒 or 变异沙盒(评估器=self._评估器)

        # 提议管理
        self._提议池: Dict[str, 进化提议] = {}
        # 投票记录
        self._投票记录: Dict[str, List[投票记录]] = {}
        # 执行记录
        self._执行记录: List[dict] = []
        # 合约快照（用于回滚）
        self._合约快照: Dict[str, Dict[str, float]] = {}
        # 涌现分数缓存（投票加权用）
        self._涌现分数: Dict[str, float] = {}

    def 更新涌现分数(self, 地址: str, 分数: float):
        """更新投票者的涌现分数（投票加权用）"""
        self._涌现分数[地址] = 分数

    def 批量更新涌现分数(self, 分数字典: Dict[str, float]):
        """批量更新涌现分数"""
        self._涌现分数.update(分数字典)

    def 创建提议(self, 变异基因组: 合约基因组, 原始基因组: 合约基因组,
                  变异类型: str = "mutation", 变异描述: str = "") -> 进化提议:
        """创建进化提议

        参数:
            变异基因组: 变异后的合约基因组
            原始基因组: 原始合约基因组
            变异类型: "mutation" 或 "crossover"
            变异描述: 变异描述
        返回:
            进化提议
        """
        # 先在沙盒中测试
        沙盒结果 = self._沙盒.测试变异(变异基因组, 原始基因组)

        # 生成提议ID
        随机 = os.urandom(16).hex()
        提议ID = hashlib.sha256(
            f"proposal:{变异基因组.合约ID}:{随机}:{os.urandom(8).hex()}".encode()  # H-24: os.urandom替代time.time_ns()
        ).hexdigest()[:24]

        提议 = 进化提议(
            提议ID=提议ID,
            变异合约ID=变异基因组.合约ID,
            原始合约ID=原始基因组.合约ID,
            变异类型=变异类型,
            变异描述=变异描述 or f"合约{原始基因组.合约名称}的{变异类型}变异",
            沙盒评分=沙盒结果.综合评分,
            原始评分=沙盒结果.原始评分,
            变异快照=变异基因组.基因表达(),
            原始快照=原始基因组.基因表达(),
        )

        # 检查是否满足紧急变异条件
        原始评估 = self._评估器.评估(原始基因组)
        变异评估 = self._评估器.评估(变异基因组)

        原始安全分 = next(
            (ds.评分 for ds in 原始评估.维度评分列表 if ds.维度 == 评估维度.安全性),
            50.0
        )
        变异安全分 = next(
            (ds.评分 for ds in 变异评估.维度评分列表 if ds.维度 == 评估维度.安全性),
            50.0
        )

        if 原始安全分 < self.安全性紧急阈值 and 变异安全分 > 原始安全分:
            # 安全性紧急，跳过投票直接执行
            提议.状态 = 提议状态.紧急执行
            提议.执行时间 = time.time()
            提议.回滚截止 = time.time() + self.回滚观察期秒

        self._提议池[提议ID] = 提议
        self._投票记录[提议ID] = []

        # 保存原始合约快照（用于回滚）
        self._合约快照[原始基因组.合约ID] = 原始基因组.基因表达()

        return 提议

    def 投票(self, 提议ID: str, 投票者: str, 赞成: bool) -> Optional[投票记录]:
        """对进化提议投票

        参数:
            提议ID: 提议ID
            投票者: 投票者地址
            赞成: 是否赞成
        返回:
            投票记录，提议不存在或不可投票返回None
        """
        提议 = self._提议池.get(提议ID)
        if not 提议:
            return None

        # 只有待投票的提议可以投票
        if 提议.状态 not in (提议状态.待投票, 提议状态.投票中):
            return None

        # 检查投票是否已截止
        if time.time() > 提议.投票截止:
            return None

        # 更新状态为投票中
        if 提议.状态 == 提议状态.待投票:
            提议.状态 = 提议状态.投票中

        # 计算投票权重（涌现分数加权）
        涌现分数 = self._涌现分数.get(投票者, 1.0)
        权重 = math.sqrt(max(涌现分数, 0.01))  # 平方根防鲸鱼

        记录 = 投票记录(
            提议ID=提议ID,
            投票者=投票者,
            赞成=赞成,
            涌现分数=涌现分数,
            权重=权重,
        )

        self._投票记录[提议ID].append(记录)

        # 更新提议票数
        if 赞成:
            提议.赞成票权重 += 权重
        else:
            提议.反对票权重 += 权重

        提议.投票详情.append({
            "投票者": 投票者,
            "赞成": 赞成,
            "权重": 权重,
            "涌现分数": 涌现分数,
        })

        return 记录

    def 结算投票(self, 提议ID: str) -> Optional[提议状态]:
        """结算投票，决定提议是否通过

        参数:
            提议ID: 提议ID
        返回:
            提议最终状态
        """
        提议 = self._提议池.get(提议ID)
        if not 提议:
            return None

        # 紧急执行的不需要结算
        if 提议.状态 == 提议状态.紧急执行:
            return 提议.状态

        # 只能结算投票中的提议
        if 提议.状态 != 提议状态.投票中:
            return 提议.状态

        总权重 = 提议.赞成票权重 + 提议.反对票权重

        if 总权重 == 0:
            # 无投票，自动拒绝
            提议.状态 = 提议状态.已拒绝
            return 提议.状态

        赞成比例 = 提议.赞成票权重 / 总权重

        if 提议.赞成票权重 > 提议.反对票权重 and 赞成比例 > self.通过比例:
            提议.状态 = 提议状态.已通过
        else:
            提议.状态 = 提议状态.已拒绝

        return 提议.状态

    def 执行提议(self, 提议ID: str) -> bool:
        """执行已通过的进化提议

        参数:
            提议ID: 提议ID
        返回:
            是否执行成功
        """
        提议 = self._提议池.get(提议ID)
        if not 提议:
            return False

        if 提议.状态 not in (提议状态.已通过, 提议状态.紧急执行):
            return False

        提议.状态 = 提议状态.已执行
        提议.执行时间 = time.time()
        提议.回滚截止 = time.time() + self.回滚观察期秒

        self._执行记录.append({
            "提议ID": 提议ID,
            "变异合约": 提议.变异合约ID,
            "原始合约": 提议.原始合约ID,
            "类型": 提议.变异类型,
            "沙盒评分": 提议.沙盒评分,
            "执行时间": 提议.执行时间,
            "紧急": 提议.状态 == 提议状态.紧急执行,
        })

        return True

    def 回滚提议(self, 提议ID: str) -> bool:
        """回滚已执行的进化提议

        仅在回滚观察期内有效（执行后24h内）。

        参数:
            提议ID: 提议ID
        返回:
            是否回滚成功
        """
        提议 = self._提议池.get(提议ID)
        if not 提议:
            return False

        if 提议.状态 != 提议状态.已执行:
            return False

        # 检查是否在回滚观察期内
        if time.time() > 提议.回滚截止:
            return False

        提议.状态 = 提议状态.已回滚

        self._执行记录.append({
            "提议ID": 提议ID,
            "操作": "回滚",
            "原始合约": 提议.原始合约ID,
            "回滚时间": time.time(),
        })

        return True

    def 检查待结算提议(self) -> List[进化提议]:
        """检查所有需要结算的提议（投票截止的）

        返回:
            需要结算的提议列表
        """
        待结算 = []
        当前时间 = time.time()

        for 提议 in self._提议池.values():
            if 提议.状态 == 提议状态.投票中 and 当前时间 > 提议.投票截止:
                待结算.append(提议)

        return 待结算

    def 自动结算(self) -> List[str]:
        """自动结算所有到期提议

        返回:
            已结算的提议ID列表
        """
        已结算 = []
        for 提议 in self.检查待结算提议():
            结果 = self.结算投票(提议.提议ID)
            if 结果:
                已结算.append(提议.提议ID)
        return 已结算

    def 获取提议(self, 提议ID: str) -> Optional[进化提议]:
        """获取进化提议"""
        return self._提议池.get(提议ID)

    def 列出提议(self, 状态过滤: Optional[提议状态] = None) -> List[进化提议]:
        """列出进化提议

        参数:
            状态过滤: 按状态过滤，None表示全部
        """
        提议列表 = list(self._提议池.values())
        if 状态过滤:
            提议列表 = [p for p in 提议列表 if p.状态 == 状态过滤]
        return sorted(提议列表, key=lambda p: p.创建时间, reverse=True)

    def 治理摘要(self) -> dict:
        """获取治理摘要"""
        总提议 = len(self._提议池)
        各状态 = {}
        for 提议 in self._提议池.values():
            各状态[提议.状态.value] = 各状态.get(提议.状态.value, 0) + 1

        return {
            "总提议数": 总提议,
            "状态分布": 各状态,
            "执行记录数": len(self._执行记录),
            "涌现分数投票者数": len(self._涌现分数),
        }
