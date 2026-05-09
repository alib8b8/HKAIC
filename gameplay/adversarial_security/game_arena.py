"""
HKC 对战竞技场 (game_arena.py)
================================
红队AI vs 蓝队AI的链上安全对战平台。
支持多种对战模式：1v1、锦标赛、生存模式、团队战。
每轮对战完整记录，可复盘分析。

对战模式：
  - 1v1：单个攻击者vs单个防御者
  - 锦标赛：多轮淘汰赛
  - 生存模式：防御者持续面对随机攻击
  - 团队战：红队vs蓝队

对战规则：
  - 每轮限时，攻击者尝试突破，防御者拦截
  - 攻击成功+分，防御成功+分
  - 资源限制：每方有限的Gas和计算资源

纯Python标准库，零外部依赖。
"""

import hashlib
import math
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .attack_scenarios import 攻击场景库, 攻击场景, 攻击类型
from .defense_strategies import 防御策略库, 防御策略, 多层防御体系


class 对战模式(Enum):
    """对战模式"""
    一对一 = "1v1"
    锦标赛 = "tournament"
    生存模式 = "survival"
    团队战 = "team"


class 回合结果(Enum):
    """单回合结果"""
    攻击成功 = "attack_win"
    防御成功 = "defense_win"
    平局 = "draw"
    超时 = "timeout"


@dataclass
class 对战者:
    """对战者（攻击者或防御者）"""
    地址: str
    名称: str
    角色: str = ""          # "attacker" / "defender"
    涌现分数: float = 1.0
    累计得分: float = 0.0
    累计胜场: int = 0
    累计败场: int = 0
    资源: float = 1000.0    # 可用资源（Gas/计算力）


@dataclass
class 回合记录:
    """单回合对战记录"""
    回合号: int
    攻击者: str
    防御者: str
    攻击场景: str            # 场景ID
    防御策略: List[str]      # 策略ID列表
    结果: 回合结果 = 回合结果.平局
    攻击得分: float = 0.0
    防御得分: float = 0.0
    详情: str = ""
    耗时秒: float = 0.0
    时间戳: float = 0.0

    def __post_init__(self):
        if self.时间戳 == 0:
            self.时间戳 = time.time()


@dataclass
class 对战结果:
    """完整对战结果"""
    对战ID: str
    模式: 对战模式
    攻击者列表: List[str]
    防御者列表: List[str]
    回合记录: List[回合记录] = field(default_factory=list)
    总回合数: int = 0
    攻击方总分: float = 0.0
    防御方总分: float = 0.0
    获胜方: str = ""          # "attacker" / "defender" / "draw"
    开始时间: float = 0.0
    结束时间: float = 0.0

    def __post_init__(self):
        if self.开始时间 == 0:
            self.开始时间 = time.time()


