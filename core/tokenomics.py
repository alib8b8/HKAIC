"""
HKAIC 代币经济学 (tokenomics.py)
=================================
2100万枚全部预铸，无挖矿产出。内循环驱动。
创世分配: 40%生态基金 / 20%团队 / 20%初始流动性 / 10%社区空投 / 10%预留
"""

import math
from typing import Dict, List
from dataclasses import dataclass

HKAIC_TOTAL_SUPPLY = 21_000_000
HONGKUN_PER_HKAIC = 10 ** 16
DECIMALS = 16

# 创世分配方案
GENESIS_ALLOCATION = {
    "生态发展基金": {"比例": 0.40, "数量": 8_400_000, "说明": "情报激励/AI服务/生态建设", "锁仓期": "线性释放4年"},
    "团队与顾问":   {"比例": 0.20, "数量": 4_200_000, "说明": "开发/运营/顾问激励",     "锁仓期": "线性释放4年"},
    "初始流动性":   {"比例": 0.20, "数量": 4_200_000, "说明": "交易所做市/流动性池",   "锁仓期": "无"},
    "社区空投":     {"比例": 0.10, "数量": 2_100_000, "说明": "早期用户/贡献者空投",   "锁仓期": "50%即时/50%6个月"},
    "长期预留":     {"比例": 0.10, "数量": 2_100_000, "说明": "未来合作/应急/治理",     "锁仓期": "治理投票解锁"},
}

# 交易费率表 (基础费率，可通过治理调整)
FEE_SCHEDULE = {
    "普通转账": 0.001,       # 0.1% of amount
    "合约执行": 0.005,       # 0.5%
    "跨链转账": 0.01,        # 1.0%
    "治理投票": 0,           # 免费
    "质押操作": 0.0005,      # 0.05%
}

# 手续费分配
FEE_DISTRIBUTION = {
    "出块者": 0.60,          # 60% 给出块节点
    "生态基金": 0.25,        # 25% 进入生态基金
    "销毁": 0.15,            # 15% 永久销毁（通缩）
}


@dataclass
class 分配项:
    名称: str; 比例: float; 数量: float; 说明: str; 锁仓期: str


