"""
EVM地址格式兼容模块 (evm_compat.py)
====================================
secp256k1椭圆曲线(纯Python)、keccak256哈希、EVM地址生成、
鸿坤地址↔EVM地址双向映射。零外部依赖。
"""

import hashlib
import os
from typing import Optional, Tuple, Dict

# ============================================================
# secp256k1 椭圆曲线参数
# ============================================================
_SECP256K1_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_SECP256K1_A = 0
_SECP256K1_B = 7
_SECP256K1_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_SECP256K1_Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
_SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_SECP256K1_G = (_SECP256K1_Gx, _SECP256K1_Gy)


def _模逆(a: int, p: int) -> int:
    """模逆 — 扩展欧几里得算法"""
    if a == 0:
        raise ValueError("模逆不存在: a=0")
    lm, hm = 1, 0
    low, high = a % p, p
    while low > 1:
        r = high // low
        nm = hm - lm * r
        new = high - low * r
        hm, lm = lm, nm
        high, low = low, new
    return lm % p


def _椭圆点加(P: Tuple[int, int], Q: Tuple[int, int], p: int = _SECP256K1_P) -> Tuple[int, int]:
    """椭圆曲线点加"""
    if P is None:
        return Q
    if Q is None:
        return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2:
        if y1 != y2:
            return None
        return _椭圆点倍(P, p)
    lam = ((y2 - y1) * _模逆(x2 - x1, p)) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def _椭圆点倍(P: Tuple[int, int], p: int = _SECP256K1_P) -> Tuple[int, int]:
    """椭圆曲线点加倍"""
    if P is None:
        return None
    x1, y1 = P
    if y1 == 0:
        return None
    lam = ((3 * x1 * x1 + _SECP256K1_A) * _模逆(2 * y1, p)) % p
    x3 = (lam * lam - 2 * x1) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def _椭圆标量乘(k: int, P: Tuple[int, int], p: int = _SECP256K1_P) -> Tuple[int, int]:
    """椭圆曲线标量乘法 — 双倍加法"""
    if k == 0 or P is None:
        return None
    if k < 0:
        k = k % _SECP256K1_N
        P = (P[0], (-P[1]) % p)
    result = None
    addend = P
    while k > 0:
        if k & 1:
            result = _椭圆点加(result, addend, p)
        addend = _椭圆点倍(addend, p)
        k >>= 1
    return result


def _生成公钥(私钥: int, 压缩: bool = False) -> bytes:
    """从私钥生成secp256k1公钥"""
    点 = _椭圆标量乘(私钥, _SECP256K1_G)
    if 点 is None:
        raise ValueError("无效私钥")
    x, y = 点
    if 压缩:
        前缀 = b'\x02' if y % 2 == 0 else b'\x03'
        return 前缀 + x.to_bytes(32, 'big')
    else:
        return b'\x04' + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')


def _rfc6979_k(消息哈希: bytes, 私钥: int) -> int:
    """RFC6979确定性nonce生成 — 防止nonce重用导致私钥泄露"""
    import hmac as _hmac
    qlen = 32  # _SECP256K1_N的字节长度
    # 步骤a: h1 = 消息哈希(已是32字节)
    h1 = 消息哈希[:32]
    # 步骤b: V = 0x01 * 32
    V = b'\x01' * 32
    # 步骤c: K = 0x00 * 32
    K = b'\x00' * 32
    # 步骤d: K = HMAC_K(V || 0x00 || int2octets(x) || bits2octets(h1))
    私钥bytes = 私钥.to_bytes(qlen, 'big')
    K = _hmac.new(K, V + b'\x00' + 私钥bytes + h1, hashlib.sha256).digest()
    # 步骤e: V = HMAC_K(V)
    V = _hmac.new(K, V, hashlib.sha256).digest()
    # 步骤f: K = HMAC_K(V || 0x01 || int2octets(x) || bits2octets(h1))
    K = _hmac.new(K, V + b'\x01' + 私钥bytes + h1, hashlib.sha256).digest()
    # 步骤g: V = HMAC_K(V)
    V = _hmac.new(K, V, hashlib.sha256).digest()
    # 步骤h: 生成k
    while True:
        T = b''
        while len(T) < qlen:
            V = _hmac.new(K, V, hashlib.sha256).digest()
            T += V
        k = int.from_bytes(T[:qlen], 'big')
        if 1 <= k < _SECP256K1_N:
            return k
        K = _hmac.new(K, V + b'\x00', hashlib.sha256).digest()
        V = _hmac.new(K, V, hashlib.sha256).digest()


