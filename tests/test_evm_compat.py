"""
EVM兼容测试模块 (test_evm_compat.py)
======================================
测试EVM地址生成、BIP39助记词、EIP-155交易签名、
JSON-RPC接口、双地址映射、HKAIC单位显示修复。
"""

import sys
import os

# 确保能找到模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest


class TestKeccak256(unittest.TestCase):
    """测试Keccak-256哈希"""

    def setUp(self):
        from hongkun_ai_lab.chain.evm_compat import keccak256
        self.keccak256 = keccak256

    def test_空输入(self):
        """keccak256(空) 应等于以太坊标准值"""
        结果 = self.keccak256(b'')
        预期 = "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
        self.assertEqual(结果.hex(), 预期)

    def test_abc输入(self):
        """keccak256('abc') 应等于标准值"""
        结果 = self.keccak256(b'abc')
        预期 = "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45"
        self.assertEqual(结果.hex(), 预期)

    def test_输出长度(self):
        """keccak256输出应为32字节"""
        结果 = self.keccak256(b'test')
        self.assertEqual(len(结果), 32)

    def test_确定性(self):
        """相同输入应产生相同输出"""
        self.assertEqual(self.keccak256(b'data'), self.keccak256(b'data'))

    def test_不同输入不同输出(self):
        """不同输入应产生不同输出"""
        self.assertNotEqual(self.keccak256(b'foo'), self.keccak256(b'bar'))


class TestEVM地址生成(unittest.TestCase):
    """测试EVM地址生成和验证"""

    def setUp(self):
        from hongkun_ai_lab.chain.evm_compat import 私钥到EVM地址, 验证EVM地址, EVM地址校验和
        self.私钥到EVM地址 = 私钥到EVM地址
        self.验证EVM地址 = 验证EVM地址
        self.EVM地址校验和 = EVM地址校验和

    def test_地址格式(self):
        """EVM地址应以0x开头，总长42字符"""
        私钥 = os.urandom(32)
        地址 = self.私钥到EVM地址(私钥)
        self.assertTrue(地址.startswith('0x'))
        self.assertEqual(len(地址), 42)

    def test_地址验证(self):
        """生成的地址应通过验证"""
        私钥 = os.urandom(32)
        地址 = self.私钥到EVM地址(私钥)
        self.assertTrue(self.验证EVM地址(地址))

    def test_无效地址验证(self):
        """无效地址应验证失败"""
        self.assertFalse(self.验证EVM地址("0x123"))  # 太短
        self.assertFalse(self.验证EVM地址("1234567890abcdef1234567890abcdef12345678"))  # 缺0x
        self.assertFalse(self.验证EVM地址("0xgghh1234567890abcdef1234567890abcdef1234"))  # 非hex

    def test_校验和地址(self):
        """EIP-55校验和地址应正确生成"""
        私钥 = os.urandom(32)
        地址 = self.私钥到EVM地址(私钥)
        校验和 = self.EVM地址校验和(地址)
        self.assertTrue(self.验证EVM地址(校验和))
        self.assertEqual(校验和.lower(), 地址.lower())

    def test_确定性生成(self):
        """同一私钥应生成同一地址"""
        私钥 = os.urandom(32)
        地址1 = self.私钥到EVM地址(私钥)
        地址2 = self.私钥到EVM地址(私钥)
        self.assertEqual(地址1, 地址2)


