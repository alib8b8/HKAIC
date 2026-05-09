"""
HKC 跨链安全层 (crosschain_security.py)
========================================
跨链操作的安全防线——保险池、断路器、敞口限制、挑战期验证。
防止跨链攻击造成系统性风险。

核心概念：
  - 断路器（Circuit Breaker）：异常时自动熔断跨链操作
  - 敞口限制（Exposure Limit）：单桥/单链的最大敞口
  - 保险池（Insurance Pool）：跨链风险保险
  - 挑战期（Challenge Period）：跨链操作的争议窗口

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 安全事件等级(Enum):
    """安全事件等级"""
    信息 = "info"
    警告 = "warning"
    危险 = "danger"
    紧急 = "critical"


@dataclass
class 安全事件:
    """安全事件"""
    事件ID: str = ""
    等级: 安全事件等级 = 安全事件等级.信息
    类型: str = ""
    描述: str = ""
    涉及桥: str = ""
    涉及链: str = ""
    时间戳: float = 0.0
    已处理: bool = False

    def __post_init__(self):
        if not self.事件ID:
            self.事件ID = hashlib.sha256(
                f"sec_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.时间戳 == 0.0:
            self.时间戳 = time.time()


@dataclass
class 敞口限制:
    """敞口限制配置"""
    单桥最大敞口: float = 1000000.0
    单链最大敞口: float = 5000000.0
    单笔最大金额: float = 100000.0
    日累计最大: float = 10000000.0


@dataclass
class 断路器状态:
    """断路器状态"""
    全局断路: bool = False
    按桥断路: Dict[str, bool] = field(default_factory=dict)
    按链断路: Dict[str, bool] = field(default_factory=dict)
    断路原因: Dict[str, str] = field(default_factory=dict)
    断路时间: Dict[str, float] = field(default_factory=dict)


class 跨链安全层:
    """
    跨链安全层
    
    管理跨链操作的5层安全防线。
    """

    def __init__(
        self,
        敞口配置: Optional[敞口限制] = None,
        保险池初始: float = 100000.0,
        挑战期秒: float = 3600.0,
        自动恢复秒: float = 7200.0,
    ):
        """
        初始化安全层
        
        Args:
            敞口配置: 敞口限制配置
            保险池初始: 保险池初始金额
            挑战期秒: 跨链操作挑战期
            自动恢复秒: 断路器自动恢复时间
        """
        self.敞口配置 = 敞口配置 or 敞口限制()
        self.保险池余额 = 保险池初始
        self.挑战期秒 = 挑战期秒
        self.自动恢复秒 = 自动恢复秒

        self._断路器 = 断路器状态()
        self._日累计: Dict[str, float] = {}  # 日期 -> 累计金额
        self._桥敞口: Dict[str, float] = {}
        self._链敞口: Dict[str, float] = {}
        self._安全事件: List[安全事件] = []
        self._挑战: Dict[str, Dict[str, Any]] = {}  # 事务ID -> 挑战信息

    def 检查敞口(self, 桥ID: str, 源链: str, 目标链: str, 金额: float) -> Tuple[bool, str]:
        """
        检查是否超出敞口限制
        
        Returns:
            (是否允许, 原因)
        """
        if self._断路器.全局断路:
            return False, "全局断路器已触发"

        if self._断路器.按桥断路.get(桥ID, False):
            return False, f"桥{桥ID}断路器已触发"

        if self._断路器.按链断路.get(源链, False) or self._断路器.按链断路.get(目标链, False):
            return False, "相关链断路器已触发"

        # 单笔检查
        if 金额 > self.敞口配置.单笔最大金额:
            return False, f"单笔金额{金额}超过上限{self.敞口配置.单笔最大金额}"

        # 单桥敞口
        当前桥敞口 = self._桥敞口.get(桥ID, 0.0) + 金额
        if 当前桥敞口 > self.敞口配置.单桥最大敞口:
            return False, f"桥{桥ID}敞口将超限"

        # 单链敞口
        for 链 in (源链, 目标链):
            当前敞口 = self._链敞口.get(链, 0.0) + 金额
            if 当前敞口 > self.敞口配置.单链最大敞口:
                return False, f"链{链}敞口将超限"

        # 日累计检查
        今日 = time.strftime("%Y%m%d")
        日累计 = self._日累计.get(今日, 0.0) + 金额
        if 日累计 > self.敞口配置.日累计最大:
            return False, f"今日累计金额将超限"

        return True, "通过"

    def 记录敞口(self, 桥ID: str, 源链: str, 目标链: str, 金额: float) -> None:
        """记录新增敞口"""
        self._桥敞口[桥ID] = self._桥敞口.get(桥ID, 0.0) + 金额
        self._链敞口[源链] = self._链敞口.get(源链, 0.0) + 金额
        self._链敞口[目标链] = self._链敞口.get(目标链, 0.0) + 金额
        今日 = time.strftime("%Y%m%d")
        self._日累计[今日] = self._日累计.get(今日, 0.0) + 金额

    def 释放敞口(self, 桥ID: str, 源链: str, 目标链: str, 金额: float) -> None:
        """释放敞口"""
        self._桥敞口[桥ID] = max(0, self._桥敞口.get(桥ID, 0.0) - 金额)
        self._链敞口[源链] = max(0, self._链敞口.get(源链, 0.0) - 金额)
        self._链敞口[目标链] = max(0, self._链敞口.get(目标链, 0.0) - 金额)

    def 触发断路器(self, 目标: str = "global", 原因: str = "") -> None:
        """触发断路器"""
        if 目标 == "global":
            self._断路器.全局断路 = True
        elif 目标.startswith("bridge:"):
            桥ID = 目标[7:]
            self._断路器.按桥断路[桥ID] = True
        elif 目标.startswith("chain:"):
            链名 = 目标[6:]
            self._断路器.按链断路[链名] = True

        self._断路器.断路原因[目标] = 原因
        self._断路器.断路时间[目标] = time.time()

        事件 = 安全事件(
            等级=安全事件等级.紧急,
            类型="断路器触发",
            描述=f"{目标}断路: {原因}",
        )
        self._安全事件.append(事件)

    def 恢复断路器(self, 目标: str = "global") -> bool:
        """恢复断路器"""
        断路时间 = self._断路器.断路时间.get(目标, 0)
        冷却期 = time.time() - 断路时间
        if 冷却期 < self.自动恢复秒:
            return False  # 冷却期未过

        if 目标 == "global":
            self._断路器.全局断路 = False
        elif 目标.startswith("bridge:"):
            self._断路器.按桥断路.pop(目标[7:], None)
        elif 目标.startswith("chain:"):
            self._断路器.按链断路.pop(目标[6:], None)

        self._断路器.断路原因.pop(目标, None)
        self._断路器.断路时间.pop(目标, None)
        return True

    def 收取保险费(self, 金额: float) -> None:
        """收取跨链保险费"""
        self.保险池余额 += 金额

    def 理赔(self, 金额: float) -> Tuple[bool, float]:
        """保险理赔"""
        赔付 = min(金额, self.保险池余额)
        self.保险池余额 -= 赔付
        return 赔付 > 0, 赔付

    def 发起挑战(self, 事务ID: str, 挑战者: str, 理由: str) -> bool:
        """发起跨链挑战"""
        if 事务ID in self._挑战:
            return False
        self._挑战[事务ID] = {
            "挑战者": 挑战者,
            "理由": 理由,
            "时间": time.time(),
            "截止": time.time() + self.挑战期秒,
        }
        return True

    def 检查挑战(self, 事务ID: str) -> Tuple[bool, str]:
        """检查事务是否有未决挑战"""
        挑战 = self._挑战.get(事务ID)
        if not 挑战:
            return False, ""
        if time.time() > 挑战["截止"]:
            del self._挑战[事务ID]
            return False, ""
        return True, 挑战["理由"]

    def 报告安全事件(self, 等级: 安全事件等级, 类型: str, 描述: str, 涉及桥: str = "", 涉及链: str = "") -> 安全事件:
        """报告安全事件"""
        事件 = 安全事件(
            等级=等级,
            类型=类型,
            描述=描述,
            涉及桥=涉及桥,
            涉及链=涉及链,
        )
        self._安全事件.append(事件)

        # 危险等级以上自动触发断路
        if 等级 in (安全事件等级.危险, 安全事件等级.紧急):
            if 涉及桥:
                self.触发断路器(f"bridge:{涉及桥}", 描述)
            if 涉及链:
                self.触发断路器(f"chain:{涉及链}", 描述)

        return 事件

    def 获取安全事件(self, 最低等级: 安全事件等级 = 安全事件等级.警告) -> List[安全事件]:
        """获取安全事件"""
        等级排序 = [安全事件等级.信息, 安全事件等级.警告, 安全事件等级.危险, 安全事件等级.紧急]
        最低索引 = 等级排序.index(最低等级)
        return [e for e in self._安全事件 if 等级排序.index(e.等级) >= 最低索引]

    def 获取统计(self) -> Dict[str, Any]:
        """获取安全统计"""
        return {
            "全局断路": self._断路器.全局断路,
            "断路桥数": sum(1 for v in self._断路器.按桥断路.values() if v),
            "断路链数": sum(1 for v in self._断路器.按链断路.values() if v),
            "保险池余额": round(self.保险池余额, 2),
            "安全事件数": len(self._安全事件),
            "待决挑战": len(self._挑战),
        }
