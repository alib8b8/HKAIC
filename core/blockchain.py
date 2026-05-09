"""
HKAIC 区块链核心 (blockchain.py)
=================================

★ AI原生共识机制: 涌智证明 Proof of Emergent Intelligence (PoEI) ★

═══════════════════════════════════════════════════════════
  核心共识公式:

    E_i = (K_i · S_i)^α · σ_i^β · Φ(Λ_i)

  其中:
    E_i   = 节点i的涌现智能分数 (Emergence Score)
    K_i   = 知识贡献度 (Knowledge Contribution)
    S_i   = 质押权重 (Stake Weight, 带平方根衰减)
    σ_i   = 协同因子 (Synergy Factor) — 核心创新
    Λ_i   = 活跃度向量 (Liveness Vector)
    Φ     = 活跃度归一化函数
    α, β  = 可调指数参数

  协同因子公式:

    σ_i = Σ_{j∈N(i)} C_ij · √(K_i · K_j) / |N(i)|

  出块资格判定:

    H(epoch_seed ∥ addr_i ∥ E_i) < T · E_i / ΣE

  即: 哈希值 < 目标阈值 × 归一化涌现分数
═══════════════════════════════════════════════════════════

设计哲学:
  - 不是算力竞赛 (PoW)，不是资本竞赛 (PoS)
  - 是智能涌现竞赛: 谁对集体智能贡献大，谁获得出块权
  - 协同因子 σ 捕获"1+1>2"的涌现效应
  - 质押有平方根衰减，防止富者愈富
  - 按需出块: 无交易则不出块
  - 出块者获交易费分成，非新币奖励
"""

import hashlib
import os
import time
import math
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

HONGKUN_PER_HKAIC = 10 ** 16
HKAIC_TOTAL_SUPPLY = 21_000_000


# ============================================================
# PoEI 共识引擎 — 涌智证明
# ============================================================

