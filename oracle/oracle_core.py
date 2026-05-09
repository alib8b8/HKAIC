"""
HKC AI原生预言机核心 (oracle_core.py)
=====================================
预言机核心数据类型、数据源注册、订阅机制、历史存储。
纯Python标准库，零外部依赖。
中文代码风格。
"""

import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum


# HKAIC精度常量
HKAIC_PRECISION = 16
HKAIC_UNIT = 10 ** HKAIC_PRECISION


class 数据类型(Enum):
    """预言机数据类型枚举"""
    价格 = "price"
    汇率 = "exchange_rate"
    波动率 = "volatility"
    TVL = "tvl"
    交易量 = "volume"
    链外事件 = "external_event"


class 数据源类型(Enum):
    """数据源类型"""
    DEX链上 = "dex_onchain"
    跨链桥 = "cross_chain"
    外部API = "external_api"
    链上推导 = "onchain_derived"


class 更新周期(Enum):
    """数据拉取周期"""
    实时 = "realtime"      # 毫秒级
    每区块 = "per_block"   # 按区块
    每分钟 = "per_minute"
    每小时 = "per_hour"


@dataclass
class 数据点:
    """预言机数据点基类"""
    数据类型: 数据类型 = 数据类型.价格
    数据源: str = ""
    数据源类型: 数据源类型 = 数据源类型.DEX链上
    数值: float = 0.0
    置信度: float = 1.0
    时间戳: float = 0.0
    区块高度: int = 0
    版本号: int = 0
    元数据: Dict[str, Any] = field(default_factory=dict)
    是否有效: bool = True

    def __post_init__(self):
        if self.时间戳 == 0:
            self.时间戳 = time.time()
        if self.版本号 == 0:
            self.版本号 = int(self.时间戳 * 1000)


@dataclass
class 价格数据点(数据点):
    """价格数据点"""
    交易对: str = ""           # e.g., "HKAIC/USDT"
    买入价: float = 0.0
    卖出价: float = 0.0
    买卖价差: float = 0.0

    def __post_init__(self):
        super().__post_init__()
        self.数据类型 = 数据类型.价格
        if self.数值 == 0 and (self.买入价 > 0 or self.卖出价 > 0):
            self.数值 = (self.买入价 + self.卖出价) / 2
        if self.买入价 > 0 and self.卖出价 > 0:
            self.买卖价差 = abs(self.卖出价 - self.买入价) / ((self.买入价 + self.卖出价) / 2)


@dataclass
class 聚合结果:
    """聚合后的数据结果"""
    键: str = ""                    # e.g., "HKAIC/USDT"
    数据类型: 数据类型 = 数据类型.价格
    聚合值: float = 0.0
    中位数: float = 0.0
    置信区间下限: float = 0.0
    置信区间上限: float = 0.0
    置信度: float = 1.0
    数据源数量: int = 0
    最大偏离度: float = 0.0
    加权权重: float = 0.0
    时间戳: float = 0.0
    区块高度: int = 0
    版本号: int = 0
    是否延迟确认: bool = False
    延迟确认区块数: int = 0

    def __post_init__(self):
        if self.时间戳 == 0:
            self.时间戳 = time.time()
        if self.版本号 == 0:
            self.版本号 = int(self.时间戳 * 1000)

    def 转为字典(self) -> Dict:
        """转换为字典格式"""
        return {
            "键": self.键,
            "数据类型": self.数据类型.value,
            "聚合值": self.聚合值,
            "中位数": self.中位数,
            "置信区间": (self.置信区间下限, self.置信区间上限),
            "置信度": self.置信度,
            "数据源数量": self.数据源数量,
            "最大偏离度": self.最大偏离度,
            "时间戳": self.时间戳,
            "区块高度": self.区块高度,
            "版本号": self.版本号,
            "延迟确认": self.是否延迟确认,
        }


class 数据订阅者:
    """数据订阅者回调"""
    def __init__(self, 回调: Callable, 过滤器: Optional[Callable] = None):
        self.回调 = 回调
        self.过滤器 = 过滤器  # 返回True表示订阅该数据


