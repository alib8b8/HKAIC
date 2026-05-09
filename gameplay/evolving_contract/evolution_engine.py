"""
HKC 进化引擎 (evolution_engine.py)
====================================
合约进化的核心驱动力——选择、变异、淘汰、种群管理。
根据链上环境（稳定/波动/危机）自适应调整变异策略。
好的变异被保留，坏的变异被淘汰，合约种群持续进化。

核心机制：
  - 锦标赛选择：从合约池中选最优
  - 自适应变异率：环境决定变异力度
  - 种群管理：淘汰底部20%，保留精英
  - 进化日志：完整记录每代变异和选择过程

纯Python标准库，零外部依赖。
"""

import hashlib
import math
import os
import time
import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .contract_genome import 合约基因组, 基因型, 变异模式
from .fitness_evaluator import 适应性评估器, 评估维度


class 环境状态(Enum):
    """链上环境状态——决定变异策略"""
    稳定 = "stable"       # 低变异率（5%），微调参数
    波动 = "volatile"     # 高变异率（20%），大胆探索
    危机 = "crisis"       # 极高变异率（40%），紧急求变


@dataclass
class 进化记录:
    """单代进化记录"""
    代数: int
    开始时间: float
    结束时间: float = 0.0
    环境状态: 环境状态 = 环境状态.稳定
    变异率: float = 0.05
    种群大小: int = 0
    淘汰数: int = 0
    新增数: int = 0
    最优适应度: float = 0.0
    平均适应度: float = 0.0
    最差适应度: float = 0.0
    变异详情: List[dict] = field(default_factory=list)
    选择详情: List[dict] = field(default_factory=list)

    def 完成记录(self):
        self.结束时间 = time.time()


