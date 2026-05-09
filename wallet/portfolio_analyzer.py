"""
AI投资组合分析 (portfolio_analyzer.py)
========================================
资产分布分析、收益追踪、AI建议、风险评估、终端可视化报告。
纯Python标准库，零外部依赖。
"""

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class 资产项:
    """单个资产"""
    代币: str
    金额: float
    链: str = "HKC"
    是否质押: bool = False
    质押年化: float = 0.0
    估值: float = 0.0      # 估值(以HKAIC计)


@dataclass
class 收益记录:
    """收益记录"""
    类型: str        # 质押/跨链套利/Gas节省
    金额: float
    代币: str = "HKAIC"
    时间: float = 0.0

    def __post_init__(self):
        if self.时间 == 0:
            self.时间 = time.time()


@dataclass
class 风险评估结果:
    """风险评估"""
    集中度风险: float = 0.0    # 0-1
    跨链风险: float = 0.0      # 0-1
    合约风险: float = 0.0      # 0-1
    综合风险: float = 0.0      # 0-1
    风险等级: str = "低"       # 低/中/高/极高
    风险描述: List[str] = field(default_factory=list)


@dataclass
class 投资组合报告:
    """AI投资组合完整报告"""
    总资产: float = 0.0
    质押占比: float = 0.0
    跨链资产占比: float = 0.0
    资产分布: List[资产项] = field(default_factory=list)
    总收益: float = 0.0
    收益明细: List[收益记录] = field(default_factory=list)
    风险评估: Optional[风险评估结果] = None
    AI建议: List[str] = field(default_factory=list)
    可视化: str = ""
    生成时间: float = 0.0

    def __post_init__(self):
        if self.生成时间 == 0:
            self.生成时间 = time.time()