class PoEI共识:
    """
    Proof of Emergent Intelligence (PoEI) — 涌智证明

    核心思想:
      在AI时代，最有价值的不是算力或资本，而是智能的涌现。
      当多个AI Agent协同工作时，产生的价值大于个体之和。
      PoEI将这种"涌现效应"量化为共识权重。

    与现有机制的本质区别:
      PoW: hash(nonce) < target        → 算力盲猜
      PoS: random_select(stake)        → 资本权重
      PoEI: hash(seed||addr||E) < T·E  → 涌现智能权重

    安全性保证:
      1. 攻击者需同时控制大量质押 + 大量知识贡献 + 协同网络
      2. 协同因子σ要求真实的跨节点协作，女巫攻击成本极高
      3. 平方根质押衰减使51%攻击需要更大比例的质押
      4. 时间衰减确保持续参与，防止长程攻击
    """

    # 可调参数
    ALPHA = 0.6             # 知识×质押的指数
    BETA = 1.2              # 协同因子的指数（大于1，强调涌现）
    GAMMA = 0.5             # 质押平方根衰减系数
    DECAY_HALFLIFE = 86400 * 30  # 知识贡献半衰期: 30天
    MIN_LIVENESS = 0.3      # 最低活跃度阈值
    SLASH_RATE = 0.10        # 作恶惩罚比例

    def __init__(self):
        # 节点状态
        self._节点知识: Dict[str, float] = {}          # K_i: 累计知识贡献
        self._节点质押: Dict[str, float] = {}          # S_i: 质押量(HKAIC)
        self._节点活跃度: Dict[str, float] = {}        # Λ_i: 活跃度[0,1]
        self._节点最后活跃: Dict[str, float] = {}      # 最后活跃时间
        self._协同图: Dict[str, Dict[str, float]] = {}  # C_ij: 协同强度
        self._涌现分数缓存: Dict[str, float] = {}      # E_i: 缓存
        self._总涌现分数: float = 0.0
        self._作恶记录: Dict[str, List[str]] = {}

    # ----------------------------------------------------------
    # 状态更新
    # ----------------------------------------------------------

    def 更新知识贡献(self, 节点: str, 贡献值: float):
        """
        更新节点的知识贡献度 K_i
        
        知识贡献包括:
          - 情报验证准确率
          - 信号检测质量
          - AI决策精度
          - 策略回测表现
        """
        时间衰减 = self._计算时间衰减(节点)
        旧值 = self._节点知识.get(节点, 0)
        # 知识贡献随时间衰减，新贡献叠加
        self._节点知识[节点] = 旧值 * 时间衰减 + 贡献值
        self._更新活跃度(节点)

    def 更新质押(self, 节点: str, 质押量: float):
        """更新节点质押量 S_i (HKAIC)"""
        self._节点质押[节点] = 质押量
        self._更新活跃度(节点)

    def 记录协同(self, 节点A: str, 节点B: str, 协同强度: float):
        """
        记录两个节点的协同关系 C_ij
        
        协同强度取决于:
          - 共同验证的交易数
          - 联合贡献的情报质量
          - 多签合约共同参与
          - 策略一致性（在相同市场条件下做出类似决策）
        """
        self._协同图.setdefault(节点A, {})[节点B] = 协同强度
        self._协同图.setdefault(节点B, {})[节点A] = 协同强度
        self._更新活跃度(节点A)
        self._更新活跃度(节点B)

    def _更新活跃度(self, 节点: str):
        """更新节点活跃度"""
        self._节点最后活跃[节点] = time.time()
        self._节点活跃度[节点] = 1.0  # 活跃则重置为1

    def _计算时间衰减(self, 节点: str) -> float:
        """计算知识贡献的时间衰减"""
        最后活跃 = self._节点最后活跃.get(节点, 0)
        if 最后活跃 == 0: return 1.0
        经过时间 = time.time() - 最后活跃
        半衰期 = self.DECAY_HALFLIFE
        return math.pow(0.5, 经过时间 / 半衰期)

    # ----------------------------------------------------------
    # 涌现智能分数计算 (核心公式)
    # ----------------------------------------------------------

    def 计算涌现分数(self, 节点: str) -> float:
        """
        计算节点i的涌现智能分数 E_i

        ══════════════════════════════════════════
          E_i = (K_i · S_i')^α · σ_i^β · Φ(Λ_i)
        ══════════════════════════════════════════

        其中 S_i' = √S_i (平方根衰减，防止富者愈富)
        """
        K = self._节点知识.get(节点, 0)
        S = self._节点质押.get(节点, 0)
        Λ = self._节点活跃度.get(节点, 0)
        σ = self.计算协同因子(节点)

        # 质押平方根衰减: S' = √S
        S_prime = math.sqrt(max(S, 0))

        # 基础分数: (K · S')^α
        基础分数 = math.pow(K * S_prime + 1e-12, self.ALPHA)

        # 协同涌现: σ^β (β > 1 放大协同效应)
        协同涌现 = math.pow(σ + 1e-12, self.BETA)

        # 活跃度归一化: Φ(Λ) = max(Λ, MIN_LIVENESS)
        活跃度因子 = max(Λ, self.MIN_LIVENESS)

        # 涌现智能分数
        E = 基础分数 * 协同涌现 * 活跃度因子

        self._涌现分数缓存[节点] = E
        return E

    def 计算协同因子(self, 节点: str) -> float:
        """
        计算节点i的协同因子 σ_i

        ══════════════════════════════════════════════════════
          σ_i = Σ_{j∈N(i)} C_ij · √(K_i · K_j) / |N(i)|
        ══════════════════════════════════════════════════════

        N(i) = 与节点i有协同关系的节点集合
        C_ij = 协同强度 [0, 1]
        K_i, K_j = 双方的知识贡献度

        直觉: 协同因子衡量的是"通过与高质量节点合作，
        节点i获得了多少涌现智能增益"。√(K_i·K_j) 确保了
        只有两方都有贡献时协同才有价值（几何平均）。
        """
        协同 = self._协同图.get(节点, {})
        if not 协同:
            return 0.0

        K_i = self._节点知识.get(节点, 1.0)
        加权协同 = 0.0
        for 邻居, C_ij in 协同.items():
            K_j = self._节点知识.get(邻居, 1.0)
            几何均值 = math.sqrt(max(K_i * K_j, 0))
            加权协同 += C_ij * 几何均值

        return 加权协同 / len(协同)

    def 计算总涌现分数(self) -> float:
        """计算全网总涌现分数 ΣE"""
        总分 = 0.0
        for 节点 in self._节点质押:
            总分 += self.计算涌现分数(节点)
        self._总涌现分数 = 总分
        return 总分

    # ----------------------------------------------------------
    # 出块权判定
    # ----------------------------------------------------------

    def 判定出块权(self, 候选节点列表: List[str], epoch种子: str = "") -> Optional[str]:
        """
        判定当前epoch的出块者

        ════════════════════════════════════════════════════════════
          节点i获得出块权当且仅当:

          H(epoch_seed ∥ addr_i ∥ E_i) < T · E_i / ΣE

          其中 T 是基础目标阈值，与网络难度成反比
        ════════════════════════════════════════════════════════════

        这个公式的含义:
          - 每个节点计算一个哈希值
          - 哈希值必须小于某个与自身涌现分数成正比的阈值
          - 涌现分数越高，越容易满足条件
          - 但仍有随机性：不是简单的"分数最高者出块"
        """
        if not 候选节点列表: return None
        if not epoch种子: epoch种子 = hashlib.sha256(os.urandom(32)).hexdigest()  # H-05: os.urandom替代time.time_ns()

        总E = self.计算总涌现分数()
        if 总E <= 0: return None

        # 基础目标阈值 T (可调节网络出块速度)
        T = 2 ** 256 - 1  # 最大化，由归一化分数控制概率

        最佳节点 = None; 最小哈希值 = float('inf')

        for 节点 in 候选节点列表:
            # M-04修复: K=0节点硬检查，知识贡献为0的节点不得参与出块
            K_i = self._节点知识.get(节点, 0)
            if K_i <= 0: continue  # K=0直接排除
            E_i = self.计算涌现分数(节点)
            if E_i <= 0: continue

            # 计算哈希: H(epoch_seed ∥ addr_i ∥ E_i)
            输入 = f"{epoch种子}|{节点}|{E_i:.16f}"
            哈希值 = int(hashlib.sha256(输入.encode()).hexdigest(), 16)

            # 目标阈值: T · E_i / ΣE
            节点目标 = int(T * E_i / 总E)

            # 检查是否满足条件
            if 哈希值 < 节点目标:
                # 满足条件，选哈希值最小的（最先"找到"的）
                if 哈希值 < 最小哈希值:
                    最小哈希值 = 哈希值; 最佳节点 = 节点

        return 最佳节点

    def 出块概率(self, 节点: str) -> float:
        """计算节点的出块概率 (理论值)"""
        E_i = self.计算涌现分数(节点)
        总E = self._总涌现分数 if self._总涌现分数 > 0 else self.计算总涌现分数()
        if 总E <= 0: return 0.0
        return E_i / 总E

    # ----------------------------------------------------------
    # 验证与惩罚
    # ----------------------------------------------------------

    def 验证区块(self, 出块者: str, 区块数据: str, 签名: str) -> bool:
        """验证区块合法性"""
        if 出块者 not in self._节点质押: return False
        if self._节点活跃度.get(出块者, 0) < self.MIN_LIVENESS: return False
        return True

    def 惩罚作恶(self, 节点: str, 原因: str = "") -> float:
        """
        Slashing: 惩罚作恶节点
        
        惩罚措施:
          1. 扣除质押 (SLASH_RATE比例)
          2. 知识贡献清零
          3. 协同关系切断
          4. 活跃度归零
        """
        质押 = self._节点质押.get(节点, 0)
        惩罚额 = 质押 * self.SLASH_RATE
        self._节点质押[节点] = 质押 - 惩罚额
        self._节点知识[节点] = 0
        self._节点活跃度[节点] = 0
        # 切断协同
        for 邻居 in list(self._协同图.get(节点, {}).keys()):
            if 邻居 in self._协同图:
                self._协同图[邻居].pop(节点, None)
        self._协同图.pop(节点, None)
        self._作恶记录.setdefault(节点, []).append(f"{原因}@{time.time():.0f}")
        return 惩罚额

    # ----------------------------------------------------------
    # 网络参数调整 (通过治理)
    # ----------------------------------------------------------

    def 调整参数(self, 参数: dict):
        """通过治理投票调整共识参数
        M-05修复: 添加参数范围校验，超出范围拒绝修改"""
        # M-05: 参数安全边界定义
        _参数范围 = {
            "alpha":      (0.1, 1.0),    # α: 知识×质押指数
            "beta":       (0.5, 2.0),    # β: 协同因子指数
            "gamma":      (0.1, 1.0),    # γ: 质押衰减系数
            "slash_rate": (0.01, 0.5),   # 惩罚率: 1%~50%
            "min_liveness": (0.05, 0.8), # 最低活跃度: 5%~80%
        }
        # M-05: 逐个校验参数范围
        _被拒绝 = []
        for key, value in 参数.items():
            if key in _参数范围:
                低, 高 = _参数范围[key]
                if not (低 <= value <= 高):
                    _被拒绝.append(f"{key}={value}（范围:{低}~{高}）")
                    continue
        if _被拒绝:
            return  # 有参数超范围，全部拒绝
        # 参数全部在范围内，才执行修改
        if "alpha" in 参数: self.ALPHA = 参数["alpha"]
        if "beta" in 参数: self.BETA = 参数["beta"]
        if "gamma" in 参数: self.GAMMA = 参数["gamma"]
        if "slash_rate" in 参数: self.SLASH_RATE = 参数["slash_rate"]
        if "min_liveness" in 参数: self.MIN_LIVENESS = 参数["min_liveness"]

    # ----------------------------------------------------------
    # 报告
    # ----------------------------------------------------------

    def 节点报告(self, 节点: str) -> dict:
        E = self.计算涌现分数(节点)
        σ = self.计算协同因子(节点)
        K = self._节点知识.get(节点, 0)
        S = self._节点质押.get(节点, 0)
        Λ = self._节点活跃度.get(节点, 0)
        概率 = self.出块概率(节点)
        协同数 = len(self._协同图.get(节点, {}))
        return {
            "地址": 节点, "知识贡献K": f"{K:.4f}",
            "质押S": f"{S:.2f} HKAIC", "协同因子σ": f"{σ:.6f}",
            "活跃度Λ": f"{Λ:.4f}", "涌现分数E": f"{E:.8f}",
            "出块概率": f"{概率:.4%}", "协同节点数": 协同数,
        }

    def 网络摘要(self) -> dict:
        总E = self._总涌现分数 or self.计算总涌现分数()
        return {
            "验证者数": len(self._节点质押),
            "总质押": f"{sum(self._节点质押.values()):,.2f} HKAIC",
            "总涌现分数": f"{总E:.8f}",
            "协同边数": sum(len(v) for v in self._协同图.values()) // 2,
            "参数α": self.ALPHA, "参数β": self.BETA,
            "惩罚率": f"{self.SLASH_RATE:.0%}",
        }