class 进化引擎:
    """
    合约进化引擎——驱使合约种群持续进化

    进化周期：默认7天一代（可加速用于测试）
    选择机制：锦标赛选择
    变异策略：根据环境状态自适应
    种群管理：淘汰底部20%，保留精英10%

    与PoEI共识联动：
      - 涌现分数影响合约适应度权重
      - 链上安全事件触发环境状态变化
    """

    # 环境状态对应的变异率
    环境变异率映射 = {
        环境状态.稳定: 0.05,
        环境状态.波动: 0.20,
        环境状态.危机: 0.40,
    }

    # 进化参数
    默认淘汰率 = 0.20       # 淘汰底部20%
    默认精英保留率 = 0.10   # 保留顶部10%精英
    默认锦标赛大小 = 3      # 锦标赛选择时每轮对比3个
    最大种群 = 100          # 种群上限
    最小种群 = 5            # 种群下限
    连续负效应暂停阈值 = 3  # 连续3代效果为负自动暂停

    def __init__(self, 评估器: Optional[适应性评估器] = None,
                 进化周期秒: float = 604800):
        """初始化进化引擎

        参数:
            评估器: 适应性评估器，为空则创建默认
            进化周期秒: 进化周期（秒），默认7天
        """
        self._评估器 = 评估器 or 适应性评估器()
        self._进化周期 = 进化周期秒

        # 种群管理
        self._种群: Dict[str, 合约基因组] = {}  # 合约ID -> 基因组
        self._环境状态: 环境状态 = 环境状态.稳定

        # 进化状态
        self._当前代数: int = 0
        self._上次进化时间: float = 0.0
        self._进化暂停: bool = False
        self._连续负效应计数: int = 0

        # 进化日志
        self._进化历史: List[进化记录] = []

        # 链上环境指标（由外部更新）
        self._波动率: float = 0.0        # 链上交易波动率
        self._安全事件数: int = 0         # 近期安全事件数
        self._平均涌现分数: float = 0.0   # 全网平均E_i

    @property
    def 当前代数(self) -> int:
        return self._当前代数

    @property
    def 环境状态(self) -> 环境状态:
        return self._环境状态

    @property
    def 进化暂停(self) -> bool:
        return self._进化暂停

    @property
    def 种群大小(self) -> int:
        return len(self._种群)

    @property
    def 变异率(self) -> float:
        """当前环境对应的变异率"""
        return self.环境变异率映射.get(self._环境状态, 0.05)

    def 注册合约(self, 基因组: 合约基因组) -> str:
        """注册合约到种群

        参数:
            基因组: 合约基因组
        返回:
            合约ID
        """
        if not 基因组.合约ID:
            # 生成合约ID
            随机 = os.urandom(16).hex()
            基因组.合约ID = hashlib.sha256(
                f"evolving_contract:{随机}:{os.urandom(8).hex()}".encode()  # H-23: os.urandom替代time.time_ns()
            ).hexdigest()[:24]

        self._种群[基因组.合约ID] = 基因组
        return 基因组.合约ID

    def 移除合约(self, 合约ID: str) -> bool:
        """从种群中移除合约"""
        if 合约ID in self._种群:
            del self._种群[合约ID]
            return True
        return False

    def 获取合约(self, 合约ID: str) -> Optional[合约基因组]:
        """获取指定合约基因组"""
        return self._种群.get(合约ID)

    def 更新环境状态(self, 波动率: float = 0.0, 安全事件数: int = 0,
                      平均涌现分数: float = 0.0):
        """更新链上环境指标，自适应调整环境状态

        判定规则：
          - 稳定：波动率<0.3 且 安全事件数=0
          - 波动：波动率>=0.3 或 安全事件数>=1
          - 危机：波动率>=0.7 或 安全事件数>=3 或 平均涌现分数大幅下降
        """
        self._波动率 = 波动率
        self._安全事件数 = 安全事件数
        self._平均涌现分数 = 平均涌现分数

        if 波动率 >= 0.7 or 安全事件数 >= 3:
            self._环境状态 = 环境状态.危机
        elif 波动率 >= 0.3 or 安全事件数 >= 1:
            self._环境状态 = 环境状态.波动
        else:
            self._环境状态 = 环境状态.稳定

    def 是否进化时间(self) -> bool:
        """判断是否到了进化时间"""
        if self._进化暂停:
            return False
        if not self._种群:
            return False
        return time.time() - self._上次进化时间 >= self._进化周期

    def 强制进化(self) -> Optional[进化记录]:
        """强制执行一代进化（不受时间限制）"""
        return self._执行进化()

    def 锦标赛选择(self, 种群列表: Optional[List[Tuple[str, float]]] = None,
                    锦标赛大小: int = 0) -> Optional[str]:
        """锦标赛选择——从合约池中选最优

        参数:
            种群列表: [(合约ID, 适应度)]，为空则使用当前种群
            锦标赛大小: 每轮对比数量，0使用默认值
        返回:
            选中的合约ID
        """
        大小 = 锦标赛大小 or self.默认锦标赛大小

        if 种群列表 is None:
            种群列表 = [(cid, g.适应度) for cid, g in self._种群.items()]

        if not 种群列表:
            return None

        if len(种群列表) <= 大小:
            # 种群太小，直接选最优
            return max(种群列表, key=lambda x: x[1])[0]

        # 随机选锦标赛大小个候选
        索引集合 = set()
        while len(索引集合) < min(大小, len(种群列表)):
            idx = int.from_bytes(os.urandom(4), 'big') % len(种群列表)
            索引集合.add(idx)

        候选 = [种群列表[i] for i in 索引集合]
        # 返回适应度最高的
        return max(候选, key=lambda x: x[1])[0]

    def _执行进化(self) -> Optional[进化记录]:
        """执行一代进化的完整流程

        流程：
        1. 评估所有合约适应度
        2. 排序种群
        3. 淘汰底部
        4. 锦标赛选择优秀个体
        5. 变异产生后代
        6. 交叉产生组合后代
        7. 记录进化日志
        """
        if not self._种群:
            return None

        记录 = 进化记录(
            代数=self._当前代数 + 1,
            开始时间=time.time(),
            环境状态=self._环境状态,
            变异率=self.变异率,
            种群大小=len(self._种群),
        )

        # 1. 评估适应度
        for cid, 基因组 in self._种群.items():
            评估 = self._评估器.评估(基因组)
            基因组.适应度 = 评估.综合评分

        # 2. 排序种群（适应度降序）
        排序种群 = sorted(
            self._种群.items(),
            key=lambda x: x[1].适应度,
            reverse=True,
        )

        if not 排序种群:
            return None

        适应度列表 = [g.适应度 for _, g in 排序种群]
        记录.最优适应度 = 适应度列表[0]
        记录.平均适应度 = sum(适应度列表) / len(适应度列表)
        记录.最差适应度 = 适应度列表[-1]

        # 3. 淘汰底部
        淘汰数 = max(1, int(len(排序种群) * self.默认淘汰率))
        淘汰数 = min(淘汰数, len(排序种群) - self.最小种群)
        淘汰的 = []
        if 淘汰数 > 0 and len(排序种群) > self.最小种群:
            淘汰的 = 排序种群[-淘汰数:]
            for cid, _ in 淘汰的:
                del self._种群[cid]
                记录.选择详情.append({
                    "合约ID": cid,
                    "操作": "淘汰",
                    "适应度": self._种群.get(cid, 合约基因组()).适应度 if cid in self._种群 else 0,
                })
        记录.淘汰数 = len(淘汰的)

        # 重新排序
        排序种群 = sorted(
            self._种群.items(),
            key=lambda x: x[1].适应度,
            reverse=True,
        )

        # 4. 精英保留
        精英数 = max(1, int(len(排序种群) * self.默认精英保留率))
        精英 = 排序种群[:精英数]

        # 5. 变异产生后代
        变异率 = self.变异率
        新增列表 = []
        for cid, 基因组 in 精英:
            后代 = 基因组.变异(变异率=变异率)
            后代.合约ID = hashlib.sha256(
                f"offspring:{cid}:{os.urandom(8).hex()}:{os.urandom(8).hex()}".encode()
            ).hexdigest()[:24]
            后代.合约名称 = f"{基因组.合约名称}_v{后代.版本号}"
            新增列表.append(后代)
            记录.变异详情.append({
                "父合约": cid,
                "子合约": 后代.合约ID,
                "操作": "变异",
                "变异率": 变异率,
                "父适应度": 基因组.适应度,
            })

        # 6. 交叉产生组合后代（如果有足够精英）
        if len(精英) >= 2:
            # 选择两个不同精英进行交叉
            父A = 精英[0]
            父B = 精英[1] if len(精英) > 1 else 精英[0]
            if 父A[0] != 父B[0]:
                交叉后代 = 合约基因组.交叉(父A[1], 父B[1], 交叉率=0.5)
                交叉后代.合约ID = hashlib.sha256(
                    f"crossover:{父A[0]}:{父B[0]}:{os.urandom(8).hex()}:{os.urandom(8).hex()}".encode()
                ).hexdigest()[:24]
                交叉后代.合约名称 = f"{父A[1].合约名称}_×_{父B[1].合约名称}"
                新增列表.append(交叉后代)
                记录.变异详情.append({
                    "父A": 父A[0],
                    "父B": 父B[0],
                    "子合约": 交叉后代.合约ID,
                    "操作": "交叉",
                })

        # 7. 添加后代到种群（不超过上限）
        for 后代 in 新增列表:
            if len(self._种群) < self.最大种群:
                self._种群[后代.合约ID] = 后代
                记录.新增数 += 1

        # 8. 检查进化效果
        if 记录.新增数 > 0:
            新平均 = sum(g.适应度 for g in self._种群.values()) / len(self._种群)
            if 新平均 < 记录.平均适应度:
                self._连续负效应计数 += 1
            else:
                self._连续负效应计数 = 0

            # 连续负效应触发暂停
            if self._连续负效应计数 >= self.连续负效应暂停阈值:
                self._进化暂停 = True

        # 更新状态
        self._当前代数 += 1
        self._上次进化时间 = time.time()
        记录.完成记录()
        self._进化历史.append(记录)

        return 记录

    def 恢复进化(self):
        """恢复被暂停的进化"""
        self._进化暂停 = False
        self._连续负效应计数 = 0

    def 获取进化历史(self, 最近N代: int = 10) -> List[dict]:
        """获取最近的进化历史摘要"""
        历史 = self._进化历史[-最近N代:]
        return [{
            "代数": r.代数,
            "环境": r.环境状态.value,
            "变异率": r.变异率,
            "种群": r.种群大小,
            "淘汰": r.淘汰数,
            "新增": r.新增数,
            "最优": f"{r.最优适应度:.4f}",
            "平均": f"{r.平均适应度:.4f}",
        } for r in 历史]

    def 种群排名(self) -> List[Tuple[str, float]]:
        """获取种群适应度排名（降序）"""
        排名 = [(cid, g.适应度) for cid, g in self._种群.items()]
        排名.sort(key=lambda x: x[1], reverse=True)
        return 排名

    def 引擎摘要(self) -> dict:
        """获取引擎摘要"""
        return {
            "当前代数": self._当前代数,
            "种群大小": len(self._种群),
            "环境状态": self._环境状态.value,
            "变异率": f"{self.变异率:.2%}",
            "进化暂停": self._进化暂停,
            "连续负效应": self._连续负效应计数,
            "进化历史数": len(self._进化历史),
        }