class 对战竞技场:
    """
    链上安全对战竞技场

    红队AI攻击、蓝队AI防御，攻击成功赚HKAIC、防御成功也赚HKAIC。
    对战结果反馈到安全排行榜和奖励分配器。

    对战流程（1v1模式为例）：
    1. 攻击者选择攻击场景
    2. 防御者部署防御策略
    3. 执行模拟攻击
    4. 计算拦截概率决定结果
    5. 分配得分和奖励

    与PoEI联动：
      - 涌现分数影响对战者资源上限
      - 对战结果影响安全排行榜
    """

    # 对战参数
    默认回合数 = 5
    默认资源上限 = 1000.0
    默认每回合时间秒 = 60.0
    攻击成功基础分 = 10.0
    防御成功基础分 = 8.0
    平局分 = 3.0

    def __init__(self, 攻击库: Optional[攻击场景库] = None,
                 防御库: Optional[防御策略库] = None):
        """初始化对战竞技场

        参数:
            攻击库: 攻击场景库
            防御库: 防御策略库
        """
        self._攻击库 = 攻击库 or 攻击场景库()
        self._防御库 = 防御库 or 防御策略库()
        self._对战者: Dict[str, 对战者] = {}
        self._对战历史: List[对战结果] = []

    def 注册对战者(self, 地址: str, 名称: str, 涌现分数: float = 1.0) -> 对战者:
        """注册对战者"""
        战者 = 对战者(
            地址=地址, 名称=名称, 涌现分数=涌现分数,
            资源=self.默认资源上限 * (1 + 涌现分数 * 0.1),
        )
        self._对战者[地址] = 战者
        return 战者

    def 获取对战者(self, 地址: str) -> Optional[对战者]:
        """获取对战者"""
        return self._对战者.get(地址)

    def 执行一对一对战(self, 攻击者地址: str, 防御者地址: str,
                        回合数: int = 0) -> 对战结果:
        """执行1v1对战

        参数:
            攻击者地址: 攻击者地址
            防御者地址: 防御者地址
            回合数: 对战回合数
        返回:
            对战结果
        """
        回合 = 回合数 or self.默认回合数
        # H-12修复: 使用os.urandom加密随机数，替代可预测的time.time_ns()
        对战ID = hashlib.sha256(
            f"arena_1v1:{攻击者地址}:{防御者地址}:{os.urandom(16).hex()}".encode()
        ).hexdigest()[:24]

        结果 = 对战结果(
            对战ID=对战ID,
            模式=对战模式.一对一,
            攻击者列表=[攻击者地址],
            防御者列表=[防御者地址],
        )

        攻击者 = self._对战者.get(攻击者地址)
        防御者 = self._对战者.get(防御者地址)

        if not 攻击者 or not 防御者:
            return 结果

        for i in range(回合):
            回合结果 = self._执行回合(
                回合号=i + 1,
                攻击者=攻击者,
                防御者=防御者,
            )
            结果.回合记录.append(回合结果)
            结果.攻击方总分 += 回合结果.攻击得分
            结果.防御方总分 += 回合结果.防御得分

        结果.总回合数 = 回合

        # 判定获胜方
        if 结果.攻击方总分 > 结果.防御方总分:
            结果.获胜方 = "attacker"
            攻击者.累计胜场 += 1
            防御者.累计败场 += 1
        elif 结果.防御方总分 > 结果.攻击方总分:
            结果.获胜方 = "defender"
            防御者.累计胜场 += 1
            攻击者.累计败场 += 1
        else:
            结果.获胜方 = "draw"

        攻击者.累计得分 += 结果.攻击方总分
        防御者.累计得分 += 结果.防御方总分
        结果.结束时间 = time.time()

        self._对战历史.append(结果)
        return 结果

    def 执行生存模式(self, 防御者地址: str, 回合数: int = 10) -> 对战结果:
        """执行生存模式——防御者持续面对随机攻击

        参数:
            防御者地址: 防御者地址
            回合数: 回合数
        返回:
            对战结果
        """
        对战ID = hashlib.sha256(
            f"arena_survival:{防御者地址}:{os.urandom(16).hex()}".encode()  # H-12: os.urandom替代time.time_ns()
        ).hexdigest()[:24]

        结果 = 对战结果(
            对战ID=对战ID,
            模式=对战模式.生存模式,
            攻击者列表=["system_random"],
            防御者列表=[防御者地址],
        )

        防御者 = self._对战者.get(防御者地址)
        if not 防御者:
            return 结果

        连续防御成功 = 0
        for i in range(回合数):
            # 随机选择攻击场景
            场景列表 = self._攻击库.随机选择(1)
            if not 场景列表:
                break

            # 创建临时攻击者
            临时攻击者 = 对战者(
                地址=f"bot_{i}", 名称=f"攻击Bot_{i}",
                角色="attacker", 涌现分数=0.5 + i * 0.05,
                资源=500 + i * 50,
            )

            回合 = self._执行回合(
                回合号=i + 1,
                攻击者=临时攻击者,
                防御者=防御者,
                强制场景=场景列表[0],
            )
            结果.回合记录.append(回合)
            结果.攻击方总分 += 回合.攻击得分
            结果.防御方总分 += 回合.防御得分

            if 回合.结果 == 回合结果.防御成功:
                连续防御成功 += 1
            else:
                连续防御成功 = 0

            # 连续防御5次获得额外奖励分
            if 连续防御成功 >= 5:
                结果.防御方总分 += 5.0  # 连续防御奖励

        结果.总回合数 = len(结果.回合记录)
        结果.获胜方 = "defender" if 结果.防御方总分 > 结果.攻击方总分 else "attacker"
        防御者.累计得分 += 结果.防御方总分
        防御者.累计胜场 += (1 if 结果.获胜方 == "defender" else 0)
        防御者.累计败场 += (1 if 结果.获胜方 == "attacker" else 0)
        结果.结束时间 = time.time()

        self._对战历史.append(结果)
        return 结果

    def 执行锦标赛(self, 参赛者地址: List[str], 类型: str = "attack") -> 对战结果:
        """执行锦标赛模式——多轮淘汰赛

        参数:
            参赛者地址: 参赛者地址列表
            类型: "attack"=攻击者锦标赛, "defense"=防御者锦标赛
        返回:
            最终对战结果
        """
        对战ID = hashlib.sha256(
            f"arena_tournament:{os.urandom(16).hex()}".encode()  # H-12: os.urandom替代time.time_ns()
        ).hexdigest()[:24]

        结果 = 对战结果(
            对战ID=对战ID,
            模式=对战模式.锦标赛,
            攻击者列表=参赛者地址 if 类型 == "attack" else ["system"],
            防御者列表=参赛者地址 if 类型 == "defense" else ["system"],
        )

        当前轮 = list(参赛者地址)
        轮次 = 0

        while len(当前轮) > 1:
            轮次 += 1
            下一轮 = []

            # 两两配对
            for j in range(0, len(当前轮), 2):
                if j + 1 >= len(当前轮):
                    下一轮.append(当前轮[j])  # 奇数人轮空
                    continue

                A = 当前轮[j]
                B = 当前轮[j + 1]

                if 类型 == "attack":
                    # 攻击者锦标赛：两人分别攻击系统防御
                    场景 = self._攻击库.随机选择(1)
                    if 场景:
                        A战者 = self._对战者.get(A)
                        B战者 = self._对战者.get(B)
                        if A战者 and B战者:
                            # 两人攻击同一防御，比较攻击得分
                            临时防御 = 对战者(地址="system", 名称="系统防御", 角色="defender")
                            A回合 = self._执行回合(轮次, A战者, 临时防御, 强制场景=场景[0])
                            B回合 = self._执行回合(轮次, B战者, 临时防御, 强制场景=场景[0])
                            胜者 = A if A回合.攻击得分 >= B回合.攻击得分 else B
                            下一轮.append(胜者)
                            结果.回合记录.extend([A回合, B回合])
                        else:
                            下一轮.append(A)
                    else:
                        下一轮.append(A)
                else:
                    # 防御者锦标赛：系统攻击两人防御
                    场景 = self._攻击库.随机选择(1)
                    if 场景:
                        A战者 = self._对战者.get(A)
                        B战者 = self._对战者.get(B)
                        if A战者 and B战者:
                            临时攻击 = 对战者(地址="system", 名称="系统攻击", 角色="attacker")
                            A回合 = self._执行回合(轮次, 临时攻击, A战者, 强制场景=场景[0])
                            B回合 = self._执行回合(轮次, 临时攻击, B战者, 强制场景=场景[0])
                            胜者 = A if A回合.防御得分 >= B回合.防御得分 else B
                            下一轮.append(胜者)
                            结果.回合记录.extend([A回合, B回合])
                        else:
                            下一轮.append(A)
                    else:
                        下一轮.append(A)

            当前轮 = 下一轮

        结果.总回合数 = len(结果.回合记录)
        结果.获胜方 = 当前轮[0] if 当前轮 else ""
        结果.结束时间 = time.time()

        self._对战历史.append(结果)
        return 结果

    def _执行回合(self, 回合号: int, 攻击者: 对战者, 防御者: 对战者,
                   强制场景: Optional[攻击场景] = None) -> 回合记录:
        """执行单个对战回合

        流程：
        1. 攻击者选择攻击场景
        2. 防御者匹配防御策略
        3. 计算拦截概率
        4. 随机决定结果
        5. 计算得分
        """
        # 1. 选择攻击场景
        if 强制场景:
            场景 = 强制场景
        else:
            候选 = self._攻击库.随机选择(1)
            if not 候选:
                return 回合记录(
                    回合号=回合号, 攻击者=攻击者.地址, 防御者=防御者.地址,
                    攻击场景="", 防御策略=[], 结果=回合结果.平局,
                )
            场景 = 候选[0]

        # 2. 匹配防御策略
        匹配策略 = self._防御库.按攻击类型匹配(场景)
        防御策略ID列表 = [s.策略ID for s in 匹配策略[:3]]  # 取前3个策略

        # 3. 计算多层防御拦截概率
        if 匹配策略:
            防御体系 = self._防御库.构建多层防御(匹配策略[:3])
            拦截概率 = 防御体系.总拦截率(场景)
        else:
            拦截概率 = 0.1  # 无防御策略时基础拦截率

        # 涌现分数修正
        if 防御者.涌现分数 > 1.0:
            拦截概率 *= (1 + math.log(防御者.涌现分数) * 0.1)
        拦截概率 = min(0.95, 拦截概率)  # 最高95%

        # 4. 随机决定结果
        随机值 = int.from_bytes(os.urandom(4), 'big') / 0xFFFFFFFF
        攻击成功 = 随机值 > 拦截概率

        # 5. 计算得分
        攻击评分 = 场景.攻击评分()
        防御评分 = sum(s.防御评分() for s in 匹配策略[:3]) / max(len(匹配策略[:3]), 1)

        if 攻击成功:
            结果 = 回合结果.攻击成功
            攻击得分 = self.攻击成功基础分 + 攻击评分 * 0.5
            防御得分 = 0
            详情 = f"攻击者使用{场景.名称}突破防御"
        else:
            结果 = 回合结果.防御成功
            攻击得分 = 0
            防御得分 = self.防御成功基础分 + 防御评分 * 0.3
            详情 = f"防御者成功拦截{场景.名称}"

        # 记录攻击执行
        self._攻击库.记录攻击执行(场景.场景ID, 攻击者.地址, 攻击成功, 详情)

        return 回合记录(
            回合号=回合号,
            攻击者=攻击者.地址,
            防御者=防御者.地址,
            攻击场景=场景.场景ID,
            防御策略=防御策略ID列表,
            结果=结果,
            攻击得分=攻击得分,
            防御得分=防御得分,
            详情=详情,
        )

    def 获取对战历史(self, 地址: str = "", 最近N场: int = 10) -> List[dict]:
        """获取对战历史"""
        历史 = self._对战历史
        if 地址:
            历史 = [h for h in 历史 if 地址 in h.攻击者列表 or 地址 in h.防御者列表]
        return [{
            "对战ID": h.对战ID,
            "模式": h.模式.value,
            "获胜方": h.获胜方,
            "总回合": h.总回合数,
            "攻击总分": f"{h.攻击方总分:.1f}",
            "防御总分": f"{h.防御方总分:.1f}",
        } for h in 历史[-最近N场:]]

    def 竞技场摘要(self) -> dict:
        """获取竞技场摘要"""
        return {
            "注册对战者": len(self._对战者),
            "历史对战数": len(self._对战历史),
            "攻击场景数": len(self._攻击库._场景池),
            "防御策略数": len(self._防御库._策略池),
        }
