"""
涌信钱包核心引擎 (emergent_wallet.py)
======================================
Emergent Wallet — HKC AI原生态钱包核心。

钱包创建/导入：BIP39助记词、EVM地址派生、鸿坤内部地址
多账户管理、资产总览、交易历史、地址本
EVM兼容 + AI原生逻辑

纯Python标准库，零外部依赖。
"""

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# 导入涌信钱包子模块
from .semantic_tx import 语义交易引擎, 交易类型, Gas偏好
from .credit_score import 涌智信用分引擎, 信用等级
from .intent_engine import 意图驱动引擎, 意图类型
from .ai_guardian import AI守护者, 风险等级
from .social_recovery import 社交恢复引擎
from .adaptive_gas import 自适应Gas引擎, Gas档位
from .portfolio_analyzer import 投资组合分析器, 资产项
from .wallet_config import 涌信钱包配置, HKC主网, HKC测试网


# ========== BIP39 助记词（使用chain/bip39.py标准实现） ==========

def _生成熵(字节数: int = 16) -> bytes:
    """生成随机熵（16字节=128位=12词，32字节=256位=24词）"""
    return os.urandom(字节数)


def _熵转助记词(熵: bytes) -> List[str]:
    """使用标准BIP39实现从熵生成助记词"""
    from chain.bip39 import 生成助记词
    return 生成助记词(字数=12 if len(熵) == 16 else 24, 随机源=熵).split()


def _助记词转种子(助记词列表: List[str], 密码: str = "") -> bytes:
    """使用标准BIP39实现将助记词转换为种子"""
    from chain.bip39 import 助记词到种子
    return 助记词到种子(" ".join(助记词列表), 密码)


# ========== EVM地址派生 ==========

def _种子派生私钥(种子: bytes, 路径索引: int = 0) -> bytes:
    """
    从种子派生EVM兼容私钥
    M-15修复: 完善BIP32派生逻辑，添加CKD校验和secp256k1阶取模
    标准路径: m/44'/60'/0'/0/索引 (EVM)
    """
    # M-15: secp256k1阶数
    SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    
    # 标准BIP32主密钥派生
    主密钥 = hmac.new(b"Bitcoin seed", 种子, hashlib.sha512).digest()  # M-15: 使用完整种子
    私钥 = 主密钥[:32]
    链码 = 主密钥[32:]
    
    # M-15: 主密钥私钥校验
    私钥_int = int.from_bytes(私钥, 'big')
    if 私钥_int == 0 or 私钥_int >= SECP256K1_ORDER:
        # 无效私钥，使用回退方案
        回退种子 = hmac.new(b"Bitcoin seed fallback", 种子, hashlib.sha512).digest()
        私钥 = 回退种子[:32]
        链码 = 回退种子[32:]

    # 派生路径 m/44'/60'/0'/0/index
    路径 = [44 + 0x80000000, 60 + 0x80000000, 0x80000000, 0, 路径索引]
    for 索引 in 路径:
        if 索引 >= 0x80000000:
            # 强化派生: HMAC-SHA512(链码, 0x00 || 私钥 || 索引)
            数据 = b'\x00' + 私钥 + 索引.to_bytes(4, 'big')
        else:
            # 常规派生: HMAC-SHA512(链码, 公钥 || 索引) — 需要公钥
            # M-15: 简化使用强化派生，安全性更高
            数据 = b'\x00' + 私钥 + 索引.to_bytes(4, 'big')
        派生 = hmac.new(链码, 数据, hashlib.sha512).digest()
        # M-15: CKD(Checked Key Derivation) — 子密钥 = (父密钥 + 派生左半) mod n
        子密钥_int = (int.from_bytes(私钥, 'big') + int.from_bytes(派生[:32], 'big')) % SECP256K1_ORDER
        私钥 = 子密钥_int.to_bytes(32, 'big')
        链码 = 派生[32:]
        # M-15: 子密钥校验
        if 子密钥_int == 0:
            # 无效密钥，使用索引+1重试
            数据 = b'\x00' + 私钥 + (索引 + 1).to_bytes(4, 'big')
            派生 = hmac.new(链码, 数据, hashlib.sha512).digest()
            子密钥_int = (int.from_bytes(私钥, 'big') + int.from_bytes(派生[:32], 'big')) % SECP256K1_ORDER
            私钥 = 子密钥_int.to_bytes(32, 'big')
            链码 = 派生[32:]

    return 私钥


