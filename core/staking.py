"""
HKAIC 质押与治理 (staking.py)
==============================
质押获得出块权+交易费分成（非新币增发）、治理投票、提案系统、委托质押。
"""

import hashlib
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

HONGKUN_PER_HKAIC = 10 ** 16


class 质押状态(Enum):
    活跃 = "active"; 解除中 = "unstaking"; 已解除 = "withdrawn"; 惩罚 = "slashed"


class 提案状态(Enum):
    投票中 = "voting"; 通过 = "passed"; 否决 = "rejected"; 执行中 = "executing"; 已执行 = "executed"


@dataclass
class 质押记录:
    """质押记录"""
    验证者地址: str; 质押金额: int  # 鸿坤
    状态: 质押状态 = 质押状态.活跃
    质押时间: float = 0.0
    解除时间: float = 0.0
    累计收益: int = 0          # 来自交易费分成
    惩罚金额: int = 0

    def 到字典(self) -> dict:
        return {"验证者": self.验证者地址,
                "金额": f"{self.质押金额/HONGKUN_PER_HKAIC:.8f} HKAIC",
                "状态": self.状态.value, "收益": f"{self.累计收益/HONGKUN_PER_HKAIC:.8f} HKAIC"}


@dataclass
class 委托记录:
    """委托质押记录"""
    委托人: str; 验证者: str; 委托金额: int; 委托时间: float = 0.0


@dataclass
class 投票:
    """治理投票"""
    投票人: str; 提案ID: str; 选项: str  # "赞成"/"反对"/"弃权"
    权重: int = 0  # 基于质押量: 1 HKAIC = 1票


@dataclass
class 提案:
    """治理提案"""
    提案ID: str; 标题: str; 描述: str; 提案人: str
    状态: 提案状态 = 提案状态.投票中
    创建时间: float = 0.0; 投票截止: float = 0.0
    赞成票: int = 0; 反对票: int = 0; 弃权票: int = 0
    参数: dict = field(default_factory=dict)

    def 投票结果(self) -> str:
        if self.赞成票 > self.反对票: return "通过"
        elif self.反对票 >= self.赞成票: return "否决"
        return "平局"