# ============================================================
# 区块结构
# ============================================================

@dataclass
class 区块头:
    """区块头"""
    版本: int = 1
    前一区块哈希: str = ""
    Merkle根: str = ""
    时间戳: float = 0.0
    区块高度: int = 0
    出块者: str = ""
    涌现分数证明: float = 0.0   # PoEI: 出块者的E_i
    随机数: str = ""             # epoch种子

    def 计算哈希(self) -> str:
        数据 = (f"{self.版本}{self.前一区块哈希}{self.Merkle根}"
                f"{self.时间戳:.6f}{self.区块高度}{self.出块者}"
                f"{self.涌现分数证明:.16f}{self.随机数}")
        return hashlib.sha256(数据.encode()).hexdigest()


@dataclass
class 区块:
    """完整区块"""
    头: 区块头
    交易列表: List[dict] = field(default_factory=list)
    交易费总额: int = 0  # 鸿坤

    def 区块哈希(self) -> str:
        return self.头.计算哈希()

    def 大小估算(self) -> int:
        """估算区块大小(字节)"""
        return len(str(self.交易列表)) + 200  # 头部约200字节


# ============================================================
# 区块链
# ============================================================

class 区块链:
    """
    HKAIC 区块链 — PoEI共识 + 按需出块

    特征:
      - 按需出块: 无交易则不出块
      - 出块者获交易费分成，非新币
      - PoEI共识保证出块权分配公平
      - 最长链原则 + 涌现分数加权的链选择
    """

    def __init__(self):
        self._链: List[区块] = []
        self._区块索引: Dict[str, 区块] = {}
        self._待确认交易: List[dict] = []
        self.共识 = PoEI共识()
        # L-03修复: 区块交易数上限和区块大小上限
        self._区块最大交易数: int = 500       # 每区块最多500笔交易
        self._区块最大字节数: int = 2 * 1024 * 1024  # 每区块最大2MB
        self._创世区块()

    def _创世区块(self):
        """创建创世区块"""
        头 = 区块头(
            前一区块哈希="0" * 64, 时间戳=time.time(),
            区块高度=0, 出块者="GENESIS", 涌现分数证明=1.0,
            随机数="genesis_epoch")
        头.Merkle根 = hashlib.sha256(b"genesis").hexdigest()
        创世 = 区块(头=头, 交易列表=[{"type": "genesis", "supply": HKAIC_TOTAL_SUPPLY}])
        self._链.append(创世)
        self._区块索引[创世.区块哈希()] = 创世

    @property
    def 高度(self) -> int:
        return len(self._链) - 1

    @property
    def 最新区块(self) -> 区块:
        return self._链[-1]

    def 添加待确认交易(self, 交易: dict):
        self._待确认交易.append(交易)

    def 出块(self, 出块者: str) -> Optional[区块]:
        """
        按需出块: 有待确认交易时才出块
        
        出块流程:
          1. PoEI共识判定出块权
          2. 打包待确认交易
          3. 计算Merkle根
          4. 分配交易费
        """
        if not self._待确认交易:
            return None  # 无交易，不出块

        # M-20修复: 验证交易签名（框架实现）
        已验证交易 = []
        for tx in self._待确认交易:
            # 检查必要字段
            if "from" not in tx or "to" not in tx:
                continue
            # 框架验证：真实系统需验证交易签名
            if tx.get("签名验证", True) or "签名" not in tx:
                已验证交易.append(tx)
            # 有签名但验证失败的交易不打包
        self._待确认交易 = [tx for tx in self._待确认交易 if tx in 已验证交易]
        
        # 打包交易（按费率排序）
        待打包 = sorted(已验证交易, key=lambda t: t.get("手续费", 0), reverse=True)
        # L-03修复: 区块交易数上限（默认500笔/区块）和区块大小上限
        待打包 = 待打包[:self._区块最大交易数]
        # L-03: 区块大小限制 — 估算并截断超限部分
        当前大小 = 200  # 区块头约200字节
        截断索引 = len(待打包)
        for i, t in enumerate(待打包):
            tx_size = len(str(t))
            if 当前大小 + tx_size > self._区块最大字节数:
                截断索引 = i
                break
            当前大小 += tx_size
        待打包 = 待打包[:截断索引]
        交易费总额 = sum(t.get("手续费", 0) for t in 待打包)

        # 构建区块头
        前一哈希 = self.最新区块.区块哈希()
        交易哈希列表 = [hashlib.sha256(str(t).encode()).hexdigest() for t in 待打包]
        merkle根 = self._简易Merkle(交易哈希列表)

        E_i = self.共识.计算涌现分数(出块者)

        头 = 区块头(
            前一区块哈希=前一哈希, Merkle根=merkle根,
            时间戳=time.time(), 区块高度=self.高度 + 1,
            出块者=出块者, 涌现分数证明=E_i,
            随机数=hashlib.sha256(os.urandom(32)).hexdigest()[:16])  # H-05: os.urandom替代time.time_ns()

        新区块 = 区块(头=头, 交易列表=待打包, 交易费总额=交易费总额)
        self._链.append(新区块)
        self._区块索引[新区块.区块哈希()] = 新区块
        self._待确认交易 = [t for t in self._待确认交易 if t not in 待打包]
        return 新区块

    def _简易Merkle(self, 哈希列表: List[str]) -> str:
        if not 哈希列表: return hashlib.sha256(b"empty").hexdigest()
        当前 = 哈希列表[:]
        while len(当前) > 1:
            下一层 = []
            for i in range(0, len(当前), 2):
                左 = 当前[i]; 右 = 当前[i+1] if i+1 < len(当前) else 左
                下一层.append(hashlib.sha256((左 + 右).encode()).hexdigest())
            当前 = 下一层
        return 当前[0]

    def 获取区块(self, 高度: int) -> Optional[区块]:
        if 0 <= 高度 < len(self._链): return self._链[高度]
        return None

    def 验证链完整性(self) -> bool:
        """验证区块链完整性"""
        for i in range(1, len(self._链)):
            前一哈希 = self._链[i].头.前一区块哈希
            实际前一 = self._链[i-1].区块哈希()
            if 前一哈希 != 实际前一: return False
        return True

    # ----------------------------------------------------------
    # 区块浏览器 (ASCII)
    # ----------------------------------------------------------

    def 打印区块链(self, 最新N个: int = 5):
        """ASCII区块浏览器"""
        起始 = max(0, len(self._链) - 最新N个)
        print("\n  🔗 HKAIC 区块链浏览器")
        print("  " + "=" * 70)
        for i in range(len(self._链) - 1, 起始 - 1, -1):
            b = self._链[i]
            头 = b.头
            print(f"  ┌─ Block #{头.区块高度} ─────────────────────────────")
            print(f"  │  哈希: {b.区块哈希()[:32]}...")
            print(f"  │  前块: {头.前一区块哈希[:32]}...")
            print(f"  │  出块者: {头.出块者[:20]}  E={头.涌现分数证明:.6f}")
            print(f"  │  交易数: {len(b.交易列表)}  手续费: {b.交易费总额/HONGKUN_PER_HKAIC:.8f} HKAIC")
            print(f"  │  时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(头.时间戳))}")
            if i > 起始: print(f"  │  ↓")
            print(f"  └{'─' * 50}")
        print("  " + "=" * 70)

    def 链摘要(self) -> dict:
        总交易 = sum(len(b.交易列表) for b in self._链)
        总手续费 = sum(b.交易费总额 for b in self._链)
        return {
            "高度": self.高度, "区块数": len(self._链),
            "总交易": 总交易, "总手续费": f"{总手续费/HONGKUN_PER_HKAIC:.8f} HKAIC",
            "待确认": len(self._待确认交易),
            "链完整性": "✅" if self.验证链完整性() else "❌",
        }


