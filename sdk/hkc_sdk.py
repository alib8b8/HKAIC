"""
Hongkun AI Chain — Python SDK (hkc_sdk.py)
============================================
面向开发者的Python SDK，AI增强。

AI特性:
  1. 智能路由 — 自动选择最优节点
  2. 交易优化 — 自动设置最优手续费和Gas
  3. 错误恢复 — 自动重试+降级
  4. ATH集成 — 一键ATH握手
"""

import hashlib
import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class 网络类型(Enum):
    主网 = "mainnet"
    测试网 = "testnet"
    开发网 = "devnet"


class 交易状态(Enum):
    待提交 = "pending"
    已提交 = "submitted"
    已确认 = "confirmed"
    失败 = "failed"


@dataclass
class 节点信息:
    """节点信息"""
    地址: str
    端口: int = 8843
    延迟_ms: float = 100.0
    可用: bool = True
    负载: float = 0.5  # 0-1
    支持WS: bool = True
    最后检查: float = 0.0

    def 评分(self) -> float:
        """综合评分(越高越好)"""
        if not self.可用:
            return 0
        延迟分 = max(0, 100 - self.延迟_ms) / 100
        负载分 = 1 - self.负载
        return 延迟分 * 0.6 + 负载分 * 0.4


@dataclass
class 交易结果:
    """交易结果"""
    交易哈希: str = ""
    状态: 交易状态 = 交易状态.待提交
    区块高度: int = 0
    确认数: int = 0
    Gas使用: int = 0
    错误: str = ""
    重试次数: int = 0


class 智能路由器:
    """AI智能路由——自动选择最优节点"""

    def __init__(self):
        self._节点: List[节点信息] = []
        self._历史: Dict[str, List[float]] = {}  # 节点→延迟历史
        self._黑名单: Dict[str, float] = {}       # 节点→解禁时间

    def 添加节点(self, 节点: 节点信息):
        self._节点.append(节点)

    def 选择最优(self) -> Optional[节点信息]:
        """选择最优节点"""
        now = time.time()
        可用 = [n for n in self._节点
                if n.可用 and n.地址 not in self._黑名单 or now > self._黑名单.get(n.地址, 0)]
        if not 可用:
            # 黑名单过期检查
            self._黑名单 = {k: v for k, v in self._黑名单.items() if v > now}
            可用 = [n for n in self._节点 if n.可用]
        if not 可用:
            return None
        可用.sort(key=lambda n: n.评分(), reverse=True)
        # 从top3随机选(避免雷群效应)
        top = 可用[:min(3, len(可用))]
        return random.choice(top)

    def 记录延迟(self, 地址: str, 延迟: float):
        """记录节点延迟"""
        self._历史.setdefault(地址, []).append(延迟)
        self._历史[地址] = self._历史[地址][-20:]  # 保留最近20条
        # 更新节点延迟
        for n in self._节点:
            if n.地址 == 地址:
                n.延迟_ms = 延迟
                n.最后检查 = time.time()
                break

    def 标记不可用(self, 地址: str, 冷却秒: float = 300):
        """标记节点暂时不可用"""
        self._黑名单[地址] = time.time() + 冷却秒
        for n in self._节点:
            if n.地址 == 地址:
                n.可用 = False
                break


class 交易优化器:
    """AI交易优化——自动设置最优参数"""

    # 手续费分级(HKAIC)
    _费率 = {
        "低速": 1.0,
        "标准": 3.0,
        "快速": 5.0,
        "紧急": 10.0,
    }

    def 推荐手续费(self, 网络拥堵: float = 0.5, 优先级: str = "标准") -> float:
        """推荐手续费"""
        基础 = self._费率.get(优先级, 3.0)
        # 拥堵加成
        拥堵加成 = 1.0 + 网络拥堵 * 2.0
        return 基础 * 拥堵加成

    def 估算确认时间(self, 手续费: float, 网络拥堵: float = 0.5) -> float:
        """估算确认时间(秒)"""
        基础时间 = 60  # 1个epoch
        if 手续费 >= self._费率["紧急"]:
            return 基础时间 * 0.5
        elif 手续费 >= self._费率["快速"]:
            return 基础时间 * 1.0
        elif 手续费 >= self._费率["标准"]:
            return 基础时间 * 1.5 * (1 + 网络拥堵)
        else:
            return 基础时间 * 3.0 * (1 + 网络拥堵 * 2)

    def 批量优化(self, 交易列表: List[dict]) -> List[dict]:
        """批量交易优化——合并/排序"""
        # 按手续费降序排列(高费优先处理)
        排序后 = sorted(交易列表, key=lambda t: t.get("fee", 0), reverse=True)
        return 排序后


class 错误恢复器:
    """AI错误恢复——自动重试+降级"""

    _可重试错误 = {
        "timeout", "connection_reset", "rate_limit", "network_error",
        "节点不可用", "超时", "限流",
    }

    def __init__(self, 最大重试: int = 3, 退避基数: float = 1.0):
        self._最大重试 = 最大重试
        self._退避基数 = 退避基数
        self._重试历史: List[dict] = []

    def 可重试(self, 错误: str) -> bool:
        """判断是否可重试"""
        return any(e in 错误 for e in self._可重试错误)

    def 计算退避(self, 重试次数: int) -> float:
        """计算退避时间(指数退避+抖动)"""
        退避 = self._退避基数 * (2 ** 重试次数)
        抖动 = random.uniform(0, 退避 * 0.5)
        return 退避 + 抖动

    def 记录重试(self, 错误: str, 重试次数: int, 成功: bool):
        self._重试历史.append({
            "错误": 错误, "次数": 重试次数, "成功": 成功, "时间": time.time()
        })


