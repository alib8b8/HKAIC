"""
HKC 语义意图解析器 (intent_parser.py)
======================================
"我要在Cosmos上用DeFi" → 自动解析为具体的跨链操作序列。
用户只需要表达意图，不需要知道技术细节。

核心概念：
  - 语义意图（Semantic Intent）：自然语言表达的跨链意图
  - 意图分解（Intent Decomposition）：将语义意图分解为可执行的子意图
  - 参数推断（Parameter Inference）：从语义推断出缺失的技术参数

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 意图类别(Enum):
    """语义意图类别"""
    跨链兑换 = "cross_chain_swap"
    跨链转移 = "cross_chain_transfer"
    跨链借贷 = "cross_chain_lending"
    跨链质押 = "cross_chain_staking"
    跨链DeFi = "cross_chain_defi"
    跨链治理 = "cross_chain_governance"
    未知 = "unknown"


@dataclass
class 解析参数:
    """解析出的参数"""
    源链: str = ""
    目标链: str = ""
    输入资产: str = ""
    输出资产: str = ""
    数量: float = 0.0
    协议: str = ""
    约束: Dict[str, Any] = field(default_factory=dict)


@dataclass
class 子意图:
    """分解后的子意图"""
    子意图ID: str = ""
    序号: int = 0
    动作: str = ""
    参数: Dict[str, Any] = field(default_factory=dict)
    依赖: List[int] = field(default_factory=list)  # 依赖的前序子意图序号
    预计耗时秒: float = 0.0
    风险等级: str = "low"

    def __post_init__(self):
        if not self.子意图ID:
            self.子意图ID = hashlib.sha256(
                f"sub_{self.序号}_{time.time()}".encode()
            ).hexdigest()[:12]


@dataclass
class 解析结果:
    """意图解析结果"""
    原始意图: str = ""
    类别: 意图类别 = 意图类别.未知
    参数: 解析参数 = field(default_factory=解析参数)
    子意图列表: List[子意图] = field(default_factory=list)
    置信度: float = 0.0  # 0~1
    歧义: List[str] = field(default_factory=list)  # 需要用户确认的歧义
    总预计耗时: float = 0.0
    总风险等级: str = "low"


class 语义解析器:
    """
    语义意图解析器
    
    将自然语言表达的跨链意图解析为可执行的参数和子意图序列。
    """

    # 链名称映射
    链映射 = {
        "以太坊": "ethereum", "eth": "ethereum", "ethereum": "ethereum",
        "cosmos": "cosmos", "atom": "cosmos",
        "solana": "solana", "sol": "solana",
        "polygon": "polygon", "matic": "polygon",
        "arbitrum": "arbitrum", "arb": "arbitrum",
        "avalanche": "avalanche", "avax": "avalanche",
        "hkc": "hkc", "鸿坤": "hkc",
        "bsc": "bsc", "币安": "bsc",
        "optimism": "optimism", "op": "optimism",
    }

    # 资产映射
    资产映射 = {
        "hkaic": "HKAIC", "hk": "HKAIC",
        "eth": "ETH", "以太币": "ETH",
        "usdt": "USDT", "usdc": "USDC", "稳定币": "USDT",
        "btc": "BTC", "比特币": "BTC",
        "atom": "ATOM",
        "sol": "SOL",
        "matic": "MATIC",
    }

    # DeFi协议映射
    协议映射 = {
        "defi": "any_defi", "借贷": "lending", "质押": "staking",
        "流动性": "liquidity", "swap": "swap", "兑换": "swap",
        "aave": "aave", "compound": "compound", "uniswap": "uniswap",
    }

    def __init__(self):
        self._自定义规则: List[Dict[str, Any]] = []

    def 解析(self, 语义意图: str) -> 解析结果:
        """
        解析语义意图
        
        Args:
            语义意图: 自然语言表达的跨链意图
        """
        结果 = 解析结果(原始意图=语义意图)

        # 步骤1：分类
        结果.类别 = self._分类(语义意图)
        if 结果.类别 == 意图类别.未知:
            结果.歧义.append("无法识别意图类别")
            return 结果

        # 步骤2：提取参数
        结果.参数 = self._提取参数(语义意图)

        # 步骤3：推断缺失参数
        self._推断参数(结果.参数, 结果.类别)

        # 步骤4：分解子意图
        结果.子意图列表 = self._分解子意图(结果.类别, 结果.参数)

        # 步骤5：计算置信度
        结果.置信度 = self._计算置信度(结果)
        结果.总预计耗时 = sum(s.预计耗时秒 for s in 结果.子意图列表)
        结果.总风险等级 = self._计算总风险(结果.子意图列表)

        return 结果

    def _分类(self, 文本: str) -> 意图类别:
        """分类语义意图"""
        文本小写 = 文本.lower()
        if any(kw in 文本小写 for kw in ["defi", "借贷", "质押", "流动性"]):
            return 意图类别.跨链DeFi
        elif any(kw in 文本小写 for kw in ["兑换", "换", "swap"]):
            return 意图类别.跨链兑换
        elif any(kw in 文本小写 for kw in ["转移", "转", "transfer", "发送"]):
            return 意图类别.跨链转移
        elif any(kw in 文本小写 for kw in ["借贷", "借", "贷", "borrow", "lend"]):
            return 意图类别.跨链借贷
        elif any(kw in 文本小写 for kw in ["质押", "抵押", "stake"]):
            return 意图类别.跨链质押
        elif any(kw in 文本小写 for kw in ["投票", "治理", "govern"]):
            return 意图类别.跨链治理
        return 意图类别.未知

    def _提取参数(self, 文本: str) -> 解析参数:
        """从文本中提取参数"""
        参数 = 解析参数()

        # 提取链
        文本小写 = 文本.lower()
        找到的链 = []
        for 关键词, 链值 in self.链映射.items():
            if 关键词 in 文本小写:
                找到的链.append(链值)
        # 去重并分配（第一个为目标链或源链）
        去重链 = list(dict.fromkeys(找到的链))
        if len(去重链) >= 1:
            参数.目标链 = 去重链[0]  # 语义意图中提到的链通常是目标
        if len(去重链) >= 2:
            参数.源链 = 去重链[1]

        # 提取资产
        for 关键词, 资产值 in self.资产映射.items():
            if 关键词 in 文本小写:
                if not 参数.输入资产:
                    参数.输入资产 = 资产值
                elif not 参数.输出资产:
                    参数.输出资产 = 资产值

        # 提取协议
        for 关键词, 协议值 in self.协议映射.items():
            if 关键词 in 文本小写:
                参数.协议 = 协议值
                break

        # 提取数量
        数量匹配 = re.search(r'(\d+\.?\d*)', 文本)
        if 数量匹配:
            参数.数量 = float(数量匹配.group(1))

        return 参数

    def _推断参数(self, 参数: 解析参数, 类别: 意图类别) -> None:
        """推断缺失参数"""
        # 默认源链为HKC
        if not 参数.源链:
            参数.源链 = "hkc"

        # 根据类别推断输出资产
        if not 参数.输出资产:
            if 类别 == 意图类别.跨链兑换:
                参数.输出资产 = "USDT"  # 默认兑换为稳定币
            elif 类别 == 意图类别.跨链转移:
                参数.输出资产 = 参数.输入资产 or "HKAIC"
            elif 类别 == 意图类别.跨链DeFi:
                参数.输出资产 = 参数.输入资产 or "ETH"

        if not 参数.输入资产:
            参数.输入资产 = "HKAIC"

    def _分解子意图(self, 类别: 意图类别, 参数: 解析参数) -> List[子意图]:
        """分解为子意图序列"""
        子意图列表 = []

        if 类别 in (意图类别.跨链兑换, 意图类别.跨链转移):
            # 步骤1：源链锁定
            子意图列表.append(子意图(
                序号=1, 动作="源链锁定",
                参数={"链": 参数.源链, "资产": 参数.输入资产, "数量": 参数.数量},
                预计耗时秒=5.0, 风险等级="low",
            ))
            # 步骤2：跨链桥传输
            子意图列表.append(子意图(
                序号=2, 动作="跨链桥传输",
                参数={"源链": 参数.源链, "目标链": 参数.目标链},
                依赖=[1],
                预计耗时秒=30.0, 风险等级="medium",
            ))
            # 步骤3：目标链铸造/释放
            子意图列表.append(子意图(
                序号=3, 动作="目标链释放",
                参数={"链": 参数.目标链, "资产": 参数.输出资产},
                依赖=[2],
                预计耗时秒=5.0, 风险等级="low",
            ))

        elif 类别 == 意图类别.跨链DeFi:
            # 先跨链，再DeFi操作
            子意图列表.append(子意图(
                序号=1, 动作="源链锁定",
                参数={"链": 参数.源链, "资产": 参数.输入资产, "数量": 参数.数量},
                预计耗时秒=5.0, 风险等级="low",
            ))
            子意图列表.append(子意图(
                序号=2, 动作="跨链桥传输",
                参数={"源链": 参数.源链, "目标链": 参数.目标链},
                依赖=[1],
                预计耗时秒=30.0, 风险等级="medium",
            ))
            子意图列表.append(子意图(
                序号=3, 动作="目标链DeFi操作",
                参数={"链": 参数.目标链, "协议": 参数.协议, "资产": 参数.输出资产},
                依赖=[2],
                预计耗时秒=10.0, 风险等级="medium",
            ))

        elif 类别 == 意图类别.跨链借贷:
            子意图列表.append(子意图(
                序号=1, 动作="跨链抵押",
                参数={"源链": 参数.源链, "目标链": 参数.目标链, "资产": 参数.输入资产},
                预计耗时秒=35.0, 风险等级="medium",
            ))
            子意图列表.append(子意图(
                序号=2, 动作="借贷执行",
                参数={"链": 参数.目标链, "资产": 参数.输出资产},
                依赖=[1],
                预计耗时秒=10.0, 风险等级="medium",
            ))

        else:
            # 通用跨链
            子意图列表.append(子意图(
                序号=1, 动作="跨链操作",
                参数={"源链": 参数.源链, "目标链": 参数.目标链},
                预计耗时秒=30.0, 风险等级="medium",
            ))

        return 子意图列表

    def _计算置信度(self, 结果: 解析结果) -> float:
        """计算解析置信度"""
        参数 = 结果.参数
        得分 = 0.5  # 基础分
        if 参数.源链: 得分 += 0.1
        if 参数.目标链: 得分 += 0.15
        if 参数.输入资产: 得分 += 0.1
        if 参数.输出资产: 得分 += 0.1
        if 参数.数量 > 0: 得分 += 0.05
        return round(min(1.0, 得分), 2)

    def _计算总风险(self, 子意图列表: List[子意图]) -> str:
        """计算总体风险等级"""
        if not 子意图列表:
            return "low"
        风险等级 = {"low": 0, "medium": 1, "high": 2}
        最大风险 = max(风险等级.get(s.风险等级, 0) for s in 子意图列表)
        if 最大风险 >= 2: return "high"
        if 最大风险 >= 1: return "medium"
        return "low"

    def 添加自定义规则(self, 模式: str, 类别: 意图类别, 参数覆盖: Dict[str, Any]) -> None:
        """添加自定义解析规则"""
        self._自定义规则.append({
            "模式": 模式,
            "类别": 类别,
            "参数覆盖": 参数覆盖,
        })
