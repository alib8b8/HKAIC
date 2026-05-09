"""
HKC 事件预言机 (event_oracle.py)
================================
链外事件数据：监管、链事件、市场事件的验证和触发。
纯Python标准库，零外部依赖。
中文代码风格。
"""

import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
from collections import defaultdict


class 事件类型(Enum):
    """事件类型"""
    监管政策 = "regulatory"
    链上升级 = "chain_upgrade"
    链上分叉 = "chain_fork"
    链上攻击 = "chain_attack"
    交易所故障 = "exchange_outage"
    大额异动 = "large_movement"
    市场异常 = "market_anomaly"
    黑天鹅 = "black_swan"
    其他 = "other"


class 事件严重级别(Enum):
    """事件严重级别"""
    信息 = "info"
    注意 = "notice"
    警告 = "warning"
    严重 = "severe"
    紧急 = "emergency"


class 事件状态(Enum):
    """事件状态"""
    待验证 = "pending"
    已确认 = "confirmed"
    已处理 = "processed"
    已过期 = "expired"
    虚假 = "false"


@dataclass
class 事件数据:
    """事件数据"""
    事件ID: str = ""
    事件类型: 事件类型 = 事件类型.其他
    严重级别: 事件严重级别 = 事件严重级别.信息
    状态: 事件状态 = 事件状态.待验证
    标题: str = ""
    描述: str = ""
    来源: List[str] = field(default_factory=list)           # 来源URL列表
    影响代币: List[str] = field(default_factory=list)        # 影响的代币
    影响模块: List[str] = field(default_factory=list)       # 影响的模块
    确认节点数: int = 0                                      # 确认的节点数
    需要确认数: int = 3                                      # 需要确认的节点数
    证据: Dict[str, Any] = field(default_factory=dict)       # 证据数据
    创建时间: float = 0.0
    确认时间: float = 0.0
    过期时间: float = 0.0                                    # 事件过期时间
    处理时间: float = 0.0
    元数据: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.创建时间 == 0:
            self.创建时间 = time.time()
        if not self.事件ID:
            self.事件ID = self._生成ID()

    def _生成ID(self) -> str:
        """生成事件ID"""
        内容 = f"{self.事件类型.value}:{self.标题}:{self.创建时间}"
        return hashlib.sha256(内容.encode()).hexdigest()[:16]

    @property
    def 是否已确认(self) -> bool:
        """是否已确认"""
        return self.状态 == 事件状态.已确认

    @property
    def 是否过期(self) -> bool:
        """是否过期"""
        if self.过期时间 <= 0:
            return False
        return time.time() > self.过期时间

    @property
    def 存活时间(self) -> float:
        """存活时间（秒）"""
        return time.time() - self.创建时间


@dataclass
class 事件预言机配置:
    """事件预言机配置"""
    需要确认数: int = 3                    # 多节点确认阈值
    确认超时秒: float = 300                 # 确认超时时间
    事件保留秒: float = 86400 * 7           # 事件保留时间（7天）
    过期检查间隔: float = 60                 # 过期检查间隔
    最大影响代币数: int = 10                 # 单事件最大影响代币


