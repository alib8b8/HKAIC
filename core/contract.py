"""
HKAIC 智能合约 (contract.py)
=============================
简单合约引擎：条件支付、多签合约、时间锁合约、合约执行验证。
纯Python，零外部依赖。
"""

import hashlib
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class 合约类型(Enum):
    条件支付 = "conditional"
    多签 = "multisig"
    时间锁 = "timelock"
    哈希锁 = "hashlock"
    自定义 = "custom"


class 合约状态(Enum):
    待执行 = "pending"; 已执行 = "executed"
    已过期 = "expired"; 已取消 = "cancelled"


@dataclass
class 合约条件:
    """合约执行条件"""
    类型: str          # "price_above", "price_below", "time_after", "time_before", "hash_match", "signature_count"
    阈值: float = 0.0
    参数: str = ""

    def 评估(self, 上下文: dict) -> bool:
        """评估条件是否满足"""
        if self.类型 == "time_after":
            return time.time() >= self.阈值
        elif self.类型 == "time_before":
            return time.time() <= self.阈值
        elif self.类型 == "price_above":
            当前价 = 上下文.get("price", 0)
            return 当前价 >= self.阈值
        elif self.类型 == "price_below":
            当前价 = 上下文.get("price", 0)
            return 当前价 <= self.阈值
        elif self.类型 == "hash_match":
            输入 = 上下文.get("hash_input", "")
            计算哈希 = hashlib.sha256(输入.encode()).hexdigest()
            return 计算哈希 == self.参数
        elif self.类型 == "signature_count":
            签名数 = 上下文.get("signatures", 0)
            return 签名数 >= self.阈值
        return False


@dataclass
class 合约:
    """智能合约实例"""
    合约ID: str; 类型: 合约类型; 创建者: str; 接收者: str
    金额: int               # 鸿坤单位
    条件列表: List[合约条件]
    超时时间: float = 0.0
    状态: 合约状态 = 合约状态.待执行
    创建时间: float = 0.0
    执行时间: float = 0.0
    数据: dict = field(default_factory=dict)

    def 所有条件满足(self, 上下文: dict) -> bool:
        return all(c.评估(上下文) for c in self.条件列表)

    def 已超时(self) -> bool:
        if self.超时时间 <= 0: return False
        return time.time() > self.超时时间


class 合约引擎:
    """
    HKAIC 智能合约引擎
    
    支持: 条件支付、多签合约、时间锁合约、哈希锁合约
    """

    def __init__(self):
        self._合约库: Dict[str, 合约] = {}
        self._执行记录: List[dict] = []
        self._自定义函数: Dict[str, Callable] = {}

    def 创建条件支付(self, 创建者: str, 接收者: str, 金额: int,
                       条件列表: List[合约条件], 超时: float = 0) -> 合约:
        """创建条件支付合约"""
        cid = self._生成ID(创建者, 接收者, 金额)
        c = 合约(合约ID=cid, 类型=合约类型.条件支付, 创建者=创建者, 接收者=接收者,
                 金额=金额, 条件列表=条件列表, 超时时间=超时 if 超时 else time.time() + 86400*30,
                 创建时间=time.time())
        self._合约库[cid] = c
        return c

    def 创建时间锁合约(self, 创建者: str, 接收者: str, 金额: int,
                         解锁时间: float) -> 合约:
        """创建时间锁合约 — 到指定时间后才可执行"""
        cid = self._生成ID(创建者, 接收者, 金额)
        条件 = 合约条件(类型="time_after", 阈值=解锁时间)
        c = 合约(合约ID=cid, 类型=合约类型.时间锁, 创建者=创建者, 接收者=接收者,
                 金额=金额, 条件列表=[条件], 超时时间=解锁时间 + 86400*365,
                 创建时间=time.time())
        self._合约库[cid] = c
        return c

    def 创建哈希锁合约(self, 创建者: str, 接收者: str, 金额: int,
                         原像哈希: str, 超时: float = 0) -> 合约:
        """创建哈希锁合约 — 需提供哈希原像才能解锁"""
        cid = self._生成ID(创建者, 接收者, 金额)
        条件 = 合约条件(类型="hash_match", 参数=原像哈希)
        c = 合约(合约ID=cid, 类型=合约类型.哈希锁, 创建者=创建者, 接收者=接收者,
                 金额=金额, 条件列表=[条件], 超时时间=超时 if 超时 else time.time() + 86400*7,
                 创建时间=time.time())
        self._合约库[cid] = c
        return c

    def 创建多签合约(self, 创建者: str, 接收者: str, 金额: int,
                      所需签名数: int) -> 合约:
        """创建多签合约"""
        cid = self._生成ID(创建者, 接收者, 金额)
        条件 = 合约条件(类型="signature_count", 阈值=所需签名数)
        c = 合约(合约ID=cid, 类型=合约类型.多签, 创建者=创建者, 接收者=接收者,
                 金额=金额, 条件列表=[条件], 超时时间=time.time() + 86400*30,
                 创建时间=time.time())
        self._合约库[cid] = c
        return c

    def 执行合约(self, 合约ID: str, 上下文: dict = None) -> Optional[dict]:
        """尝试执行合约"""
        c = self._合约库.get(合约ID)
        if not c: return None
        if c.状态 != 合约状态.待执行: return None
        if c.已超时():
            c.状态 = 合约状态.已过期; return None
        if not c.所有条件满足(上下文 or {}): return None
        c.状态 = 合约状态.已执行; c.执行时间 = time.time()
        记录 = {"合约ID": c.合约ID, "类型": c.类型.value, "创建者": c.创建者,
                "接收者": c.接收者, "金额": c.金额, "执行时间": c.执行时间}
        self._执行记录.append(记录)
        return 记录

    def 取消合约(self, 合约ID: str) -> bool:
        c = self._合约库.get(合约ID)
        if not c or c.状态 != 合约状态.待执行: return False
        c.状态 = 合约状态.已取消; return True

    def 查询合约(self, 合约ID: str) -> Optional[合约]:
        return self._合约库.get(合约ID)

    def 列出待执行(self) -> List[合约]:
        return [c for c in self._合约库.values() if c.状态 == 合约状态.待执行]

    def 注册自定义函数(self, 名称: str, 函数: Callable):
        self._自定义函数[名称] = 函数

    def _生成ID(self, *args) -> str:
        """H-04修复: 使用os.urandom加密随机数，替代可预测的time.time_ns()"""
        import os as _os
        数据 = "_".join(str(a) for a in args) + _os.urandom(16).hex()
        return hashlib.sha256(数据.encode()).hexdigest()[:24]

    def 引擎摘要(self) -> dict:
        状态统计 = {}
        for c in self._合约库.values():
            状态统计[c.状态.value] = 状态统计.get(c.状态.value, 0) + 1
        return {"合约总数": len(self._合约库), "已执行": len(self._执行记录),
                "状态分布": 状态统计}


