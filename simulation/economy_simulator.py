"""
Hongkun AI Chain — HKAIC经济仿真器 (economy_simulator.py)
=========================================================
AI驱动的代币经济仿真系统。

核心能力:
  1. 蒙特卡洛仿真 — 万次随机模拟
  2. 参数寻优 — 寻找最优经济参数
  3. 可视化 — ASCII图表输出
  4. 压力测试 — 极端场景模拟

代币参数:
  总量: 21,000,000 HKAIC
  销毁率: 15%手续费销毁
  质押收益: 动态APY
"""

import hashlib
import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class 仿真场景(Enum):
    正常 = "normal"
    牛市 = "bull"
    熊市 = "bear"
    极端压力 = "stress"
    女巫攻击 = "sybil"


@dataclass
class 仿真参数:
    """仿真参数"""
    总量: float = 21_000_000
    销毁率: float = 0.15
    基础APY: float = 0.08
    质押率: float = 0.3
    交易量_日: float = 10000
    平均手续费: float = 3.0
    节点数: int = 21
    新增用户率: float = 0.01


@dataclass
class 仿真快照:
    """仿真时间快照"""
    天数: int
    流通量: float
    质押量: float
    销毁量: float
    价格: float
    APY: float
    TPS: float
    节点数: int
    用户数: int


class 蒙特卡洛引擎:
    """蒙特卡洛仿真引擎"""

    def __init__(self, 参数: 仿真参数 = None):
        self._参数 = 参数 or 仿真参数()
        self._随机种子: int = 42

    def 设置种子(self, 种子: int):
        self._随机种子 = 种子
        random.seed(种子)

    def 单次仿真(self, 天数: int = 365, 场景: 仿真场景 = 仿真场景.正常) -> List[仿真快照]:
        """执行一次完整仿真"""
        random.seed(self._随机种子 + int(time.time_ns() % 10000))
        p = self._参数
        快照列表 = []

        流通量 = p.总量 * (1 - p.质押率)
        质押量 = p.总量 * p.质押率
        累计销毁 = 0.0
        价格 = 1.0
        用户数 = 1000

        for 天 in range(1, 天数 + 1):
            # 场景因子
            if 场景 == 仿真场景.牛市:
                增长因子 = random.uniform(1.01, 1.05)
                交易增长 = 1.05
            elif 场景 == 仿真场景.熊市:
                增长因子 = random.uniform(0.95, 1.0)
                交易增长 = 0.95
            elif 场景 == 仿真场景.极端压力:
                增长因子 = random.choice([0.8, 0.9, 1.1, 1.3])
                交易增长 = random.uniform(0.5, 3.0)
            else:
                增长因子 = random.uniform(0.98, 1.03)
                交易增长 = 1.01

            # 交易手续费销毁
            日交易 = p.交易量_日 * (交易增长 ** (天 / 30))
            日销毁 = 日交易 * p.平均手续费 * p.销毁率
            累计销毁 += 日销毁

            # 质押收益
            APY = p.基础APY * (1 + (p.质押率 - 0.5) * 0.5)  # 质押少→APY高
            质押收益 = 质押量 * APY / 365

            # 价格模型(简化)
            需求 = 用户数 * random.uniform(0.8, 1.2) * 0.01
            供给 = 流通量 * random.uniform(0.001, 0.01)
            价格变动 = (需求 - 供给) / max(供给, 1) * 0.1
            价格 *= (1 + 价格变动) * 增长因子 ** (1 / 365)
            价格 = max(0.01, 价格)

            # 用户增长
            用户数 = int(用户数 * (1 + p.新增用户率 * 增长因子))

            # 质押率微调
            质押调整 = random.uniform(-0.001, 0.002)
            新质押率 = min(0.8, max(0.1, p.质押率 + 质押调整))
            质押量 = 流通量 * 新质押率 / (1 - 新质押率)

            快照 = 仿真快照(
                天数=天,
                流通量=流通量,
                质押量=质押量,
                销毁量=累计销毁,
                价格=价格,
                APY=APY,
                TPS=min(500, 日交易 / 86400 * 10),
                节点数=p.节点数 + int(random.uniform(-1, 2)),
                用户数=用户数,
            )
            快照列表.append(快照)

        return 快照列表

    def 多次仿真(self, 次数: int = 100, 天数: int = 365,
                  场景: 仿真场景 = 仿真场景.正常) -> Dict[str, List[float]]:
        """多次仿真,返回统计结果"""
        所有终态 = {
            "终态价格": [], "终态APY": [], "总销毁": [],
            "终态用户": [], "终态TPS": [],
        }
        for _ in range(次数):
            快照列表 = self.单次仿真(天数, 场景)
            if 快照列表:
                最后 = 快照列表[-1]
                所有终态["终态价格"].append(最后.价格)
                所有终态["终态APY"].append(最后.APY)
                所有终态["总销毁"].append(最后.销毁量)
                所有终态["终态用户"].append(最后.用户数)
                所有终态["终态TPS"].append(最后.TPS)

        return 所有终态