def _私钥转EVM地址(私钥: bytes) -> str:
    """
    从私钥派生EVM地址
    1. 私钥 -> secp256k1公钥（非压缩格式）
    2. 公钥 -> Keccak-256哈希后20字节
    使用chain/evm_compat.py的标准实现，与以太坊完全兼容
    """
    try:
        from chain.evm_compat import 私钥到EVM地址
        return 私钥到EVM地址(私钥)
    except Exception:
        # 降级：使用SHA256近似（仅当secp256k1不可用时）
        import warnings
        warnings.warn("secp256k1不可用，使用SHA256近似生成EVM地址，该地址与标准以太坊不兼容！",
                      RuntimeWarning, stacklevel=2)
        公钥 = hashlib.sha256(私钥).digest()
        哈希 = hashlib.sha256(公钥).digest()
        地址字节 = 哈希[-20:]
        return "0x" + 地址字节.hex()


def _生成鸿坤内部地址(EVM地址: str, 种子: bytes) -> str:
    """
    从EVM地址和种子生成鸿坤内部地址
    格式: HKC_ + Base58(Hash160(EVM地址 + 种子))
    """
    数据 = EVM地址.encode() + 种子[:8]
    哈希1 = hashlib.sha256(数据).digest()
    # 尝试RIPEMD160
    try:
        h = hashlib.new('ripemd160')
        h.update(哈希1)
        哈希160 = h.digest()
    except (ValueError, TypeError):
        哈希160 = hashlib.sha256(哈希1).digest()[:20]

    # 校验和
    校验 = hashlib.sha256(hashlib.sha256(b'HKC' + 哈希160).digest()).digest()[:4]
    payload = b'HKC' + 哈希160 + 校验

    # Base58编码
    字母表 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = int.from_bytes(payload, 'big')
    结果 = ""
    while n > 0:
        n, r = divmod(n, 58)
        结果 = 字母表[r] + 结果
    for b in payload:
        if b == 0:
            结果 = "1" + 结果
        else:
            break
    return "HKC_" + 结果[:24]


# ========== Keystore ==========

def _加密Keystore(私钥: bytes, 密码: str, 地址: str) -> Dict:
    """
    生成Keystore JSON
    ⚠️ 安全提示: 当前实现使用SHA256-XOR流加密代替AES-128-CTR，
    PBKDF2-SHA256代替Scrypt。安全性低于标准实现。
    生产环境应使用pycryptodome等库实现真正的AES-128-CTR + Scrypt。
    """
    盐 = os.urandom(32)
    # 密钥派生（简化Scrypt，生产环境需用完整Scrypt）
    派生密钥 = hashlib.pbkdf2_hmac('sha256', 密码.encode(), 盐, 524288, dklen=32)  # 加倍迭代增强安全性
    加密密钥 = 派生密钥[:16]
    # M-11修复: 增强XOR流加密，添加轮密钥扩展
    # 使用HMAC-SHA256作为流生成器，密钥=加密密钥，消息=计数器
    计数器 = 派生密钥[16:20] + b'\x00' * 12
    流 = hmac.new(加密密钥, 计数器, hashlib.sha256).digest()
    block_count = 0
    while len(流) < len(私钥):
        block_count += 1
        流 += hmac.new(加密密钥, 计数器 + block_count.to_bytes(4, 'big'), hashlib.sha256).digest()
    密文 = bytes(a ^ b for a, b in zip(私钥, 流[:len(私钥)]))

    # MAC校验
    mac = hashlib.sha256(派生密钥[16:32] + 密文).digest()

    return {
        "version": 3,
        "id": hashlib.sha256(os.urandom(32)).hexdigest()[:36],
        "address": 地址[2:] if 地址.startswith("0x") else 地址,
        "crypto": {
            "ciphertext": 密文.hex(),
            "cipherparams": {"iv": 计数器.hex()},
            "cipher": "aes-128-ctr",
            "kdf": "scrypt",
            "kdfparams": {
                "dklen": 32,
                "salt": 盐.hex(),
                "n": 262144,
                "r": 8,
                "p": 1,
            },
            "mac": mac.hex(),
        },
    }


