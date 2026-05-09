"""
HKAIC 市场与定价 (market.py)
=============================
订单簿(限价/市价)、K线数据、深度图、交易对模拟。
纯Python，零外部依赖。
"""

import hashlib
import os
import time
import random
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

HONGKUN_PER_HKAIC = 10 ** 16


class 订单方向(Enum):
    买入 = "buy"; 卖出 = "sell"

class 订单类型(Enum):
    限价 = "limit"; 市价 = "market"

class 订单状态(Enum):
    待成交 = "open"; 部分成交 = "partial"; 已成交 = "filled"; 已取消 = "cancelled"


@dataclass
class 订单:
    """交易订单"""
    订单ID: str; 方向: 订单方向; 类型: 订单类型
    交易对: str; 价格: float; 数量: float; 剩余: float
    下单者: str; 时间戳: float = 0.0
    状态: 订单状态 = 订单状态.待成交

@dataclass
class 成交记录:
    """成交记录"""
    成交ID: str; 交易对: str; 价格: float; 数量: float
    买方: str; 卖方: str; 时间戳: float

@dataclass
class K线数据:
    """K线(OHLCV)"""
    开盘时间: float; 开盘: float; 最高: float; 最低: float; 收盘: float
    成交量: float; 交易对: str


class 订单簿:
    """订单簿 — 维护买卖挂单"""

    def __init__(self, 交易对: str):
        self.交易对 = 交易对
        self._买单: List[订单] = []  # 按价格降序
        self._卖单: List[订单] = []  # 按价格升序
        self._成交历史: List[成交记录] = []
        self._订单索引: Dict[str, 订单] = {}

    def 添加订单(self, order: 订单) -> List[成交记录]:
        """添加订单，尝试撮合"""
        self._订单索引[order.订单ID] = order
        成交列表 = []
        if order.方向 == 订单方向.买入:
            成交列表 = self._撮合买入(order)
            if order.剩余 > 0 and order.类型 == 订单类型.限价:
                self._买单.append(order)
                self._买单.sort(key=lambda o: o.价格, reverse=True)
        else:
            成交列表 = self._撮合卖出(order)
            if order.剩余 > 0 and order.类型 == 订单类型.限价:
                self._卖单.append(order)
                self._卖单.sort(key=lambda o: o.价格)
        return 成交列表

    def _撮合买入(self, 买: 订单) -> List[成交记录]:
        成交 = []
        while 买.剩余 > 0 and self._卖单:
            卖 = self._卖单[0]
            if 买.类型 == 订单类型.限价 and 买.价格 < 卖.价格: break
            成交价 = 卖.价格
            成交量 = min(买.剩余, 卖.剩余)
            买.剩余 -= 成交量; 卖.剩余 -= 成交量
            记录 = 成交记录(成交ID=self._新ID(), 交易对=self.交易对,
                           价格=成交价, 数量=成交量, 买方=买.下单者,
                           卖方=卖.下单者, 时间戳=time.time())
            成交.append(记录); self._成交历史.append(记录)
            if 卖.剩余 <= 0:
                卖.状态 = 订单状态.已成交; self._卖单.pop(0)
            else:
                卖.状态 = 订单状态.部分成交
        买.状态 = 订单状态.已成交 if 买.剩余 <= 0 else (
            订单状态.部分成交 if 买.剩余 < 买.数量 else 订单状态.待成交)
        return 成交

    def _撮合卖出(self, 卖: 订单) -> List[成交记录]:
        成交 = []
        while 卖.剩余 > 0 and self._买单:
            买 = self._买单[0]
            if 卖.类型 == 订单类型.限价 and 卖.价格 > 买.价格: break
            成交价 = 买.价格
            成交量 = min(买.剩余, 卖.剩余)
            买.剩余 -= 成交量; 卖.剩余 -= 成交量
            记录 = 成交记录(成交ID=self._新ID(), 交易对=self.交易对,
                           价格=成交价, 数量=成交量, 买方=买.下单者,
                           卖方=卖.下单者, 时间戳=time.time())
            成交.append(记录); self._成交历史.append(记录)
            if 买.剩余 <= 0:
                买.状态 = 订单状态.已成交; self._买单.pop(0)
            else:
                买.状态 = 订单状态.部分成交
        卖.状态 = 订单状态.已成交 if 卖.剩余 <= 0 else (
            订单状态.部分成交 if 卖.剩余 < 卖.数量 else 订单状态.待成交)
        return 成交

    def 取消订单(self, 订单ID: str) -> bool:
        o = self._订单索引.get(订单ID)
        if not o or o.状态 not in (订单状态.待成交, 订单状态.部分成交): return False
        o.状态 = 订单状态.已取消
        if o.方向 == 订单方向.买入: self._买单 = [x for x in self._买单 if x.订单ID != 订单ID]
        else: self._卖单 = [x for x in self._卖单 if x.订单ID != 订单ID]
        return True

    def 买一(self) -> Optional[float]:
        return self._买单[0].价格 if self._买单 else None
    def 卖一(self) -> Optional[float]:
        return self._卖单[0].价格 if self._卖单 else None
    def 最新价(self) -> Optional[float]:
        return self._成交历史[-1].价格 if self._成交历史 else None

    def 深度(self, 档位: int = 10) -> dict:
        """获取订单簿深度"""
        买盘 = [(o.价格, o.剩余) for o in self._买单[:档位]]
        卖盘 = [(o.价格, o.剩余) for o in self._卖单[:档位]]
        return {"买盘": 买盘, "卖盘": 卖盘}

    def 深度图数据(self) -> dict:
        """深度图数据（累计）"""
        买累计 = []; 累计 = 0
        for o in self._买单:
            累计 += o.剩余; 买累计.append((o.价格, 累计))
        卖累计 = []; 累计 = 0
        for o in self._卖单:
            累计 += o.剩余; 卖累计.append((o.价格, 累计))
        return {"买盘累计": 买累计, "卖盘累计": 卖累计}

    def K线(self, 周期秒: int = 3600, 数量: int = 24) -> List[K线数据]:
        """生成K线数据"""
        if not self._成交历史: return []
        klines = []; 当前 = []; 周期开始 = 0
        for 交易 in sorted(self._成交历史, key=lambda t: t.时间戳):
            槽位 = int(交易.时间戳 // 周期秒)
            if 槽位 != 周期开始 and 当前:
                klines.append(self._合并K线(当前, 周期秒))
                当前 = []; 周期开始 = 槽位
            当前.append(交易)
        if 当前: klines.append(self._合并K线(当前, 周期秒))
        return klines[-数量:]

    def _合并K线(self, 成交列表: List[成交记录], 周期: int) -> K线数据:
        价格 = [t.价格 for t in 成交列表]
        return K线数据(
            开盘时间=成交列表[0].时间戳, 开盘=价格[0], 最高=max(价格),
            最低=min(价格), 收盘=价格[-1], 成交量=sum(t.数量 for t in 成交列表),
            交易对=self.交易对)

    def _新ID(self) -> str:
        """H-01修复: 使用os.urandom加密随机数，替代可预测的time.time_ns()+random.random()"""
        return hashlib.sha256(os.urandom(32)).hexdigest()[:12]


class 市场引擎:
    """HKAIC 市场引擎 — 多交易对订单簿"""

    def __init__(self):
        self._订单簿: Dict[str, 订单簿] = {}
        self._交易对 = ["HKAIC/USD", "HKAIC/BTC", "HKAIC/ETH"]
        for 对 in self._交易对:
            self._订单簿[对] = 订单簿(对)

    def 下单(self, 交易对: str, 方向: 订单方向, 类型: 订单类型,
             价格: float, 数量: float, 下单者: str) -> Tuple[订单, List[成交记录]]:
        """下单"""
        簿 = self._订单簿.get(交易对)
        if not 簿: raise ValueError(f"不支持的交易对: {交易对}")
        oid = hashlib.sha256(f"{下单者}{交易对}{os.urandom(16).hex()}".encode()).hexdigest()[:12]  # H-01: os.urandom替代time.time_ns()
        order = 订单(订单ID=oid, 方向=方向, 类型=类型, 交易对=交易对,
                    价格=价格, 数量=数量, 剩余=数量, 下单者=下单者, 时间戳=time.time())
        成交 = 簿.添加订单(order)
        return order, 成交

    def 获取订单簿(self, 交易对: str) -> Optional[订单簿]:
        return self._订单簿.get(交易对)

    def 行情(self) -> dict:
        """获取所有交易对行情"""
        结果 = {}
        for 对, 簿 in self._订单簿.items():
            最新 = 簿.最新价()
            结果[对] = {"最新价": 最新 or "N/A", "买一": 簿.买一(), "卖一": 簿.卖一(),
                       "成交数": len(簿._成交历史)}
        return 结果

    def 打印订单簿ASCII(self, 交易对: str, 档位: int = 5):
        """ASCII订单簿"""
        簿 = self._订单簿.get(交易对)
        if not 簿: return
        深度 = 簿.深度(档位)
        print(f"\n  📊 {交易对} 订单簿")
        print("  " + "=" * 40)
        print(f"  {'价格':>12} {'数量':>12}  │  {'数量':>12} {'价格':>12}")
        print("  " + "-" * 40)
        卖盘 = list(reversed(深度["卖盘"]))
        买盘 = 深度["买盘"]
        for i in range(档位):
            卖 = 卖盘[i] if i < len(卖盘) else (0, 0)
            买 = 买盘[i] if i < len(买盘) else (0, 0)
            print(f"  {卖[0]:>12.4f} {卖[1]:>12.2f}  │  {买[1]:>12.2f} {买[0]:>12.4f}")

    def 模拟交易(self, 交易对: str, 轮数: int = 20):
        """模拟交易生成行情数据
        M-17: 注意random模块仅用于模拟交易，不影响真实交易安全性
        """
        簿 = self._订单簿.get(交易对)
        if not 簿: return
        基础价 = {"HKAIC/USD": 1.0, "HKAIC/BTC": 0.000015, "HKAIC/ETH": 0.0003}.get(交易对, 1.0)
        价格 = 基础价
        for _ in range(轮数):
            价格 *= (1 + random.gauss(0, 0.02))
            方向 = random.choice([订单方向.买入, 订单方向.卖出])
            数量 = random.uniform(10, 500)
            oid = hashlib.sha256(f"sim{os.urandom(16).hex()}".encode()).hexdigest()[:12]  # H-01: os.urandom替代time.time_ns()+random.random()
            order = 订单(订单ID=oid, 方向=方向, 类型=订单类型.限价, 交易对=交易对,
                        价格=价格, 数量=数量, 剩余=数量, 下单者="sim_bot", 时间戳=time.time())
            簿.添加订单(order)


if __name__ == "__main__":
    print("=" * 60)
    print("  HKAIC 市场引擎 Demo")
    print("=" * 60)

    M = 市场引擎()

    # 手动下单
    print("\n📋 手动下单 HKAIC/USD:")
    M.下单("HKAIC/USD", 订单方向.卖出, 订单类型.限价, 1.05, 1000, "Alice")
    M.下单("HKAIC/USD", 订单方向.卖出, 订单类型.限价, 1.03, 2000, "Bob")
    M.下单("HKAIC/USD", 订单方向.卖出, 订单类型.限价, 1.01, 1500, "Carol")
    M.下单("HKAIC/USD", 订单方向.买入, 订单类型.限价, 0.99, 3000, "Dave")
    M.下单("HKAIC/USD", 订单方向.买入, 订单类型.限价, 0.97, 2000, "Eve")
    # 市价单
    _, 成交 = M.下单("HKAIC/USD", 订单方向.买入, 订单类型.市价, 0, 500, "Frank")
    print(f"  市价买入500: 成交{len(成交)}笔")
    M.打印订单簿ASCII("HKAIC/USD")

    # 模拟交易
    print("\n🎰 模拟交易:")
    M.模拟交易("HKAIC/USD", 50)
    最新 = M._订单簿["HKAIC/USD"].最新价()
    print(f"  50轮模拟后最新价: ${最新:.4f}" if 最新 else "  无成交")

    # 行情总览
    print("\n📈 行情总览:")
    for 对, 数据 in M.行情().items():
        print(f"  {对}: 最新={数据['最新价']} 买一={数据['买一']} 卖一={数据['卖一']}")

    print("\n✅ 市场引擎Demo完成！")
