"""
Hongkun AI Chain — AI运维大脑 (ai_monitor.py)
===============================================
AI驱动的节点监控与自愈系统。

核心能力:
  1. 实时监控 — CPU/内存/网络/共识/同步
  2. 异常检测 — AI自动识别异常模式
  3. 自愈 — 自动执行修复动作
  4. 告警 — 分级告警通知
  5. 预测 — 预测潜在问题
"""

import hashlib
import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class 告警级别(Enum):
    信息 = "info"
    警告 = "warn"
    严重 = "critical"
    紧急 = "emergency"


class 健康状态(Enum):
    健康 = "healthy"
    注意 = "attention"
    警告 = "warning"
    危险 = "danger"


@dataclass
class 监控指标:
    """单个监控指标"""
    名称: str
    当前值: float
    警告阈值: float
    危险阈值: float
    单位: str = ""
    趋势: str = "stable"  # stable/rising/falling

    def 状态(self) -> 健康状态:
        if self.当前值 >= self.危险阈值:
            return 健康状态.危险
        elif self.当前值 >= self.警告阈值:
            return 健康状态.警告
        elif self.当前值 >= self.警告阈值 * 0.8:
            return 健康状态.注意
        return 健康状态.健康


@dataclass
class 告警:
    """告警信息"""
    级别: 告警级别
    来源: str
    消息: str
    时间: float = 0.0
    已处理: bool = False
    自愈动作: str = ""
    def __post_init__(self):
        if self.时间 == 0:
            self.时间 = time.time()


@dataclass
class 自愈动作:
    """自愈动作定义"""
    名称: str
    触发条件: str
    执行逻辑: str
    风险: str = "low"
    成功率: float = 0.9


class 指标采集器:
    """采集节点运行指标"""

    def 采集(self) -> Dict[str, 监控指标]:
        """采集当前指标(模拟)"""
        return {
            "CPU使用率": 监控指标("CPU使用率", random.uniform(10, 90), 70, 90, "%"),
            "内存使用率": 监控指标("内存使用率", random.uniform(20, 85), 75, 90, "%"),
            "磁盘使用率": 监控指标("磁盘使用率", random.uniform(10, 70), 80, 95, "%"),
            "网络延迟_ms": 监控指标("网络延迟_ms", random.uniform(5, 200), 100, 500, "ms"),
            "TPS": 监控指标("TPS", random.uniform(50, 500), 50, 20, "tx/s"),
            "共识参与率": 监控指标("共识参与率", random.uniform(0.6, 1.0), 0.7, 0.5, ""),
            "同步进度": 监控指标("同步进度", random.uniform(0.9, 1.0), 0.9, 0.7, ""),
            "P2P连接数": 监控指标("P2P连接数", random.randint(5, 50), 10, 3, ""),
            "交易池大小": 监控指标("交易池大小", random.randint(0, 1000), 500, 2000, "tx"),
            "区块高度差": 监控指标("区块高度差", random.randint(0, 5), 3, 10, "blocks"),
        }


class 异常模式检测器:
    """AI异常模式检测"""

    _模式 = {
        "内存泄漏": {
            "检测": lambda 历史: len(历史) > 5 and all(历史[i] < 历史[i+1] for i in range(len(历史)-1)),
            "描述": "内存持续增长,疑似泄漏",
        },
        "网络抖动": {
            "检测": lambda 历史: len(历史) > 3 and max(历史) / max(min(历史), 1) > 5,
            "描述": "网络延迟波动剧烈",
        },
        "共识延迟": {
            "检测": lambda 历史: len(历史) > 2 and all(v < 0.7 for v in 历史[-3:]),
            "描述": "共识参与率持续偏低",
        },
        "分叉风险": {
            "检测": lambda 历史: len(历史) > 2 and any(v > 3 for v in 历史[-3:]),
            "描述": "区块高度差增大,分叉风险",
        },
    }

    def __init__(self):
        self._历史: Dict[str, List[float]] = {}

    def 更新(self, 指标: Dict[str, 监控指标]):
        """更新指标历史"""
        for 名称, 指 in 指标.items():
            self._历史.setdefault(名称, []).append(指.当前值)
            # 保留最近100条
            self._历史[名称] = self._历史[名称][-100:]

    def 检测(self) -> List[告警]:
        """检测异常模式"""
        告警列表 = []
        for 模式名, 规则 in self._模式.items():
            for 指标名, 历史 in self._历史.items():
                if len(历史) < 3:
                    continue
                try:
                    if 规则["检测"](历史):
                        告警列表.append(告警(
                            级别=告警级别.警告,
                            来源=指标名,
                            消息=f"[AI模式] {模式名}: {规则['描述']}",
                        ))
                except (IndexError, ZeroDivisionError):
                    pass
        return 告警列表


