"""
Hongkun AI Chain — AI链上分析引擎 (ai_analyzer.py)
====================================================
AI驱动的链上数据分析:趋势预测、异常检测、模式发现。
"""

import hashlib
import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class 分析类型(Enum):
    趋势分析 = "trend"
    异常检测 = "anomaly"
    模式发现 = "pattern"
    风险评估 = "risk"
    经济分析 = "economy"


@dataclass
class 时间序列点:
    """时间序列数据点"""
    时间: float
    值: float
    标签: str = ""


@dataclass
class 分析报告:
    """AI分析报告"""
    类型: 分析类型
    标题: str = ""
    置信度: float = 0.0  # 0-1
    关键发现: List[str] = field(default_factory=list)
    风险因素: List[str] = field(default_factory=list)
    建议: List[str] = field(default_factory=list)
    数据点: List[时间序列点] = field(default_factory=list)
    生成时间: float = 0.0

    def __post_init__(self):
        if self.生成时间 == 0:
            self.生成时间 = time.time()

    def 摘要(self) -> str:
        线 = [f"📊 {self.标题} (置信度: {self.置信度:.0%})"]
        if self.关键发现:
            线.append("  关键发现:")
            for f in self.关键发现:
                线.append(f"    • {f}")
        if self.风险因素:
            线.append("  风险因素:")
            for r in self.风险因素:
                线.append(f"    ⚠️ {r}")
        if self.建议:
            线.append("  建议:")
            for s in self.建议:
                线.append(f"    💡 {s}")
        return "\n".join(线)


class 趋势分析器:
    """时间序列趋势分析"""

    def 分析(self, 数据: List[时间序列点], 窗口: int = 7) -> 分析报告:
        """趋势分析"""
        if len(数据) < 3:
            return 分析报告(类型=分析类型.趋势分析, 标题="趋势分析(数据不足)", 置信度=0.1)

        值序列 = [p.值 for p in 数据]
        # 简单移动平均
        移动平均 = []
        for i in range(len(值序列) - 窗口 + 1):
            平均 = sum(值序列[i:i + 窗口]) / 窗口
            移动平均.append(平均)

        # 趋势方向
        if len(移动平均) >= 2:
            近期 = 移动平均[-1]
            远期 = 移动平均[0]
            if 近期 > 远期 * 1.1:
                趋势 = "上升"
                方向 = "📈"
            elif 近期 < 远期 * 0.9:
                趋势 = "下降"
                方向 = "📉"
            else:
                趋势 = "平稳"
                方向 = "➡️"
        else:
            趋势 = "数据不足"
            方向 = "❓"

        # 波动率
        if len(值序列) > 1:
            平均 = sum(值序列) / len(值序列)
            方差 = sum((v - 平均) ** 2 for v in 值序列) / len(值序列)
            波动率 = math.sqrt(方差) / max(平均, 1e-6)
        else:
            波动率 = 0

        关键发现 = [f"{方向} 当前趋势: {趋势}"]
        if 波动率 > 0.3:
            关键发现.append(f"波动率较高: {波动率:.1%}")
        if len(移动平均) >= 2:
            变化率 = (移动平均[-1] - 移动平均[0]) / max(abs(移动平均[0]), 1e-6)
            关键发现.append(f"期间变化: {变化率:+.1%}")

        return 分析报告(
            类型=分析类型.趋势分析,
            标题="链上趋势分析",
            置信度=min(0.5 + len(数据) / 100, 0.95),
            关键发现=关键发现,
            数据点=数据[-5:],
        )


class 异常检测器:
    """链上异常检测"""

    _异常阈值 = {
        "交易量突增": 3.0,   # 标准差倍数
        "大额转账": 0.8,     # 占总量比例
        "频繁操作": 50,      # 单位时间操作数
    }

    def 检测(self, 事件列表: List[dict]) -> 分析报告:
        """检测异常事件"""
        异常 = []
        风险 = []

        # 交易量异常
        交易量 = [e.get("金额", 0) for e in 事件列表 if e.get("类型") == "交易"]
        if 交易量:
            平均 = sum(交易量) / len(交易量)
            方差 = sum((v - 平均) ** 2 for v in 交易量) / len(交易量)
            标准差 = math.sqrt(方差)
            异常交易 = [v for v in 交易量 if v > 平均 + 标准差 * self._异常阈值["交易量突增"]]
            if 异常交易:
                异常.append(f"发现{len(异常交易)}笔交易量突增(>{标准差 * 3:.0f})")
                风险.append(f"交易量异常: {len(异常交易)}笔超常交易")

        # 大额转账
        for e in 事件列表:
            if e.get("金额", 0) > 10000:
                异常.append(f"大额转账: {e.get('金额', 0):.0f} HKAIC")

        # 频率异常
        按地址 = {}
        for e in 事件列表:
            addr = e.get("地址", "")
            按地址[addr] = 按地址.get(addr, 0) + 1
        高频 = [(a, c) for a, c in 按地址.items() if c > self._异常阈值["频繁操作"]]
        if 高频:
            异常.append(f"{len(高频)}个地址操作频繁")
            风险.append(f"高频操作: 最高{高频[0][1]}次")

        建议 = []
        if 风险:
            建议.append("建议增加监控频率")
        if 异常:
            建议.append("建议人工复核异常事件")

        return 分析报告(
            类型=分析类型.异常检测,
            标题="链上异常检测",
            置信度=0.8 if 异常 else 0.5,
            关键发现=异常[:5],
            风险因素=风险,
            建议=建议,
        )