class 事件预言机:
    """
    HKC 事件预言机
    
    AI原生创新点：
    1. 事件类型覆盖：监管、链事件、市场事件
    2. 多节点确认：事件真实性需多节点验证
    3. 合约触发：订阅特定事件，触发时自动执行
    4. 事件溯源：每个事件有来源URL和时间戳
    5. 智能分类：自动分类和影响评估
    
    事件流：
    1. 事件上报 → 2. 多节点验证 → 3. 确认/拒绝 → 4. 触发订阅者
    """

    def __init__(self, 配置: Optional[事件预言机配置] = None):
        self._配置 = 配置 or 事件预言机配置()
        
        # 事件存储: {事件ID: 事件数据}
        self._事件: Dict[str, 事件数据] = {}
        
        # 事件索引: {事件类型: [事件ID]}
        self._事件索引: Dict[事件类型, List[str]] = defaultdict(list)
        
        # 事件索引: {代币: [事件ID]}
        self._代币索引: Dict[str, List[str]] = defaultdict(list)
        
        # 事件索引: {模块: [事件ID]}
        self._模块索引: Dict[str, List[str]] = defaultdict(list)
        
        # 事件订阅: {事件类型: [回调]}
        self._类型订阅: Dict[事件类型, List[Callable]] = defaultdict(list)
        
        # 事件订阅: {代币: [回调]}
        self._代币订阅: Dict[str, List[Callable]] = defaultdict(list)
        
        # 事件订阅: {模块: [回调]}
        self._模块订阅: Dict[str, List[Callable]] = defaultdict(list)
        
        # 全局订阅: [回调]
        self._全局订阅: List[Callable] = []
        
        # 确认记录: {事件ID: {节点: True}}
        self._确认记录: Dict[str, Dict[str, bool]] = defaultdict(dict)
        
        # 统计数据
        self._上报事件数: int = 0
        self._确认事件数: int = 0
        self._触发回调数: int = 0

    # ==================== 事件上报 ====================

    def 上报事件(
        self,
        事件类型: 事件类型,
        标题: str,
        描述: str,
        来源: Optional[List[str]] = None,
        影响代币: Optional[List[str]] = None,
        影响模块: Optional[List[str]] = None,
        严重级别: 事件严重级别 = 事件严重级别.信息,
        过期时间: float = 0,
        元数据: Optional[Dict] = None,
        上报节点: str = "default"
    ) -> str:
        """
        上报事件
        
        参数:
            事件类型: 事件类型
            标题: 事件标题
            描述: 事件描述
            来源: 来源URL列表
            影响代币: 影响的代币列表
            影响模块: 影响的模块列表
            严重级别: 严重级别
            过期时间: 过期时间戳
            元数据: 额外元数据
            上报节点: 上报的节点ID
            
        返回:
            事件ID
        """
        self._上报事件数 += 1
        
        # 限制影响代币数
        影响代币 = 影响代币 or []
        if len(影响代币) > self._配置.最大影响代币数:
            影响代币 = 影响代币[:self._配置.最大影响代币数]
        
        # 创建事件
        事件 = 事件数据(
            事件类型=事件类型,
            严重级别=严重级别,
            状态=事件状态.待验证,
            标题=标题,
            描述=描述,
            来源=来源 or [],
            影响代币=影响代币,
            影响模块=影响模块 or [],
            需要确认数=self._配置.需要确认数,
            过期时间=过期时间,
            元数据=元数据 or {}
        )
        
        # 存储事件
        self._事件[事件.事件ID] = 事件
        
        # 更新索引
        self._事件索引[事件类型].append(事件.事件ID)
        for 代币 in 影响代币:
            self._代币索引[代币].append(事件.事件ID)
        for 模块 in (影响模块 or []):
            self._模块索引[模块].append(事件.事件ID)
        
        # 记录确认
        self._确认记录[事件.事件ID][上报节点] = True
        事件.确认节点数 = 1
        
        # 检查是否需要确认
        self._检查确认(事件)
        
        return 事件.事件ID

    def 确认事件(
        self,
        事件ID: str,
        节点: str,
        证据: Optional[Dict] = None
    ) -> bool:
        """
        确认事件
        
        参数:
            事件ID: 事件ID
            节点: 确认的节点
            证据: 额外证据
            
        返回:
            是否确认成功
        """
        if 事件ID not in self._事件:
            return False
        
        事件 = self._事件[事件ID]
        
        # 检查是否已处理
        if 事件.状态 in [事件状态.已处理, 事件状态.已过期, 事件状态.虚假]:
            return False
        
        # 记录确认
        if 节点 in self._确认记录[事件ID]:
            return False  # 已确认
        
        self._确认记录[事件ID][节点] = True
        事件.确认节点数 = len(self._确认记录[事件ID])
        
        # 添加证据
        if 证据:
            事件.证据.update(证据)
        
        # 检查确认
        return self._检查确认(事件)

    def 拒绝事件(
        self,
        事件ID: str,
        节点: str,
        原因: str
    ) -> bool:
        """
        拒绝事件
        
        参数:
            事件ID: 事件ID
            节点: 拒绝的节点
            原因: 拒绝原因
            
        返回:
            是否拒绝成功
        """
        if 事件ID not in self._事件:
            return False
        
        事件 = self._事件[事件ID]
        
        # 检查是否已处理
        if 事件.状态 in [事件状态.已处理, 事件状态.已确认]:
            return False
        
        # 标记为虚假
        事件.状态 = 事件状态.虚假
        事件.描述 = f"{事件.描述}\n\n[拒绝原因 by {节点}]: {原因}"
        事件.处理时间 = time.time()
        
        return True

    def _检查确认(self, 事件: 事件数据) -> bool:
        """检查是否满足确认条件"""
        if 事件.确认节点数 >= 事件.需要确认数:
            事件.状态 = 事件状态.已确认
            事件.确认时间 = time.time()
            self._确认事件数 += 1
            
            # 触发订阅者
            self._触发事件(事件)
            
            return True
        return False

    # ==================== 事件查询 ====================

    def 获取事件(
        self,
        事件ID: str
    ) -> Optional[事件数据]:
        """获取事件"""
        return self._事件.get(事件ID)

    def 查询事件(
        self,
        事件类型: Optional[事件类型] = None,
        严重级别: Optional[事件严重级别] = None,
        状态: Optional[事件状态] = None,
        影响代币: Optional[str] = None,
        影响模块: Optional[str] = None,
        时间范围: Optional[Tuple[float, float]] = None,
        数量: int = 20
    ) -> List[事件数据]:
        """
        查询事件
        
        参数:
            事件类型: 事件类型过滤
            严重级别: 严重级别过滤
            状态: 状态过滤
            影响代币: 影响代币过滤
            影响模块: 影响模块过滤
            时间范围: (开始时间, 结束时间)
            数量: 返回数量
            
        返回:
            事件列表
        """
        结果 = list(self._事件.values())
        
        # 按时间过滤
        if 时间范围:
            开始时间, 结束时间 = 时间范围
            结果 = [
                e for e in 结果
                if 开始时间 <= e.创建时间 <= 结束时间
            ]
        
        # 按类型过滤
        if 事件类型:
            结果 = [e for e in 结果 if e.事件类型 == 事件类型]
        
        # 按严重级别过滤
        if 严重级别:
            结果 = [e for e in 结果 if e.严重级别 == 严重级别]
        
        # 按状态过滤
        if 状态:
            结果 = [e for e in 结果 if e.状态 == 状态]
        
        # 按代币过滤
        if 影响代币:
            结果 = [e for e in 结果 if 影响代币 in e.影响代币]
        
        # 按模块过滤
        if 影响模块:
            结果 = [e for e in 结果 if 影响模块 in e.影响模块]
        
        # 按时间排序
        结果.sort(key=lambda x: x.创建时间, reverse=True)
        
        return 结果[:数量]

    def 获取待确认事件(self) -> List[事件数据]:
        """获取待确认事件"""
        return [
            e for e in self._事件.values()
            if e.状态 == 事件状态.待验证
        ]

    # ==================== 订阅机制 ====================

    def 订阅类型(
        self,
        事件类型: 事件类型,
        回调: Callable[[事件数据], None]
    ) -> None:
        """订阅事件类型"""
        self._类型订阅[事件类型].append(回调)

    def 订阅代币(
        self,
        代币: str,
        回调: Callable[[事件数据], None]
    ) -> None:
        """订阅代币相关事件"""
        self._代币订阅[代币].append(回调)

    def 订阅模块(
        self,
        模块: str,
        回调: Callable[[事件数据], None]
    ) -> None:
        """订阅模块相关事件"""
        self._模块订阅[模块].append(回调)

    def 订阅全部(
        self,
        回调: Callable[[事件数据], None]
    ) -> None:
        """订阅所有事件"""
        self._全局订阅.append(回调)

    def 取消订阅(
        self,
        回调: Callable,
        类型: Optional[事件类型] = None,
        代币: Optional[str] = None,
        模块: Optional[str] = None
    ) -> bool:
        """取消订阅"""
        目标列表 = []
        
        if 类型:
            目标列表 = self._类型订阅.get(类型, [])
        elif 代币:
            目标列表 = self._代币订阅.get(代币, [])
        elif 模块:
            目标列表 = self._模块订阅.get(模块, [])
        else:
            目标列表 = self._全局订阅
        
        try:
            目标列表.remove(回调)
            return True
        except ValueError:
            return False

    def _触发事件(self, 事件: 事件数据) -> None:
        """触发事件的订阅回调"""
        # 类型订阅
        for 回调 in self._类型订阅.get(事件.事件类型, []):
            try:
                回调(事件)
                self._触发回调数 += 1
            except Exception:
                pass
        
        # 代币订阅
        for 代币 in 事件.影响代币:
            for 回调 in self._代币订阅.get(代币, []):
                try:
                    回调(事件)
                    self._触发回调数 += 1
                except Exception:
                    pass
        
        # 模块订阅
        for 模块 in 事件.影响模块:
            for 回调 in self._模块订阅.get(模块, []):
                try:
                    回调(事件)
                    self._触发回调数 += 1
                except Exception:
                    pass
        
        # 全局订阅
        for 回调 in self._全局订阅:
            try:
                回调(事件)
                self._触发回调数 += 1
            except Exception:
                pass

    # ==================== 事件处理 ====================

    def 标记已处理(self, 事件ID: str) -> bool:
        """标记事件已处理"""
        事件 = self._事件.get(事件ID)
        if 事件 and 事件.状态 == 事件状态.已确认:
            事件.状态 = 事件状态.已处理
            事件.处理时间 = time.time()
            return True
        return False

    def 检查过期事件(self) -> int:
        """
        检查并处理过期事件
        
        返回:
            处理的事件数
        """
        处理数 = 0
        当前时间 = time.time()
        
        for 事件 in self._事件.values():
            if 事件.状态 in [事件状态.已处理, 事件状态.已过期, 事件状态.虚假]:
                continue
            
            # 检查过期时间
            if 事件.过期时间 > 0 and 当前时间 > 事件.过期时间:
                事件.状态 = 事件状态.已过期
                事件.处理时间 = 当前时间
                处理数 += 1
        
        return 处理数

    # ==================== 工具方法 ====================

    def 获取事件统计(self) -> Dict:
        """获取事件统计"""
        按类型统计: Dict[str, int] = defaultdict(int)
        按级别统计: Dict[str, int] = defaultdict(int)
        按状态统计: Dict[str, int] = defaultdict(int)
        
        for 事件 in self._事件.values():
            按类型统计[事件.事件类型.value] += 1
            按级别统计[事件.严重级别.value] += 1
            按状态统计[事件.状态.value] += 1
        
        return {
            "总事件数": len(self._事件),
            "上报事件数": self._上报事件数,
            "确认事件数": self._确认事件数,
            "触发回调数": self._触发回调数,
            "待确认事件数": 按状态统计.get("pending", 0),
            "按类型统计": dict(按类型统计),
            "按级别统计": dict(按级别统计),
            "按状态统计": dict(按状态统计),
        }

    def 清理过期数据(self, 最大保留秒: float = 0) -> int:
        """
        清理过期数据
        
        参数:
            最大保留秒: 最大保留时间，默认使用配置
            
        返回:
            清理的事件数
        """
        if 最大保留秒 <= 0:
            最大保留秒 = self._配置.事件保留秒
        
        当前时间 = time.time()
        清理数 = 0
        需删除ID = []
        
        for 事件ID, 事件 in self._事件.items():
            存活时间 = 当前时间 - 事件.创建时间
            if 存活时间 > 最大保留秒:
                需删除ID.append(事件ID)
        
        for 事件ID in 需删除ID:
            事件 = self._事件[事件ID]
            
            # 从索引中移除
            if 事件.事件类型 in self._事件索引:
                try:
                    self._事件索引[事件.事件类型].remove(事件ID)
                except ValueError:
                    pass
            
            for 代币 in 事件.影响代币:
                if 代币 in self._代币索引:
                    try:
                        self._代币索引[代币].remove(事件ID)
                    except ValueError:
                        pass
            
            for 模块 in 事件.影响模块:
                if 模块 in self._模块索引:
                    try:
                        self._模块索引[模块].remove(事件ID)
                    except ValueError:
                        pass
            
            # 删除事件
            del self._事件[事件ID]
            清理数 += 1
        
        return 清理数

    # ==================== 预设事件类型 ====================

    def 上报监管政策(
        self,
        标题: str,
        描述: str,
        来源: List[str],
        严重级别: 事件严重级别 = 事件严重级别.警告,
        影响代币: Optional[List[str]] = None,
        影响模块: Optional[List[str]] = None
    ) -> str:
        """快速上报监管政策事件"""
        return self.上报事件(
            事件类型=事件类型.监管政策,
            标题=标题,
            描述=描述,
            来源=来源,
            影响代币=影响代币,
            影响模块=影响模块,
            严重级别=严重级别
        )

    def 上报链上攻击(
        self,
        标题: str,
        描述: str,
        来源: List[str],
        严重级别: 事件严重级别 = 事件严重级别.紧急,
        影响代币: Optional[List[str]] = None,
        影响模块: Optional[List[str]] = None
    ) -> str:
        """快速上报链上攻击事件"""
        return self.上报事件(
            事件类型=事件类型.链上攻击,
            标题=标题,
            描述=描述,
            来源=来源,
            影响代币=影响代币,
            影响模块=影响模块,
            严重级别=严重级别
        )

    def 上报市场异常(
        self,
        标题: str,
        描述: str,
        代币: str,
        价格变化: float,
        严重级别: 事件严重级别 = 事件严重级别.警告
    ) -> str:
        """快速上报市场异常事件"""
        return self.上报事件(
            事件类型=事件类型.市场异常,
            标题=标题,
            描述=f"{描述}\n价格变化: {价格变化:.2%}",
            影响代币=[代币],
            严重级别=严重级别,
            元数据={"价格变化": 价格变化}
        )