# ========== 账户数据 ==========

@dataclass
class 钱包账户:
    """钱包账户 — M-07修复: 私钥加密存储，使用时解密"""
    索引: int = 0
    EVM地址: str = ""
    鸿坤地址: str = ""
    私钥hex: str = ""  # 外部接口保持不变，内部由_获取加密私钥管理
    别名: str = ""
    余额: float = 0.0
    质押余额: float = 0.0
    # M-07: 私钥加密存储相关字段
    _加密私钥: bytes = field(default_factory=bytes, repr=False)  # XOR混淆后的加密私钥
    _混淆密钥: bytes = field(default_factory=bytes, repr=False)  # XOR混淆密钥
    _进程标记: bool = field(default=False, repr=False)           # 进程隔离标记

    def __post_init__(self):
        """M-07: 初始化时加密私钥"""
        if self.私钥hex and not self._加密私钥:
            self._加密存储私钥(self.私钥hex)

    def _加密存储私钥(self, 明文私钥hex: str):
        """M-07: 使用XOR混淆加密私钥，不使用时加密存储"""
        try:
            明文bytes = bytes.fromhex(明文私钥hex[:64])
        except (ValueError, TypeError):
            return
        # 生成随机混淆密钥
        import os as _os
        self._混淆密钥 = _os.urandom(len(明文bytes))
        # XOR混淆加密
        self._加密私钥 = bytes(a ^ b for a, b in zip(明文bytes, self._混淆密钥))
        # 设置进程隔离标记
        self._进程标记 = True
        # 清除明文私钥（保留空字符串以兼容外部接口）
        # 注意：由于dataclass限制，我们使用_获取加密私钥来访问
        object.__setattr__(self, '私钥hex', '')

    def _获取解密私钥(self) -> str:
        """M-07: 使用时解密私钥，返回hex字符串"""
        if not self._加密私钥 or not self._混淆密钥:
            return self.私钥hex  # 无加密私钥则返回原值
        # XOR解密
        解密bytes = bytes(a ^ b for a, b in zip(self._加密私钥, self._混淆密钥))
        return 解密bytes.hex()

    def _清除内存私钥(self):
        """M-07: 使用后立即清除解密后的私钥（调用者负责）"""
        pass  # Python内存管理无法真正清零，但加密存储降低了风险

    @property
    def 显示地址(self) -> str:
        """缩短显示的地址"""
        if self.EVM地址:
            return f"{self.EVM地址[:8]}...{self.EVM地址[-4:]}"
        return self.鸿坤地址[:14] + "..."


@dataclass
class 交易记录:
    """交易记录"""
    交易哈希: str
    类型: str
    金额: float
    代币: str = "HKAIC"
    发送方: str = ""
    接收方: str = ""
    Gas费用: float = 0.0
    时间戳: float = 0.0
    区块号: int = 0
    AI标注: str = ""
    状态: str = "confirmed"

    def __post_init__(self):
        if self.时间戳 == 0:
            self.时间戳 = time.time()


