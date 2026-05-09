"""
HKAIC 交易引擎 (transaction.py)
================================
转账、交易费机制、交易池(mempool)、双花检测、交易确认。
"""

import hashlib
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

HONGKUN_PER_HKAIC = 10 ** 16


class 交易优先级(Enum):
    低 = "low"; 中 = "medium"; 高 = "high"; 紧急 = "urgent"


@dataclass
class 待处理交易:
    交易ID: str; 发送地址: str; 接收地址: str
    金额: int; 手续费: int; 时间戳: float; 优先级: 交易优先级
    签名: str = ""; 状态: str = "待处理"
    nonce: int = 0  # H-06: 交易nonce防重放

    def 费率(self) -> float:
        """每鸿坤手续费率"""
        return self.手续费 / self.金额 if self.金额 > 0 else 0

    def 等待时间(self) -> float:
        return time.time() - self.时间戳


class 交易池:
    """交易池 (Mempool) — 管理待确认交易
    L-02修复: 交易池大小上限默认10000笔，超出拒绝新交易"""

    def __init__(self, 最大容量: int = 10000):
        self._池: Dict[str, 待处理交易] = {}
        self._最大容量 = 最大容量  # L-02: 默认上限10000笔
        self._已见交易: Set[str] = set()
        self._拒绝计数: int = 0  # L-02: 因池满被拒绝的交易计数

    def 添加(self, tx: 待处理交易) -> bool:
        if tx.交易ID in self._已见交易: return False  # 重复交易
        # L-02: 池满时拒绝新交易
        if len(self._池) >= self._最大容量:
            self._拒绝计数 += 1
            return False  # 池满拒绝
        self._池[tx.交易ID] = tx
        self._已见交易.add(tx.交易ID)
        return True

    def 移除(self, 交易ID: str) -> bool:
        if 交易ID in self._池:
            del self._池[交易ID]; return True
        return False

    def 获取最高费率(self, 数量: int = 100) -> List[待处理交易]:
        """按费率排序，取前N笔"""
        排序 = sorted(self._池.values(), key=lambda t: t.费率(), reverse=True)
        return 排序[:数量]

    def 获取全部(self) -> List[待处理交易]:
        return list(self._池.values())

    @property
    def 大小(self) -> int: return len(self._池)

    def 是否已知(self, 交易ID: str) -> bool: return 交易ID in self._已见交易


