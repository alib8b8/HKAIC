"""
Hongkun AI Chain — 智能水龙头 (ai_faucet.py)
==============================================
不是"给钱就发"，而是AI评估信誉后智能分配。

智能特性:
  1. 信誉评估 — 新用户低额,活跃用户高额
  2. 反女巫 — 同一指纹/行为模式识别
  3. 动态配额 — 根据网络拥堵度调整发放量
  4. ATH联动 — ATH握手通过的用户享受更高配额
"""

import hashlib
import time
import math
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class 领取等级(Enum):
    基础 = "basic"       # 新用户
    活跃 = "active"      # 活跃用户
    信任 = "trusted"     # ATH验证通过
    VIP = "vip"          # 长期贡献者


@dataclass
class 领取记录:
    """领取记录"""
    地址: str
    金额: float
    时间戳: float = 0.0
    等级: 领取等级 = 领取等级.基础
    指纹哈希: str = ""
    成功: bool = True
    失败原因: str = ""
    def __post_init__(self):
        if self.时间戳 == 0:
            self.时间戳 = time.time()


@dataclass
class 用户画像:
    """AI用户画像"""
    地址: str
    注册时间: float = 0.0
    领取次数: int = 0
    总领取: float = 0.0
    信誉评分: float = 30.0    # 0-100
    行为指纹: str = ""
    ATH验证: bool = False
    贡献分: float = 0.0
    风险标记: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.注册时间 == 0:
            self.注册时间 = time.time()
        if not self.行为指纹:
            self.行为指纹 = hashlib.sha256(self.地址.encode()).hexdigest()[:16]

    def 等级(self) -> 领取等级:
        if self.贡献分 > 50 and self.ATH验证:
            return 领取等级.VIP
        elif self.ATH验证 and self.信誉评分 > 60:
            return 领取等级.信任
        elif self.信誉评分 > 50 and self.领取次数 > 5:
            return 领取等级.活跃
        return 领取等级.基础


class 反女巫引擎:
    """识别和阻止女巫攻击"""

    def __init__(self):
        self._指纹库: Dict[str, List[str]] = {}   # 指纹→地址列表
        self._行为模式: Dict[str, dict] = {}        # 地址→行为特征
        self._黑名单: Dict[str, str] = {}           # 地址→原因

    def 检查(self, 地址: str, 指纹: str = "") -> Tuple[bool, str]:
        """检查是否为女巫,返回(通过,原因)"""
        # 黑名单检查
        if 地址 in self._黑名单:
            return False, f"黑名单: {self._黑名单[地址]}"

        # 指纹关联检查
        if 指纹:
            相关 = self._指纹库.setdefault(指纹, [])
            if 地址 not in 相关:
                相关.append(地址)
            if len(相关) > 3:
                # 同一指纹超过3个地址→疑似女巫
                return False, f"指纹关联{len(相关)}个地址,疑似女巫"

        # 行为模式检查
        模式 = self._行为模式.get(地址, {})
        快速领取 = 模式.get("快速领取次数", 0)
        if 快速领取 > 5:
            return False, "频繁领取,疑似自动化脚本"

        return True, ""

    def 记录行为(self, 地址: str, 行为: str):
        """记录用户行为"""
        模式 = self._行为模式.setdefault(地址, {})
        if 行为 == "快速领取":
            模式["快速领取次数"] = 模式.get("快速领取次数", 0) + 1

    def 加入黑名单(self, 地址: str, 原因: str):
        self._黑名单[地址] = 原因


class 动态配额管理器:
    """根据网络状态动态调整配额"""

    # 等级对应的基础配额(HKAIC)
    _基础配额 = {
        领取等级.基础: 10,
        领取等级.活跃: 50,
        领取等级.信任: 100,
        领取等级.VIP: 500,
    }

    def __init__(self, 池余额: float = 100000):
        self._池余额 = 池余额
        self._日发放: float = 0
        self._日限额: float = 池余额 * 0.01  # 每日最多发1%
        self._冷却期: Dict[str, float] = {}   # 地址→下次可领时间

    def 计算配额(self, 用户: 用户画像, 网络拥堵: float = 0.5) -> float:
        """计算用户可领取额度"""
        等级 = 用户.等级()
        基础 = self._基础配额[等级]

        # 网络拥堵调整:拥堵时减少
        拥堵系数 = max(0.3, 1.0 - 网络拥堵 * 0.5)

        # 池余额调整:余额低时减少
        余额比例 = self._池余额 / max(self._日限额 * 100, 1)
        余额系数 = min(1.0, 余额比例)

        # ATH加成
        ath加成 = 1.5 if 用户.ATH验证 else 1.0

        配额 = 基础 * 拥堵系数 * 余额系数 * ath加成
        return round(配额, 8)

    def 检查冷却(self, 地址: str) -> Tuple[bool, float]:
        """检查冷却期,返回(可领,剩余秒)"""
        下次 = self._冷却期.get(地址, 0)
        now = time.time()
        if now < 下次:
            return False, 下次 - now
        return True, 0

    def 设置冷却(self, 地址: str, 秒数: float = 3600):
        """设置冷却期"""
        self._冷却期[地址] = time.time() + 秒数

    def 扣除(self, 金额: float) -> bool:
        """从池中扣除"""
        if self._日发放 + 金额 > self._日限额:
            return False
        self._池余额 -= 金额
        self._日发放 += 金额
        return True

    def 状态(self) -> dict:
        return {
            "池余额": f"{self._池余额:.2f} HKAIC",
            "日发放": f"{self._日发放:.2f} HKAIC",
            "日限额": f"{self._日限额:.2f} HKAIC",
        }