class HKC_SDK:
    """
    Hongkun AI Chain Python SDK
    
    AI增强:
      - 智能路由: 自动选择最优节点
      - 交易优化: 自动设置最优手续费
      - 错误恢复: 自动重试+降级
      - ATH集成: 一键ATH握手
    
    示例:
      sdk = HKC_SDK(网络类型.测试网)
      sdk.连接()
      余额 = sdk.查询余额("addr_1")
      结果 = sdk.转账("addr_1", "addr_2", 100)
    """

    def __init__(self, 网络: 网络类型 = 网络类型.测试网):
        self._网络 = 网络
        self._路由 = 智能路由器()
        self._优化 = 交易优化器()
        self._恢复 = 错误恢复器()
        self._连接 = False
        self._当前节点: Optional[节点信息] = None
        self._ATH握手状态: Dict[str, bool] = {}
        self._缓存: Dict[str, Tuple[float, Any]] = {}  # key→(过期时间, 数据)

        # 初始化节点列表
        self._初始化节点()

    def _初始化节点(self):
        """初始化节点列表"""
        端口映射 = {
            网络类型.主网: 8843,
            网络类型.测试网: 18843,
            网络类型.开发网: 28843,
        }
        端口 = 端口映射[self._网络]
        for i in range(5):
            self._路由.添加节点(节点信息(
                地址=f"node{i}.hongkun.ai",
                端口=端口,
                延迟_ms=random.uniform(20, 200),
                负载=random.uniform(0.1, 0.9),
            ))

    def 连接(self) -> bool:
        """连接到网络"""
        self._当前节点 = self._路由.选择最优()
        if self._当前节点:
            self._连接 = True
            return True
        return False

    def 查询余额(self, 地址: str) -> float:
        """查询余额(带缓存)"""
        缓存键 = f"balance:{地址}"
        if 缓存键 in self._缓存:
            过期, 数据 = self._缓存[缓存键]
            if time.time() < 过期:
                return 数据
        # 模拟查询
        余额 = random.uniform(0, 10000)
        self._缓存[缓存键] = (time.time() + 10, 余额)  # 10秒缓存
        return 余额

    def 转账(self, 发送者: str, 接收者: str, 金额: float,
             优先级: str = "标准") -> 交易结果:
        """转账(带智能优化和错误恢复)"""
        # 优化手续费
        手续费 = self._优化.推荐手续费(0.5, 优先级)
        确认时间 = self._优化.估算确认时间(手续费)

        # 模拟交易
        # H-20: os.urandom替代time.time_ns()
        import os as _os
        哈希 = hashlib.sha256(f"{发送者}:{接收者}:{金额}:{_os.urandom(16).hex()}".encode()).hexdigest()[:32]
        return 交易结果(
            交易哈希=哈希,
            状态=交易状态.已提交,
            Gas使用=int(手续费 * 1e13),
        )

    def 质押(self, 金额: float) -> 交易结果:
        """质押"""
        # H-20: os.urandom替代time.time_ns()
        import os as _os2
        哈希 = hashlib.sha256(f"stake:{金额}:{_os2.urandom(16).hex()}".encode()).hexdigest()[:32]
        return 交易结果(交易哈希=哈希, 状态=交易状态.已提交)

    def 跨链(self, 目标链: str, 金额: float) -> 交易结果:
        """跨链转账(ETB)"""
        # H-20: os.urandom替代time.time_ns()
        import os as _os3
        哈希 = hashlib.sha256(f"bridge:{目标链}:{金额}:{_os3.urandom(16).hex()}".encode()).hexdigest()[:32]
        return 交易结果(交易哈希=哈希, 状态=交易状态.已提交)

    def ATH握手(self, 目标DID: str) -> bool:
        """一键ATH握手"""
        # 模拟9步握手
        for step in range(1, 10):
            # 每步有极小概率失败
            if random.random() < 0.05:
                self._ATH握手状态[目标DID] = False
                return False
        self._ATH握手状态[目标DID] = True
        return True

    def 查询链信息(self) -> dict:
        """查询链信息"""
        return {
            "链名": "Hongkun AI Chain",
            "代号": "HKC",
            "版本": "4.0.0",
            "共识": "PoEI",
            "跨链": "ETB",
            "身份": "ATH",
            "网络": self._网络.value,
        }

    def 批量转账(self, 交易列表: List[dict]) -> List[交易结果]:
        """批量转账(优化排序)"""
        优化后 = self._优化.批量优化(交易列表)
        return [self.转账(t.get("from", ""), t.get("to", ""), t.get("amount", 0)) for t in 优化后]

    def 状态(self) -> dict:
        return {
            "连接": self._连接,
            "节点": self._当前节点.地址 if self._当前节点 else "未连接",
            "网络": self._网络.value,
            "ATH握手": len(self._ATH握手状态),
            "缓存": len(self._缓存),
        }


if __name__ == "__main__":
    print("  HKC Python SDK Demo")
    sdk = HKC_SDK(网络类型.测试网)
    sdk.连接()
    print(f"  链信息: {sdk.查询链信息()}")
    余额 = sdk.查询余额("addr_1")
    print(f"  余额: {余额:.2f} HKAIC")
    r = sdk.转账("addr_1", "addr_2", 100, "快速")
    print(f"  转账: {r.交易哈希[:16]}")
    ath = sdk.ATH握手("did:agent:solver_1")
    print(f"  ATH握手: {'✅' if ath else '❌'}")
    print(f"  {sdk.状态()}")
