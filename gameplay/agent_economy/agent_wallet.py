"""
HKC Agent独立钱包 (agent_wallet.py)
=====================================
每个Agent拥有独立钱包，支持自适应Gas、涌智信用分额度、多资产管理。

核心概念：
  - 自适应Gas（Adaptive Gas）：根据Agent等级自动调整Gas额度
  - 涌智信用额度（Credit Line）：基于涌智信用分的透支额度
  - 多资产（Multi-Asset）：支持HKAIC、稳定币、NFT等

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 交易类型(Enum):
    """钱包交易类型"""
    转入 = "deposit"
    转出 = "withdraw"
    服务收入 = "service_income"
    协作分红 = "dividend"
    惩罚扣款 = "penalty"
    Gas费 = "gas_fee"


@dataclass
class 钱包交易:
    """钱包交易记录"""
    交易ID: str = ""
    AgentID: str = ""
    类型: 交易类型 = 交易类型.转入
    资产: str = "HKAIC"
    数量: float = 0.0
    余额快照: float = 0.0
    时间戳: float = 0.0
    备注: str = ""

    def __post_init__(self):
        if not self.交易ID:
            self.交易ID = hashlib.sha256(
                f"wallet_tx_{self.AgentID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()


@dataclass
class Agent钱包:
    """Agent独立钱包"""
    钱包地址: str = ""
    AgentID: str = ""
    余额: Dict[str, float] = field(default_factory=lambda: {"HKAIC": 0.0})
    信用额度: float = 0.0
    已用信用: float = 0.0
    Gas额度: float = 100.0
    已用Gas: float = 0.0
    交易历史: List[钱包交易] = field(default_factory=list)
    锁定资金: Dict[str, float] = field(default_factory=dict)
    创建时间: float = 0.0

    def __post_init__(self):
        if not self.钱包地址:
            self.钱包地址 = hashlib.sha256(
                f"wallet_{self.AgentID}".encode()
            ).hexdigest()[:20]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()

    def 可用余额(self, 资产: str = "HKAIC") -> float:
        """获取可用余额（扣除锁定部分）"""
        总额 = self.余额.get(资产, 0.0)
        锁定 = self.锁定资金.get(资产, 0.0)
        return max(0, 总额 - 锁定)

    def 可用信用(self) -> float:
        """获取可用信用额度"""
        return max(0, self.信用额度 - self.已用信用)


class 钱包管理器:
    """
    Agent钱包管理器
    
    管理所有Agent钱包的创建、交易、Gas和信用额度。
    """

    # 等级对应的Gas额度和信用额度
    等级配置 = {
        1: {"Gas额度": 100.0, "信用额度": 500.0},
        2: {"Gas额度": 500.0, "信用额度": 2000.0},
        3: {"Gas额度": 2000.0, "信用额度": 10000.0},
        4: {"Gas额度": 10000.0, "信用额度": 50000.0},
        5: {"Gas额度": 50000.0, "信用额度": 500000.0},
    }

    def __init__(self):
        self._钱包: Dict[str, Agent钱包] = {}  # AgentID -> 钱包

    def 创建钱包(self, AgentID: str, 初始等级: int = 1) -> Agent钱包:
        """为Agent创建钱包"""
        if AgentID in self._钱包:
            return self._钱包[AgentID]

        配置 = self.等级配置.get(初始等级, self.等级配置[1])
        钱包 = Agent钱包(
            AgentID=AgentID,
            Gas额度=配置["Gas额度"],
            信用额度=配置["信用额度"],
        )
        self._钱包[AgentID] = 钱包
        return 钱包

    def 存入(self, AgentID: str, 资产: str, 数量: float, 备注: str = "") -> Optional[钱包交易]:
        """存入资产"""
        钱包 = self._钱包.get(AgentID)
        if not 钱包:
            return None
        if 数量 <= 0:
            return None

        钱包.余额[资产] = 钱包.余额.get(资产, 0.0) + 数量
        交易 = 钱包交易(
            AgentID=AgentID,
            类型=交易类型.转入,
            资产=资产,
            数量=数量,
            余额快照=钱包.余额[资产],
            备注=备注,
        )
        钱包.交易历史.append(交易)
        return 交易

    def 提取(self, AgentID: str, 资产: str, 数量: float, 备注: str = "") -> Optional[钱包交易]:
        """提取资产"""
        钱包 = self._钱包.get(AgentID)
        if not 钱包:
            return None

        可用 = 钱包.可用余额(资产)
        if 可用 < 数量:
            return None

        钱包.余额[资产] -= 数量
        交易 = 钱包交易(
            AgentID=AgentID,
            类型=交易类型.转出,
            资产=资产,
            数量=数量,
            余额快照=钱包.余额[资产],
            备注=备注,
        )
        钱包.交易历史.append(交易)
        return 交易

    def 扣除Gas(self, AgentID: str, Gas量: float) -> bool:
        """扣除Gas费用"""
        钱包 = self._钱包.get(AgentID)
        if not 钱包:
            return False
        if 钱包.已用Gas + Gas量 > 钱包.Gas额度:
            return False

        钱包.已用Gas += Gas量
        # 从HKAIC余额扣除
        Gas费 = Gas量 * 0.001  # Gas单价
        if 钱包.余额.get("HKAIC", 0.0) >= Gas费:
            钱包.余额["HKAIC"] -= Gas费
            交易 = 钱包交易(
                AgentID=AgentID, 类型=交易类型.Gas费,
                资产="HKAIC", 数量=Gas费, 备注=f"Gas: {Gas量}",
            )
            钱包.交易历史.append(交易)
        return True

    def 使用信用(self, AgentID: str, 数量: float) -> bool:
        """使用信用额度"""
        钱包 = self._钱包.get(AgentID)
        if not 钱包:
            return False
        if 钱包.可用信用() < 数量:
            return False

        钱包.已用信用 += 数量
        钱包.余额["HKAIC"] = 钱包.余额.get("HKAIC", 0.0) + 数量
        return True

    def 偿还信用(self, AgentID: str, 数量: float) -> bool:
        """偿还信用"""
        钱包 = self._钱包.get(AgentID)
        if not 钱包:
            return False

        可用HKAIC = 钱包.可用余额("HKAIC")
        偿还量 = min(数量, 钱包.已用信用, 可用HKAIC)
        if 偿还量 <= 0:
            return False

        钱包.余额["HKAIC"] -= 偿还量
        钱包.已用信用 -= 偿还量
        return True

    def 升级额度(self, AgentID: str, 新等级: int) -> bool:
        """根据等级升级Gas和信用额度"""
        钱包 = self._钱包.get(AgentID)
        if not 钱包:
            return False
        配置 = self.等级配置.get(新等级)
        if not 配置:
            return False
        钱包.Gas额度 = 配置["Gas额度"]
        钱包.信用额度 = 配置["信用额度"]
        return True

    def 锁定资金(self, AgentID: str, 资产: str, 数量: float) -> bool:
        """锁定资金"""
        钱包 = self._钱包.get(AgentID)
        if not 钱包:
            return False
        if 钱包.可用余额(资产) < 数量:
            return False
        钱包.锁定资金[资产] = 钱包.锁定资金.get(资产, 0.0) + 数量
        return True

    def 解锁资金(self, AgentID: str, 资产: str, 数量: float) -> bool:
        """解锁资金"""
        钱包 = self._钱包.get(AgentID)
        if not 钱包:
            return False
        锁定量 = 钱包.锁定资金.get(资产, 0.0)
        if 锁定量 < 数量:
            return False
        钱包.锁定资金[资产] = 锁定量 - 数量
        return True

    def 获取钱包(self, AgentID: str) -> Optional[Agent钱包]:
        """获取钱包"""
        return self._钱包.get(AgentID)

    def 转账(self, 源AgentID: str, 目标AgentID: str, 资产: str, 数量: float, 备注: str = "") -> Tuple[bool, str]:
        """Agent间转账"""
        源钱包 = self._钱包.get(源AgentID)
        目标钱包 = self._钱包.get(目标AgentID)
        if not 源钱包 or not 目标钱包:
            return False, "钱包不存在"
        if 源钱包.可用余额(资产) < 数量:
            return False, "余额不足"

        源钱包.余额[资产] -= 数量
        目标钱包.余额[资产] = 目标钱包.余额.get(资产, 0.0) + 数量

        源交易 = 钱包交易(AgentID=源AgentID, 类型=交易类型.转出, 资产=资产, 数量=数量, 备注=备注)
        目标交易 = 钱包交易(AgentID=目标AgentID, 类型=交易类型.转入, 资产=资产, 数量=数量, 备注=备注)
        源钱包.交易历史.append(源交易)
        目标钱包.交易历史.append(目标交易)
        return True, "转账成功"