class 智能水龙头:
    """
    HKC 智能水龙头
    
    AI评估→反女巫→动态配额→发放
    
    不是简单的"输入地址就给钱":
      1. AI评估用户信誉和等级
      2. 反女巫引擎检查
      3. 动态配额计算
      4. 冷却期控制
      5. ATH联动(ATH验证用户享受更高配额)
    """

    def __init__(self, 池余额: float = 100000):
        self._用户: Dict[str, 用户画像] = {}
        self._配额 = 动态配额管理器(池余额)
        self._反女巫 = 反女巫引擎()
        self._记录: List[领取记录] = []
        self._统计 = {"总领取": 0, "总金额": 0.0, "拒绝": 0}

    @property
    def 配额管理器(self): return self._配额
    @property
    def 反女巫引擎_(self): return self._反女巫

    def 注册用户(self, 地址: str, ATH验证: bool = False) -> 用户画像:
        """注册新用户"""
        if 地址 in self._用户:
            return self._用户[地址]
        用户 = 用户画像(地址=地址, ATH验证=ATH验证)
        self._用户[地址] = 用户
        return 用户

    def 领取(self, 地址: str, 指纹: str = "", 网络拥堵: float = 0.5) -> 领取记录:
        """智能领取"""
        # 1. 检查用户
        用户 = self._用户.get(地址)
        if not 用户:
            用户 = self.注册用户(地址)

        # 2. 反女巫检查
        通过, 原因 = self._反女巫.检查(地址, 指纹 or 用户.行为指纹)
        if not 通过:
            self._统计["拒绝"] += 1
            self._反女巫.记录行为(地址, "快速领取")
            return 领取记录(地址=地址, 金额=0, 等级=用户.等级(), 成功=False, 失败原因=原因)

        # 3. 冷却检查
        可领, 剩余 = self._配额.检查冷却(地址)
        if not 可领:
            return 领取记录(地址=地址, 金额=0, 等级=用户.等级(), 成功=False,
                           失败原因=f"冷却中,剩余{剩余:.0f}秒")

        # 4. 计算配额
        金额 = self._配额.计算配额(用户, 网络拥堵)
        if 金额 <= 0:
            return 领取记录(地址=地址, 金额=0, 等级=用户.等级(), 成功=False, 失败原因="配额为0")

        # 5. 扣除池余额
        if not self._配额.扣除(金额):
            return 领取记录(地址=地址, 金额=0, 等级=用户.等级(), 成功=False, 失败原因="池余额不足")

        # 6. 成功发放
        self._配额.设置冷却(地址)
        用户.领取次数 += 1
        用户.总领取 += 金额
        用户.信誉评分 = min(100, 用户.信誉评分 + 0.5)

        记录 = 领取记录(地址=地址, 金额=金额, 等级=用户.等级(), 指纹哈希=用户.行为指纹)
        self._记录.append(记录)
        self._统计["总领取"] += 1
        self._统计["总金额"] += 金额

        return 记录

    def 设置ATH验证(self, 地址: str, 通过: bool = True):
        """ATH联动:设置用户ATH验证状态"""
        用户 = self._用户.get(地址)
        if 用户:
            用户.ATH验证 = 通过
            if 通过:
                用户.信誉评分 = min(100, 用户.信誉评分 + 10)

    def 状态(self) -> dict:
        return {
            "注册用户": len(self._用户),
            "领取记录": len(self._记录),
            "统计": self._统计,
            "配额": self._配额.状态(),
        }


if __name__ == "__main__":
    print("  HKC 智能水龙头 Demo")
    faucet = 智能水龙头(100000)
    # 测试领取
    for i in range(5):
        r = faucet.领取(f"addr_{i}")
        print(f"  addr_{i}: {'✅' if r.成功 else '❌'} {r.金额:.2f} HKAIC ({r.等级.value})")
    # ATH验证用户
    faucet.注册用户("addr_vip", ATH验证=True)
    r = faucet.领取("addr_vip")
    print(f"  ATH用户: {'✅' if r.成功 else '❌'} {r.金额:.2f} HKAIC ({r.等级.value})")
    # 女巫攻击
    for i in range(10):
        r = faucet.领取("addr_0", 指纹="same_fingerprint")
    print(f"  女巫测试: {'✅' if r.成功 else '❌'} {r.失败原因}")
    print(f"  {faucet.状态()}")