class 参数寻优器:
    """经济参数寻优"""

    def __init__(self):
        self._参数空间 = {
            "销毁率": (0.05, 0.30),
            "基础APY": (0.03, 0.15),
            "质押率": (0.1, 0.7),
        }
        self._最优: Optional[仿真参数] = None
        self._最优评分: float = 0

    def 评估(self, 参数: 仿真参数) -> float:
        """评估参数组合评分"""
        引擎 = 蒙特卡洛引擎(参数)
        结果 = 引擎.多次仿真(50, 180)

        # 评分: 价格稳定+销毁足够+APY合理
        价格 = 结果.get("终态价格", [1.0])
        平均价格 = sum(价格) / max(len(价格), 1)
        价格波动 = math.sqrt(sum((p - 平均价格) ** 2 for p in 价格) / max(len(价格), 1))

        销毁 = 结果.get("总销毁", [0])
        平均销毁 = sum(销毁) / max(len(销毁), 1)

        # 评分函数
        稳定性分 = 1.0 / (1 + 价格波动 / max(平均价格, 0.01))
        销毁分 = min(平均销毁 / 100000, 1.0)
        APY分 = 1.0 if 0.03 <= 参数.基础APY <= 0.12 else 0.5

        评分 = 稳定性分 * 0.4 + 销毁分 * 0.3 + APY分 * 0.3
        return 评分

    def 网格搜索(self, 步数: int = 5) -> 仿真参数:
        """网格搜索最优参数"""
        最佳参数 = 仿真参数()
        最佳评分 = 0

        for 销毁率_步 in range(步数):
            for APY_步 in range(步数):
                for 质押率_步 in range(步数):
                    参数 = 仿真参数(
                        销毁率=self._插值("销毁率", 销毁率_步, 步数),
                        基础APY=self._插值("基础APY", APY_步, 步数),
                        质押率=self._插值("质押率", 质押率_步, 步数),
                    )
                    评分 = self.评估(参数)
                    if 评分 > 最佳评分:
                        最佳评分 = 评分
                        最佳参数 = 参数

        self._最优 = 最佳参数
        self._最优评分 = 最佳评分
        return 最佳参数

    def _插值(self, 参数名: str, 步: int, 总步: int) -> float:
        最小, 最大 = self._参数空间[参数名]
        return 最小 + (最大 - 最小) * 步 / max(总步 - 1, 1)