class 质押引擎:
    """
    HKAIC 质押与治理引擎
    
    核心设计:
      - 质押不产生新币，收益来自交易费分成
      - 质押量 + AI贡献度 = 出块权重
      - 1 HKAIC = 1 投票权
      - 委托质押：普通用户可委托给验证者
    """

    def __init__(self):
        self._质押记录: Dict[str, 质押记录] = {}
        self._委托记录: Dict[str, List[委托记录]] = {}
        self._提案库: Dict[str, 提案] = {}
        self._投票记录: Dict[str, List[投票]] = {}
        self._总质押量: int = 0
        self._手续费池: int = 0  # 待分配的交易费
        self._惩罚池: int = 0

    # ----------------------------------------------------------
    # 质押操作
    # ----------------------------------------------------------

    def 质押(self, 地址: str, 金额_鸿坤: int) -> 质押记录:
        """质押HKAIC，获得出块权和治理权"""
        if 金额_鸿坤 <= 0: raise ValueError("质押金额必须大于0")
        最低质押 = 1000 * HONGKUN_PER_HKAIC  # 最低1000 HKAIC
        if 金额_鸿坤 < 最低质押 and 地址 not in self._质押记录:
            raise ValueError(f"首次质押最低1000 HKAIC")
        if 地址 in self._质押记录:
            rec = self._质押记录[地址]
            if rec.状态 != 质押状态.活跃: raise ValueError("质押状态异常")
            rec.质押金额 += 金额_鸿坤
        else:
            rec = 质押记录(验证者地址=地址, 质押金额=金额_鸿坤,
                          质押时间=time.time())
            self._质押记录[地址] = rec
        self._总质押量 += 金额_鸿坤
        return rec

    def 解除质押(self, 地址: str, 金额_鸿坤: int = 0) -> 质押记录:
        """解除质押（7天冷却期）"""
        rec = self._质押记录.get(地址)
        if not rec or rec.状态 != 质押状态.活跃: raise ValueError("无活跃质押")
        解除量 = 金额_鸿坤 if 金额_鸿坤 > 0 else rec.质押金额
        if 解除量 > rec.质押金额: raise ValueError("解除量超过质押量")
        rec.质押金额 -= 解除量
        self._总质押量 -= 解除量
        if rec.质押金额 == 0:
            rec.状态 = 质押状态.解除中
            rec.解除时间 = time.time() + 86400 * 7  # 7天冷却
        return rec

    def 惩罚(self, 地址: str, 比例: float, 原因: str = "") -> int:
        """Slashing — 惩罚作恶验证者"""
        rec = self._质押记录.get(地址)
        if not rec: return 0
        惩罚额 = int(rec.质押金额 * 比例)
        rec.质押金额 -= 惩罚额; rec.惩罚金额 += 惩罚额
        self._总质押量 -= 惩罚额; self._惩罚池 += 惩罚额
        if 惩罚额 > 0: rec.状态 = 质押状态.惩罚
        return 惩罚额

    def 委托质押(self, 委托人: str, 验证者: str, 金额_鸿坤: int, 委托人余额: int = 0) -> 委托记录:
        """委托质押 — 委托人将币委托给验证者
        M-18修复: 添加委托人余额检查，防止超额委托"""
        # M-18: 检查委托人是否有足够余额
        if 金额_鸿坤 <= 0:
            raise ValueError("委托金额必须大于0")
        # 计算已委托总额
        已委托 = sum(r.委托金额 for r in self._委托记录.get(委托人, []))
        if 委托人余额 > 0 and 已委托 + 金额_鸿坤 > 委托人余额:
            raise ValueError(f"委托金额({金额_鸿坤/HONGKUN_PER_HKAIC:.2f} HKAIC)超出可用余额")
        # M-18: 检查验证者是否存在
        if 验证者 not in self._质押记录:
            raise ValueError(f"验证者{验证者}不存在，无法委托")
        rec = 委托记录(委托人=委托人, 验证者=验证者,
                       委托金额=金额_鸿坤, 委托时间=time.time())
        self._委托记录.setdefault(委托人, []).append(rec)
        # 增加验证者的有效质押量
        if 验证者 in self._质押记录:
            self._质押记录[验证者].质押金额 += 金额_鸿坤
            self._总质押量 += 金额_鸿坤
        return rec

    # ----------------------------------------------------------
    # 收益分配（交易费分成，非新币增发）
    # ----------------------------------------------------------

    def 分配交易费(self, 总手续费_鸿坤: int, 出块者地址: str,
                    生态基金比例: float = 0.25, 销毁比例: float = 0.15) -> dict:
        """分配区块交易手续费"""
        出块者份额 = 1.0 - 生态基金比例 - 销毁比例
        出块者收入 = int(总手续费_鸿坤 * 出块者份额)
        生态基金收入 = int(总手续费_鸿坤 * 生态基金比例)
        销毁量 = 总手续费_鸿坤 - 出块者收入 - 生态基金收入
        # 出块者收益记入质押记录
        if 出块者地址 in self._质押记录:
            self._质押记录[出块者地址].累计收益 += 出块者收入
        # 委托人分成（90%给出块者，10%按委托比例分给委托人）
        委托人分成 = int(出块者收入 * 0.10)
        出块者净收入 = 出块者收入 - 委托人分成
        return {"出块者": 出块者净收入, "委托人池": 委托人分成,
                "生态基金": 生态基金收入, "销毁": 销毁量}

    def 估算APY(self, 年手续费总额: float, 质押率: float) -> float:
        """估算质押年化收益率"""
        if 质押率 <= 0 or self._总质押量 <= 0: return 0.0
        出块者分成 = 年手续费总额 * 0.60  # 出块者得60%
        质押总HKAIC = self._总质押量 / HONGKUN_PER_HKAIC
        return (出块者分成 / 质押总HKAIC) * 100

    # ----------------------------------------------------------
    # 治理投票
    # ----------------------------------------------------------

    def 创建提案(self, 标题: str, 描述: str, 提案人: str,
                  投票期天数: int = 7, 参数: dict = None) -> 提案:
        """创建治理提案"""
        # H-11修复: 使用os.urandom加密随机数，替代可预测的time.time_ns()
        import os as _os
        pid = hashlib.sha256(f"{标题}{提案人}{_os.urandom(16).hex()}".encode()).hexdigest()[:16]
        p = 提案(提案ID=pid, 标题=标题, 描述=描述, 提案人=提案人,
                创建时间=time.time(), 投票截止=time.time() + 86400 * 投票期天数,
                参数=参数 or {})
        self._提案库[pid] = p; self._投票记录[pid] = []
        return p

    def 投票(self, 提案ID: str, 投票人: str, 选项: str) -> bool:
        """1 HKAIC = 1票"""
        p = self._提案库.get(提案ID)
        if not p or p.状态 != 提案状态.投票中: return False
        if time.time() > p.投票截止: return False
        # 投票权重 = 质押量 + 委托量
        权重 = 0
        if 投票人 in self._质押记录:
            权重 += self._质押记录[投票人].质押金额
        # 检查是否已投
        已投 = any(v.投票人 == 投票人 for v in self._投票记录[提案ID])
        if 已投: return False
        v = 投票(投票人=投票人, 提案ID=提案ID, 选项=选项, 权重=权重)
        self._投票记录[提案ID].append(v)
        if 选项 == "赞成": p.赞成票 += 权重
        elif 选项 == "反对": p.反对票 += 权重
        else: p.弃权票 += 权重
        return True

    def 结算提案(self, 提案ID: str) -> str:
        """结算提案"""
        p = self._提案库.get(提案ID)
        if not p: return "不存在"
        if time.time() < p.投票截止: return "投票未截止"
        结果 = p.投票结果()
        if 结果 == "通过":
            p.状态 = 提案状态.通过
            # 检查是否满足最低参与率
            总投票 = p.赞成票 + p.反对票 + p.弃权票
            参与率 = 总投票 / self._总质押量 if self._总质押量 > 0 else 0
            if 参与率 < 0.10:  # 最低10%参与率
                p.状态 = 提案状态.否决
                return "参与率不足，否决"
        else:
            p.状态 = 提案状态.否决
        return p.状态.value

    def 查询提案(self, 提案ID: str) -> Optional[提案]:
        return self._提案库.get(提案ID)

    def 列出提案(self) -> List[提案]:
        return list(self._提案库.values())

    # ----------------------------------------------------------
    # 查询
    # ----------------------------------------------------------

    def 查询质押(self, 地址: str) -> Optional[质押记录]:
        return self._质押记录.get(地址)

    @property
    def 总质押量(self) -> int: return self._总质押量

    def 质押率(self, 总供给_鸿坤: int) -> float:
        """质押率 = 总质押 / 总供给"""
        if 总供给_鸿坤 <= 0: return 0.0
        return (self._总质押量 / 总供给_鸿坤) * 100

    def 引擎摘要(self) -> dict:
        return {"验证者数": len(self._质押记录),
                "总质押": f"{self._总质押量/HONGKUN_PER_HKAIC:,.2f} HKAIC",
                "活跃提案": len([p for p in self._提案库.values() if p.状态 == 提案状态.投票中]),
                "惩罚池": f"{self._惩罚池/HONGKUN_PER_HKAIC:,.8f} HKAIC"}


