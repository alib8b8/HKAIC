"""
Hongkun AI Chain (HKC) 链层模块包
===================================
Hongkun AI Chain — 全球首条AI原生区块链。

模块:
    p2p_network      - 涌知路由 (知识引力+智能衰减Gossip+协同净化)
    node_sync        - 预测同步 (AI预加载+知识图谱索引)
    rpc_api          - 语义接口 (RESTful+自然语言查询+智能限流+以太坊RPC)
    etb_bridge       - 涌信桥ETB (意图驱动+动态验证组+保险池)
    consensus_engine - PoEI共识引擎 (自适应参数+Slashing)
    testnet          - 进化沙盒 (AI攻击生成+防御进化)
    evm_compat       - EVM地址兼容 (secp256k1+keccak256+双向映射)
    bip39            - BIP39/BIP44助记词 (生成/恢复/HD派生)
    eip155           - EIP-155交易签名 (RLP编码+链ID)
    evm_config       - EVM钱包配置 (MetaMask/SafePal/imToken/Trust Wallet)
    wallet_adapter   - 兼容性适配器 (地址/交易/日志转换)
"""

from .p2p_network import P2P网络, Kademlia路由表, Gossip广播器
from .node_sync import 节点同步器, 快速同步器, 状态同步器
from .rpc_api import RPC服务器, RESTful处理器, WebSocket推送器, 以太坊RPC处理器, 创建EVM兼容RPC
from .evm_compat import keccak256, 私钥到EVM地址, 验证EVM地址, 双向地址映射, 从私钥生成双地址
from .bip39 import 生成助记词, 验证助记词, 助记词到私钥, 助记词到EVM地址, 安全检查助记词
from .eip155 import EIP155交易, HKC_MAINNET_CHAIN_ID, HKC_TESTNET_CHAIN_ID, rlp_encode, rlp_decode, 智能Gas估算器, 交易安全检测器
from .evm_config import HKC主网配置, HKC测试网配置, MetaMask主网配置, MetaMask测试网配置
from .wallet_adapter import 地址适配器, 交易适配器, 日志适配器
from .etb_bridge import 涌信桥, Solver竞争器, 涌信保险池
from .consensus_engine import PoEI共识引擎, Epoch管理器, 出块者选举器
from .testnet import 测试网, 网络拓扑构建器, 压力测试器

__all__ = [
    'P2P网络', 'Kademlia路由表', 'Gossip广播器',
    '节点同步器', '快速同步器', '状态同步器',
    'RPC服务器', 'RESTful处理器', 'WebSocket推送器', '以太坊RPC处理器', '创建EVM兼容RPC',
    '涌信桥', 'Solver竞争器', '涌信保险池',
    'PoEI共识引擎', 'Epoch管理器', '出块者选举器',
    '测试网', '网络拓扑构建器', '压力测试器',
    'keccak256', '私钥到EVM地址', '验证EVM地址', '双向地址映射', '从私钥生成双地址',
    '生成助记词', '验证助记词', '助记词到私钥', '助记词到EVM地址', '安全检查助记词',
    'EIP155交易', 'HKC_MAINNET_CHAIN_ID', 'HKC_TESTNET_CHAIN_ID', 'rlp_encode', 'rlp_decode',
    '智能Gas估算器', '交易安全检测器',
    'HKC主网配置', 'HKC测试网配置', 'MetaMask主网配置', 'MetaMask测试网配置',
    '地址适配器', '交易适配器', '日志适配器',
]
