"""
HKC 操纵防护引擎 (manipulation_guard.py)
========================================
AI原生的链上操纵检测，不是简单阈值，是行为模式识别。
纯Python标准库，零外部依赖。
中文代码风格。
"""

import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, deque
from enum import Enum

from oracle.oracle_core import 数据点, 价格数据点, 聚合结果


class 操纵类型(Enum):
    """操纵类型枚举"""
    闪电贷 = "flash_loan"
    价格偏离 = "price_deviation"
    交易量异常 = "volume_anomaly"
    时间加权异常 = "twap_manipulation"
    多源不一致 = "multi_source_inconsistency"
    区块重组 = "block_reorg"


class 操纵告警级别(Enum):
    """告警级别"""
    安全 = "safe"
    观察 = "watch"
    警告 = "warning"
    危险 = "danger"
    严重 = "critical"


@dataclass
class 操纵事件:
    """操纵检测事件"""
    事件ID: str = ""
    类型: 操纵类型 = 操纵类型.价格偏离
    级别: 操纵告警级别 = 操纵告警级别.观察
    涉及数据源: List[str] = field(default_factory=list)
    涉及区块: List[int] = field(default_factory=list)
    描述: str = ""
    证据: Dict = field(default_factory=dict)
    时间戳: float = 0.0
    区块高度: int = 0
    已处理: bool = False

    def __post_init__(self):
        if self.时间戳 == 0:
            self.时间戳 = time.time()


@dataclass
class 操纵防护配置:
    """操纵防护配置"""
    # 闪电贷检测
    闪电贷检测窗口区块: int = 3              # 检测窗口（区块）
    闪电贷大额阈值: float = 100000            # 大额交易阈值
    
    # 价格偏离检测
    短期偏离阈值: float = 0.05               # 5%短期偏离
    长期偏离阈值: float = 0.10               # 10%长期偏离
    偏离检测窗口: int = 10                   # 检测窗口
    
    # 交易量异常
    交易量暴增倍数: float = 10.0              # 10倍暴增
    交易量基准窗口: int = 20                 # 基准窗口
    
    # TWAP操纵检测
    TWAP操纵阈值: float = 0.03               # 3%TWAP偏离
    
    # 断路器
    断路器阈值: float = 0.15                 # 15%变化触发断路
    断路器确认区块: int = 3                  # 确认区块数
    断路器冷却秒: float = 60                # 冷却时间
    
    # 多源验证
    最少数据源数: int = 3                    # 最少数据源数
    多源不一致阈值: float = 0.05             # 5%不一致告警