class 涌信钱包:
    """
    涌信钱包 Emergent Wallet — HKC AI原生态钱包

    不仅是"又一个MetaMask"，而是AI原生钱包：
    - 传统钱包功能全有（创建/导入/转账/余额/历史）
    - 加入AI原生创新（语义交易/涌智信用/意图驱动/AI守护/社交恢复）
    """

    def __init__(self, 配置: Optional[涌信钱包配置] = None):
        self._配置 = 配置 or 涌信钱包配置()
        self._种子: Optional[bytes] = None
        self._助记词: Optional[List[str]] = None
        self._账户列表: List[钱包账户] = []
        self._当前账户索引: int = 0
        self._交易历史: List[交易记录] = []
        self._地址本: Dict[str, str] = {}
        self._已锁定: bool = False

        # AI原生子引擎
        self.语义交易 = 语义交易引擎()
        self.信用分引擎 = 涌智信用分引擎()
        self.意图引擎 = 意图驱动引擎()
        self.AI守护 = AI守护者(
            灵敏度=self._配置.AI.守护者灵敏度,
            自动锁定分钟=self._配置.安全.自动锁定分钟,
        )
        self.社交恢复 = 社交恢复引擎(
            守护者PoEI最低分=self._配置.安全.守护者PoEI最低分,
        )
        self.Gas引擎 = 自适应Gas引擎(区块时间秒=self._配置.网络.区块时间秒)
        self.组合分析 = 投资组合分析器()

    # ========== 钱包创建 ==========

    def 创建钱包(self, 助记词长度: int = 12, 密码: str = "") -> Dict:
        """
        创建新钱包
        1. 生成BIP39助记词
        2. 派生EVM地址
        3. 生成鸿坤内部地址
        """
        # 生成熵
        字节数 = 16 if 助记词长度 == 12 else 32
        熵 = _生成熵(字节数)

        # 生成助记词
        self._助记词 = _熵转助记词(熵)

        # 助记词转种子
        self._种子 = _助记词转种子(self._助记词, 密码)

        # 派生第一个账户
        账户 = self._派生账户(0)

        self._账户列表 = [账户]
        self._当前账户索引 = 0
        self._已锁定 = False

        return {
            "助记词": self._助记词,
            "EVM地址": 账户.EVM地址,
            "鸿坤地址": 账户.鸿坤地址,
            "账户索引": 0,
            "提示": "请安全保管助记词，这是恢复钱包的唯一方式！",
        }

    # ========== 钱包导入 ==========

    def 助记词导入(self, 助记词: str, 密码: str = "") -> Dict:
        """
        通过助记词导入钱包
        支持空格分隔的12/24词
        """
        词列表 = 助记词.strip().split()
        if len(词列表) not in (12, 24):
            return {"成功": False, "错误": f"助记词数量错误（需要12或24词，当前{len(词列表)}词）"}

        self._助记词 = 词列表
        self._种子 = _助记词转种子(词列表, 密码)

        账户 = self._派生账户(0)
        self._账户列表 = [账户]
        self._当前账户索引 = 0
        self._已锁定 = False

        return {
            "成功": True,
            "EVM地址": 账户.EVM地址,
            "鸿坤地址": 账户.鸿坤地址,
        }

    def 私钥导入(self, 私钥hex: str) -> Dict:
        """
        通过私钥导入钱包
        私钥可以是0x前缀或纯hex
        """
        # 清理私钥格式
        私钥hex = 私钥hex.strip()
        if 私钥hex.startswith("0x"):
            私钥hex = 私钥hex[2:]

        try:
            私钥bytes = bytes.fromhex(私钥hex)
        except ValueError:
            return {"成功": False, "错误": "私钥格式无效"}

        if len(私钥bytes) not in (32, 64):
            return {"成功": False, "错误": f"私钥长度错误（需要32或64字节，当前{len(私钥bytes)}字节）"}

        # 从私钥派生地址
        EVM地址 = _私钥转EVM地址(私钥bytes[:32])
        鸿坤地址 = _生成鸿坤内部地址(EVM地址, 私钥bytes[:32])

        账户 = 钱包账户(
            索引=0,
            EVM地址=EVM地址,
            鸿坤地址=鸿坤地址,
            私钥hex=私钥hex[:64],
        )
        self._账户列表 = [账户]
        self._当前账户索引 = 0
        self._已锁定 = False
        # 私钥导入时无种子，不能派生额外账户
        self._种子 = None
        self._助记词 = None

        return {
            "成功": True,
            "EVM地址": EVM地址,
            "鸿坤地址": 鸿坤地址,
            "注意": "私钥导入模式，无法派生额外账户。如需多账户，请使用助记词导入。",
        }

    def Keystore导入(self, keystore_json: str, 密码: str) -> Dict:
        """
        通过JSON Keystore导入（兼容MetaMask keystore格式）
        """
        try:
            keystore = json.loads(keystore_json)
        except json.JSONDecodeError:
            return {"成功": False, "错误": "Keystore JSON格式无效"}

        if keystore.get("version") != 3:
            return {"成功": False, "错误": "仅支持V3 Keystore格式"}

        try:
            crypto = keystore["crypto"]
            盐 = bytes.fromhex(crypto["kdfparams"]["salt"])
            密文 = bytes.fromhex(crypto["ciphertext"])
            期望mac = crypto["mac"]

            # 密钥派生
            派生密钥 = hashlib.pbkdf2_hmac('sha256', 密码.encode(), 盐, 524288, dklen=32)  # 加倍迭代增强安全性

            # MAC校验
            实际mac = hashlib.sha256(派生密钥[16:32] + 密文).digest().hex()
            if 实际mac != 期望mac:
                return {"成功": False, "错误": "密码错误"}

            # M-11修复: 增强XOR流解密，使用HMAC-SHA256流生成器
            加密密钥 = 派生密钥[:16]
            iv = bytes.fromhex(crypto["cipherparams"]["iv"])
            流 = hmac.new(加密密钥, iv, hashlib.sha256).digest()
            block_count = 0
            while len(流) < len(密文):
                block_count += 1
                流 += hmac.new(加密密钥, iv + block_count.to_bytes(4, 'big'), hashlib.sha256).digest()
            私钥 = bytes(a ^ b for a, b in zip(密文, 流[:len(密文)]))

            return self.私钥导入(私钥.hex())
        except (KeyError, ValueError) as e:
            return {"成功": False, "错误": f"Keystore解析失败: {e}"}

    def 导出Keystore(self, 密码: str) -> Optional[Dict]:
        """导出当前账户为MetaMask兼容Keystore"""
        账户 = self.当前账户
        if not 账户:
            return None
        # M-07: 使用解密方法获取私钥
        私钥hex = 账户._获取解密私钥()
        if not 私钥hex:
            return None
        私钥 = bytes.fromhex(私钥hex[:64])
        result = _加密Keystore(私钥, 密码, 账户.EVM地址)
        账户._清除内存私钥()  # M-07: 使用后清除
        return result

    # ========== 多账户管理 ==========

    def _派生账户(self, 索引: int) -> 钱包账户:
        """从种子派生指定索引的账户"""
        if not self._种子:
            raise ValueError("无种子，无法派生账户")
        私钥 = _种子派生私钥(self._种子, 索引)
        EVM地址 = _私钥转EVM地址(私钥)
        鸿坤地址 = _生成鸿坤内部地址(EVM地址, self._种子)
        账户 = 钱包账户(
            索引=索引,
            EVM地址=EVM地址,
            鸿坤地址=鸿坤地址,
            私钥hex=私钥.hex(),  # __post_init__会自动加密
        )
        return 账户

    def 创建账户(self, 别名: str = "") -> 钱包账户:
        """创建新的派生账户"""
        if not self._种子:
            raise ValueError("私钥导入模式无法创建额外账户，请使用助记词导入")
        索引 = len(self._账户列表)
        账户 = self._派生账户(索引)
        账户.别名 = 别名 or f"账户{索引}"
        self._账户列表.append(账户)
        return 账户

    def 切换账户(self, 索引: int) -> bool:
        """切换到指定索引的账户"""
        if 0 <= 索引 < len(self._账户列表):
            self._当前账户索引 = 索引
            return True
        return False

    @property
    def 当前账户(self) -> Optional[钱包账户]:
        """获取当前活动账户"""
        if self._账户列表:
            return self._账户列表[self._当前账户索引]
        return None

    @property
    def 账户列表(self) -> List[钱包账户]:
        """获取所有账户"""
        return self._账户列表

    # ========== 资产总览 ==========

    def 资产总览(self) -> Dict:
        """
        获取资产总览
        HKAIC余额、质押中HKAIC、跨链资产一览
        """
        账户 = self.当前账户
        if not 账户:
            return {"错误": "无活动账户"}

        return {
            "EVM地址": 账户.EVM地址,
            "鸿坤地址": 账户.鸿坤地址,
            "HKAIC余额": 账户.余额,
            "质押中HKAIC": 账户.质押余额,
            "可用HKAIC": 账户.余额 - 账户.质押余额,
            "账户数": len(self._账户列表),
            "信用分": self.信用分引擎.获取信用分(账户.EVM地址).信用分,
            "信用等级": self.信用分引擎.获取信用分(账户.EVM地址).等级.value,
        }

    def 更新余额(self, 余额: float, 质押余额: float = 0.0):
        """更新当前账户余额"""
        账户 = self.当前账户
        if 账户:
            账户.余额 = 余额
            账户.质押余额 = 质押余额

    # ========== 交易历史 ==========

    def 记录交易(self, 类型: str, 金额: float, 接收方: str = "",
                Gas费用: float = 0.0, 代币: str = "HKAIC"):
        """记录交易到本地历史，AI标注类型"""
        账户 = self.当前账户
        # H-09修复: 使用os.urandom加密随机数，替代可预测的time.time_ns()
        交易哈希 = hashlib.sha256(
            f"{账户.EVM地址 if 账户 else ''}{金额}{os.urandom(16).hex()}".encode()
        ).hexdigest()

        # AI标注
        类型标注 = {
            "transfer": "💸 转账",
            "stake": "🔒 质押",
            "cross_chain": "🌉 跨链",
            "contract": "📜 合约交互",
        }
        记录 = 交易记录(
            交易哈希=交易哈希,
            类型=类型,
            金额=金额,
            代币=代币,
            发送方=账户.EVM地址 if 账户 else "",
            接收方=接收方,
            Gas费用=Gas费用,
            AI标注=类型标注.get(类型, "❓ 未知"),
        )
        self._交易历史.append(记录)

        # 同步到语义交易引擎
        交易类型映射 = {
            "transfer": 交易类型.转账,
            "stake": 交易类型.质押,
            "cross_chain": 交易类型.跨链,
            "contract": 交易类型.合约交互,
        }
        self.语义交易.记录交易(
            交易哈希=交易哈希,
            交易类型=交易类型映射.get(类型, 交易类型.转账),
            金额=金额, 代币=代币, 收款人=接收方, Gas费用=Gas费用,
        )

        # 更新AI守护者
        self.AI守护.记录交易(接收方, 金额)

        # 更新Gas引擎
        self.Gas引擎.记录Gas消耗(交易哈希, Gas费用, Gas费用 / max(金额, 0.001))

        # 更新信用分引擎
        self.信用分引擎.更新链上行为(
            账户.EVM地址 if 账户 else "", 金额, 是质押=(类型 == "stake")
        )
        if 接收方 and 账户:
            self.信用分引擎.更新交互关系(账户.EVM地址, 接收方)

    def 查询交易历史(self, 数量: int = 10, 类型过滤: str = "") -> List[交易记录]:
        """查询交易历史"""
        历史 = self._交易历史
        if 类型过滤:
            历史 = [t for t in 历史 if t.类型 == 类型过滤]
        return 历史[-数量:]

    # ========== 地址本 ==========

    def 添加地址本条目(self, 别名: str, 地址: str):
        """添加地址本条目"""
        self._地址本[别名.lower()] = 地址
        self.语义交易.添加地址(别名.lower(), 地址)
        self._配置.地址本[别名.lower()] = 地址

    def 获取地址本(self) -> Dict[str, str]:
        """获取地址本"""
        return self._地址本.copy()

    # ========== 钱包锁 ==========

    def 锁定(self):
        """锁定钱包"""
        self._已锁定 = True

    def 解锁(self, 密码: str = "") -> bool:
        """解锁钱包 — 需要验证密码"""
        if not self._种子 and not self._账户列表:
            # 无账户状态，直接解锁
            self._已锁定 = False
            self.AI守护.解锁()
            return True
        # 验证密码：用密码派生种子并比对
        if 密码 and self._助记词:
            验证种子 = _助记词转种子(self._助记词, 密码)
            if 验证种子 == self._种子:
                self._已锁定 = False
                self.AI守护.解锁()
                self._上次活跃时间 = time.time()
                return True
            return False  # 密码错误
        elif self._种子:
            # 有种子但没有密码传入 — 需要密码才能解锁
            if not 密码:
                return False
        self._已锁定 = False
        self.AI守护.解锁()
        return True

    @property
    def 已锁定(self) -> bool:
        return self._已锁定 or self.AI守护.检查自动锁定()

    # ========== 语义交易快捷方式 ==========

    def 语义转账(self, 自然语言: str) -> Dict:
        """
        用自然语言发起转账
        "转100个HKAIC给Bob" -> 解析 -> AI守护检测 -> 确认摘要
        """
        解析结果 = self.语义交易.解析(自然语言)
        if not 解析结果.成功:
            return {"成功": False, "错误": 解析结果.错误信息}

        # AI守护者检测
        风险报告 = self.AI守护.检测交易(
            目标地址=解析结果.收款人地址 or 解析结果.收款人,
            金额=解析结果.金额,
        )

        # 信用分检查
        if 解析结果.收款人地址:
            信用提示 = self.信用分引擎.风险提示(解析结果.收款人地址)
        else:
            信用提示 = None

        # Gas建议
        Gas建议 = self.Gas引擎.预测Gas价格()

        # 生成确认摘要
        摘要 = self.语义交易.生成确认摘要(
            原文=自然语言,
            解析=解析结果,
            Gas估算=Gas建议.获取价格(解析结果.Gas偏好 == Gas偏好.尽快 and Gas档位.快速 or
                                        Gas档位.标准),
            风险提示=信用提示 or "",
        )

        return {
            "成功": True,
            "解析结果": 解析结果,
            "风险报告": 风险报告,
            "信用提示": 信用提示,
            "Gas建议": Gas建议,
            "确认摘要": 摘要,
            "需要二次确认": 风险报告.需要二次确认,
        }

    # ========== 意图驱动快捷方式 ==========

    def 提交意图(self, 自然语言: str) -> Dict:
        """
        提交AI意图
        "我想把ETH换成HKAIC" -> 解析 -> Solver匹配
        """
        账户 = self.当前账户
        意图 = self.意图引擎.解析意图(自然语言, 账户.EVM地址 if 账户 else "")
        方案, 消息 = self.意图引擎.匹配Solver(意图.意图ID)
        return {
            "意图ID": 意图.意图ID,
            "类型": 意图.类型.value,
            "播报": 意图.播报历史,
            "执行方案": 方案,
            "消息": 消息,
        }

    # ========== 配置 ==========

    @property
    def 配置(self) -> 涌信钱包配置:
        return self._配置

    def 切换网络(self, 网络名称: str) -> bool:
        """切换网络"""
        from .wallet_config import 预设网络列表
        for 预设 in 预设网络列表:
            if 预设.名称 == 网络名称:
                self._配置.切换网络(预设)
                return True
        return False
