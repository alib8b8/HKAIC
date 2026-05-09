"""
自适应Gas模块 (adaptive_gas.py)
================================
Gas价格AI预测、3档建议、时段优化、批量合并、Gas对冲、消耗报告。
纯Python标准库，零外部依赖。
"""

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class Gas档位(Enum):
    """Gas费三档"""
    快速 = "fast"
    标准 = "standard"
    省钱 = "economical"


@dataclass
class Gas建议:
    """Gas价格建议"""
    快速: float = 0.0     # Gwei
    标准: float = 0.0
    省钱: float = 0.0
    预计确认秒_快速: float = 6.0
    预计确认秒_标准: float = 18.0
    预计确认秒_省钱: float = 60.0
    网络拥堵度: float = 0.0   # 0-1
    AI建议档位: Gas档位 = Gas档位.标准
    AI建议原因: str = ""

    def 获取价格(self, 档位: Gas档位) -> float:
        if 档位 == Gas档位.快速:
            return self.快速
        elif 档位 == Gas档位.省钱:
            return self.省钱
        return self.标准


@dataclass
class Gas历史记录:
    """单个区块的Gas数据"""
    区块号: int
    Gas使用率: float     # 0-1
    基础费: float        # Gwei
    时间戳: float


@dataclass
class Gas周报:
    """Gas消耗周报"""
    总Gas消耗: float = 0.0
    总交易笔数: int = 0
    平均Gas单价: float = 0.0
    最贵交易Gas: float = 0.0
    最便宜交易Gas: float = 0.0
    最拥堵时段: str = ""
    最省钱时段: str = ""
    AI建议: str = ""


