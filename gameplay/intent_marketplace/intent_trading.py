"""
HKC 意图交易 (intent_trading.py)
=================================
意图本身可以交易——我有个意图，别人可以买走替我执行赚差价。
这让意图市场变成一个真正的交易市场，而不只是撮合引擎。

核心概念：
  - 意图包（Intent Bundle）：打包多个相似意图一起执行，降低成本
  - 意图拍卖（Intent Auction）：Solver竞拍执行权
  - 差价套利（Spread Arbitrage）：Solver通过更优路径赚取差价

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 交易类型(Enum):
    """意图交易类型"""
    直接执行 = "direct_execute"
    拍卖 = "auction"
    打包执行 = "bundle"
    差价套利 = "spread_arbitrage"


class 交易状态(Enum):
    """交易状态"""
    待处理 = "pending"
    已锁定 = "locked"
    执行中 = "executing"
    已完成 = "completed"
    已取消 = "cancelled"
    争议中 = "disputed"


@dataclass
class 意图包:
    """打包多个相似意图"""
    包ID: str = ""
    类型: 交易类型 = 交易类型.打包执行
    意图ID列表: List[str] = field(default_factory=list)
    总输入量: float = 0.0
    共享路径: Optional[str] = None
    预计节省费率: float = 0.0
    创建时间: float = 0.0

    def __post_init__(self):
        if not self.包ID:
            self.包ID = hashlib.sha256(
                f"bundle_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()


@dataclass
class 拍卖:
    """意图拍卖"""
    拍卖ID: str = ""
    意图ID: str = ""
    起拍价: float = 0.0
    当前最高出价: float = 0.0
    当前最高出价者: str = ""
    出价记录: List[Dict[str, Any]] = field(default_factory=list)
    开始时间: float = 0.0
    结束时间: float = 0.0
    状态: str = "open"  # open/closed/settled

    def __post_init__(self):
        if not self.拍卖ID:
            self.拍卖ID = hashlib.sha256(
                f"auction_{self.意图ID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.开始时间 == 0.0:
            self.开始时间 = time.time()
        if self.结束时间 == 0.0:
            self.结束时间 = self.开始时间 + 60  # 默认60秒拍卖

    def 出价(self, 出价者: str, 金额: float) -> bool:
        """出价"""
        if 金额 <= self.当前最高出价:
            return False
        if time.time() > self.结束时间:
            return False
        self.当前最高出价 = 金额
        self.当前最高出价者 = 出价者
        self.出价记录.append({
            "出价者": 出价者,
            "金额": 金额,
            "时间": time.time(),
        })
        return True


@dataclass
class 意图交易:
    """意图交易记录"""
    交易ID: str = ""
    意图ID: str = ""
    类型: 交易类型 = 交易类型.直接执行
    执行者: str = ""
    买入价: float = 0.0   # Solver为获得执行权支付的价格
    执行收益: float = 0.0  # Solver执行后获得的收益
    差价: float = 0.0      # 执行收益 - 买入价
    状态: 交易状态 = 交易状态.待处理
    创建时间: float = 0.0
    结算时间: float = 0.0

    def __post_init__(self):
        if not self.交易ID:
            self.交易ID = hashlib.sha256(
                f"itx_{self.意图ID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()


class 意图交易市场:
    """
    意图交易市场
    
    管理意图的打包、拍卖和差价套利交易。
    """

    def __init__(
        self,
        最小打包数: int = 3,
        拍卖时长秒: float = 60.0,
        差价上限: float = 0.05,  # 最大允许差价5%
    ):
        self.最小打包数 = 最小打包数
        self.拍卖时长秒 = 拍卖时长秒
        self.差价上限 = 差价上限

        self._交易: Dict[str, 意图交易] = {}
        self._拍卖: Dict[str, 拍卖] = {}
        self._意图包: Dict[str, 意图包] = {}

    def 创建拍卖(self, 意图ID: str, 起拍价: float) -> 拍卖:
        """为意图创建拍卖"""
        新拍卖 = 拍卖(
            意图ID=意图ID,
            起拍价=起拍价,
            当前最高出价=起拍价,
            结束时间=time.time() + self.拍卖时长秒,
        )
        self._拍卖[新拍卖.拍卖ID] = 新拍卖
        return 新拍卖

    def 竞拍(self, 拍卖ID: str, 出价者: str, 金额: float) -> bool:
        """参与竞拍"""
        拍卖obj = self._拍卖.get(拍卖ID)
        if not 拍卖obj:
            return False
        return 拍卖obj.出价(出价者, 金额)

    def 结算拍卖(self, 拍卖ID: str) -> Optional[意图交易]:
        """结算拍卖"""
        拍卖obj = self._拍卖.get(拍卖ID)
        if not 拍卖obj or 拍卖obj.状态 != "open":
            return None

        拍卖obj.状态 = "closed"
        if not 拍卖obj.当前最高出价者:
            return None

        交易 = 意图交易(
            意图ID=拍卖obj.意图ID,
            类型=交易类型.拍卖,
            执行者=拍卖obj.当前最高出价者,
            买入价=拍卖obj.当前最高出价,
        )
        self._交易[交易.交易ID] = 交易
        拍卖obj.状态 = "settled"
        return 交易

    def 打包意图(self, 意图ID列表: List[str]) -> 意图包:
        """打包多个意图"""
        包 = 意图包(
            类型=交易类型.打包执行,
            意图ID列表=意图ID列表,
        )
        self._意图包[包.包ID] = 包
        return 包

    def 创建差价交易(self, 意图ID: str, 执行者: str, 买入价: float) -> 意图交易:
        """创建差价套利交易"""
        交易 = 意图交易(
            意图ID=意图ID,
            类型=交易类型.差价套利,
            执行者=执行者,
            买入价=买入价,
        )
        self._交易[交易.交易ID] = 交易
        return 交易

    def 结算交易(self, 交易ID: str, 执行收益: float) -> Optional[意图交易]:
        """结算交易"""
        交易 = self._交易.get(交易ID)
        if not 交易:
            return None

        交易.执行收益 = 执行收益
        交易.差价 = 执行收益 - 交易.买入价
        交易.状态 = 交易状态.已完成
        交易.结算时间 = time.time()

        # 差价检查
        if 交易.买入价 > 0:
            差价比率 = abs(交易.差价) / 交易.买入价
            if 差价比率 > self.差价上限:
                交易.状态 = 交易状态.争议中

        return 交易

    def 获取交易(self, 交易ID: str) -> Optional[意图交易]:
        """获取交易"""
        return self._交易.get(交易ID)

    def 获取拍卖(self, 拍卖ID: str) -> Optional[拍卖]:
        """获取拍卖"""
        return self._拍卖.get(拍卖ID)

    def 获取统计(self) -> Dict[str, Any]:
        """获取市场统计"""
        return {
            "总交易数": len(self._交易),
            "活跃拍卖": sum(1 for a in self._拍卖.values() if a.状态 == "open"),
            "意图包数": len(self._意图包),
            "争议数": sum(1 for t in self._交易.values() if t.状态 == 交易状态.争议中),
        }