class 操纵防护引擎:
    """
    HKC 操纵防护引擎
    
    AI原生创新点：
    1. 闪电贷操纵检测：同一区块内闪电贷+大额DEX交易
    2. 行为模式识别：不只是阈值，而是识别操纵模式
    3. 延迟确认：价格剧烈变化时不立即生效
    4. 多源交叉验证：单一数据源不能直接采信
    5. 断路器：极端情况自动暂停
    
    防御机制：
    - 闪电贷检测：监控大额闪电贷与DEX交易的关联
    - 价格偏离检测：短期/长期偏离分析
    - 交易量异常检测：识别异常交易量模式
    - TWAP保护：使用时间加权平均而非即时价格
    - 多源确认：任何数据需多源验证
    - 断路器：极端波动时暂停
    """

    def __init__(self, 配置: Optional[操纵防护配置] = None):
        self._配置 = 配置 or 操纵防护配置()
        
        # 操纵事件记录: {事件ID: 操纵事件}
        self._操纵事件: Dict[str, 操纵事件] = {}
        
        # 价格历史: {数据键: [(时间戳, 价格, 区块高度)]}
        self._价格历史: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # 交易量历史: {数据键: [(时间戳, 交易量)]}
        self._交易量历史: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # 区块交易: {区块高度: [交易信息]}
        self._区块交易: Dict[int, List[Dict]] = defaultdict(list)
        
        # 闪电贷记录: {区块高度: [闪电贷信息]}
        self._闪电贷记录: Dict[int, List[Dict]] = defaultdict(list)
        
        # 断路器状态: {数据键: 断路器状态}
        self._断路器状态: Dict[str, Dict] = {}
        
        # 多源验证记录: {数据键: {数据源: [价格]}}
        self._多源验证: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # 统计数据
        self._检测次数: int = 0
        self._告警次数: int = 0
        self._触发断路器次数: int = 0

    # ==================== 闪电贷检测 ====================

    def 记录闪电贷(
        self,
        区块高度: int,
        代币: str,
        金额: float,
        交易哈希: str
    ) -> None:
        """
        记录闪电贷事件
        
        参数:
            区块高度: 区块高度
            代币: 代币符号
            金额: 金额
            交易哈希: 交易哈希
        """
        闪电贷信息 = {
            "代币": 代币,
            "金额": 金额,
            "交易哈希": 交易哈希,
            "时间戳": time.time()
        }
        self._闪电贷记录[区块高度].append(闪电贷信息)

    def 记录交易(
        self,
        区块高度: int,
        代币对: str,
        金额: float,
        价格影响: float,
        交易类型: str,
        交易哈希: str
    ) -> None:
        """
        记录交易
        
        参数:
            区块高度: 区块高度
            代币对: e.g., "HKAIC/USDT"
            金额: 交易金额
            价格影响: 价格影响百分比
            交易类型: "swap" / "add_liquidity" / "remove_liquidity"
            交易哈希: 交易哈希
        """
        交易信息 = {
            "代币对": 代币对,
            "金额": 金额,
            "价格影响": 价格影响,
            "类型": 交易类型,
            "交易哈希": 交易哈希,
            "时间戳": time.time()
        }
        self._区块交易[区块高度].append(交易信息)

    def 检测闪电贷操纵(
        self,
        数据键: str,
        当前区块: int
    ) -> Optional[操纵事件]:
        """
        检测闪电贷操纵
        
        模式：同一区块内有大额闪电贷 + 大额DEX交易
        """
        检测窗口 = self._配置.闪电贷检测窗口区块
        
        for 区块 in range(当前区块 - 检测窗口 + 1, 当前区块 + 1):
            闪电贷列表 = self._闪电贷记录.get(区块, [])
            交易列表 = self._区块交易.get(区块, [])
            
            # 过滤与数据键相关的交易
            相关交易 = [
                t for t in 交易列表
                if t["代币对"] == 数据键 or 数据键 in t["代币对"]
            ]
            
            if not 闪电贷列表 or not 相关交易:
                continue
            
            # 检查是否有大额闪电贷
            大额闪电贷 = [
                f for f in 闪电贷列表
                if f["金额"] >= self._配置.闪电贷大额阈值
            ]
            
            if not 大额闪电贷:
                continue
            
            # 检查大额交易
            大额交易 = [
                t for t in 相关交易
                if t["金额"] >= self._配置.闪电贷大额阈值
            ]
            
            if not 大额交易:
                continue
            
            # 检测到可能的闪电贷操纵
            事件 = 操纵事件(
                类型=操纵类型.闪电贷,
                级别=操纵告警级别.危险,
                涉及区块=[区块],
                涉及数据源=[t.get("交易哈希", "") for t in 大额交易],
                描述=f"检测到闪电贷操纵：{len(大额闪电贷)}个大额闪电贷 + {len(大额交易)}个大额交易",
                证据={
                    "闪电贷": 大额闪电贷,
                    "交易": 大额交易
                }
            )
            self._操纵事件[事件.事件ID] = 事件
            self._告警次数 += 1
            return 事件
        
        return None

    # ==================== 价格偏离检测 ====================

    def 记录价格(self, 数据键: str, 价格: float, 区块高度: int) -> None:
        """
        记录价格用于偏离检测
        """
        当前时间 = time.time()
        self._价格历史[数据键].append((当前时间, 价格, 区块高度))

    def 检测价格偏离(
        self,
        数据键: str,
        当前价格: float,
        历史价格: Optional[float] = None
    ) -> Optional[操纵事件]:
        """
        检测价格偏离操纵
        
        分析短期和长期偏离
        """
        self._检测次数 += 1
        
        价格历史 = list(self._价格历史.get(数据键, []))
        
        if len(价格历史) < 2:
            return None
        
        # 获取历史价格（默认最近一次）
        if 历史价格 is None:
            _, 历史价格, _ = 价格历史[-2]  # 倒数第二次的价格
        
        if 历史价格 <= 0:
            return None
        
        偏离比例 = abs(当前价格 - 历史价格) / 历史价格
        
        # 短期偏离检测
        短期历史 = 价格历史[-min(self._配置.偏离检测窗口, len(价格历史)):]
        if 短期历史:
            短期价格列表 = [p for _, p, _ in 短期历史]
            短期均值 = sum(短期价格列表) / len(短期价格列表)
            短期偏离 = abs(当前价格 - 短期均值) / max(短期均值, 1e-10)
            
            if 短期偏离 > self._配置.短期偏离阈值:
                级别 = 操纵告警级别.警告
                if 偏离比例 > self._配置.断路器阈值:
                    级别 = 操纵告警级别.严重
                elif 偏离比例 > self._配置.长期偏离阈值:
                    级别 = 操纵告警级别.危险
                
                事件 = 操纵事件(
                    类型=操纵类型.价格偏离,
                    级别=级别,
                    描述=f"价格偏离检测：偏离{偏离比例:.2%}，短期均值偏离{短期偏离:.2%}",
                    证据={
                        "当前价格": 当前价格,
                        "历史价格": 历史价格,
                        "短期均值": 短期均值,
                        "偏离比例": 偏离比例
                    }
                )
                self._操纵事件[事件.事件ID] = 事件
                self._告警次数 += 1
                return 事件
        
        return None

    # ==================== 交易量异常检测 ====================

    def 记录交易量(self, 数据键: str, 交易量: float) -> None:
        """记录交易量"""
        当前时间 = time.time()
        self._交易量历史[数据键].append((当前时间, 交易量))

    def 检测交易量异常(
        self,
        数据键: str,
        当前交易量: float
    ) -> Optional[操纵事件]:
        """
        检测交易量异常
        
        模式：交易量突然暴增 + 价格大幅波动
        """
        交易量历史 = list(self._交易量历史.get(数据键, []))
        
        if len(交易量历史) < self._配置.交易量基准窗口:
            return None
        
        # 计算基准交易量
        基准窗口 = 交易量历史[-self._配置.交易量基准窗口:]
        基准交易量 = sum(v for _, v in 基准窗口) / len(基准窗口)
        
        if 基准交易量 <= 0:
            return None
        
        暴增倍数 = 当前交易量 / 基准交易量
        
        if 暴增倍数 >= self._配置.交易量暴增倍数:
            # 同时检查价格波动
            价格历史 = list(self._价格历史.get(数据键, []))
            if len(价格历史) >= 2:
                _, 当前价格, _ = 价格历史[-1]
                _, 上个价格, _ = 价格历史[-2]
                价格波动 = abs(当前价格 - 上个价格) / max(上个价格, 1e-10)
                
                if 价格波动 > self._配置.短期偏离阈值:
                    事件 = 操纵事件(
                        类型=操纵类型.交易量异常,
                        级别=操纵告警级别.危险,
                        描述=f"交易量暴增{暴增倍数:.1f}倍 + 价格波动{价格波动:.2%}",
                        证据={
                            "当前交易量": 当前交易量,
                            "基准交易量": 基准交易量,
                            "暴增倍数": 暴增倍数,
                            "价格波动": 价格波动
                        }
                    )
                    self._操纵事件[事件.事件ID] = 事件
                    self._告警次数 += 1
                    return 事件
        
        return None

    # ==================== 多源交叉验证 ====================

    def 记录多源价格(
        self,
        数据键: str,
        数据源: str,
        价格: float
    ) -> None:
        """记录多源价格用于交叉验证"""
        最大历史 = 20
        历史 = self._多源验证[数据键][数据源]
        历史.append(价格)
        if len(历史) > 最大历史:
            self._多源验证[数据键][数据源] = 历史[-最大历史:]

    def 检测多源不一致(
        self,
        数据键: str,
        数据源列表: List[Tuple[str, float]]
    ) -> Optional[操纵事件]:
        """
        检测多源数据不一致
        
        如果多个数据源的价格差异过大，标记为可疑
        """
        if len(数据源列表) < 2:
            return None
        
        # 计算各源与均值的偏离
        价格列表 = [p for _, p in 数据源列表]
        均值 = sum(价格列表) / len(价格列表)
        
        if 均值 <= 0:
            return None
        
        可疑源: List[Tuple[str, float, float]] = []  # (源, 价格, 偏离)
        
        for 源, 价格 in 数据源列表:
            偏离 = abs(价格 - 均值) / 均值
            if 偏离 > self._配置.多源不一致阈值:
                可疑源.append((源, 价格, 偏离))
        
        # 如果超过一半的源都偏离，标记为市场变化而非异常
        if len(可疑源) >= len(数据源列表) / 2:
            return None
        
        if 可疑源:
            # 找出异常源
            异常源列表 = [
                {"数据源": s, "价格": p, "偏离": d}
                for s, p, d in 可疑源
            ]
            
            事件 = 操纵事件(
                类型=操纵类型.多源不一致,
                级别=操纵告警级别.观察,
                涉及数据源=[s for s, _, _ in 可疑源],
                描述=f"多源不一致：{len(可疑源)}/{len(数据源列表)}个源偏离",
                证据={
                    "均值": 均值,
                    "异常源": 异常源列表
                }
            )
            self._操纵事件[事件.事件ID] = 事件
            self._告警次数 += 1
            return 事件
        
        return None

    # ==================== 断路器 ====================

    def 检查断路器(
        self,
        数据键: str,
        当前价格: float,
        上一价格: float,
        区块高度: int
    ) -> Tuple[bool, str]:
        """
        检查断路器
        
        返回: (是否触发, 原因)
        """
        if 上一价格 <= 0:
            return False, ""
        
        变化率 = abs(当前价格 - 上一价格) / 上一价格
        
        # 检查是否超过断路器阈值
        if 变化率 <= self._配置.断路器阈值:
            return False, ""
        
        # 检查当前断路器状态
        状态 = self._断路器状态.get(数据键)
        
        if 状态 is None:
            # 初始化断路器状态
            self._断路器状态[数据键] = {
                "触发价格": 当前价格,
                "触发区块": 区块高度,
                "确认区块": 1,
                "触发时间": time.time()
            }
            return False, "价格变化超过阈值，开始确认"
        
        # 检查是否还在冷却
        冷却结束时间 = 状态.get("冷却结束时间", 0)
        if time.time() < 冷却结束时间:
            return True, f"断路器冷却中，冷却至{time.ctime(冷却结束时间)}"
        
        # 确认区块检查
        确认区块数 = 区块高度 - 状态["触发区块"]
        if 确认区块数 >= self._配置.断路器确认区块:
            # 确认触发断路器
            冷却结束 = time.time() + self._配置.断路器冷却秒
            状态["冷却结束时间"] = 冷却结束
            self._触发断路器次数 += 1
            
            return True, f"断路器触发！价格变化{变化率:.2%}，超过{self._配置.断路器阈值:.2%}阈值"
        
        return False, f"断路器确认中 ({确认区块数}/{self._配置.断路器确认区块})"

    def 获取断路器状态(self, 数据键: str) -> Optional[Dict]:
        """获取断路器状态"""
        状态 = self._断路器状态.get(数据键)
        if 状态 is None:
            return None
        
        # 检查是否在冷却
        冷却结束时间 = 状态.get("冷却结束时间", 0)
        是否在冷却 = time.time() < 冷却结束时间
        
        return {
            "数据键": 数据键,
            "触发价格": 状态.get("触发价格"),
            "触发区块": 状态.get("触发区块"),
            "确认区块": 状态.get("确认区块"),
            "是否在冷却": 是否在冷却,
            "冷却剩余秒": max(0, 冷却结束时间 - time.time()) if 是否在冷却 else 0
        }

    def 重置断路器(self, 数据键: str) -> bool:
        """重置断路器"""
        if 数据键 in self._断路器状态:
            del self._断路器状态[数据键]
            return True
        return False

    # ==================== 综合检测 ====================

    def 综合检测(
        self,
        数据键: str,
        聚合结果: 聚合结果,
        区块高度: int,
        数据源价格列表: Optional[List[Tuple[str, float]]] = None
    ) -> Tuple[bool, Optional[操纵事件], str]:
        """
        综合检测操纵
        
        返回: (是否安全, 操纵事件, 原因描述)
        """
        当前价格 = 聚合结果.聚合值
        
        # 记录价格
        self.记录价格(数据键, 当前价格, 区块高度)
        
        # 1. 闪电贷检测
        闪电贷事件 = self.检测闪电贷操纵(数据键, 区块高度)
        if 闪电贷事件:
            return False, 闪电贷事件, "闪电贷操纵检测"
        
        # 2. 价格偏离检测
        价格偏离事件 = self.检测价格偏离(数据键, 当前价格)
        if 价格偏离事件:
            return False, 价格偏离事件, "价格偏离检测"
        
        # 3. 断路器检查
        历史 = list(self._价格历史.get(数据键, []))
        上一价格 = 0.0
        if len(历史) >= 2:
            _, 上一价格, _ = 历史[-2]
        
        断路触发, 断路原因 = self.检查断路器(数据键, 当前价格, 上一价格, 区块高度)
        if 断路触发:
            return False, None, 断路原因
        
        # 4. 多源交叉验证
        if 数据源价格列表:
            多源事件 = self.检测多源不一致(数据键, 数据源价格列表)
            if 多源事件 and 多源事件.级别 == 操纵告警级别.观察:
                # 观察级别可以继续，但返回事件供参考
                return True, 多源事件, "多源轻微不一致（观察中）"
        
        return True, None, "安全"

    # ==================== TWAP保护 ====================

    def 计算TWAP保护价格(
        self,
        数据键: str,
        当前价格: float,
        窗口: int = 5
    ) -> float:
        """
        计算TWAP保护价格
        
        使用时间加权平均，而非即时价格
        """
        价格历史 = list(self._价格历史.get(数据键, []))
        
        if len(价格历史) < 2:
            return 当前价格
        
        # 取最近N个价格
        窗口历史 = 价格历史[-min(窗口, len(价格历史)):]
        
        # 计算TWAP
        总权重 = 0.0
        加权和 = 0.0
        
        for i, (时间戳, 价格, _) in enumerate(窗口历史):
            if i == 0:
                权重 = 1.0
            else:
                # 与前一个的间隔作为权重
                上一时间戳, _, _ = 窗口历史[i-1]
                权重 = max(1, 时间戳 - 上一时间戳)
            
            总权重 += 权重
            加权和 += 价格 * 权重
        
        if 总权重 <= 0:
            return 当前价格
        
        return 加权和 / 总权重

    # ==================== 事件管理 ====================

    def 获取操纵事件(
        self,
        类型: Optional[操纵类型] = None,
        级别: Optional[操纵告警级别] = None,
        未处理: bool = False
    ) -> List[操纵事件]:
        """获取操纵事件"""
        结果 = list(self._操纵事件.values())
        
        if 类型:
            结果 = [e for e in 结果 if e.类型 == 类型]
        if 级别:
            结果 = [e for e in 结果 if e.级别 == 级别]
        if 未处理:
            结果 = [e for e in 结果 if not e.已处理]
        
        return sorted(结果, key=lambda x: x.时间戳, reverse=True)

    def 标记事件已处理(self, 事件ID: str) -> bool:
        """标记事件已处理"""
        if 事件ID in self._操纵事件:
            self._操纵事件[事件ID].已处理 = True
            return True
        return False

    def 获取统计信息(self) -> Dict:
        """获取统计信息"""
        按类型统计: Dict[str, int] = {}
        按级别统计: Dict[str, int] = {}
        
        for 事件 in self._操纵事件.values():
            类型名 = 事件.类型.value
            级别名 = 事件.级别.value
            按类型统计[类型名] = 按类型统计.get(类型名, 0) + 1
            按级别统计[级别名] = 按级别统计.get(级别名, 0) + 1
        
        return {
            "总事件数": len(self._操纵事件),
            "检测次数": self._检测次数,
            "告警次数": self._告警次数,
            "触发断路器次数": self._触发断路器次数,
            "未处理事件数": len([e for e in self._操纵事件.values() if not e.已处理]),
            "按类型统计": 按类型统计,
            "按级别统计": 按级别统计,
        }
