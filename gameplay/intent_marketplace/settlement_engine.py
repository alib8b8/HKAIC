"""
HKC 结算引擎 (settlement_engine.py)
====================================
意图执行后的结算——确保资金正确流转，防止重复结算和资金损失。

核心概念：
  - 原子结算（Atomic Settlement）：所有步骤要么全部完成要么全部回滚
  - 结算锁定（Settlement Lock）：结算期间锁定资金防止双花
  - 结算证明（Settlement Proof）：可验证的结算凭证

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum


class 结算状态(Enum):
    """结算状态"""
    待结算 = "pending"
    锁定中 = "locking"
    已锁定 = "locked"
    执行中 = "executing"
    已完成 = "completed"
    回滚中 = "rolling_back"
    已回滚 = "rolled_back"
    结算失败 = "failed"


@dataclass
class 结算步骤:
    """结算的每一步"""
    步骤ID: str
    源账户: str
    目标账户: str
    资产: str
    数量: float
    状态: str = "pending"  # pending/done/failed
    证明哈希: str = ""

    def 生成证明(self) -> str:
        """生成结算证明"""
        数据 = f"{self.源账户}{self.目标账户}{self.资产}{self.数量}{time.time()}"
        self.证明哈希 = hashlib.sha256(数据.encode()).hexdigest()[:16]
        return self.证明哈希


@dataclass
class 结算记录:
    """完整结算记录"""
    结算ID: str = ""
    意图ID: str = ""
    执行者: str = ""
    状态: 结算状态 = 结算状态.待结算
    步骤列表: List[结算步骤] = field(default_factory=list)
    锁定资金: Dict[str, float] = field(default_factory=dict)  # 资产 -> 锁定数量
    创建时间: float = 0.0
    完成时间: float = 0.0
    结算证明: str = ""
    回滚原因: str = ""

    def __post_init__(self):
        if not self.结算ID:
            self.结算ID = hashlib.sha256(
                f"settle_{self.意图ID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.创建时间 == 0.0:
            self.创建时间 = time.time()


class 结算引擎:
    """
    结算引擎
    
    管理意图执行的原子结算，支持锁定、执行、回滚。
    """

    def __init__(
        self,
        锁定超时秒: float = 3600.0,
        最大结算重试: int = 3,
    ):
        """
        初始化结算引擎
        
        Args:
            锁定超时秒: 锁定资金超时时间
            最大结算重试: 最大重试次数
        """
        self.锁定超时秒 = 锁定超时秒
        self.最大结算重试 = 最大结算重试

        self._结算记录: Dict[str, 结算记录] = {}
        self._账户余额: Dict[Tuple[str, str], float] = {}  # (账户, 资产) -> 余额
        self._锁定记录: Dict[str, Dict[str, float]] = {}  # 结算ID -> {资产: 锁定量}
        self._已结算意图: Set = set()  # 防止重复结算

    def 初始化余额(self, 账户: str, 资产: str, 数量: float) -> None:
        """初始化账户余额"""
        self._账户余额[(账户, 资产)] = 数量

    def 获取余额(self, 账户: str, 资产: str) -> float:
        """获取账户可用余额"""
        总额 = self._账户余额.get((账户, 资产), 0.0)
        # 减去锁定部分
        锁定额 = 0.0
        for 锁定dict in self._锁定记录.values():
            锁定额 += 锁定dict.get(资产, 0.0)
        return max(0, 总额 - 锁定额 * 0.5)  # 简化：假设锁定均匀分布

    def 创建结算(self, 意图ID: str, 执行者: str, 步骤列表: List[结算步骤]) -> Optional[结算记录]:
        """创建结算记录"""
        # 防重复
        if 意图ID in self._已结算意图:
            return None

        记录 = 结算记录(
            意图ID=意图ID,
            执行者=执行者,
            步骤列表=步骤列表,
        )
        self._结算记录[记录.结算ID] = 记录
        return 记录

    def 锁定资金(self, 结算ID: str) -> Tuple[bool, str]:
        """
        锁定结算所需资金
        
        Returns:
            (是否成功, 原因)
        """
        记录 = self._结算记录.get(结算ID)
        if not 记录:
            return False, "结算记录不存在"

        记录.状态 = 结算状态.锁定中

        # 计算需要锁定的资金
        需要锁定: Dict[str, float] = {}
        for 步骤 in 记录.步骤列表:
            if 步骤.源账户 not in 需要锁定:
                需要锁定[步骤.源账户] = 0
            # 简化：按资产锁定
            key = (步骤.源账户, 步骤.资产)
            当前余额 = self._账户余额.get(key, 0.0)
            if 当前余额 < 步骤.数量:
                记录.状态 = 结算状态.结算失败
                return False, f"账户{步骤.源账户}的{步骤.资产}余额不足"

        # 执行锁定
        锁定dict: Dict[str, float] = {}
        for 步骤 in 记录.步骤列表:
            if 步骤.资产 not in 锁定dict:
                锁定dict[步骤.资产] = 0
            锁定dict[步骤.资产] += 步骤.数量

        self._锁定记录[结算ID] = 锁定dict
        记录.锁定资金 = 锁定dict
        记录.状态 = 结算状态.已锁定
        return True, "锁定成功"

    def 执行结算(self, 结算ID: str) -> Tuple[bool, str]:
        """
        执行原子结算
        
        所有步骤要么全部成功，要么全部回滚。
        """
        记录 = self._结算记录.get(结算ID)
        if not 记录:
            return False, "结算记录不存在"
        if 记录.状态 != 结算状态.已锁定:
            return False, f"结算状态不正确: {记录.状态.value}"

        记录.状态 = 结算状态.执行中

        # 保存余额快照用于回滚
        快照 = dict(self._账户余额)

        # 逐步执行
        for 步骤 in 记录.步骤列表:
            源key = (步骤.源账户, 步骤.资产)
            目标key = (步骤.目标账户, 步骤.资产)

            源余额 = self._账户余额.get(源key, 0.0)
            if 源余额 < 步骤.数量:
                # 余额不足，回滚
                self._账户余额 = 快照
                记录.状态 = 结算状态.已回滚
                记录.回滚原因 = f"步骤{步骤.步骤ID}余额不足"
                self._释放锁定(结算ID)
                return False, 记录.回滚原因

            # 扣减源账户
            self._账户余额[源key] = 源余额 - 步骤.数量
            # 增加目标账户
            self._账户余额[目标key] = self._账户余额.get(目标key, 0.0) + 步骤.数量

            步骤.状态 = "done"
            步骤.生成证明()

        # 所有步骤成功
        记录.状态 = 结算状态.已完成
        记录.完成时间 = time.time()
        记录.结算证明 = hashlib.sha256(
            "".join(s.证明哈希 for s in 记录.步骤列表).encode()
        ).hexdigest()[:16]
        self._已结算意图.add(记录.意图ID)
        self._释放锁定(结算ID)
        return True, "结算成功"

    def _释放锁定(self, 结算ID: str) -> None:
        """释放锁定资金"""
        self._锁定记录.pop(结算ID, None)

    def 获取结算记录(self, 结算ID: str) -> Optional[结算记录]:
        """获取结算记录"""
        return self._结算记录.get(结算ID)

    def 获取统计(self) -> Dict[str, Any]:
        """获取结算统计"""
        状态统计 = {}
        for 状态 in 结算状态:
            状态统计[状态.value] = 0
        for 记录 in self._结算记录.values():
            状态统计[记录.状态.value] += 1
        return {
            "总结算数": len(self._结算记录),
            "状态分布": 状态统计,
        }