if __name__ == "__main__":
    print("=" * 60)
    print("  HKAIC 智能合约 Demo")
    print("=" * 60)

    E = 合约引擎()
    A, B = "addr_A", "addr_B"

    # 1. 条件支付 — BTC价格到10万时自动转账
    print("\n📌 条件支付: BTC≥100000时转1 HKAIC")
    c1 = E.创建条件支付(A, B, 10**16,
                         [合约条件(类型="price_above", 阈值=100000)])
    r = E.执行合约(c1.合约ID, {"price": 95000})
    print(f"  BTC=95000: {'✅执行' if r else '❌未满足'}")
    r = E.执行合约(c1.合约ID, {"price": 105000})
    print(f"  BTC=105000: {'✅执行' if r else '❌未满足'}")

    # 2. 时间锁合约
    print("\n⏰ 时间锁合约: 1小时后可提取")
    解锁时间 = time.time() + 3600
    c2 = E.创建时间锁合约(A, B, 5*10**16, 解锁时间)
    r = E.执行合约(c2.合约ID)
    print(f"  现在: {'✅执行' if r else '❌未到时间'}")
    # 模拟时间已过
    r = E.执行合约(c2.合约ID, {"time_override": True})
    print(f"  1小时后: 需等待解锁")

    # 3. 哈希锁合约
    print("\n🔐 哈希锁合约: 提供原像解锁")
    原像 = "HKAIC_secret_preimage"
    哈希 = hashlib.sha256(原像.encode()).hexdigest()
    c3 = E.创建哈希锁合约(A, B, 3*10**16, 哈希)
    r = E.执行合约(c3.合约ID, {"hash_input": "wrong"})
    print(f"  错误原像: {'✅执行' if r else '❌哈希不匹配'}")
    r = E.执行合约(c3.合约ID, {"hash_input": 原像})
    print(f"  正确原像: {'✅执行' if r else '❌哈希不匹配'}")

    # 4. 多签合约
    print("\n🔏 多签合约: 需要3个签名")
    c4 = E.创建多签合约(A, B, 2*10**16, 所需签名数=3)
    r = E.执行合约(c4.合约ID, {"signatures": 2})
    print(f"  2个签名: {'✅执行' if r else '❌签名不足'}")
    r = E.执行合约(c4.合约ID, {"signatures": 3})
    print(f"  3个签名: {'✅执行' if r else '❌签名不足'}")

    print(f"\n📊 合约引擎摘要:")
    for k, v in E.引擎摘要().items(): print(f"  {k}: {v}")
    print("\n✅ 智能合约Demo完成！")
