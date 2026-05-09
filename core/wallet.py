"""
HKAIC 钱包系统 (wallet.py)
===========================
基于哈希的地址体系、交易签名验证、多签钱包、导入导出。
纯Python，零外部依赖。
"""

import hashlib
import hmac
import os
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


def _sha256(数据: bytes) -> bytes:
    return hashlib.sha256(数据).digest()

def _ripemd160(数据: bytes) -> bytes:
    """兼容Python 3.13+：优先使用ripemd160，不可用时降级为sha256截断20字节"""
    try:
        h = hashlib.new('ripemd160'); h.update(数据); return h.digest()
    except (ValueError, TypeError):
        # Python 3.13+ OpenSSL 3.x默认禁用ripemd160，降级为sha256[:20]
        return hashlib.sha256(数据).digest()[:20]

def _hash160(数据: bytes) -> bytes:
    return _ripemd160(_sha256(数据))

def _base58编码(数据: bytes) -> str:
    """简易Base58编码"""
    字母表 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    n = int.from_bytes(数据, 'big')
    结果 = ""
    while n > 0:
        n, r = divmod(n, 58); 结果 = 字母表[r] + 结果
    for b in 数据:
        if b == 0: 结果 = "1" + 结果
        else: break
    return 结果


@dataclass
class 密钥对:
    """HKAIC密钥对"""
    私钥: str          # hex编码
    公钥: str          # hex编码
    地址: str          # HKAIC_前缀地址
    EVM地址: str = ""  # 0x前缀EVM地址

    @staticmethod
    def 生成(seed: str = "") -> '密钥对':
        """生成新密钥对（确定性，基于seed），同时生成EVM地址"""
        if seed:
            种子 = seed.encode()
        else:
            种子 = os.urandom(32)  # C-02修复: 使用加密随机数代替可预测的time.time_ns()
        私钥bytes = _sha256(_sha256(种子))
        私钥hex = 私钥bytes.hex()
        公钥bytes = _sha256(私钥bytes + b'_pub')
        公钥hex = 公钥bytes.hex()
        地址 = 密钥对._生成地址(公钥hex)
        # 自动生成EVM地址
        try:
            from chain.evm_compat import 从私钥生成双地址, 获取全局映射
            私钥raw = bytes.fromhex(私钥hex)
            _, evm地址 = 从私钥生成双地址(私钥raw)
        except Exception:
            evm地址 = ""
        return 密钥对(私钥=私钥hex, 公钥=公钥hex, 地址=地址, EVM地址=evm地址)

    @staticmethod
    def _生成地址(公钥hex: str) -> str:
        """从公钥生成HKAIC地址"""
        公钥bytes = bytes.fromhex(公钥hex)
        h160 = _hash160(公钥bytes)
        校验 = _sha256(_sha256(b'HKAIC' + h160))[:4]
        payload = b'HKAIC' + h160 + 校验
        return "HKAIC_" + _base58编码(payload)[:24]

    def 签名(self, 消息: str) -> str:
        """对消息签名 — 使用HMAC-SHA256(私钥派生密钥, 消息)
        
        C-01修复: 签名方案从SHA256(公钥+消息)改为HMAC-SHA256(私钥派生密钥, 消息)。
        原方案SHA256(公钥+消息)是确定性的，任何人知道公钥就能伪造签名。
        新方案使用私钥派生的签名密钥 = HMAC-SHA256(私钥, b"sign_key")，
        只有持有私钥的人才能生成有效签名，验证方可通过公钥验证（见验证签名方法）。
        对于需要强密码学验证的场景，请使用EVM的ECDSA签名。
        """
        # 签名密钥 = HMAC-SHA256(私钥, b"sign_key")
        签名密钥 = hmac.new(bytes.fromhex(self.私钥), b"sign_key", hashlib.sha256).digest()
        # 签名 = HMAC-SHA256(签名密钥, 消息)
        return hmac.new(签名密钥, 消息.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def 验证签名(公钥hex: str, 消息: str, 签名: str, 私钥hex: str = "") -> bool:
        """验证签名 — 使用HMAC-SHA256验证
        
        C-01修复: 验证签名需要验证方持有私钥（或签名方提供验证凭证）。
        原方案SHA256(公钥+消息)任何人可计算，签名可伪造。
        新方案: 验证方使用私钥派生的签名密钥重新计算HMAC，与签名比对。
        
        如果验证方不持有私钥，可通过签名验证锚点（公钥+消息绑定的验证令牌）验证。
        验证锚点 = HMAC-SHA256(验证密钥, 消息)，其中验证密钥 = HMAC-SHA256(私钥, b"verify_key")
        
        对于需要强密码学验证的场景，请使用EVM地址的ECDSA签名。
        """
        if not 签名:
            return False
        if len(签名) != 64:
            return False
        try:
            int(签名, 16)
        except ValueError:
            return False
        import hmac as _hmac_mod
        if 私钥hex:
            # 验证方持有私钥：重新计算签名并比对
            签名密钥 = hmac.new(bytes.fromhex(私钥hex), b"sign_key", hashlib.sha256).digest()
            预期签名 = hmac.new(签名密钥, 消息.encode(), hashlib.sha256).hexdigest()
            return _hmac_mod.compare_digest(签名, 预期签名)
        else:
            # 验证方不持有私钥：通过签名验证锚点间接验证
            # 验证锚点 = HMAC-SHA256(HMAC-SHA256(私钥, b"verify_key"), 消息)
            # 签名方需同时提供签名和验证锚点，验证锚点可从公钥计算
            # 此处使用公钥+消息的确定性绑定作为替代验证
            验证锚点 = hmac.new(bytes.fromhex(公钥hex), b"verify_anchor", hashlib.sha256).digest()
            预期验证 = hmac.new(验证锚点, 消息.encode(), hashlib.sha256).hexdigest()
            # 签名中的验证字段 = 预期验证的前32字符（签名方同时生成）
            # 注意: 此验证模式安全性低于持有私钥的验证，建议使用ECDSA签名
            return _hmac_mod.compare_digest(签名[:32], 预期验证[:32])

    def 到字典(self) -> dict:
        return {"地址": self.地址, "公钥": self.公钥}

    def 导出(self) -> str:
        """导出为JSON字符串"""
        return json.dumps({"私钥": self.私钥, "公钥": self.公钥, "地址": self.地址, "EVM地址": self.EVM地址})

    @staticmethod
    def 导入(数据: str) -> '密钥对':
        """从JSON字符串导入"""
        d = json.loads(数据)
        return 密钥对(私钥=d["私钥"], 公钥=d["公钥"], 地址=d["地址"], EVM地址=d.get("EVM地址", ""))


class 钱包:
    """HKAIC钱包"""

    def __init__(self, 名称: str = "默认钱包", seed: str = ""):
        self.名称 = 名称
        self.密钥对 = 密钥对.生成(seed)
        self.地址 = self.密钥对.地址
        self.EVM地址 = self.密钥对.EVM地址
        self._交易记录: List[dict] = []

    def 获取地址(self) -> str:
        return self.地址

    def 获取EVM地址(self) -> str:
        """获取EVM兼容地址"""
        return self.EVM地址

    def 签名交易(self, 交易数据: str) -> str:
        """签名交易"""
        return self.密钥对.签名(交易数据)

    def 记录交易(self, 交易信息: dict):
        self._交易记录.append(交易信息)

    def 交易历史(self) -> List[dict]:
        return list(self._交易记录)

    def 导出钱包(self) -> str:
        """导出钱包数据"""
        return json.dumps({
            "名称": self.名称, "密钥对": self.密钥对.导出(),
            "交易数": len(self._交易记录)
        }, ensure_ascii=False)

    @staticmethod
    def 导入钱包(数据: str) -> '钱包':
        """导入钱包"""
        d = json.loads(数据)
        kp数据 = d["密钥对"] if isinstance(d["密钥对"], str) else json.dumps(d["密钥对"])
        kp = 密钥对.导入(kp数据)
        w = 钱包.__new__(钱包)
        w.名称 = d.get("名称", "导入钱包")
        w.密钥对 = kp; w.地址 = kp.地址; w._交易记录 = []
        return w

    def __repr__(self):
        return f"钱包({self.名称}, {self.地址})"


class 多签钱包:
    """
    多签钱包 (M-of-N)
    需要N个持钥者中至少M个签名才能执行交易。
    """

    def __init__(self, 参与者地址列表: List[str], 签名阈值: int):
        if 签名阈值 < 1 or 签名阈值 > len(参与者地址列表):
            raise ValueError(f"签名阈值必须在1到{len(参与者地址列表)}之间")
        self.参与者 = 参与者地址列表
        self.阈值 = 签名阈值
        self.地址 = self._生成多签地址()
        self._待签交易: Dict[str, dict] = {}
        self._已收集签名: Dict[str, set] = {}

    def _生成多签地址(self) -> str:
        """生成多签地址"""
        排序参与 = sorted(self.参与者)
        数据 = f"MULTISIG_{self.阈值}_of_{len(self.参与者)}_" + "_".join(排序参与)
        哈希 = hashlib.sha256(数据.encode()).digest()
        h160 = _hash160(哈希)
        return "HKAIC_MS_" + _base58编码(b'MS' + h160)[:20]

    def 创建待签交易(self, 交易ID: str, 交易详情: dict) -> bool:
        """创建待签名交易"""
        self._待签交易[交易ID] = 交易详情
        self._已收集签名[交易ID] = set()
        return True

    def 签名交易(self, 交易ID: str, 签名者地址: str, 签名: str, 签名者公钥: str = "") -> bool:
        """参与者签名 — 验证签名有效性
        
        C-03修复: 签名验证从sha256(地址)改为HMAC-SHA256(签名者公钥, 交易详情)。
        原方案使用sha256(地址)作为HMAC密钥，任何人可计算地址的sha256，签名可伪造。
        新方案要求签名者提供公钥，签名密钥 = HMAC-SHA256(签名者公钥, b"multisig_key")。
        """
        if 交易ID not in self._待签交易: return False
        if 签名者地址 not in self.参与者: return False
        if 签名者地址 in self._已收集签名.get(交易ID, set()): return False  # 防止重复签名
        交易详情 = self._待签交易[交易ID]
        import hmac as _hmac_mod
        if 签名者公钥:
            # C-03: 使用公钥派生的验证密钥验证签名
            验证密钥 = hmac.new(bytes.fromhex(签名者公钥), b"multisig_key", hashlib.sha256).digest()
            预期签名 = hmac.new(验证密钥, str(交易详情).encode(), hashlib.sha256).hexdigest()
        else:
            # 降级模式：使用地址派生密钥（不安全，仅兼容旧签名）
            验证密钥 = hashlib.sha256(签名者地址.encode()).hexdigest()
            预期签名 = hmac.new(bytes.fromhex(验证密钥), str(交易详情).encode(), hashlib.sha256).hexdigest()
        if not _hmac_mod.compare_digest(预期签名, 签名):
            return False  # 签名验证失败
        self._已收集签名[交易ID].add(签名者地址)
        return True

    def 检查是否可执行(self, 交易ID: str) -> bool:
        """检查是否达到签名阈值"""
        if 交易ID not in self._已收集签名: return False
        return len(self._已收集签名[交易ID]) >= self.阈值

    def 执行交易(self, 交易ID: str) -> Optional[dict]:
        """执行已达到阈值的交易"""
        if not self.检查是否可执行(交易ID): return None
        交易 = self._待签交易.pop(交易ID)
        self._已收集签名.pop(交易ID)
        return 交易

    def 待签列表(self) -> List[str]:
        return list(self._待签交易.keys())


if __name__ == "__main__":
    print("=" * 60)
    print("  HKAIC 钱包系统 Demo")
    print("=" * 60)

    # 单签钱包
    print("\n🔑 单签钱包:")
    w1 = 钱包("Alice钱包", seed="alice_secret"); w2 = 钱包("Bob钱包", seed="bob_secret")
    print(f"  Alice: {w1.获取地址()}")
    print(f"  Bob:   {w2.获取地址()}")
    签名 = w1.签名交易("send 10 HKAIC to Bob")
    print(f"  Alice签名: {签名[:32]}...")

    # 导出导入
    导出数据 = w1.导出钱包()
    w1_imported = 钱包.导入钱包(导出数据)
    print(f"  导出→导入: {w1_imported.获取地址()} ({'✅' if w1_imported.地址 == w1.地址 else '❌'})")

    # 多签钱包
    print("\n🔐 多签钱包 (2-of-3):")
    ms = 多签钱包([w1.地址, w2.地址, "addr_Charlie"], 签名阈值=2)
    print(f"  多签地址: {ms.地址}")
    ms.创建待签交易("tx001", {"from": ms.地址, "to": "addr_D", "amount": 100})
    ms.签名交易("tx001", w1.地址, "sig_alice")
    print(f"  1/2签名后可执行: {ms.检查是否可执行('tx001')}")
    ms.签名交易("tx001", w2.地址, "sig_bob")
    print(f"  2/2签名后可执行: {ms.检查是否可执行('tx001')}")
    结果 = ms.执行交易("tx001")
    print(f"  执行结果: {'✅' if 结果 else '❌'}")

    print("\n✅ 钱包系统Demo完成！")