def _ecdsa签名(消息哈希: bytes, 私钥: int) -> Tuple[int, int]:
    """ECDSA签名 — 使用RFC6979确定性nonce，返回(r, s)，低S规范化"""
    z = int.from_bytes(消息哈希, 'big')
    # 使用RFC6979确定性nonce代替随机nonce
    k = _rfc6979_k(消息哈希, 私钥)
    点 = _椭圆标量乘(k, _SECP256K1_G)
    if 点 is None:
        raise ValueError("无效的nonce k")
    r = 点[0] % _SECP256K1_N
    if r == 0:
        raise ValueError("r=0, 签名失败")
    k逆 = _模逆(k, _SECP256K1_N)
    s = (k逆 * (z + r * 私钥)) % _SECP256K1_N
    if s == 0:
        raise ValueError("s=0, 签名失败")
    if s > _SECP256K1_N // 2:
        s = _SECP256K1_N - s
    return (r, s)


def _ecdsa验证(消息哈希: bytes, 签名: Tuple[int, int], 公钥点: Tuple[int, int]) -> bool:
    """ECDSA验证"""
    r, s = 签名
    if not (1 <= r < _SECP256K1_N and 1 <= s < _SECP256K1_N):
        return False
    z = int.from_bytes(消息哈希, 'big')
    s逆 = _模逆(s, _SECP256K1_N)
    u1 = (z * s逆) % _SECP256K1_N
    u2 = (r * s逆) % _SECP256K1_N
    点 = _椭圆点加(_椭圆标量乘(u1, _SECP256K1_G), _椭圆标量乘(u2, 公钥点))
    if 点 is None:
        return False
    return 点[0] % _SECP256K1_N == r


def _从签名恢复公钥(消息哈希: bytes, r: int, s: int, v: int) -> Optional[Tuple[int, int]]:
    """从ECDSA签名恢复公钥点 (用于交易验证)"""
    if v < 27 or v > 30:
        return None
    recovery = v - 27
    x = r
    # 计算y² = x³ + 7 (mod p)
    y平方 = (pow(x, 3, _SECP256K1_P) + _SECP256K1_B) % _SECP256K1_P
    y = pow(y平方, (_SECP256K1_P + 1) // 4, _SECP256K1_P)
    if y * y % _SECP256K1_P != y平方:
        return None
    # 根据recovery bit选择y
    if y % 2 != recovery % 2:
        y = _SECP256K1_P - y
    R = (x, y)
    # 验证R在曲线上且在正确子群中
    if _椭圆标量乘(_SECP256K1_N, R) is not None:
        return None
    r逆 = _模逆(r, _SECP256K1_N)
    z = int.from_bytes(消息哈希, 'big')
    # 公钥 = r⁻¹(s·R - z·G)
    u1 = ((_SECP256K1_N - z) * r逆) % _SECP256K1_N
    u2 = (s * r逆) % _SECP256K1_N
    公钥点 = _椭圆点加(_椭圆标量乘(u1, _SECP256K1_G), _椭圆标量乘(u2, R))
    return 公钥点


# ============================================================
# Keccak-256 纯Python实现
# ============================================================
_KECCAK_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

_KECCAK_ROT = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]

_MASK64 = (1 << 64) - 1


def _rot64(x: int, n: int) -> int:
    """64位循环左移"""
    if n == 0:
        return x
    return ((x << n) | (x >> (64 - n))) & _MASK64


def _keccak_f1600(状态: list) -> list:
    """Keccak-f[1600] 置换 — 24轮"""
    for 轮 in range(24):
        # θ步骤: 列奇偶校验混合
        C = [状态[x] ^ 状态[x+5] ^ 状态[x+10] ^ 状态[x+15] ^ 状态[x+20] for x in range(5)]
        D = [C[(x-1)%5] ^ _rot64(C[(x+1)%5], 1) for x in range(5)]
        状态 = [(状态[i] ^ D[i%5]) & _MASK64 for i in range(25)]

        # ρ和π步骤: 旋转和位置置换
        B = [0] * 25
        for x in range(5):
            for y in range(5):
                新x = y
                新y = (2 * x + 3 * y) % 5
                B[新x + 5 * 新y] = _rot64(状态[x + 5 * y], _KECCAK_ROT[x][y])

        # χ步骤: 非线性混合
        for y5 in range(0, 25, 5):
            t = B[y5:y5+5]
            状态[y5]   = (t[0] ^ ((~t[1]) & t[2])) & _MASK64
            状态[y5+1] = (t[1] ^ ((~t[2]) & t[3])) & _MASK64
            状态[y5+2] = (t[2] ^ ((~t[3]) & t[4])) & _MASK64
            状态[y5+3] = (t[3] ^ ((~t[4]) & t[0])) & _MASK64
            状态[y5+4] = (t[4] ^ ((~t[0]) & t[1])) & _MASK64

        # ι步骤: 轮常数异或
        状态[0] = (状态[0] ^ _KECCAK_RC[轮]) & _MASK64

    return 状态


