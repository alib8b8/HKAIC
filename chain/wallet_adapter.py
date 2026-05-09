"""
兼容性适配器 (wallet_adapter.py)
==================================
EVM地址和鸿坤内部地址的转换、
EVM交易→鸿坤内部交易格式转换、
鸿坤事件→EVM日志格式转换。
"""

import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple

from .evm_compat import 验证EVM地址, 获取全局映射
from .eip155 import HKC_MAINNET_CHAIN_ID, EIP155交易, rlp_encode
from .evm_config import HKC主网配置, HKC测试网配置, 获取网络配置


# ============================================================
# 地址转换适配器
# ============================================================
class 地址适配器:
    """EVM地址 ↔ 鸿坤内部地址 双向转换"""

    def __init__(self):
        self._映射 = 获取全局映射()

    def EVM到HKC(self, evm地址: str) -> Optional[str]:
        """EVM地址 → 鸿坤地址"""
        return self._映射.查HKC地址(evm地址)

    def HKC到EVM(self, hkc地址: str) -> Optional[str]:
        """鸿坤地址 → EVM地址"""
        return self._映射.查EVM地址(hkc地址)

    def 解析地址(self, 地址: str) -> Dict[str, str]:
        """
        智能解析地址, 自动判断EVM或HKC格式
        返回: {类型, evm地址, hkc地址}
        """
        if 地址.startswith("0x") and 验证EVM地址(地址):
            return {
                "类型": "EVM",
                "evm地址": 地址,
                "hkc地址": self.EVM到HKC(地址) or "未映射",
            }
        elif 地址.startswith("HKAIC_"):
            return {
                "类型": "HKC",
                "evm地址": self.HKC到EVM(地址) or "未映射",
                "hkc地址": 地址,
            }
        else:
            return {"类型": "未知", "evm地址": "未知", "hkc地址": "未知"}


# ============================================================
# 交易格式转换适配器
# ============================================================
class 交易适配器:
    """EVM交易 ↔ 鸿坤内部交易格式转换"""

    def __init__(self):
        self._地址适配 = 地址适配器()

    def EVM交易到内部(self, tx: EIP155交易) -> Dict[str, Any]:
        """
        EVM交易 → 鸿坤内部交易格式
        将EIP-155交易转换为鸿坤交易引擎可处理的格式
        """
        发送者 = tx.发送者地址()
        接收者EVM = tx.to

        # 尝试转换地址
        接收者HKC = self._地址适配.EVM到HKC(接收者EVM) if 接收者EVM else None
        发送者HKC = self._地址适配.EVM到HKC(发送者) if 发送者 else None

        return {
            "交易类型": "EVM兼容",
            "发送地址_EVM": 发送者 or "待恢复",
            "发送地址_HKC": 发送者HKC or "未映射",
            "接收地址_EVM": 接收者EVM,
            "接收地址_HKC": 接收者HKC or "未映射",
            "金额_鸿坤": tx.value,
            "金额_HKAIC": tx.value / (10 ** 16),
            "手续费_鸿坤": tx.gas_price * tx.gas_limit,
            "nonce": tx.nonce,
            "data": "0x" + tx.data.hex() if tx.data else "0x",
            "chainId": tx.chain_id,
            "交易哈希": "0x" + tx.交易哈希().hex() if tx.v is not None else None,
        }

    def 内部交易到EVM(self, 发送地址: str, 接收地址: str,
                      金额_鸿坤: int, 手续费_鸿坤: int = 0,
                      nonce: int = 0, chain_id: int = HKC_MAINNET_CHAIN_ID,
                      data: bytes = b'') -> EIP155交易:
        """
        鸿坤内部交易 → EVM交易格式
        """
        # 地址转换
        发送EVM = self._地址适配.HKC到EVM(发送地址) or 发送地址
        接收EVM = self._地址适配.HKC到EVM(接收地址) or 接收地址

        # Gas估算
        gas_limit = 21000  # 标准转账
        if data:
            gas_limit = max(gas_limit, 21000 + 16 * len(data))
        gas_price = 手续费_鸿坤 // gas_limit if gas_limit > 0 and 手续费_鸿坤 > 0 else 10 ** 10

        return EIP155交易(
            nonce=nonce,
            gas_price=gas_price,
            gas_limit=gas_limit,
            to=接收EVM,
            value=金额_鸿坤,
            data=data,
            chain_id=chain_id,
        )