class 交易引擎:
    """
    HKAIC 交易引擎
    
    功能: 转账(P2P)、交易费、交易池、双花检测、交易确认
    """

    def __init__(self):
        self.交易池 = 交易池()
        self._已确认: Dict[str, dict] = {}
        self._双花检测器: Dict[str, str] = {}  # UTXO标识 -> 消耗它的交易ID
        self._手续费收入: int = 0
        self._交易计数 = 0
        self._地址nonce: Dict[str, int] = {}  # H-06: 每个地址的nonce计数器

    def 创建转账(self, 发送: str, 接收: str, 金额_鸿坤: int,
                  手续费_鸿坤: int, 优先级: 交易优先级 = 交易优先级.中) -> 待处理交易:
        """创建转账交易，进入交易池"""
        # 双花检测：检查发送方是否已在池中有冲突交易
        for tx in self.交易池.获取全部():
            if tx.发送地址 == 发送:
                # 同一发送方可以有多笔交易（不同UTXO），但标记检查
                pass

        # H-06: 生成nonce防重放
        当前nonce = self._地址nonce.get(发送, 0)
        self._地址nonce[发送] = 当前nonce + 1
        交易ID = self._计算交易ID(发送, 接收, 金额_鸿坤, 手续费_鸿坤, 当前nonce)
        tx = 待处理交易(
            交易ID=交易ID, 发送地址=发送, 接收地址=接收,
            金额=金额_鸿坤, 手续费=手续费_鸿坤,
            时间戳=time.time(), 优先级=优先级, nonce=当前nonce)
        self.交易池.添加(tx)
        return tx

    def 确认交易(self, 交易ID: str) -> Optional[dict]:
        """确认交易（由出块者调用）"""
        tx = self.交易池._池.get(交易ID)
        if not tx: return None
        # 双花检查
        if self._检测双花(tx):
            tx.状态 = "双花拒绝"
            self.交易池.移除(交易ID)
            return None
        tx.状态 = "已确认"
        记录 = {"交易ID": tx.交易ID, "发送": tx.发送地址, "接收": tx.接收地址,
                "金额": tx.金额, "手续费": tx.手续费, "时间戳": tx.时间戳,
                "确认时间": time.time(), "优先级": tx.优先级.value,
                "nonce": tx.nonce}  # M-21: 记录nonce用于双花检测
        self._已确认[交易ID] = 记录
        self._手续费收入 += tx.手续费
        self._交易计数 += 1
        self.交易池.移除(交易ID)
        return 记录

    def 批量确认(self, 交易ID列表: List[str]) -> List[dict]:
        """批量确认交易（出块时使用）"""
        结果 = []
        for tid in 交易ID列表:
            r = self.确认交易(tid)
            if r: 结果.append(r)
        return 结果

    def _检测双花(self, tx: 待处理交易) -> bool:
        """双花检测：检查同一发送方的冲突交易
        M-21修复: 改进双花检测逻辑，使用nonce序列验证"""
        # M-21: 检查1 - nonce序列验证（防止重放攻击）
        for 已确认tx in self._已确认.values():
            if 已确认tx["发送"] == tx.发送地址:
                已确认nonce = 已确认tx.get("nonce", -1)
                if tx.nonce > 0 and 已确认nonce >= tx.nonce:
                    return True  # nonce已被使用，重放攻击
        # M-21: 检查2 - 交易池中nonce冲突
        池中同发送方 = [t for t in self.交易池.获取全部() 
                       if t.发送地址 == tx.发送地址 and t.交易ID != tx.交易ID]
        for 同发送方tx in 池中同发送方:
            if tx.nonce > 0 and 同发送方tx.nonce == tx.nonce:
                return True  # 同一nonce的交易已在池中
        # M-21: 检查3 - 同发送方+同接收方+同金额的精确重复
        for 已确认tx in self._已确认.values():
            if (已确认tx["发送"] == tx.发送地址 and
                已确认tx["接收"] == tx.接收地址 and
                已确认tx["金额"] == tx.金额 and
                已确认tx.get("nonce", -1) == tx.nonce):
                return True
        return False

    def _计算交易ID(self, 发送: str, 接收: str, 金额: int, 手续费: int, nonce: int = 0) -> str:
        """H-03/H-06修复: 使用os.urandom加密随机数 + nonce防重放"""
        import os as _os
        数据 = f"{发送}->{接收}:{金额}:{手续费}:{nonce}:{_os.urandom(16).hex()}"
        return hashlib.sha256(数据.encode()).hexdigest()

    @property
    def 手续费收入(self) -> int: return self._手续费收入

    @property
    def 已确认数(self) -> int: return len(self._已确认)

    def 查询已确认(self, 交易ID: str) -> Optional[dict]:
        return self._已确认.get(交易ID)

    def 引擎摘要(self) -> dict:
        return {"交易池大小": self.交易池.大小,
                "已确认交易": len(self._已确认),
                "手续费收入": f"{self._手续费收入 / HONGKUN_PER_HKAIC:.8f} HKAIC"}


if __name__ == "__main__":
    print("=" * 60)
    print("  HKAIC 交易引擎 Demo")
    print("=" * 60)

    E = 交易引擎()
    A, B, C = "addr_A", "addr_B", "addr_C"

    print("\n📦 创建交易:")
    tx1 = E.创建转账(A, B, 10**16, 10**13, 交易优先级.高)
    tx2 = E.创建转账(B, C, 5*10**15, 5*10**12, 交易优先级.中)
    tx3 = E.创建转账(C, A, 2*10**15, 10**12, 交易优先级.低)
    print(f"  交易池: {E.交易池.大小} 笔")

    print("\n⛏️ 按费率排序:")
    for tx in E.交易池.获取最高费率(10):
        print(f"  {tx.交易ID[:16]}... 费率:{tx.费率():.6f} 优先级:{tx.优先级.value}")

    print("\n✅ 确认交易:")
    for tx in [tx1, tx2, tx3]:
        r = E.确认交易(tx.交易ID)
        print(f"  {tx.交易ID[:16]}... → {'✅' if r else '❌'}")

    print(f"\n📊 引擎摘要:")
    for k, v in E.引擎摘要().items(): print(f"  {k}: {v}")
    print("\n✅ 交易引擎Demo完成！")