class Test双地址映射(unittest.TestCase):
    """测试HKAIC地址↔EVM地址双向映射"""

    def setUp(self):
        from hongkun_ai_lab.chain.evm_compat import 双向地址映射, 私钥到EVM地址
        self.映射 = 双向地址映射()
        self.私钥到EVM地址 = 私钥到EVM地址

    def test_注册和查询(self):
        """注册映射后应能双向查询"""
        hkc地址 = "HKAIC_TestAddr123"
        evm地址 = "0x1234567890abcdef1234567890abcdef12345678"
        self.映射.注册映射(hkc地址, evm地址)
        self.assertEqual(self.映射.查EVM地址(hkc地址), evm地址)
        self.assertEqual(self.映射.查HKC地址(evm地址), hkc地址)

    def test_从私钥注册(self):
        """从私钥自动注册映射"""
        私钥 = os.urandom(32)
        hkc地址 = "HKAIC_FromPrivKey"
        evm地址 = self.映射.从私钥注册(私钥, hkc地址)
        self.assertTrue(evm地址.startswith('0x'))
        self.assertEqual(self.映射.查EVM地址(hkc地址), evm地址)
        self.assertEqual(self.映射.查HKC地址(evm地址), hkc地址)

    def test_未注册地址查询(self):
        """未注册的地址查询应返回None"""
        self.assertIsNone(self.映射.查EVM地址("未注册"))
        self.assertIsNone(self.映射.查HKC地址("0x0000000000000000000000000000000000000000"))


class TestBIP39(unittest.TestCase):
    """测试BIP39助记词生成和恢复"""

    def setUp(self):
        from hongkun_ai_lab.chain.bip39 import 生成助记词, 验证助记词, 助记词到私钥, 助记词到种子
        self.生成助记词 = 生成助记词
        self.验证助记词 = 验证助记词
        self.助记词到私钥 = 助记词到私钥
        self.助记词到种子 = 助记词到种子

    def test_生成12词助记词(self):
        """应生成12个词的助记词"""
        助记词 = self.生成助记词(12)
        词数 = len(助记词.split())
        self.assertEqual(词数, 12)

    def test_生成24词助记词(self):
        """应生成24个词的助记词"""
        助记词 = self.生成助记词(24)
        词数 = len(助记词.split())
        self.assertEqual(词数, 24)

    def test_验证有效助记词(self):
        """生成的助记词应通过验证"""
        助记词 = self.生成助记词(12)
        self.assertTrue(self.验证助记词(助记词))

    def test_验证无效助记词(self):
        """无效助记词应验证失败"""
        self.assertFalse(self.验证助记词("invalid words that are not bip39"))
        self.assertFalse(self.验证助记词("abandon abandon abandon"))

    def test_助记词到私钥(self):
        """助记词应能派生出32字节私钥"""
        助记词 = self.生成助记词(12)
        私钥 = self.助记词到私钥(助记词)
        self.assertEqual(len(私钥), 32)
        self.assertNotEqual(私钥, b'\x00' * 32)

    def test_确定性派生(self):
        """同一助记词应派生出同一私钥"""
        助记词 = self.生成助记词(12)
        私钥1 = self.助记词到私钥(助记词)
        私钥2 = self.助记词到私钥(助记词)
        self.assertEqual(私钥1, 私钥2)

    def test_种子长度(self):
        """PBKDF2种子应为64字节"""
        助记词 = self.生成助记词(12)
        种子 = self.助记词到种子(助记词)
        self.assertEqual(len(种子), 64)


class TestEIP155(unittest.TestCase):
    """测试EIP-155交易签名"""

    def setUp(self):
        from hongkun_ai_lab.chain.eip155 import EIP155交易, HKC_MAINNET_CHAIN_ID, rlp_encode, rlp_decode
        self.EIP155交易 = EIP155交易
        self.HKC_MAINNET_CHAIN_ID = HKC_MAINNET_CHAIN_ID
        self.rlp_encode = rlp_encode
        self.rlp_decode = rlp_decode

    def test_RLP编码解码(self):
        """RLP编码后解码应得到原始数据"""
        原始 = [b'\x01', b'\x02', b'\x03']
        编码 = self.rlp_encode(原始)
        解码 = self.rlp_decode(编码)
        self.assertEqual(解码, 原始)

    def test_RLP编码空列表(self):
        """空列表RLP编码"""
        编码 = self.rlp_encode([])
        self.assertIsInstance(编码, bytes)

    def test_交易创建(self):
        """应能创建EIP-155交易"""
        tx = self.EIP155交易(
            nonce=0,
            gas_price=10**10,
            gas_limit=21000,
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38",
            value=10**16,
            chain_id=self.HKC_MAINNET_CHAIN_ID,
        )
        self.assertEqual(tx.nonce, 0)
        self.assertEqual(tx.chain_id, 9901)

    def test_交易未签名RLP(self):
        """未签名交易应能RLP编码"""
        tx = self.EIP155交易(nonce=0, gas_price=10**10, gas_limit=21000,
                            to="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38",
                            value=10**16, chain_id=self.HKC_MAINNET_CHAIN_ID)
        rlp = tx.未签名RLP()
        self.assertIsInstance(rlp, bytes)
        self.assertGreater(len(rlp), 0)

    def test_链ID(self):
        """HKC主网chainId应为9901"""
        self.assertEqual(self.HKC_MAINNET_CHAIN_ID, 9901)