if __name__ == "__main__":
    print("=" * 60)
    print("  HKAIC 质押与治理 Demo — 交易费驱动·非增发")
    print("=" * 60)
    E = 质押引擎()
    A, B, C = "validator_A", "validator_B", "delegator_C"

    print("\n💰 质押:")
    E.质押(A, 10000 * HONGKUN_PER_HKAIC)
    E.质押(B, 5000 * HONGKUN_PER_HKAIC)
    print(f"  A质押: {E.查询质押(A).到字典()}")
    print(f"  B质押: {E.查询质押(B).到字典()}")

    print("\n🤝 委托质押:")
    E.委托质押(C, A, 2000 * HONGKUN_PER_HKAIC)
    print(f"  C委托A 2000 HKAIC")

    print("\n💸 手续费分配 (100 HKAIC):")
    分配 = E.分配交易费(100 * HONGKUN_PER_HKAIC, A)
    for 角色, 金额 in 分配.items():
        print(f"  {角色}: {金额/HONGKUN_PER_HKAIC:.4f} HKAIC")

    print("\n🗳️ 治理投票:")
    p = E.创建提案("调整手续费率", "将普通转账费率从0.1%调整至0.08%", A, 投票期天数=1)
    print(f"  提案: {p.标题}")
    E.投票(p.提案ID, A, "赞成")
    E.投票(p.提案ID, B, "反对")
    print(f"  赞成: {p.赞成票/HONGKUN_PER_HKAIC:.0f} 票 | 反对: {p.反对票/HONGKUN_PER_HKAIC:.0f} 票")

    print("\n⚠️ Slashing:")
    惩罚 = E.惩罚(A, 0.05, "双签")
    print(f"  A被惩罚5%: {惩罚/HONGKUN_PER_HKAIC:.2f} HKAIC")

    print(f"\n📊 引擎摘要:")
    for k, v in E.引擎摘要().items(): print(f"  {k}: {v}")
    print("\n✅ 质押与治理Demo完成！")
