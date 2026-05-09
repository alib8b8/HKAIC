"""
EIP-155交易签名模块 (eip155.py)
================================
EIP-155格式交易序列化(RLP编码)、签名、验证。
chainId: HKC主网=9901, 测试网=9902
纯Python实现，零外部依赖。
"""

import hashlib
from typing import List, Optional, Tuple, Any

# ============================================================
# HKC链ID定义
# ============================================================
HKC_MAINNET_CHAIN_ID = 9901  # HKC主网
HKC_TESTNET_CHAIN_ID = 9902  # HKC测试网


# ============================================================
# RLP编码/解码 (纯Python实现)
# ============================================================
def _rlp_encode_length(长度: int, 偏移: int) -> bytes:
    """RLP编码长度字段"""
    if 长度 < 56:
        return bytes([偏移 + 长度])
    else:
        长度bytes = 长度.to_bytes((长度.bit_length() + 7) // 8, 'big')
        return bytes([偏移 + 55 + len(长度bytes)]) + 长度bytes


def rlp_encode(数据: Any) -> bytes:
    """
    RLP编码 (递归长度前缀)
    支持bytes和list类型
    """
    if isinstance(数据, bytes):
        if len(数据) == 1 and 数据[0] < 0x80:
            return 数据
        return _rlp_encode_length(len(数据), 0x80) + 数据
    elif isinstance(数据, list):
        有效项 = []
        for 项 in 数据:
            if 项 is None or 项 == b'':
                有效项.append(b'')
            elif isinstance(项, int):
                if 项 == 0:
                    有效项.append(b'')
                else:
                    # 整数转大端字节，去掉前导零
                    byte_len = (项.bit_length() + 7) // 8
                    有效项.append(项.to_bytes(byte_len, 'big'))
            elif isinstance(项, bytes):
                有效项.append(项)
            elif isinstance(项, str):
                有效项.append(项.encode('utf-8'))
            else:
                有效项.append(b'')
        编码项 = b''.join(rlp_encode(项) for 项 in 有效项)
        return _rlp_encode_length(len(编码项), 0xc0) + 编码项
    elif 数据 is None:
        return b'\x80'
    elif isinstance(数据, int):
        if 数据 == 0:
            return b'\x80'
        byte_len = (数据.bit_length() + 7) // 8
        数据bytes = 数据.to_bytes(byte_len, 'big')
        return rlp_encode(数据bytes)
    else:
        return b'\x80'


def rlp_decode(数据: bytes) -> Any:
    """RLP解码"""
    if not 数据:
        return b''

    类型 = 数据[0]

    if 类型 < 0x80:
        return bytes([类型])
    elif 类型 <= 0xb7:
        长度 = 类型 - 0x80
        return 数据[1:1 + 长度]
    elif 类型 <= 0xbf:
        长度长度 = 类型 - 0xb7
        长度 = int.from_bytes(数据[1:1 + 长度长度], 'big')
        return 数据[1 + 长度长度:1 + 长度长度 + 长度]
    elif 类型 <= 0xf7:
        列表长度 = 类型 - 0xc0
        列表数据 = 数据[1:1 + 列表长度]
        结果 = []
        偏移 = 0
        while 偏移 < len(列表数据):
            项, 消耗 = _rlp_decode_item(列表数据[偏移:])
            结果.append(项)
            偏移 += 消耗
        return 结果
    else:
        长度长度 = 类型 - 0xf7
        列表长度 = int.from_bytes(数据[1:1 + 长度长度], 'big')
        列表数据 = 数据[1 + 长度长度:1 + 长度长度 + 列表长度]
        结果 = []
        偏移 = 0
        while 偏移 < len(列表数据):
            项, 消耗 = _rlp_decode_item(列表数据[偏移:])
            结果.append(项)
            偏移 += 消耗
        return 结果


def _rlp_decode_item(数据: bytes) -> Tuple[Any, int]:
    """解码单个RLP项, 返回(项, 消耗字节数)"""
    if not 数据:
        return b'', 0

    类型 = 数据[0]

    if 类型 < 0x80:
        return bytes([类型]), 1
    elif 类型 <= 0xb7:
        长度 = 类型 - 0x80
        return 数据[1:1 + 长度], 1 + 长度
    elif 类型 <= 0xbf:
        长度长度 = 类型 - 0xb7
        长度 = int.from_bytes(数据[1:1 + 长度长度], 'big')
        总消耗 = 1 + 长度长度 + 长度
        return 数据[1 + 长度长度:总消耗], 总消耗
    elif 类型 <= 0xf7:
        列表长度 = 类型 - 0xc0
        return 数据[:1 + 列表长度], 1 + 列表长度
    else:
        长度长度 = 类型 - 0xf7
        列表长度 = int.from_bytes(数据[1:1 + 长度长度], 'big')
        总消耗 = 1 + 长度长度 + 列表长度
        return 数据[:总消耗], 总消耗


# ============================================================
# EIP-155交易
# ============================================================
class EIP155交易:
    """
    EIP-155交易格式
    字段: nonce, gasPrice, gasLimit, to, value, data, chainId
    签名后增加: v, r, s
    """

    def __init__(self, nonce: int = 0, gas_price: int = 0, gas_limit: int = 21000,
                 to: str = "", value: int = 0, data: bytes = b'',
                 chain_id: int = HKC_MAINNET_CHAIN_ID):
        self.nonce = nonce
        self.gas_price = gas_price
        self.gas_limit = gas_limit
        self.to = to  # 0x前缀的EVM地址
        self.value = value  # 单位: wei (鸿坤)
        self.data = data if isinstance(data, bytes) else bytes.fromhex(data.replace('0x', ''))
        self.chain_id = chain_id
        # 签名字段
        self.v: Optional[int] = None
        self.r: Optional[int] = None
        self.s: Optional[int] = None

    def 未签名RLP(self) -> bytes:
        """未签名交易的RLP编码 (用于签名)"""
        to_bytes = b''
        if self.to and self.to.startswith('0x'):
            to_bytes = bytes.fromhex(self.to[2:])
        elif self.to:
            to_bytes = bytes.fromhex(self.to)

        字段 = [
            self.nonce,
            self.gas_price,
            self.gas_limit,
            to_bytes,
            self.value,
            self.data,
            self.chain_id,
            0,  # 空的v
            0,  # 空的r
            0,  # 空的s
        ]
        return rlp_encode(字段)

    def 签名哈希(self) -> bytes:
        """计算签名哈希 (keccak256(未签名RLP))"""
        from .evm_compat import keccak256
        return keccak256(self.未签名RLP())

    def 签名(self, 私钥: bytes) -> 'EIP155交易':
        """使用私钥对交易进行EIP-155签名"""
        from .evm_compat import _ecdsa签名, _SECP256K1_N
        哈希 = self.签名哈希()
        私钥int = int.from_bytes(私钥, 'big')
        r, s = _ecdsa签名(哈希, 私钥int)

        # 确定recovery id (v)
        # 对于EIP-155: v = chain_id * 2 + 35 + recovery_id
        # recovery_id = 0 或 1
        from .evm_compat import _从签名恢复公钥, 私钥到EVM地址

        # 尝试recovery_id = 0和1
        for recovery_id in (0, 1):
            v = self.chain_id * 2 + 35 + recovery_id
            公钥点 = _从签名恢复公钥(哈希, r, s, v)
            if 公钥点 is not None:
                from .evm_compat import _生成公钥
                x, y = 公钥点
                非压缩公钥 = b'\x04' + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')
                from .evm_compat import keccak256
                恢复地址 = "0x" + keccak256(非压缩公钥[1:])[-20:].hex()
                预期地址 = 私钥到EVM地址(私钥).lower()
                if 恢复地址 == 预期地址:
                    self.v = v
                    self.r = r
                    self.s = s
                    return self

        # 如果恢复失败，使用默认值
        self.v = self.chain_id * 2 + 35
        self.r = r
        self.s = s
        return self

    def 已签名RLP(self) -> bytes:
        """已签名交易的RLP编码 (用于广播)"""
        if self.v is None:
            raise ValueError("交易尚未签名")

        to_bytes = b''
        if self.to and self.to.startswith('0x'):
            to_bytes = bytes.fromhex(self.to[2:])
        elif self.to:
            to_bytes = bytes.fromhex(self.to)

        字段 = [
            self.nonce,
            self.gas_price,
            self.gas_limit,
            to_bytes,
            self.value,
            self.data,
            self.v,
            self.r,
            self.s,
        ]
        return rlp_encode(字段)

    def 交易哈希(self) -> bytes:
        """计算交易哈希"""
        from .evm_compat import keccak256
        return keccak256(self.已签名RLP())

    def 发送者地址(self) -> Optional[str]:
        """从签名恢复发送者地址"""
        if self.v is None or self.r is None or self.s is None:
            return None
        from .evm_compat import _从签名恢复公钥, keccak256
        哈希 = self.签名哈希()
        公钥点 = _从签名恢复公钥(哈希, self.r, self.s, self.v)
        if 公钥点 is None:
            return None
        x, y = 公钥点
        非压缩公钥 = b'\x04' + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')
        return "0x" + keccak256(非压缩公钥[1:])[-20:].hex()

    def 到字典(self) -> dict:
        """转换为字典"""
        return {
            "nonce": hex(self.nonce),
            "gasPrice": hex(self.gas_price),
            "gasLimit": hex(self.gas_limit),
            "to": self.to,
            "value": hex(self.value),
            "data": "0x" + self.data.hex() if self.data else "0x",
            "chainId": hex(self.chain_id),
            "v": hex(self.v) if self.v is not None else None,
            "r": hex(self.r) if self.r is not None else None,
            "s": hex(self.s) if self.s is not None else None,
        }

    @staticmethod
    def 从原始交易(raw: bytes) -> 'EIP155交易':
        """从原始交易字节解码"""
        解码 = rlp_decode(raw)
        if not isinstance(解码, list) or len(解码) < 9:
            raise ValueError("无效的交易格式")

        nonce = int.from_bytes(解码[0], 'big') if 解码[0] else 0
        gas_price = int.from_bytes(解码[1], 'big') if 解码[1] else 0
        gas_limit = int.from_bytes(解码[2], 'big') if 解码[2] else 0
        to = "0x" + 解码[3].hex() if 解码[3] else ""
        value = int.from_bytes(解码[4], 'big') if 解码[4] else 0
        data = 解码[5] if len(解码) > 5 else b''
        v = int.from_bytes(解码[6], 'big') if len(解码) > 6 and 解码[6] else 0
        r = int.from_bytes(解码[7], 'big') if len(解码) > 7 and 解码[7] else 0
        s = int.from_bytes(解码[8], 'big') if len(解码) > 8 and 解码[8] else 0

        # 从v恢复chainId
        if v >= 35:
            chain_id = (v - 35) // 2
        else:
            chain_id = 0

        tx = EIP155交易(nonce, gas_price, gas_limit, to, value, data, chain_id)
        tx.v = v
        tx.r = r
        tx.s = s
        return tx


# ============================================================
# AI增强: 智能Gas估算
# ============================================================
class 智能Gas估算器:
    """
    AI增强: 根据网络拥堵度预测最优Gas价格
    基于历史Gas价格数据的简单模型
    """

    def __init__(self, 基础Gas价格: int = 10 ** 10):  # 10 Gwei
        self._基础价格 = 基础Gas价格
        self._历史价格: List[int] = []
        self._拥堵因子 = 1.0

    def 更新网络状态(self, 当前Gas价格: int, 待处理交易数: int, 区块利用率: float):
        """更新网络状态, 调整拥堵因子"""
        self._历史价格.append(当前Gas价格)
        if len(self._历史价格) > 100:
            self._历史价格 = self._历史价格[-100:]
        # 拥堵因子: 基于区块利用率和待处理交易数
        self._拥堵因子 = 1.0 + 区块利用率 * 0.5 + min(待处理交易数 / 1000, 2.0)

    def 估算Gas价格(self, 优先级: str = "中") -> int:
        """
        AI预测最优Gas价格
        优先级: 低/中/高/紧急
        """
        优先级映射 = {"低": 0.8, "中": 1.0, "高": 1.5, "紧急": 2.0}
        倍数 = 优先级映射.get(优先级, 1.0)

        基础 = self._基础价格
        if self._历史价格:
            # 取最近10个价格的中位数
            最近 = sorted(self._历史价格[-10:])
            中位数 = 最近[len(最近) // 2]
            基础 = max(基础, 中位数)

        return int(基础 * self._拥堵因子 * 倍数)

    def 估算GasLimit(self, 交易类型: str = "转账") -> int:
        """估算Gas Limit"""
        GasLimit映射 = {
            "转账": 21000,
            "合约调用": 100000,
            "合约部署": 500000,
            "代币转账": 65000,
        }
        return GasLimit映射.get(交易类型, 21000)


# ============================================================
# AI增强: 交易安全检测
# ============================================================
class 交易安全检测器:
    """
    AI增强: 分析交易对手地址风险
    """

    def __init__(self):
        self._黑名单: set = set()
        self._风险地址: dict = {}  # 地址 → 风险评分

    def 添加黑名单(self, 地址: str):
        """添加黑名单地址"""
        self._黑名单.add(地址.lower())

    def 分析风险(self, 发送地址: str, 接收地址: str, 金额: int) -> dict:
        """
        AI分析交易风险
        返回: {风险等级, 风险因素, 建议}
        """
        风险因素 = []
        风险评分 = 0

        # 黑名单检查
        if 接收地址.lower() in self._黑名单:
            风险因素.append("接收地址在黑名单中")
            风险评分 += 90

        # 大额交易
        if 金额 > 10 ** 18:  # 超过1个代币单位
            风险因素.append("大额交易")
            风险评分 += 20

        # 零地址
        if 接收地址 == "0x" + "0" * 40:
            风险因素.append("接收地址为零地址")
            风险评分 += 50

        # 合约地址检测 (简化)
        if len(接收地址) == 42 and not 接收地址.startswith("0x"):
            风险因素.append("地址格式异常")
            风险评分 += 30

        # 确定风险等级
        if 风险评分 >= 80:
            风险等级 = "高"
            建议 = "建议取消此交易"
        elif 风险评分 >= 40:
            风险等级 = "中"
            建议 = "建议仔细确认交易细节"
        else:
            风险等级 = "低"
            建议 = "交易安全"

        return {
            "风险等级": 风险等级,
            "风险评分": 风险评分,
            "风险因素": 风险因素 if 风险因素 else ["未检测到风险"],
            "建议": 建议,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("  EIP-155交易签名模块 Demo")
    print("=" * 60)

    # RLP编码测试
    编码 = rlp_encode([b'\x01', b'\x02'])
    print(f"\nRLP编码 [1, 2]: {编码.hex()}")

    # 创建EIP-155交易
    tx = EIP155交易(
        nonce=0,
        gas_price=10 ** 10,  # 10 Gwei
        gas_limit=21000,
        to="0x742d35Cc6634C0532925a3b844Bc9e7595f2bD38",
        value=10 ** 16,  # 0.01 HKAIC
        chain_id=HKC_MAINNET_CHAIN_ID,
    )
    print(f"\n未签名RLP: {tx.未签名RLP().hex()[:64]}...")
    print(f"签名哈希: {tx.签名哈希().hex()}")

    # 智能Gas估算
    估算器 = 智能Gas估算器()
    估算器.更新网络状态(10 ** 10, 50, 0.5)
    print(f"\nGas价格估算(中): {估算器.估算Gas价格('中')}")
    print(f"Gas Limit(转账): {估算器.估算GasLimit('转账')}")

    # 安全检测
    检测器 = 交易安全检测器()
    风险 = 检测器.分析风险("0xabc", "0xdef", 10 ** 16)
    print(f"\n交易安全: {风险}")

    print("\n✅ EIP-155模块Demo完成！")