class TestJSONRPC(unittest.TestCase):
    """测试以太坊JSON-RPC接口"""

    def setUp(self):
        from hongkun_ai_lab.chain.rpc_api import 以太坊RPC处理器
        self.rpc = 以太坊RPC处理器(链ID=9901)

    def test_eth_chainId(self):
        """eth_chainId应返回0x26ad (9901)"""
        响应 = self.rpc.处理JSONRPC("eth_chainId", [])
        self.assertEqual(响应["result"], "0x26ad")

    def test_net_version(self):
        """net_version应返回9901"""
        响应 = self.rpc.处理JSONRPC("net_version", [])
        self.assertEqual(响应["result"], "9901")

    def test_web3_clientVersion(self):
        """web3_clientVersion应包含HKC标识"""
        响应 = self.rpc.处理JSONRPC("web3_clientVersion", [])
        self.assertIn("HongkunAIChain", 响应["result"])

    def test_eth_gasPrice(self):
        """eth_gasPrice应返回有效值"""
        响应 = self.rpc.处理JSONRPC("eth_gasPrice", [])
        self.assertTrue(响应["result"].startswith("0x"))

    def test_eth_blockNumber(self):
        """eth_blockNumber应返回块高"""
        响应 = self.rpc.处理JSONRPC("eth_blockNumber", [])
        self.assertTrue(响应["result"].startswith("0x"))

    def test_eth_getTransactionCount(self):
        """eth_getTransactionCount应返回nonce"""
        响应 = self.rpc.处理JSONRPC("eth_getTransactionCount",
            ["0x1234567890abcdef1234567890abcdef12345678", "latest"])
        self.assertTrue(响应["result"].startswith("0x"))

    def test_eth_estimateGas(self):
        """eth_estimateGas应返回Gas估算"""
        响应 = self.rpc.处理JSONRPC("eth_estimateGas", [{}])
        self.assertEqual(响应["result"], "0x5208")

    def test_未知方法(self):
        """未知方法应返回错误"""
        响应 = self.rpc.处理JSONRPC("eth_unknownMethod", [])
        self.assertIn("error", 响应)


class TestEVM配置(unittest.TestCase):
    """测试EVM钱包配置"""

    def setUp(self):
        from hongkun_ai_lab.chain.evm_config import HKC主网配置, HKC测试网配置, MetaMask主网配置
        self.主网配置 = HKC主网配置
        self.测试网配置 = HKC测试网配置
        self.MetaMask主网配置 = MetaMask主网配置

    def test_主网chainId(self):
        """主网chainId应为9901"""
        self.assertEqual(self.主网配置["chainId"], 9901)

    def test_测试网chainId(self):
        """测试网chainId应为9902"""
        self.assertEqual(self.测试网配置["chainId"], 9902)

    def test_货币符号(self):
        """主网货币符号应为HKAIC"""
        self.assertEqual(self.主网配置["货币符号"], "HKAIC")

    def test_MetaMask配置(self):
        """MetaMask配置应包含必要字段"""
        配置 = self.MetaMask主网配置()
        self.assertIn("chainId", 配置)
        self.assertIn("chainName", 配置)
        self.assertIn("nativeCurrency", 配置)
        self.assertIn("rpcUrls", 配置)
        self.assertEqual(配置["nativeCurrency"]["symbol"], "HKAIC")
        self.assertEqual(配置["nativeCurrency"]["decimals"], 16)


