"""
涌智信用分模块 (credit_score.py)
=================================
基于PoEI涌现分数的地址信用评估系统。
0-1000分，5个等级，实时更新，转账前自动风险提示。
纯Python标准库，零外部依赖。
"""

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class 信用等级(Enum):
    """信用分等级"""
    涌金级 = "gold"       # 900+
    涌银级 = "silver"     # 700-899
    涌铜级 = "bronze"     # 500-699
    普通级 = "normal"     # 300-499
    风险级 = "risk"       # <300


@dataclass
class 信用分详情:
    """信用分完整详情"""
    地址: str
    信用分: float = 0.0
    等级: 信用等级 = 信用等级.普通级
    # 各维度得分
    链上行为分: float = 0.0       # 0-250
    PoEI涌现分: float = 0.0      # 0-250
    网络中心度: float = 0.0       # 0-200
    协作指数: float = 0.0         # 0-200
    风险扣分: float = 0.0         # 0-100 (扣分项)
    # 元数据
    更新时间: float = 0.0
    更新区块: int = 0

    def __post_init__(self):
        if self.更新时间 == 0:
            self.更新时间 = time.time()


class 涌智信用分引擎:
    """
    涌智信用分计算引擎

    信用分 = 链上行为分(250) + PoEI涌现分(250) + 网络中心度(200) + 协作指数(200) - 风险扣分(100)
    总分范围: 0-1000

    等级:
      涌金级(900+): 金色标识，享受低Gas费
      涌银级(700-899): 银色标识
      涌铜级(500-699): 铜色标识
      普通级(300-499): 无特殊标识
      风险级(<300): 红色警告
    """

    def __init__(self):
        # 存储各地址的信用分记录
        self._信用记录: Dict[str, 信用分详情] = {}
        # 链上行为历史缓存
        self._交易频率: Dict[str, List[float]] = {}       # 地址 -> 交易时间戳列表
        self._持仓时间: Dict[str, float] = {}              # 地址 -> 首次活跃时间
        self._质押记录: Dict[str, float] = {}              # 地址 -> 质押总额
        # PoEI涌现分数缓存
        self._PoEI分数: Dict[str, float] = {}              # 地址 -> E_i
        # 网络拓扑（简化版）
        self._交互图: Dict[str, set] = {}                  # 地址 -> 交互过的地址集合
        # 风险标记
        self._Slashing记录: Dict[str, int] = {}            # 地址 -> Slashing次数
        self._可疑交易: Dict[str, int] = {}                # 地址 -> 可疑交易次数
        # 高信用地址集合（用于协作指数计算）
        self._高信用地址: set = set()

    def 更新链上行为(self, 地址: str, 交易金额: float = 0.0, 是质押: bool = False):
        """更新地址的链上行为数据"""
        now = time.time()
        # 交易频率
        if 地址 not in self._交易频率:
            self._交易频率[地址] = []
        self._交易频率[地址].append(now)
        # 只保留最近30天
        cutoff = now - 30 * 86400
        self._交易频率[地址] = [t for t in self._交易频率[地址] if t > cutoff]
        # 持仓时间
        if 地址 not in self._持仓时间:
            self._持仓时间[地址] = now
        # 质押记录
        if 是质押:
            self._质押记录[地址] = self._质押记录.get(地址, 0.0) + 交易金额

    def 更新PoEI分数(self, 地址: str, E_i: float):
        """更新地址的PoEI涌现分数"""
        self._PoEI分数[地址] = E_i

    def 更新交互关系(self, 地址A: str, 地址B: str):
        """更新两个地址之间的交互关系"""
        if 地址A not in self._交互图:
            self._交互图[地址A] = set()
        if 地址B not in self._交互图:
            self._交互图[地址B] = set()
        self._交互图[地址A].add(地址B)
        self._交互图[地址B].add(地址A)

    def 标记风险(self, 地址: str, Slashing: bool = False, 可疑: bool = False):
        """标记地址风险"""
        if Slashing:
            self._Slashing记录[地址] = self._Slashing记录.get(地址, 0) + 1
        if 可疑:
            self._可疑交易[地址] = self._可疑交易.get(地址, 0) + 1

    def 计算链上行为分(self, 地址: str) -> float:
        """
        链上行为分 (0-250)
        - 交易频率: 活跃度越高分越高
        - 持仓时间: 越久分越高
        - 质押记录: 有质押加分
        """
        分数 = 0.0
        # 交易频率分 (0-100)
        交易列表 = self._交易频率.get(地址, [])
        交易次数 = len(交易列表)
        if 交易次数 > 0:
            # 日均交易次数 -> 分数映射
            天数 = max(1, (time.time() - self._持仓时间.get(地址, time.time())) / 86400)
            日均 = 交易次数 / 天数
            分数 += min(100, 日均 * 50)  # 日均2笔=满分
        # 持仓时间分 (0-100)
        首次活跃 = self._持仓时间.get(地址, 0)
        if 首次活跃 > 0:
            持仓天数 = (time.time() - 首次活跃) / 86400
            分数 += min(100, 持仓天数 * 0.5)  # 200天=满分
        # 质押加分 (0-50)
        质押额 = self._质押记录.get(地址, 0)
        if 质押额 > 0:
            分数 += min(50, 质押额 * 0.1)  # 500 HKAIC质押=满分
        return min(250, 分数)

    def 计算PoEI涌现分(self, 地址: str) -> float:
        """
        PoEI涌现分 (0-250)
        基于E_i归一化值
        """
        E_i = self._PoEI分数.get(地址, 0.0)
        if E_i <= 0:
            return 0.0
        # E_i归一化: 假设E_i范围0-200，映射到0-250
        归一化 = min(1.0, E_i / 100.0)
        return 归一化 * 250

    def 计算网络中心度(self, 地址: str) -> float:
        """
        网络位置中心度 (0-200)
        基于该地址在网络拓扑中的连接数和重要性
        使用简化的度中心度+介数中心度
        """
        邻居 = self._交互图.get(地址, set())
        度 = len(邻居)
        if 度 == 0:
            return 0.0
        # 度中心度: 连接越多越重要 (0-100)
        度分 = min(100, 度 * 5)  # 20个不同交互=满分
        # 介数简化: 邻居之间的共同连接数 (0-100)
        共同连接 = 0
        邻居列表 = list(邻居)
        for i in range(len(邻居列表)):
            for j in range(i + 1, len(邻居列表)):
                ni, nj = 邻居列表[i], 邻居列表[j]
                if nj in self._交互图.get(ni, set()):
                    共同连接 += 1
        介数分 = min(100, 共同连接 * 2)
        return min(200, 度分 + 介数分)

    def 计算协作指数(self, 地址: str) -> float:
        """
        协作指数 (0-200)
        与多少高信用地址交互过
        """
        邻居 = self._交互图.get(地址, set())
        if not 邻居:
            return 0.0
        # 统计与高信用地址交互的比例
        高信用交互 = sum(1 for n in 邻居 if n in self._高信用地址)
        比例 = 高信用交互 / len(邻居) if 邻居 else 0
        # 交互数量也计入
        数量分 = min(100, len(邻居) * 5)
        质量分 = 比例 * 100
        return min(200, 数量分 + 质量分)

    def 计算风险扣分(self, 地址: str) -> float:
        """
        风险扣分 (0-100)
        Slashing重罚，可疑交易轻罚
        """
        扣分 = 0.0
        # Slashing: 每次扣30分
        扣分 += self._Slashing记录.get(地址, 0) * 30
        # 可疑交易: 每次扣5分
        扣分 += self._可疑交易.get(地址, 0) * 5
        return min(100, 扣分)

    def 计算信用分(self, 地址: str, 区块号: int = 0) -> 信用分详情:
        """
        计算地址的完整信用分
        每出一个新区块可调用此方法更新
        """
        链上行为分 = self.计算链上行为分(地址)
        PoEI分 = self.计算PoEI涌现分(地址)
        网络中心 = self.计算网络中心度(地址)
        协作 = self.计算协作指数(地址)
        风险 = self.计算风险扣分(地址)

        总分 = max(0, 链上行为分 + PoEI分 + 网络中心 + 协作 - 风险)
        等级 = self._分数转等级(总分)

        详情 = 信用分详情(
            地址=地址,
            信用分=总分,
            等级=等级,
            链上行为分=链上行为分,
            PoEI涌现分=PoEI分,
            网络中心度=网络中心,
            协作指数=协作,
            风险扣分=风险,
            更新时间=time.time(),
            更新区块=区块号,
        )
        self._信用记录[地址] = 详情

        # 更新高信用地址集合
        if 总分 >= 700:
            self._高信用地址.add(地址)
        elif 地址 in self._高信用地址:
            self._高信用地址.discard(地址)

        return 详情

    def _分数转等级(self, 分数: float) -> 信用等级:
        """分数转信用等级"""
        if 分数 >= 900:
            return 信用等级.涌金级
        elif 分数 >= 700:
            return 信用等级.涌银级
        elif 分数 >= 500:
            return 信用等级.涌铜级
        elif 分数 >= 300:
            return 信用等级.普通级
        else:
            return 信用等级.风险级

    def 获取信用分(self, 地址: str) -> 信用分详情:
        """获取地址的信用分（如有缓存则返回缓存）"""
        if 地址 in self._信用记录:
            return self._信用记录[地址]
        return self.计算信用分(地址)

    def 批量更新(self, 地址列表: List[str], 区块号: int = 0):
        """批量更新多个地址的信用分（每出一个新区块调用）"""
        结果 = {}
        for 地址 in 地址列表:
            结果[地址] = self.计算信用分(地址, 区块号)
        return 结果

    def 风险提示(self, 目标地址: str) -> Optional[str]:
        """
        向目标地址转账前的风险提示
        低信用地址返回提示，高信用地址返回None
        """
        详情 = self.获取信用分(目标地址)
        if 详情.等级 == 信用等级.风险级:
            return f"⚠ 危险：目标地址 {目标地址[:10]}... 信用分为 {详情.信用分:.0f}（风险级），建议勿向此地址转账！"
        elif 详情.等级 == 信用等级.普通级 and 详情.信用分 < 400:
            return f"⚠ 注意：目标地址 {目标地址[:10]}... 信用分为 {详情.信用分:.0f}（普通级偏低），请确认交易安全。"
        return None

    def 等级标识(self, 等级: 信用等级) -> str:
        """获取等级的ASCII标识符号"""
        标识 = {
            信用等级.涌金级: "★★★ 涌金 ★★★",
            信用等级.涌银级: "★★ 涌银 ★★",
            信用等级.涌铜级: "★ 涌铜 ★",
            信用等级.普通级: "  普通  ",
            信用等级.风险级: "!! 风险 !!",
        }
        return 标识.get(等级, "  未知  ")

    def 等级颜色代码(self, 等级: 信用等级) -> str:
        """获取等级对应的终端颜色代码"""
        颜色 = {
            信用等级.涌金级: "\033[93m",   # 亮黄/金色
            信用等级.涌银级: "\033[37m",   # 银白色
            信用等级.涌铜级: "\033[33m",   # 铜黄色
            信用等级.普通级: "\033[0m",     # 默认
            信用等级.风险级: "\033[91m",    # 红色
        }
        return 颜色.get(等级, "\033[0m")