class ASCII可视化器:
    """ASCII图表可视化"""

    def 折线图(self, 数据: List[float], 宽度: int = 50, 高度: int = 10, 标题: str = "") -> str:
        """ASCII折线图"""
        if not 数据:
            return "  (无数据)"

        最小 = min(数据)
        最大 = max(数据)
        范围 = 最大 - 最小 if 最大 > 最小 else 1

        线 = []
        if 标题:
            线.append(f"  {标题}")

        # 降采样
        步长 = max(1, len(数据) // 宽度)
        采样 = 数据[::步长][:宽度]

        for 行 in range(高度, 0, -1):
            阈值 = 最小 + 范围 * 行 / 高度
            行字符 = []
            for 值 in 采样:
                if 值 >= 阈值:
                    行字符.append("█")
                else:
                    行字符.append(" ")
            标签 = f"{阈值:.1f}" if 行 % 3 == 0 else "   "
            线.append(f"  {标签}|{''.join(行字符)}")

        线.append(f"     +{'─' * len(采样)}")
        线.append(f"      {最小:.1f}{' ' * (len(采样) - 8)}{最大:.1f}")
        return "\n".join(线)

    def 柱状图(self, 标签值: List[Tuple[str, float]], 宽度: int = 30) -> str:
        """ASCII柱状图"""
        if not 标签值:
            return "  (无数据)"
        最大 = max(v for _, v in 标签值)
        线 = []
        for 标签, 值 in 标签值:
            柱长 = int(值 / max(最大, 1e-6) * 宽度)
            线.append(f"  {标签:>8} |{'█' * 柱长} {值:.1f}")
        return "\n".join(线)


class HKAIC经济仿真器:
    """
    HKAIC经济仿真器
    
    整合: 蒙特卡洛 + 参数寻优 + 可视化
    
    使用:
      sim = HKAIC经济仿真器()
      sim.运行仿真(365, 仿真场景.正常)
      sim.可视化()
    """

    def __init__(self, 参数: 仿真参数 = None):
        self._参数 = 参数 or 仿真参数()
        self._引擎 = 蒙特卡洛引擎(self._参数)
        self._寻优 = 参数寻优器()
        self._可视化 = ASCII可视化器()
        self._快照: List[仿真快照] = []
        self._多次结果: Dict[str, List[float]] = {}

    def 运行仿真(self, 天数: int = 365, 场景: 仿真场景 = 仿真场景.正常) -> List[仿真快照]:
        """运行单次仿真"""
        self._快照 = self._引擎.单次仿真(天数, 场景)
        return self._快照

    def 运行蒙特卡洛(self, 次数: int = 100, 天数: int = 365,
                      场景: 仿真场景 = 仿真场景.正常) -> Dict[str, List[float]]:
        """运行蒙特卡洛仿真"""
        self._多次结果 = self._引擎.多次仿真(次数, 天数, 场景)
        return self._多次结果

    def 参数寻优(self) -> 仿真参数:
        """寻找最优经济参数"""
        return self._寻优.网格搜索(3)

    def 可视化价格(self) -> str:
        """价格趋势图"""
        if not self._快照:
            return "  请先运行仿真"
        价格 = [s.价格 for s in self._快照]
        return self._可视化.折线图(价格, 标题="HKAIC 价格趋势")

    def 可视化销毁(self) -> str:
        """销毁量柱状图"""
        if not self._快照:
            return "  请先运行仿真"
        # 每季度汇总
        季度 = []
        for i in range(0, len(self._快照), 90):
            段 = self._快照[i:i + 90]
            if 段:
                季度.append((f"Q{i // 90 + 1}", 段[-1].销毁量 - 段[0].销毁量))
        return self._可视化.柱状图(季度, 标题="HKAIC 季度销毁量")

    def 仿真报告(self) -> str:
        """生成仿真报告"""
        if not self._快照:
            return "  请先运行仿真"
        最后 = self._快照[-1]
        线 = [
            "=" * 50,
            "  HKAIC 经济仿真报告",
            "=" * 50,
            f"  仿真天数: {最后.天数}",
            f"  流通量: {最后.流通量:,.0f} HKAIC",
            f"  质押量: {最后.质押量:,.0f} HKAIC",
            f"  累计销毁: {最后.销毁量:,.0f} HKAIC",
            f"  价格: ${最后.价格:.4f}",
            f"  APY: {最后.APY:.2%}",
            f"  TPS: {最后.TPS:.0f}",
            f"  用户数: {最后.用户数:,}",
            f"  节点数: {最后.节点数}",
        ]
        if self._多次结果:
            价格 = self._多次结果.get("终态价格", [])
            if 价格:
                线.append(f"  蒙特卡洛价格范围: ${min(价格):.4f} - ${max(价格):.4f}")
        线.append("=" * 50)
        return "\n".join(线)

    def 状态(self) -> dict:
        return {
            "快照数": len(self._快照),
            "参数": f"销毁={self._参数.销毁率:.0%} APY={self._参数.基础APY:.0%}",
        }


if __name__ == "__main__":
    print("  HKAIC 经济仿真器 Demo")
    sim = HKAIC经济仿真器()
    sim.运行仿真(365, 仿真场景.正常)
    print(sim.仿真报告())
    print(sim.可视化价格())