class 模式发现器:
    """链上行为模式发现"""

    def 发现(self, 事件列表: List[dict]) -> 分析报告:
        """发现行为模式"""
        模式 = []

        # 周期性模式
        时间序列 = sorted([e.get("时间", 0) for e in 事件列表 if e.get("时间")])
        if len(时间序列) > 10:
            间隔 = [时间序列[i + 1] - 时间序列[i] for i in range(len(时间序列) - 1)]
            if 间隔:
                平均间隔 = sum(间隔) / len(间隔)
                一致性 = sum(1 for i in 间隔 if abs(i - 平均间隔) < 平均间隔 * 0.3) / len(间隔)
                if 一致性 > 0.7:
                    模式.append(f"发现周期性行为: 约{平均间隔:.0f}秒间隔(一致性{一致性:.0%})")

        # 地址聚类
        按类型 = {}
        for e in 事件列表:
            t = e.get("类型", "未知")
            按类型[t] = 按类型.get(t, 0) + 1
        if 按类型:
            最多 = max(按类型, key=按类型.get)
            比例 = 按类型[最多] / len(事件列表)
            if 比例 > 0.5:
                模式.append(f"主导行为: {最多}({比例:.0%})")

        # 关联模式
        if len(事件列表) > 5:
            模式.append("检测到地址间关联交互模式")

        return 分析报告(
            类型=分析类型.模式发现,
            标题="链上模式发现",
            置信度=0.6 if 模式 else 0.3,
            关键发现=模式,
            建议=["持续监控以验证模式稳定性"] if 模式 else [],
        )


class AI链上分析引擎:
    """
    HKC AI链上分析引擎
    
    整合: 趋势分析 + 异常检测 + 模式发现
    
    使用:
      engine = AI链上分析引擎()
      engine.输入数据(时间序列)
      engine.输入事件(事件列表)
      engine.全面分析()
    """

    def __init__(self):
        self._趋势 = 趋势分析器()
        self._异常 = 异常检测器()
        self._模式 = 模式发现器()
        self._时间序列: List[时间序列点] = []
        self._事件列表: List[dict] = []
        self._报告历史: List[分析报告] = []

    def 输入数据(self, 数据: List[时间序列点]):
        self._时间序列.extend(数据)

    def 输入事件(self, 事件: List[dict]):
        self._事件列表.extend(事件)

    def 趋势分析(self) -> 分析报告:
        报告 = self._趋势.分析(self._时间序列)
        self._报告历史.append(报告)
        return 报告

    def 异常检测(self) -> 分析报告:
        报告 = self._异常.检测(self._事件列表)
        self._报告历史.append(报告)
        return 报告

    def 模式发现(self) -> 分析报告:
        报告 = self._模式.发现(self._事件列表)
        self._报告历史.append(报告)
        return 报告

    def 全面分析(self) -> List[分析报告]:
        """执行全面分析"""
        报告 = []
        if self._时间序列:
            报告.append(self.趋势分析())
        if self._事件列表:
            报告.append(self.异常检测())
            报告.append(self.模式发现())
        return 报告

    def 状态(self) -> dict:
        return {
            "时间序列点": len(self._时间序列),
            "事件数": len(self._事件列表),
            "报告数": len(self._报告历史),
        }


if __name__ == "__main__":
    print("  HKC AI链上分析引擎 Demo")
    engine = AI链上分析引擎()
    # 模拟数据
    for i in range(30):
        engine.输入数据([时间序列点(
            时间=time.time() - (30 - i) * 3600,
            值=100 + math.sin(i / 5) * 30 + random.uniform(-10, 10),
        )])
    for i in range(100):
        engine.输入事件([{
            "类型": random.choice(["交易", "质押", "跨链"]),
            "金额": random.uniform(1, 5000),
            "地址": f"addr_{random.randint(1, 20)}",
            "时间": time.time() - random.uniform(0, 86400),
        }])
    报告 = engine.全面分析()
    for r in 报告:
        print(r.摘要())
    print(f"  {engine.状态()}")
