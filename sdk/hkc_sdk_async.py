"""
Hongkun AI Chain — 异步SDK (hkc_sdk_async.py)
===============================================
异步版Python SDK，高并发场景使用。

特性:
  - 异步请求处理
  - 并行查询
  - 流式事件订阅
  - 连接池管理
"""

import hashlib
import time
import math
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class 异步任务:
    """异步任务"""
    任务ID: str
    类型: str
    状态: str = "pending"  # pending/running/done/failed
    结果: Any = None
    回调: Optional[Callable] = None
    创建时间: float = 0.0
    完成时间: float = 0.0

    def __post_init__(self):
        if self.创建时间 == 0:
            self.创建时间 = time.time()


class 连接池:
    """连接池管理"""

    def __init__(self, 最大连接: int = 10):
        self._最大 = 最大连接
        self._活跃: Dict[str, dict] = {}
        self._空闲: List[str] = []

    def 获取(self) -> Optional[str]:
        """获取连接"""
        if self._空闲:
            cid = self._空闲.pop()
            self._活跃[cid]["使用中"] = True
            return cid
        if len(self._活跃) < self._最大:
            cid = f"conn_{len(self._活跃)}"
            self._活跃[cid] = {"使用中": True, "创建": time.time()}
            return cid
        return None

    def 释放(self, cid: str):
        """释放连接"""
        if cid in self._活跃:
            self._活跃[cid]["使用中"] = False
            self._空闲.append(cid)

    def 状态(self) -> dict:
        return {
            "最大": self._最大,
            "活跃": len([c for c in self._活跃.values() if c["使用中"]]),
            "空闲": len(self._空闲),
        }


class 事件订阅器:
    """流式事件订阅"""

    def __init__(self):
        self._订阅: Dict[str, List[Callable]] = {}
        self._事件队列: List[dict] = []

    def 订阅(self, 事件类型: str, 回调: Callable):
        self._订阅.setdefault(事件类型, []).append(回调)

    def 取消订阅(self, 事件类型: str, 回调: Callable):
        if 事件类型 in self._订阅:
            self._订阅[事件类型] = [cb for cb in self._订阅[事件类型] if cb != 回调]

    def 发布事件(self, 事件类型: str, 数据: Any):
        self._事件队列.append({"类型": 事件类型, "数据": 数据, "时间": time.time()})
        for 回调 in self._订阅.get(事件类型, []):
            try:
                回调(数据)
            except Exception:
                pass

    def 处理队列(self) -> int:
        """处理事件队列"""
        n = len(self._事件队列)
        self._事件队列.clear()
        return n


class HKC异步SDK:
    """
    HKC异步SDK
    
    高并发场景使用:
      - 异步请求处理
      - 并行查询
      - 流式事件订阅
      - 连接池管理
    """

    def __init__(self, 最大连接: int = 10):
        self._池 = 连接池(最大连接)
        self._事件 = 事件订阅器()
        self._任务: Dict[str, 异步任务] = {}
        self._结果缓存: Dict[str, Any] = {}

    @property
    def 连接池_(self): return self._池
    @property
    def 事件系统(self): return self._事件

    def 提交异步任务(self, 类型: str, 参数: dict = None, 回调: Callable = None) -> 异步任务:
        """提交异步任务"""
        # H-21: os.urandom替代time.time_ns()
        import os as _os
        tid = hashlib.sha256(f"{类型}:{_os.urandom(16).hex()}".encode()).hexdigest()[:12]
        任务 = 异步任务(任务ID=tid, 类型=类型, 回调=回调)
        self._任务[tid] = 任务
        # 模拟异步执行
        任务.状态 = "running"
        return 任务

    def 并行查询余额(self, 地址列表: List[str]) -> Dict[str, float]:
        """并行查询多个地址余额"""
        结果 = {}
        for addr in 地址列表:
            # 模拟并行查询
            conn = self._池.获取()
            if conn:
                结果[addr] = random.uniform(0, 10000)
                self._池.释放(conn)
            else:
                结果[addr] = 0.0
        return 结果

    def 订阅新区块(self, 回调: Callable):
        """订阅新区块事件"""
        self._事件.订阅("new_block", 回调)

    def 订阅交易确认(self, 回调: Callable):
        """订阅交易确认事件"""
        self._事件.订阅("tx_confirmed", 回调)

    def 模拟事件(self):
        """模拟事件(测试用)"""
        self._事件.发布事件("new_block", {"高度": 12345, "哈希": "0xabc"})
        self._事件.发布事件("tx_confirmed", {"哈希": "0xdef", "确认数": 3})

    def 状态(self) -> dict:
        return {
            "连接池": self._池.状态(),
            "任务": len(self._任务),
            "缓存": len(self._结果缓存),
        }


if __name__ == "__main__":
    print("  HKC 异步SDK Demo")
    sdk = HKC异步SDK(5)
    # 并行查询
    余额 = sdk.并行查询余额(["addr_1", "addr_2", "addr_3"])
    print(f"  并行余额: {余额}")
    # 事件订阅
    def on_block(数据):
        print(f"  📦 新区块: {数据}")
    sdk.订阅新区块(on_block)
    sdk.模拟事件()
    print(f"  {sdk.状态()}")