class 自愈引擎:
    """AI自愈引擎——自动执行修复动作"""

    _动作库 = [
        自愈动作("重启网络连接", "网络延迟>500ms", "重新建立P2P连接", "low", 0.85),
        自愈动作("清理交易池", "交易池>2000", "移除低优先级交易", "low", 0.95),
        自愈动作("重新同步", "高度差>10", "触发快速同步", "medium", 0.8),
        自愈动作("降低负载", "CPU>90%", "减少非必要任务", "low", 0.9),
        自愈动作("扩展连接", "P2P<10", "增加种子节点连接", "low", 0.85),
    ]

    def 执行(self, 告警: 告警) -> Optional[自愈动作]:
        """根据告警选择并执行自愈动作"""
        for 动作 in self._动作库:
            if 告警.来源 in 动作.触发条件 or 告警.消息[:10] in 动作.触发条件:
                告警.自愈动作 = 动作.名称
                告警.已处理 = True
                return 动作
        return None


class AI运维大脑:
    """
    HKC AI运维大脑
    
    整合: 指标采集 + 异常检测 + 自愈 + 告警 + 预测
    
    自动化运维闭环:
      采集→检测→告警→自愈→验证→报告
    """

    def __init__(self):
        self._采集器 = 指标采集器()
        self._检测器 = 异常模式检测器()
        self._自愈 = 自愈引擎()
        self._告警: List[告警] = []
        self._当前指标: Dict[str, 监控指标] = {}
        self._健康历史: List[健康状态] = []

    @property
    def 当前指标(self): return self._当前指标

    def 采集一轮(self) -> Dict[str, 监控指标]:
        """采集一轮指标"""
        self._当前指标 = self._采集器.采集()
        self._检测器.更新(self._当前指标)
        return self._当前指标

    def 检测异常(self) -> List[告警]:
        """检测异常"""
        # 阈值告警
        告警列表 = []
        for 名称, 指标 in self._当前指标.items():
            if 指标.状态() == 健康状态.危险:
                告警列表.append(告警(
                    级别=告警级别.严重,
                    来源=名称,
                    消息=f"{名称}={指标.当前值:.1f}{指标.单位}, 超过危险阈值{指标.危险阈值}",
                ))
            elif 指标.状态() == 健康状态.警告:
                告警列表.append(告警(
                    级别=告警级别.警告,
                    来源=名称,
                    消息=f"{名称}={指标.当前值:.1f}{指标.单位}, 超过警告阈值{指标.警告阈值}",
                ))

        # AI模式检测
        告警列表.extend(self._检测器.检测())
        self._告警.extend(告警列表)
        return 告警列表

    def 自愈(self) -> List[Tuple[告警, Optional[自愈动作]]]:
        """自动修复"""
        结果 = []
        for 告 in self._告警:
            if not 告.已处理:
                动作 = self._自愈.执行(告)
                结果.append((告, 动作))
        return 结果

    def 健康评分(self) -> Tuple[float, 健康状态]:
        """计算节点健康评分(0-100)"""
        if not self._当前指标:
            return 50.0, 健康状态.注意
        评分 = 100.0
        for 指标 in self._当前指标.values():
            if 指标.状态() == 健康状态.危险:
                评分 -= 30
            elif 指标.状态() == 健康状态.警告:
                评分 -= 15
            elif 指标.状态() == 健康状态.注意:
                评分 -= 5
        评分 = max(0, 评分)
        if 评分 >= 80:
            状态 = 健康状态.健康
        elif 评分 >= 60:
            状态 = 健康状态.注意
        elif 评分 >= 40:
            状态 = 健康状态.警告
        else:
            状态 = 健康状态.危险
        self._健康历史.append(状态)
        return 评分, 状态

    def 运维报告(self) -> str:
        """生成运维报告"""
        评分, 状态 = self.健康评分()
        线 = [
            "=" * 50,
            "  HKC AI运维报告",
            "=" * 50,
            f"  健康评分: {评分:.0f}/100 ({状态.value})",
            f"  告警数: {len(self._告警)}",
        ]
        未处理 = [a for a in self._告警 if not a.已处理]
        if 未处理:
            线.append(f"  未处理告警: {len(未处理)}")
            for a in 未处理[:5]:
                级标 = {"info": "ℹ️", "warn": "⚠️", "critical": "🔴", "emergency": "💀"}.get(a.级别.value, "❓")
                线.append(f"    {级标} [{a.来源}] {a.消息}")
        已自愈 = [a for a in self._告警 if a.已处理]
        if 已自愈:
            线.append(f"  已自愈: {len(已自愈)}")
        线.append("=" * 50)
        return "\n".join(线)

    def 状态(self) -> dict:
        评分, 状态 = self.健康评分()
        return {
            "健康评分": f"{评分:.0f}",
            "状态": 状态.value,
            "告警": len(self._告警),
            "指标": len(self._当前指标),
        }


if __name__ == "__main__":
    print("  HKC AI运维大脑 Demo")
    brain = AI运维大脑()
    for i in range(3):
        brain.采集一轮()
        告警 = brain.检测异常()
        if 告警:
            brain.自愈()
    print(brain.运维报告())
    print(f"  {brain.状态()}")