class 自适应Gas引擎:
    """
    自适应Gas引擎

    核心功能：
      1. Gas价格AI预测：基于历史区块Gas使用率预测趋势
      2. 3档Gas建议：快速/标准/省钱
      3. 时段优化：非紧急交易自动选择低Gas时段
      4. 批量合并：5分钟内多笔转账合并省Gas
      5. Gas对冲：质押收益自动抵扣Gas费
      6. Gas消耗报告：每周AI生成分析报告
    """

    def __init__(self, 基础Gas: float = 1.0, 区块时间秒: float = 6.0):
        self._基础Gas = 基础Gas  # Gwei
        self._区块时间秒 = 区块时间秒
        # 历史Gas数据
        self._Gas历史: List[Gas历史记录] = []
        # 用户Gas消耗记录
        self._消耗记录: List[Dict] = []
        # 待合并交易队列
        self._待合并队列: List[Dict] = []
        self._合并窗口秒 = 300.0  # 5分钟
        # Gas对冲
        self._质押收益余额: float = 0.0
        self._对冲比例: float = 0.5  # 50%质押收益用于抵扣
        # 拥堵模式检测
        self._拥堵事件: List[Dict] = []

    # ========== Gas价格预测 ==========

    def 记录区块Gas(self, 区块号: int, Gas使用率: float, 基础费: float):
        """记录新区块的Gas数据"""
        记录 = Gas历史记录(
            区块号=区块号,
            Gas使用率=Gas使用率,
            基础费=基础费,
            时间戳=time.time(),
        )
        self._Gas历史.append(记录)
        # 只保留最近1000个区块
        if len(self._Gas历史) > 1000:
            self._Gas历史 = self._Gas历史[-1000:]

    def 预测Gas价格(self) -> Gas建议:
        """
        AI预测Gas价格并给出3档建议
        基于历史Gas使用率趋势，识别拥堵模式
        """
        if not self._Gas历史:
            # 无历史数据，返回默认值
            return Gas建议(
                快速=self._基础Gas * 2.0,
                标准=self._基础Gas,
                省钱=self._基础Gas * 0.5,
                AI建议档位=Gas档位.标准,
                AI建议原因="无历史数据，使用默认Gas价格",
            )

        # 计算最近Gas使用率趋势
        最近 = self._Gas历史[-100:]
        平均使用率 = sum(r.Gas使用率 for r in 最近) / len(最近)
        基础费 = 最近[-1].基础费

        # 趋势分析：最近10个区块vs前10个区块
        if len(最近) >= 20:
            近期使用率 = sum(r.Gas使用率 for r in 最近[-10:]) / 10
            前期使用率 = sum(r.Gas使用率 for r in 最近[-20:-10]) / 10
            趋势 = 近期使用率 - 前期使用率
        else:
            趋势 = 0.0

        # 拥堵度
        拥堵度 = min(1.0, 平均使用率)
        是否拥堵 = 拥堵度 > 0.7
        是否上升趋势 = 趋势 > 0.1

        # 预测Gas价格
        if 是否拥堵:
            快速价 = 基础费 * 3.0
            标准价 = 基础费 * 2.0
            省钱价 = 基础费 * 1.2
        elif 是否上升趋势:
            快速价 = 基础费 * 2.0
            标准价 = 基础费 * 1.3
            省钱价 = 基础费 * 0.8
        else:
            快速价 = 基础费 * 1.5
            标准价 = 基础费 * 1.0
            省钱价 = 基础费 * 0.5

        # AI建议档位
        if 是否拥堵:
            建议档位 = Gas档位.快速
            建议原因 = "网络拥堵中，建议使用快速档确保交易被打包"
        elif 是否上升趋势:
            建议档位 = Gas档位.标准
            建议原因 = "Gas价格呈上升趋势，标准档位性价比较高"
        else:
            建议档位 = Gas档位.省钱
            建议原因 = "网络空闲，省钱档位即可快速确认"

        return Gas建议(
            快速=快速价,
            标准=标准价,
            省钱=省钱价,
            预计确认秒_快速=self._区块时间秒,
            预计确认秒_标准=self._区块时间秒 * 3,
            预计确认秒_省钱=self._区块时间秒 * 10,
            网络拥堵度=拥堵度,
            AI建议档位=建议档位,
            AI建议原因=建议原因,
        )

    # ========== 拥堵模式检测 ==========

    def 检测拥堵模式(self) -> Optional[str]:
        """
        检测是否因大事件/空投等导致拥堵
        返回拥堵模式描述或None
        """
        if len(self._Gas历史) < 20:
            return None
        最近 = self._Gas历史[-20:]
        平均使用率 = sum(r.Gas使用率 for r in 最近) / len(最近)
        if 平均使用率 > 0.9:
            return "极端拥堵：网络Gas使用率超过90%，可能有大事件或空投正在进行"
        elif 平均使用率 > 0.7:
            return "中度拥堵：Gas使用率较高，建议非紧急交易延后"
        return None

    # ========== 批量合并 ==========

    def 添加待合并交易(self, 目标地址: str, 金额: float) -> Dict:
        """添加交易到合并队列"""
        交易 = {
            "目标地址": 目标地址,
            "金额": 金额,
            "时间": time.time(),
        }
        self._待合并队列.append(交易)
        return 交易

    def 检查批量合并(self) -> Optional[List[Dict]]:
        """
        检查是否有可合并的批量交易
        5分钟内3笔以上转账可合并为一笔
        """
        if len(self._待合并队列) < 3:
            return None
        now = time.time()
        # 过滤窗口内交易
        窗口内 = [t for t in self._待合并队列 if now - t["时间"] < self._合并窗口秒]
        if len(窗口内) >= 3:
            self._待合并队列 = [t for t in self._待合并队列 if now - t["时间"] >= self._合并窗口秒]
            return 窗口内
        return None

    # ========== Gas对冲 ==========

    def 设置质押收益(self, 收益金额: float):
        """设置可用的质押收益余额"""
        self._质押收益余额 = 收益金额

    def 计算Gas对冲(self, Gas费用: float) -> Tuple[float, float]:
        """
        计算Gas对冲金额
        返回 (实际支付, 对冲抵扣)
        """
        可抵扣 = min(Gas费用 * self._对冲比例, self._质押收益余额)
        实际支付 = Gas费用 - 可抵扣
        self._质押收益余额 -= 可抵扣
        return 实际支付, 可抵扣

    # ========== Gas消耗记录 ==========

    def 记录Gas消耗(self, 交易哈希: str, Gas费用: float, Gas单价: float, 时间戳: float = 0.0):
        """记录一笔Gas消耗"""
        self._消耗记录.append({
            "交易哈希": 交易哈希,
            "Gas费用": Gas费用,
            "Gas单价": Gas单价,
            "时间戳": 时间戳 or time.time(),
        })

    def 生成周报(self) -> Gas周报:
        """AI生成Gas消耗周报"""
        now = time.time()
        一周前 = now - 7 * 86400
        周记录 = [r for r in self._消耗记录 if r["时间戳"] > 一周前]
        if not 周记录:
            return Gas周报(AI建议="本周无Gas消耗记录。")

        总消耗 = sum(r["Gas费用"] for r in 周记录)
        总笔数 = len(周记录)
        平均单价 = sum(r["Gas单价"] for r in 周记录) / 总笔数
        最贵 = max(周记录, key=lambda r: r["Gas费用"])
        最便宜 = min(周记录, key=lambda r: r["Gas费用"])

        # 分析时段
        小时分布 = [0] * 24
        for r in 周记录:
            小时 = time.localtime(r["时间戳"]).tm_hour
            小时分布[小时] += r["Gas费用"]
        最拥堵时段 = f"{小时分布.index(max(小时分布))}:00"
        最省钱时段 = f"{小时分布.index(min(小时分布))}:00"

        # AI建议
        if 总消耗 > 100:
            建议 = "本周Gas消耗较高，建议使用省钱档位或选择低峰时段交易。"
        elif 总消耗 > 50:
            建议 = "本周Gas消耗适中，当前策略合理。"
        else:
            建议 = "本周Gas消耗很低，策略优秀！"

        return Gas周报(
            总Gas消耗=总消耗,
            总交易笔数=总笔数,
            平均Gas单价=平均单价,
            最贵交易Gas=最贵["Gas费用"],
            最便宜交易Gas=最便宜["Gas费用"],
            最拥堵时段=最拥堵时段,
            最省钱时段=最省钱时段,
            AI建议=建议,
        )