class TestHKAIC单位修复(unittest.TestCase):
    """测试HKAIC单位显示修复"""

    def setUp(self):
        from hongkun_ai_lab.core.ledger import 账本, 格式化金额, HKAIC转鸿坤, 鸿坤转HKAIC, HONGKUN_PER_HKAIC
        self.账本 = 账本()
        self.格式化金额 = 格式化金额
        self.HKAIC转鸿坤 = HKAIC转鸿坤
        self.鸿坤转HKAIC = 鸿坤转HKAIC
        self.HONGKUN_PER_HKAIC = HONGKUN_PER_HKAIC

    def test_零金额显示(self):
        """零金额应显示为'0 HKAIC'"""
        self.assertEqual(self.格式化金额(0), "0 HKAIC")

    def test_整数金额显示(self):
        """整数金额应正确显示"""
        金额 = self.HKAIC转鸿坤(100)
        结果 = self.格式化金额(金额)
        self.assertIn("100", 结果)
        self.assertIn("HKAIC", 结果)

    def test_小额金额显示(self):
        """小额金额不应显示0.00000000"""
        金额 = self.HKAIC转鸿坤(0.5)
        结果 = self.格式化金额(金额)
        self.assertNotEqual(结果, "0.00000000 HKAIC")
        self.assertIn("0.5", 结果)

    def test_单位转换精度(self):
        """HKAIC和鸿坤之间转换应精确"""
        hkaic = 1.5
        鸿坤 = self.HKAIC转鸿坤(hkaic)
        转回 = self.鸿坤转HKAIC(鸿坤)
        self.assertEqual(转回, hkaic)

    def test_账本余额查询(self):
        """账本余额查询应正确显示"""
        self.账本.铸币("addr_A", self.HKAIC转鸿坤(100))
        余额 = self.账本.查询余额_HKAIC("addr_A")
        self.assertEqual(余额, 100.0)


class Test交易适配器(unittest.TestCase):
    """测试交易格式适配"""

    def setUp(self):
        from hongkun_ai_lab.chain.wallet_adapter import 交易适配器, 地址适配器, 日志适配器
        self.交易适配 = 交易适配器()
        self.地址适配 = 地址适配器()
        self.日志适配 = 日志适配器()

    def test_地址解析EVM(self):
        """应正确解析EVM地址"""
        结果 = self.地址适配.解析地址("0x1234567890abcdef1234567890abcdef12345678")
        self.assertEqual(结果["类型"], "EVM")

    def test_地址解析HKC(self):
        """应正确解析HKAIC地址"""
        结果 = self.地址适配.解析地址("HKAIC_TestAddr")
        self.assertEqual(结果["类型"], "HKC")

    def test_内部交易到EVM(self):
        """内部交易应能转换为EVM格式"""
        tx = self.交易适配.内部交易到EVM(
            "HKAIC_Alice", "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38",
            10 ** 16)
        self.assertEqual(tx.value, 10 ** 16)
        self.assertEqual(tx.to, "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38")

    def test_鸿坤事件到EVM日志(self):
        """鸿坤事件应能转换为EVM日志格式"""
        事件 = {"块高": 100, "交易哈希": "0xabc123", "日志索引": 0}
        日志 = self.日志适配.鸿坤事件到EVM日志(事件)
        self.assertEqual(日志["blockNumber"], "0x64")
        self.assertEqual(日志["removed"], False)


if __name__ == "__main__":
    print("=" * 60)
    print("  HKC EVM兼容测试")
    print("=" * 60)
    unittest.main(verbosity=2)