# ============================================================
# 日志格式转换适配器
# ============================================================
class 日志适配器:
    """鸿坤事件 → EVM日志格式转换"""

    def 鸿坤事件到EVM日志(self, 事件: Dict[str, Any]) -> Dict[str, Any]:
        """
        将鸿坤内部事件转换为EVM兼容的日志格式
        """
        return {
            "removed": False,
            "logIndex": hex(事件.get("日志索引", 0)),
            "transactionIndex": hex(事件.get("交易索引", 0)),
            "transactionHash": 事件.get("交易哈希", "0x" + "0" * 64),
            "blockHash": 事件.get("区块哈希", "0x" + "0" * 64),
            "blockNumber": hex(事件.get("块高", 0)),
            "address": 事件.get("合约地址", "0x" + "0" * 40),
            "data": 事件.get("数据", "0x"),
            "topics": 事件.get("主题列表", []),
        }

    def 鸿坤交易到EVM回执(self, 交易: Dict[str, Any]) -> Dict[str, Any]:
        """
        将鸿坤交易转换为EVM交易回执格式
        """
        状态 = "0x1" if 交易.get("状态") == "已确认" else "0x0"
        return {
            "transactionHash": 交易.get("交易哈希", "0x" + "0" * 64),
            "transactionIndex": hex(交易.get("交易索引", 0)),
            "blockHash": 交易.get("区块哈希", "0x" + "0" * 64),
            "blockNumber": hex(交易.get("块高", 0)),
            "from": 交易.get("发送地址", "0x" + "0" * 40),
            "to": 交易.get("接收地址", "0x" + "0" * 40),
            "cumulativeGasUsed": hex(交易.get("累计Gas", 21000)),
            "gasUsed": hex(交易.get("Gas使用", 21000)),
            "contractAddress": None,
            "logs": 交易.get("日志列表", []),
            "logsBloom": "0x" + "0" * 512,
            "status": 状态,
            "effectiveGasPrice": hex(交易.get("Gas价格", 10 ** 10)),
        }

    def 鸿坤交易到EVM格式(self, 交易: Dict[str, Any]) -> Dict[str, Any]:
        """
        将鸿坤交易转换为EVM eth_getTransactionByHash 格式
        """
        return {
            "hash": 交易.get("交易哈希", "0x" + "0" * 64),
            "nonce": hex(交易.get("nonce", 0)),
            "blockHash": 交易.get("区块哈希", "0x" + "0" * 64),
            "blockNumber": hex(交易.get("块高", 0)),
            "transactionIndex": hex(交易.get("交易索引", 0)),
            "from": 交易.get("发送地址", "0x" + "0" * 40),
            "to": 交易.get("接收地址", "0x" + "0" * 40),
            "value": hex(交易.get("金额", 0)),
            "gas": hex(交易.get("Gas限制", 21000)),
            "gasPrice": hex(交易.get("Gas价格", 10 ** 10)),
            "input": 交易.get("数据", "0x"),
            "v": hex(交易.get("v", 0)),
            "r": hex(交易.get("r", 0)),
            "s": hex(交易.get("s", 0)),
        }


if __name__ == "__main__":
    print("=" * 60)
    print("  兼容性适配器 Demo")
    print("=" * 60)

    # 地址适配
    适配 = 地址适配器()
    print(f"\n解析0x地址: {适配.解析地址('0x1234567890abcdef1234567890abcdef12345678')}")
    print(f"解析HKAIC地址: {适配.解析地址('HKAIC_test')}")

    # 交易适配
    交易适配 = 交易适配器()
    tx = 交易适配.内部交易到EVM("HKAIC_Alice", "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38", 10 ** 16)
    print(f"\n内部→EVM: nonce={tx.nonce}, to={tx.to}, value={tx.value}")

    # 日志适配
    日志适配 = 日志适配器()
    事件 = {"块高": 100, "交易哈希": "0xabc", "日志索引": 0}
    日志 = 日志适配.鸿坤事件到EVM日志(事件)
    print(f"\n事件→日志: blockNumber={日志['blockNumber']}")

    print("\n✅ 适配器Demo完成！")