@dataclass
class 订阅记录:
    """订阅记录"""
    订阅ID: str = ""
    订阅者: str = ""               # 合约地址或模块名
    数据键: str = ""                # e.g., "HKAIC/USDT"
    数据类型: 数据类型 = 数据类型.价格
    回调函数: Any = None            # 实际是Callable，但避免序列化问题
    创建时间: float = 0.0
    活动状态: bool = True
    优先级: int = 0                 # 0-100, 越高越优先

    def __post_init__(self):
        if self.创建时间 == 0:
            self.创建时间 = time.time()
        if not self.订阅ID:
            self.订阅ID = hashlib.sha256(
                f"sub:{self.订阅者}:{self.数据键}:{time.time()}".encode()
            ).hexdigest()[:16]


class 预言机核心:
    """
    HKC AI原生预言机核心
    
    职责：
    1. 数据类型管理
    2. 数据源注册
    3. 订阅机制
    4. 历史数据存储
    5. 数据版本控制
    
    特性：
    - 事件驱动的数据推送
    - 版本化数据历史
    - 多数据类型支持
    """

    def __init__(self):
        # 数据源注册: {数据源名称: 元数据}
        self._数据源注册: Dict[str, Dict] = {}
        
        # 活跃数据: {数据键: 数据点列表}
        self._活跃数据: Dict[str, List[数据点]] = {}
        
        # 聚合结果: {数据键: 聚合结果}
        self._聚合结果: Dict[str, 聚合结果] = {}
        
        # 历史数据: {数据键: [聚合结果]}
        self._历史数据: Dict[str, List[聚合结果]] = {}
        
        # 订阅者: {数据键: [订阅记录]}
        self._订阅者: Dict[str, List[订阅记录]] = {}
        
        # 区块信息
        self._当前区块: int = 0
        self._区块时间戳: Dict[int, float] = {}
        
        # 统计数据
        self._数据更新次数: int = 0
        self._订阅触发次数: int = 0
        
        # 最大历史保留
        self._最大历史条数: int = 1000
        self._最大活跃数据条数: int = 100
        
        # 全局版本号
        self._全局版本号: int = 0

    # ==================== 数据源管理 ====================

    def 注册数据源(
        self,
        名称: str,
        源类型: 数据源类型,
        元数据: Optional[Dict] = None
    ) -> bool:
        """
        注册新的数据源
        
        参数:
            名称: 数据源名称
            源类型: 数据源类型
            元数据: 额外配置信息
            
        返回:
            是否注册成功
        """
        if 名称 in self._数据源注册:
            # 更新已存在的数据源
            self._数据源注册[名称]["源类型"] = 源类型
            self._数据源注册[名称]["元数据"] = 元数据 or {}
            self._数据源注册[名称]["更新时间"] = time.time()
            return True
        
        self._数据源注册[名称] = {
            "名称": 名称,
            "源类型": 源类型,
            "元数据": 元数据 or {},
            "注册时间": time.time(),
            "更新时间": time.time(),
            "可用状态": True,
            "响应时间": 0.0,
            "更新次数": 0,
            "错误次数": 0,
        }
        return True

    def 注销数据源(self, 名称: str) -> bool:
        """注销数据源"""
        if 名称 in self._数据源注册:
            del self._数据源注册[名称]
            return True
        return False

    def 获取数据源列表(self) -> List[Dict]:
        """获取所有已注册数据源"""
        return list(self._数据源注册.values())

    def 更新数据源状态(self, 名称: str, 可用: bool, 响应时间: float = 0) -> bool:
        """更新数据源状态"""
        if 名称 not in self._数据源注册:
            return False
        self._数据源注册[名称]["可用状态"] = 可用
        if 响应时间 > 0:
            self._数据源注册[名称]["响应时间"] = 响应时间
        self._数据源注册[名称]["更新时间"] = time.time()
        return True

    # ==================== 数据操作 ====================

    def 添加数据点(
        self,
        数据点: 数据点,
        数据键: Optional[str] = None
    ) -> bool:
        """
        添加新的数据点
        
        参数:
            数据点: 数据点实例
            数据键: 数据键，默认为数据点的交易对或键
            
        返回:
            是否添加成功
        """
        # 确定数据键
        if 数据键 is None:
            if isinstance(数据点, 价格数据点):
                数据键 = 数据点.交易对
            else:
                数据键 = f"{数据点.数据类型.value}"

        # 更新区块信息
        if 数据点.区块高度 > self._当前区块:
            self._当前区块 = 数据点.区块高度
        self._区块时间戳[数据点.区块高度] = 数据点.时间戳

        # 递增全局版本号
        self._全局版本号 += 1
        数据点.版本号 = self._全局版本号

        # 添加到活跃数据
        if 数据键 not in self._活跃数据:
            self._活跃数据[数据键] = []
        self._活跃数据[数据键].append(数据点)

        # 限制活跃数据条数
        if len(self._活跃数据[数据键]) > self._最大活跃数据条数:
            self._活跃数据[数据键] = self._活跃数据[数据键][-self._最大活跃数据条数:]

        # 更新统计数据
        self._数据更新次数 += 1

        # 更新数据源的更新次数
        if 数据点.数据源 in self._数据源注册:
            self._数据源注册[数据点.数据源]["更新次数"] += 1

        return True

    def 获取活跃数据(
        self,
        数据键: str,
        最大年龄: float = 0
    ) -> List[数据点]:
        """
        获取活跃数据
        
        参数:
            数据键: 数据键
            最大年龄: 最大数据年龄（秒），0表示不限制
            
        返回:
            数据点列表
        """
        if 数据键 not in self._活跃数据:
            return []
        
        当前时间 = time.time()
        数据列表 = self._活跃数据[数据键]
        
        if 最大年龄 > 0:
            数据列表 = [
                d for d in 数据列表
                if 当前时间 - d.时间戳 <= 最大年龄
            ]
        
        return 数据列表

    def 设置聚合结果(self, 结果: 聚合结果) -> None:
        """设置聚合结果"""
        self._聚合结果[结果.键] = 结果
        
        # 添加到历史
        if 结果.键 not in self._历史数据:
            self._历史数据[结果.键] = []
        self._历史数据[结果.键].append(结果)
        
        # 限制历史条数
        if len(self._历史数据[结果.键]) > self._最大历史条数:
            self._历史数据[结果.键] = self._历史数据[结果.键][-self._最大历史条数:]
        
        # 触发订阅者
        self._触发订阅者(结果)

    def 获取聚合结果(
        self,
        数据键: str,
        最大年龄: float = 0
    ) -> Optional[聚合结果]:
        """
        获取聚合结果
        
        参数:
            数据键: 数据键
            最大年龄: 最大数据年龄（秒），0表示不限制
            
        返回:
            聚合结果或None
        """
        结果 = self._聚合结果.get(数据键)
        if 结果 is None:
            return None
        
        if 最大年龄 > 0:
            当前时间 = time.time()
            if 当前时间 - 结果.时间戳 > 最大年龄:
                return None
        
        return 结果

    def 获取历史数据(
        self,
        数据键: str,
        数量: int = 10,
        最大年龄: float = 0
    ) -> List[聚合结果]:
        """
        获取历史数据
        
        参数:
            数据键: 数据键
            数量: 返回条数
            最大年龄: 最大数据年龄（秒），0表示不限制
            
        返回:
            历史数据列表
        """
        if 数据键 not in self._历史数据:
            return []
        
        历史 = self._历史数据[数据键]
        
        if 最大年龄 > 0:
            当前时间 = time.time()
            历史 = [
                h for h in 历史
                if 当前时间 - h.时间戳 <= 最大年龄
            ]
        
        return 历史[-数量:]

    # ==================== 订阅机制 ====================

    def 订阅数据(
        self,
        订阅者: str,
        数据键: str,
        数据类型: 数据类型 = 数据类型.价格,
        优先级: int = 50
    ) -> str:
        """
        订阅数据更新
        
        参数:
            订阅者: 订阅者标识（合约地址或模块名）
            数据键: 数据键
            数据类型: 数据类型
            优先级: 优先级 0-100
            
        返回:
            订阅ID
        """
        订阅 = 订阅记录(
            订阅者=订阅者,
            数据键=数据键,
            数据类型=数据类型,
            优先级=优先级
        )
        
        if 数据键 not in self._订阅者:
            self._订阅者[数据键] = []
        self._订阅者[数据键].append(订阅)
        
        # 按优先级排序
        self._订阅者[数据键].sort(key=lambda x: x.优先级, reverse=True)
        
        return 订阅.订阅ID

    def 取消订阅(self, 订阅ID: str) -> bool:
        """取消订阅"""
        for 数据键, 订阅列表 in self._订阅者.items():
            for i, 订阅 in enumerate(订阅列表):
                if 订阅.订阅ID == 订阅ID:
                    self._订阅者[数据键].pop(i)
                    订阅.活动状态 = False
                    return True
        return False

    def 获取订阅列表(self, 数据键: str) -> List[订阅记录]:
        """获取数据键的订阅列表"""
        return self._订阅者.get(数据键, [])

    def _触发订阅者(self, 结果: 聚合结果) -> None:
        """触发订阅者回调"""
        数据键 = 结果.键
        if 数据键 not in self._订阅者:
            return
        
        for 订阅 in self._订阅者[数据键]:
            if not 订阅.活动状态:
                continue
            try:
                # 调用回调函数
                if callable(订阅.回调函数):
                    订阅.回调函数(结果)
                self._订阅触发次数 += 1
            except Exception:
                # 静默处理回调异常
                pass

    # ==================== 区块管理 ====================

    def 设置区块高度(self, 区块高度: int, 时间戳: float = 0) -> None:
        """设置当前区块高度"""
        self._当前区块 = 区块高度
        if 时间戳 == 0:
            时间戳 = time.time()
        self._区块时间戳[区块高度] = 时间戳

    def 获取区块时间戳(self, 区块高度: int) -> Optional[float]:
        """获取区块时间戳"""
        return self._区块时间戳.get(区块高度)

    @property
    def 当前区块高度(self) -> int:
        """获取当前区块高度"""
        return self._当前区块

    # ==================== 工具方法 ====================

    def 计算数据新鲜度(self, 数据键: str) -> float:
        """
        计算数据新鲜度（0-1）
        
        0 = 完全过期
        1 = 刚刚更新
        """
        结果 = self._聚合结果.get(数据键)
        if 结果 is None:
            return 0.0
        
        当前时间 = time.time()
        年龄 = 当前时间 - 结果.时间戳
        
        # 假设60秒为完全过期阈值
        新鲜度 = max(0, 1 - 年龄 / 60)
        return 新鲜度

    def 获取预言机统计(self) -> Dict:
        """获取预言机统计信息"""
        return {
            "注册数据源数": len(self._数据源注册),
            "跟踪数据键数": len(self._活跃数据),
            "聚合结果数": len(self._聚合结果),
            "总订阅数": sum(len(s) for s in self._订阅者.values()),
            "历史数据条数": sum(len(h) for h in self._历史数据.values()),
            "数据更新次数": self._数据更新次数,
            "订阅触发次数": self._订阅触发次数,
            "当前区块": self._当前区块,
            "全局版本号": self._全局版本号,
        }

    def 清理过期数据(self, 最大年龄秒: float = 3600) -> int:
        """
        清理过期数据
        
        返回清理的数据条数
        """
        当前时间 = time.time()
        清理数 = 0
        
        # 清理活跃数据
        for 数据键 in list(self._活跃数据.keys()):
            原始长度 = len(self._活跃数据[数据键])
            self._活跃数据[数据键] = [
                d for d in self._活跃数据[数据键]
                if 当前时间 - d.时间戳 <= 最大年龄秒
            ]
            清理数 += 原始长度 - len(self._活跃数据[数据键])
            
            # 如果为空，删除键
            if not self._活跃数据[数据键]:
                del self._活跃数据[数据键]
        
        return 清理数
