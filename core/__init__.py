"""
HKAIC 核心模块包
================

包含 Hongkun AI Coin 虚拟币系统的所有核心组件。
共识机制: PoEI — 涌智证明 (Proof of Emergent Intelligence)
"""

from .ledger import 账本
from .tokenomics import 代币经济学
from .wallet import 钱包, 多签钱包
from .transaction import 交易引擎
from .contract import 合约引擎
from .staking import 质押引擎
from .market import 市场引擎
from .blockchain import 区块链, PoEI共识

__all__ = [
    '账本', '代币经济学', '钱包', '多签钱包',
    '交易引擎', '合约引擎', '质押引擎', '市场引擎',
    '区块链', 'PoEI共识',
]