class 投资组合分析器:
    """
    AI投资组合分析器

    功能：
      1. 资产分布分析：HKAIC持有量、质押占比、跨链资产分布
      2. 收益追踪：质押收益、跨链套利收益、Gas支出
      3. AI建议：基于持仓和市场数据给出调整建议
      4. 风险评估：集中度风险、跨链风险、合约风险
      5. 可视化报告：终端输出资产分布图
    """

    def __init__(self):
        self._资产列表: List[资产项] = []
        self._收益记录: List[收益记录] = []
        self._Gas支出: List[Dict] = []
        self._市场价格: Dict[str, float] = {"HKAIC": 1.0, "ETH": 3500.0, "BTC": 60000.0}

    def 设置资产(self, 资产列表: List[资产项]):
        """设置当前资产"""
        self._资产列表 = 资产列表

    def 添加资产(self, 资产: 资产项):
        """添加单个资产"""
        self._资产列表.append(资产)

    def 更新价格(self, 代币: str, 价格: float):
        """更新代币价格"""
        self._市场价格[代币] = 价格

    def 记录收益(self, 类型: str, 金额: float, 代币: str = "HKAIC"):
        """记录收益"""
        self._收益记录.append(收益记录(类型=类型, 金额=金额, 代币=代币))

    def 记录Gas支出(self, 金额: float, 描述: str = ""):
        """记录Gas支出"""
        self._Gas支出.append({"金额": 金额, "描述": 描述, "时间": time.time()})

    # ========== 资产分布分析 ==========

    def 分析资产分布(self) -> Dict:
        """分析资产分布"""
        if not self._资产列表:
            return {"总资产": 0.0, "分布": {}}

        总资产 = sum(a.估值 or a.金额 * self._市场价格.get(a.代币, 1.0) for a in self._资产列表)
        质押资产 = sum(a.估值 or a.金额 for a in self._资产列表 if a.是否质押)
        跨链资产 = sum(a.估值 or a.金额 for a in self._资产列表 if a.链 != "HKC")

        # 按代币分组
        代币分布: Dict[str, float] = {}
        for a in self._资产列表:
            估值 = a.估值 or a.金额 * self._市场价格.get(a.代币, 1.0)
            代币分布[a.代币] = 代币分布.get(a.代币, 0.0) + 估值

        # 按链分组
        链分布: Dict[str, float] = {}
        for a in self._资产列表:
            估值 = a.估值 or a.金额 * self._市场价格.get(a.代币, 1.0)
            链分布[a.链] = 链分布.get(a.链, 0.0) + 估值

        return {
            "总资产": 总资产,
            "质押资产": 质押资产,
            "质押占比": 质押资产 / 总资产 if 总资产 > 0 else 0,
            "跨链资产": 跨链资产,
            "跨链占比": 跨链资产 / 总资产 if 总资产 > 0 else 0,
            "代币分布": 代币分布,
            "链分布": 链分布,
        }

    # ========== 收益追踪 ==========

    def 计算总收益(self, 天数: int = 30) -> Dict:
        """计算指定天数内的总收益"""
        cutoff = time.time() - 天数 * 86400
        期间收益 = [r for r in self._收益记录 if r.时间 > cutoff]
        期间Gas = [g for g in self._Gas支出 if g["时间"] > cutoff]

        总收益 = sum(r.金额 for r in 期间收益 if r.金额 > 0)
        总Gas = sum(g["金额"] for g in 期间Gas)
        净收益 = 总收益 - 总Gas

        # 按类型分
        分类收益: Dict[str, float] = {}
        for r in 期间收益:
            分类收益[r.类型] = 分类收益.get(r.类型, 0.0) + r.金额

        return {
            "总收益": 总收益,
            "总Gas支出": 总Gas,
            "净收益": 净收益,
            "分类收益": 分类收益,
            "期间天数": 天数,
        }

    # ========== AI建议 ==========

    def 生成AI建议(self) -> List[str]:
        """基于持仓和市场数据给出AI调整建议"""
        建议 = []
        分布 = self.分析资产分布()

        # 集中度建议
        代币分布 = 分布.get("代币分布", {})
        if 代币分布:
            最大占比代币 = max(代币分布, key=代币分布.get)
            最大占比 = 代币分布[最大占比代币] / 分布["总资产"] if 分布["总资产"] > 0 else 0
            if 最大占比 > 0.9:
                建议.append(f"⚠ 资产过度集中：{最大占比代币}占比{最大占比:.0%}，建议分散到其他代币或链")
            elif 最大占比 > 0.7:
                建议.append(f"📊 资产较集中：{最大占比代币}占比{最大占比:.0%}，可适当分散配置")

        # 质押建议
        质押占比 = 分布.get("质押占比", 0)
        if 质押占比 < 0.3 and 分布["总资产"] > 100:
            建议.append("💰 质押占比较低，建议将部分HKAIC质押获取收益")
        elif 质押占比 > 0.8:
            建议.append("⚠ 质押占比过高，建议保留足够的流动性")

        # 跨链建议
        跨链占比 = 分布.get("跨链占比", 0)
        if 跨链占比 == 0 and 分布["总资产"] > 500:
            建议.append("🌐 所有资产集中在HKC，可考虑跨链分散降低风险")
        elif 跨链占比 > 0.5:
            建议.append("⚠ 跨链资产占比较高，注意跨链桥风险")

        # 如果没有建议
        if not 建议:
            建议.append("✅ 投资组合配置合理，当前无需调整")

        return 建议

    # ========== 风险评估 ==========

    def 评估风险(self) -> 风险评估结果:
        """评估投资组合风险"""
        分布 = self.分析资产分布()
        风险描述 = []

        # 1. 集中度风险
        代币分布 = 分布.get("代币分布", {})
        集中度风险 = 0.0
        if 代币分布 and 分布["总资产"] > 0:
            # 赫芬达尔指数
            hhi = sum((v / 分布["总资产"]) ** 2 for v in 代币分布.values())
            集中度风险 = min(1.0, hhi)  # HHI=1表示完全集中
            if 集中度风险 > 0.8:
                风险描述.append(f"集中度风险高：资产过度集中于单一代币(HHI={hhi:.2f})")

        # 2. 跨链风险
        跨链风险 = 0.0
        链分布 = 分布.get("链分布", {})
        if 链分布 and 分布["总资产"] > 0:
            链数 = len(链分布)
            if 链数 > 3:
                跨链风险 = 0.3 + (链数 - 3) * 0.1  # 链越多风险越高
                风险描述.append(f"跨链风险：资产分布在{链数}条链上，桥安全风险增加")
            elif 链数 > 1:
                跨链风险 = 0.15
        跨链风险 = min(1.0, 跨链风险)

        # 3. 合约风险
        合约风险 = 0.0
        质押资产 = [a for a in self._资产列表 if a.是否质押]
        if 质押资产:
            合约风险 = 0.2  # 质押有合约风险
            风险描述.append("合约风险：部分资产在质押合约中，存在智能合约风险")

        # 综合风险
        综合风险 = 集中度风险 * 0.4 + 跨链风险 * 0.3 + 合约风险 * 0.3

        # 风险等级
        if 综合风险 < 0.2:
            等级 = "低"
        elif 综合风险 < 0.4:
            等级 = "中"
        elif 综合风险 < 0.7:
            等级 = "高"
        else:
            等级 = "极高"

        return 风险评估结果(
            集中度风险=集中度风险,
            跨链风险=跨链风险,
            合约风险=合约风险,
            综合风险=综合风险,
            风险等级=等级,
            风险描述=风险描述,
        )

    # ========== 生成完整报告 ==========

    def 生成报告(self) -> 投资组合报告:
        """生成AI投资组合完整报告"""
        分布 = self.分析资产分布()
        收益 = self.计算总收益(30)
        风险 = self.评估风险()
        建议 = self.生成AI建议()
        可视化 = self._生成可视化(分布)

        return 投资组合报告(
            总资产=分布["总资产"],
            质押占比=分布.get("质押占比", 0),
            跨链资产占比=分布.get("跨链占比", 0),
            资产分布=self._资产列表,
            总收益=收益["净收益"],
            收益明细=self._收益记录,
            风险评估=风险,
            AI建议=建议,
            可视化=可视化,
        )

    def _生成可视化(self, 分布: Dict) -> str:
        """生成终端ASCII可视化资产分布图"""
        线 = []
        线.append("=" * 50)
        线.append("  涌信钱包 · AI投资组合分析")
        线.append("=" * 50)

        总资产 = 分布.get("总资产", 0)
        线.append(f"  总资产估值: {总资产:,.2f} HKAIC")
        线.append("")

        # 代币分布条形图
        代币分布 = 分布.get("代币分布", {})
        if 代币分布 and 总资产 > 0:
            线.append("  [代币分布]")
            for 代币, 金额 in sorted(代币分布.items(), key=lambda x: x[1], reverse=True):
                占比 = 金额 / 总资产
                条长 = int(占比 * 30)
                条 = "█" * 条长 + "░" * (30 - 条长)
                线.append(f"  {代币:6s} |{条}| {占比:.1%} ({金额:,.1f})")
            线.append("")

        # 链分布
        链分布 = 分布.get("链分布", {})
        if 链分布 and 总资产 > 0:
            线.append("  [链分布]")
            for 链名, 金额 in sorted(链分布.items(), key=lambda x: x[1], reverse=True):
                占比 = 金额 / 总资产
                条长 = int(占比 * 30)
                条 = "█" * 条长 + "░" * (30 - 条长)
                线.append(f"  {链名:16s} |{条}| {占比:.1%}")
            线.append("")

        # 质押信息
        质押占比 = 分布.get("质押占比", 0)
        线.append(f"  质押占比: {质押占比:.1%}")
        跨链占比 = 分布.get("跨链占比", 0)
        线.append(f"  跨链资产占比: {跨链占比:.1%}")
        线.append("=" * 50)

        return "\n".join(线)