def keccak256(数据: bytes) -> bytes:
    """
    Keccak-256哈希 (以太坊使用的原始Keccak, 非NIST SHA-3)
    纯Python实现, 零外部依赖。
    
    已通过pycryptodome参考实现验证: 多种输入长度均匹配 ✓
    注意: Keccak-256 ≠ SHA3-256 (NIST标准), 填充字节不同(0x01 vs 0x06)
    """
    速率 = 136  # 1088位 = 136字节 (rate = (1600 - 2*256) / 8)
    数据 = bytearray(数据)

    # 填充: Keccak pad10*1 (0x01...0x80)
    填充长度 = 速率 - (len(数据) % 速率)
    填充 = bytearray(填充长度)
    填充[0] = 0x01
    填充[-1] |= 0x80  # 合并最后一个字节
    数据.extend(填充)

    # 初始化状态 (25个64位Lane)
    状态 = [0] * 25

    # 吸收阶段
    for 块偏移 in range(0, len(数据), 速率):
        块 = 数据[块偏移:块偏移 + 速率]
        for i in range(速率 // 8):
            状态[i] ^= int.from_bytes(块[i*8:i*8+8], 'little')
        状态 = _keccak_f1600(状态)

    # 挤压阶段 (256位 = 32字节)
    输出 = b''
    for i in range(4):
        输出 += 状态[i].to_bytes(8, 'little')
    return 输出[:32]


# ============================================================
# EVM地址生成与验证
# ============================================================
def 私钥到EVM地址(私钥_bytes: bytes) -> str:
    """
    从私钥生成EVM地址
    流程: 私钥 → secp256k1公钥(非压缩) → keccak256 → 取后20字节 → 0x前缀
    """
    私钥int = int.from_bytes(私钥_bytes, 'big')
    if not (1 <= 私钥int < _SECP256K1_N):
        raise ValueError("私钥超出有效范围")
    公钥 = _生成公钥(私钥int, 压缩=False)
    哈希 = keccak256(公钥[1:])  # 去掉0x04前缀
    地址字节 = 哈希[-20:]
    return "0x" + 地址字节.hex()


def 公钥到EVM地址(公钥_bytes: bytes) -> str:
    """
    从公钥生成EVM地址
    支持非压缩格式(65字节, 0x04前缀)和压缩格式(33字节)
    """
    if len(公钥_bytes) == 65 and 公钥_bytes[0] == 0x04:
        哈希 = keccak256(公钥_bytes[1:])
    elif len(公钥_bytes) == 33 and 公钥_bytes[0] in (0x02, 0x03):
        # 解压公钥
        x = int.from_bytes(公钥_bytes[1:], 'big')
        y平方 = (pow(x, 3, _SECP256K1_P) + _SECP256K1_B) % _SECP256K1_P
        y = pow(y平方, (_SECP256K1_P + 1) // 4, _SECP256K1_P)
        if y % 2 != 公钥_bytes[0] % 2:
            y = _SECP256K1_P - y
        非压缩 = b'\x04' + x.to_bytes(32, 'big') + y.to_bytes(32, 'big')
        哈希 = keccak256(非压缩[1:])
    else:
        哈希 = keccak256(公钥_bytes)
    return "0x" + 哈希[-20:].hex()


def 验证EVM地址(地址: str) -> bool:
    """验证EVM地址格式 (0x + 40个十六进制字符)"""
    if not 地址.startswith("0x"):
        return False
    if len(地址) != 42:
        return False
    try:
        int(地址[2:], 16)
        return True
    except ValueError:
        return False


def EVM地址校验和(地址: str) -> str:
    """
    EIP-55 混合大小写校验和地址
    根据地址哈希决定每个字符的大小写, 用于防止输入错误
    """
    if not 验证EVM地址(地址):
        raise ValueError("无效的EVM地址")
    小写 = 地址[2:].lower()
    哈希 = keccak256(小写.encode('ascii')).hex()
    结果 = "0x"
    for i, c in enumerate(小写):
        if c in '0123456789':
            结果 += c
        else:
            结果 += c.upper() if int(哈希[i], 16) >= 8 else c.lower()
    return 结果


def 验证EVM校验和地址(地址: str) -> bool:
    """验证EIP-55校验和地址"""
    return EVM地址校验和(地址) == 地址


# ============================================================
# 鸿坤地址 ↔ EVM地址 双向映射
# ============================================================
class 双向地址映射:
    """
    维护 HKAIC_地址 ↔ 0x地址 的双向映射关系
    映射规则: 同一私钥 → HKAIC_地址(哈希体系) + 0x地址(secp256k1+keccak256)
    """

    def __init__(self):
        self._hkc_to_evm: Dict[str, str] = {}
        self._evm_to_hkc: Dict[str, str] = {}

    def 注册映射(self, hkc地址: str, evm地址: str):
        """注册一对映射关系"""
        if not 验证EVM地址(evm地址):
            raise ValueError(f"无效EVM地址: {evm地址}")
        self._hkc_to_evm[hkc地址] = evm地址
        self._evm_to_hkc[evm地址.lower()] = hkc地址

    def 从私钥注册(self, 私钥_bytes: bytes, hkc地址: str):
        """从私钥自动生成EVM地址并注册映射"""
        evm地址 = 私钥到EVM地址(私钥_bytes)
        self.注册映射(hkc地址, evm地址)
        return evm地址

    def 查EVM地址(self, hkc地址: str) -> Optional[str]:
        """根据鸿坤地址查EVM地址"""
        return self._hkc_to_evm.get(hkc地址)

    def 查HKC地址(self, evm地址: str) -> Optional[str]:
        """根据EVM地址查鸿坤地址"""
        return self._evm_to_hkc.get(evm地址.lower())

    def 所有映射(self) -> Dict[str, str]:
        """返回所有 HKAIC→EVM 映射"""
        return dict(self._hkc_to_evm)

    def 映射数量(self) -> int:
        return len(self._hkc_to_evm)

    def 批量注册(self, 映射列表: list):
        """批量注册 [(hkc, evm), ...]"""
        for hkc, evm in 映射列表:
            self.注册映射(hkc, evm)


# ============================================================
# 全局映射与便捷函数
# ============================================================
_全局映射 = 双向地址映射()


def 获取全局映射() -> 双向地址映射:
    """获取全局地址映射实例"""
    return _全局映射


def 从私钥生成双地址(私钥_bytes: bytes) -> Tuple[str, str]:
    """
    从私钥同时生成HKAIC地址和EVM地址
    返回: (hkc地址, evm地址)
    """
    def _sha256(d):
        return hashlib.sha256(d).digest()

    def _ripemd160(d):
        try:
            h = hashlib.new('ripemd160'); h.update(d); return h.digest()
        except (ValueError, TypeError):
            return hashlib.sha256(d).digest()[:20]

    def _hash160(d):
        return _ripemd160(_sha256(d))

    def _base58(d):
        字母表 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        n = int.from_bytes(d, 'big')
        结果 = ""
        while n > 0:
            n, r = divmod(n, 58); 结果 = 字母表[r] + 结果
        for b in d:
            if b == 0: 结果 = "1" + 结果
            else: break
        return 结果

    # HKAIC地址 (与core/wallet.py一致)
    公钥bytes = _sha256(私钥_bytes + b'_pub')
    h160 = _hash160(公钥bytes)
    校验 = _sha256(_sha256(b'HKAIC' + h160))[:4]
    payload = b'HKAIC' + h160 + 校验
    hkc地址 = "HKAIC_" + _base58(payload)[:24]

    # EVM地址 (secp256k1 + keccak256)
    evm地址 = 私钥到EVM地址(私钥_bytes)

    # 注册映射
    _全局映射.注册映射(hkc地址, evm地址)

    return (hkc地址, evm地址)


if __name__ == "__main__":
    print("=" * 60)
    print("  EVM地址兼容模块 Demo")
    print("=" * 60)

    # 测试keccak256
    测试 = keccak256(b'')
    预期 = "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    print(f"\nkeccak256(空): {'✅' if 测试.hex() == 预期 else '❌'}")

    测试2 = keccak256(b'abc')
    预期2 = "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45"
    print(f"keccak256(abc): {'✅' if 测试2.hex() == 预期2 else '❌'}")

    # 生成EVM地址
    私钥 = os.urandom(32)
    evm地址 = 私钥到EVM地址(私钥)
    print(f"\nEVM地址: {evm地址}")
    print(f"校验和: {EVM地址校验和(evm地址)}")
    print(f"验证: {'✅' if 验证EVM地址(evm地址) else '❌'}")

    # 双地址生成
    hkc, evm = 从私钥生成双地址(私钥)
    print(f"\n双地址: HKC={hkc}, EVM={evm}")

    # 映射查询
    映射 = 获取全局映射()
    print(f"HKC→EVM: {映射.查EVM地址(hkc)}")
    print(f"EVM→HKC: {映射.查HKC地址(evm)}")

    # secp256k1验证
    私钥int = int.from_bytes(私钥, 'big')
    公钥点 = _椭圆标量乘(私钥int, _SECP256K1_G)
    哈希 = keccak256(b'test message')
    r, s = _ecdsa签名(哈希, 私钥int)
    验证结果 = _ecdsa验证(哈希, (r, s), 公钥点)
    print(f"\nECDSA签名验证: {'✅' if 验证结果 else '❌'}")

    print("\n✅ EVM兼容模块Demo完成！")