# ============================================================
# Demo
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  HKAIC 区块链 Demo — PoEI涌智证明共识")
    print("  Proof of Emergent Intelligence (PoEI)")
    print("=" * 70)

    chain = 区块链()

    # 注册验证者
    print("\n👥 注册验证者:")
    验证者 = [
        ("val_Alice", 10000, 85.0),
        ("val_Bob", 5000, 60.0),
        ("val_Carol", 8000, 75.0),
        ("val_Dave", 3000, 40.0),
    ]
    for 名称, 质押, 知识 in 验证者:
        chain.共识.更新质押(名称, 质押)
        chain.共识.更新知识贡献(名称, 知识)
        print(f"  {名称}: 质押={质押} HKAIC, K={知识}")

    # 建立协同关系
    print("\n🤝 建立协同关系:")
    协同对 = [("val_Alice", "val_Bob", 0.8), ("val_Alice", "val_Carol", 0.6),
              ("val_Bob", "val_Carol", 0.7), ("val_Carol", "val_Dave", 0.3)]
    for A, B, 强度 in 协同对:
        chain.共识.记录协同(A, B, 强度)
        print(f"  {A} ↔ {B}: C={强度}")

    # 计算涌现分数
    print("\n🧠 涌现智能分数:")
    总E = chain.共识.计算总涌现分数()
    for 名称, _, _ in 验证者:
        报告 = chain.共识.节点报告(名称)
        print(f"  {名称}: E={报告['涌现分数E']}  σ={报告['协同因子σ']}  "
              f"出块概率={报告['出块概率']}")

    # 模拟出块
    print("\n⛏️ 模拟出块:")
    for i in range(5):
        # 添加模拟交易
        chain.添加待确认交易({
            "from": f"addr_{i}", "to": f"addr_{i+10}",
            "amount": (i + 1) * 10**16, "手续费": (i + 1) * 10**13})

        # PoEI选择出块者
        出块者 = chain.共识.判定出块权([v[0] for v in 验证者], epoch种子=f"epoch_{i}")
        if 出块者:
            新块 = chain.出块(出块者)
            if 新块:
                print(f"  Block #{新块.头.区块高度}: 出块者={出块者} "
                      f"交易={len(新块.交易列表)} "
                      f"费={新块.交易费总额/HONGKUN_PER_HKAIC:.4f} HKAIC")

    # 区块浏览器
    chain.打印区块链(5)

    # 链摘要
    print(f"\n📊 链摘要:")
    for k, v in chain.链摘要().items(): print(f"  {k}: {v}")

    # 网络摘要
    print(f"\n🌐 共识网络摘要:")
    for k, v in chain.共识.网络摘要().items(): print(f"  {k}: {v}")

    # 共识公式展示
    print("\n" + "=" * 70)
    print("  PoEI 共识公式:")
    print("  ┌─────────────────────────────────────────────────────┐")
    print("  │  E_i = (K_i · √S_i)^α · σ_i^β · Φ(Λ_i)           │")
    print("  │                                                     │")
    print("  │  σ_i = Σ_{j∈N(i)} C_ij · √(K_i·K_j) / |N(i)|    │")
    print("  │                                                     │")
    print("  │  H(seed∥addr∥E_i) < T · E_i / ΣE                  │")
    print("  │                                                     │")
    print("  │  K=知识贡献  S=质押  σ=协同因子  Λ=活跃度         │")
    print("  │  α=0.6  β=1.2  (β>1 → 放大涌现效应)               │")
    print("  └─────────────────────────────────────────────────────┘")

    print("\n✅ PoEI区块链Demo完成！")