class 代币经济学:
    """
    HKAIC 代币经济学引擎
    
    核心特征:
      - 固定供给：21,000,000 HKAIC，全部预铸，永不增发
      - 内循环驱动：交易手续费是主要流转动力
      - 通缩机制：15%手续费永久销毁
      - 质押收益：来自交易费分成，非增发
    """

    def __init__(self):
        self._总供给 = HKAIC_TOTAL_SUPPLY
        self._已流通 = 0.0
        self._已销毁 = 0.0
        self._累计手续费 = 0.0
        self._生态基金余额 = GENESIS_ALLOCATION["生态发展基金"]["数量"]
        self._预留余额 = GENESIS_ALLOCATION["长期预留"]["数量"]
        self._费率表 = dict(FEE_SCHEDULE)
        self._费率分配 = dict(FEE_DISTRIBUTION)

    @property
    def 总供给(self) -> float: return self._总供给

    @property
    def 已流通(self) -> float: return self._已流通

    @property
    def 已销毁(self) -> float: return self._已销毁

    @property
    def 实际流通(self) -> float: return self._总供给 - self._已销毁

    @property
    def 生态基金(self) -> float: return self._生态基金余额

    @property
    def 预留余额(self) -> float: return self._预留余额

    def 计算手续费(self, 金额: float, 类型: str = "普通转账") -> float:
        """计算交易手续费"""
        费率 = self._费率表.get(类型, 0.001)
        return 金额 * 费率

    def 分配手续费(self, 手续费: float) -> Dict[str, float]:
        """按比例分配手续费"""
        结果 = {}
        for 角色, 比例 in self._费率分配.items():
            结果[角色] = 手续费 * 比例
        # 销毁部分
        self._已销毁 += 结果.get("销毁", 0)
        # 生态基金部分
        self._生态基金余额 += 结果.get("生态基金", 0)
        self._累计手续费 += 手续费
        return 结果

    def 从生态基金发放(self, 金额: float, 用途: str = "") -> bool:
        """从生态基金发放激励"""
        if 金额 <= 0 or 金额 > self._生态基金余额:
            return False
        self._生态基金余额 -= 金额
        self._已流通 += 金额
        return True

    def 通胀率(self) -> float:
        """通胀率 = 0%（固定供给，永不增发）"""
        return 0.0

    def 通缩率(self) -> float:
        """通缩率 = 已销毁 / 总供给"""
        if self._总供给 == 0: return 0.0
        return (self._已销毁 / self._总供给) * 100

    def 流通率(self) -> float:
        """流通率 = (总供给 - 销毁 - 锁仓) / 总供给"""
        锁仓 = self._生态基金余额 + self._预留余额
        return ((self._总供给 - self._已销毁 - 锁仓) / self._总供给) * 100

    def 创世分配表(self) -> List[分配项]:
        """返回创世分配明细"""
        结果 = []
        for 名称, 信息 in GENESIS_ALLOCATION.items():
            结果.append(分配项(名称=名称, 比例=信息["比例"],
                               数量=信息["数量"], 说明=信息["说明"], 锁仓期=信息["锁仓期"]))
        return 结果

    def 预估年手续费(self, 日交易量: float, 平均费率: float = 0.002) -> float:
        """预估年手续费收入"""
        return 日交易量 * 平均费率 * 365

    def 预估质押APY(self, 质押率: float, 日交易量: float) -> float:
        """
        预估质押年化收益率
        APY = (出块者分成 * 年手续费) / (总供给 * 质押率)
        """
        if 质押率 <= 0: return 0.0
        年手续费 = self.预估年手续费(日交易量)
        出块者收入 = 年手续费 * self._费率分配.get("出块者", 0.60)
        质押总额 = self._总供给 * 质押率
        return (出块者收入 / 质押总额) * 100

    def 经济摘要(self) -> dict:
        return {
            "总供给": f"{self._总供给:,.0f} HKAIC",
            "已销毁": f"{self._已销毁:,.8f} HKAIC",
            "实际流通": f"{self.实际流通:,.8f} HKAIC",
            "通胀率": f"{self.通胀率():.2f}%",
            "通缩率": f"{self.通缩率():.4f}%",
            "流通率": f"{self.流通率():.2f}%",
            "生态基金": f"{self._生态基金余额:,.0f} HKAIC",
            "累计手续费": f"{self._累计手续费:,.8f} HKAIC",
        }


if __name__ == "__main__":
    print("=" * 60)
    print("  HKAIC 代币经济学 Demo — 固定供给·内循环驱动")
    print("=" * 60)
    E = 代币经济学()

    print("\n📋 创世分配:")
    print(f"  {'名称':<12} {'比例':>6} {'数量':>12} {'说明'}")
    print("  " + "-" * 60)
    for 项 in E.创世分配表():
        print(f"  {项.名称:<12} {项.比例:>5.0%} {项.数量:>12,.0f}  {项.说明} [{项.锁仓期}]")

    print(f"\n💰 手续费计算:")
    for 类型 in FEE_SCHEDULE:
        费 = E.计算手续费(1000, 类型)
        print(f"  {类型}: 1000 HKAIC → {费:.4f} HKAIC 手续费")

    print(f"\n📊 手续费分配 (100 HKAIC手续费):")
    for 角色, 金额 in E.分配手续费(100).items():
        print(f"  {角色}: {金额:.2f} HKAIC")

    print(f"\n📈 质押APY估算 (日交易量100万HKAIC):")
    for 质押率 in [0.1, 0.3, 0.5, 0.7]:
        apy = E.预估质押APY(质押率, 1_000_000)
        print(f"  质押率{质押率:.0%}: APY ≈ {apy:.2f}%")

    print(f"\n📋 经济摘要:")
    for k, v in E.经济摘要().items(): print(f"  {k}: {v}")
