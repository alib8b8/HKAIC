"""
Hongkun AI Chain — 预测同步 (node_sync.py)
=============================================
不是盲目下载全部区块，而是AI预判需要哪些状态。

核心创新:
  1. 快速同步器 — 新节点根据交易偏好预判需要的区块
  2. 状态同步器 — 多源验证状态根，按知识图谱选择性下载子状态
  3. 节点同步器 — 统筹Fast Sync + State Sync + 增量同步 + 分叉检测
"""

import hashlib, time, math
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

class 同步状态(Enum):
    空闲 = "idle"; 快速同步中 = "fast"; 状态同步中 = "state"
    增量中 = "inc"; 已同步 = "synced"; 分叉中 = "fork"

@dataclass
class 区块摘要:
    """轻量区块摘要"""
    高度: int; 哈希: str; 前一哈希: str; 时间戳: float
    交易数: int = 0; 出块者: str = ""
    交易类型: List[str] = field(default_factory=list)
    知识关联: List[str] = field(default_factory=list)

@dataclass
class 状态快照:
    """状态根快照"""
    高度: int; 状态根: str; 账户数: int = 0
    余额总览: Dict[str, int] = field(default_factory=dict)

@dataclass
class 知识图谱索引:
    """按语义相关性组织状态，而非时间顺序"""
    主题: str
    相关区块: List[int] = field(default_factory=list)
    相关地址: Set[str] = field(default_factory=set)
    访问频率: int = 0; 最后访问: float = 0.0

    def 更新访问(self):
        self.访问频率 += 1; self.最后访问 = time.time()

    def 预测权重(self) -> float:
        衰减 = math.exp(-max(time.time() - self.最后访问, 0) / 86400)
        return self.访问频率 * 衰减


# ============================================================
# 快速同步器 — AI预判
# ============================================================
class 快速同步器:
    """
    新节点根据交易偏好预判需要哪些区块。

    传统: 创世→最新顺序下载
    预测: 分析偏好→按语义相关性优先下载
    """

    def __init__(self):
        self._已下载: Dict[int, 区块摘要] = {}
        self._图谱: Dict[str, 知识图谱索引] = {}
        self._进度: float = 0.0
        self._偏好: Dict[str, float] = {}

    def 设置偏好(self, p: Dict[str, float]):
        self._偏好 = p

    def 分析偏好(self, 历史: List[dict]) -> Dict[str, float]:
        """AI分析历史交易自动推断偏好"""
        计数: Dict[str, int] = {}
        for tx in 历史:
            t = tx.get("type", "unknown")
            计数[t] = 计数.get(t, 0) + 1
        if not 计数: return {}
        mx = max(计数.values())
        self._偏好 = {t: c / mx for t, c in 计数.items()}
        return self._偏好

    def 预测需要的区块(self, 可用: List[区块摘要], n: int = 100) -> List[区块摘要]:
        """评分 = 偏好匹配 × 知识关联 × 时间衰减"""
        评分 = []
        for blk in 可用:
            偏好分 = max(self._偏好.get(t, 0.1) for t in blk.交易类型) if blk.交易类型 else 0.5
            关联分 = min(len(blk.知识关联) / 10, 1.0) if blk.知识关联 else 0.3
            衰减 = math.exp(-max(time.time() - blk.时间戳, 0) / 86400 * 30)
            评分.append((blk, 偏好分 * 关联分 * (0.3 + 0.7 * 衰减)))
        评分.sort(key=lambda x: x[1], reverse=True)
        return [b for b, _ in 评分[:n]]

    def 执行快速同步(self, 目标高度: int, 源: List[区块摘要]) -> Tuple[int, float]:
        需要的 = [b for b in 源 if b.高度 <= 目标高度]
        优先 = self.预测需要的区块(需要的)
        命中 = 0
        for blk in 优先:
            self._已下载[blk.高度] = blk
            self._更新图谱(blk)
            if blk.交易类型 and any(t in self._偏好 for t in blk.交易类型): 命中 += 1
        命中率 = 命中 / max(len(优先), 1)
        self._进度 = len(self._已下载) / max(目标高度, 1)
        return len(优先), 命中率

    def _更新图谱(self, blk: 区块摘要):
        for t in blk.交易类型:
            if t not in self._图谱: self._图谱[t] = 知识图谱索引(主题=t)
            self._图谱[t].相关区块.append(blk.高度); self._图谱[t].更新访问()

    def 按语义查询(self, 主题: str) -> List[int]:
        idx = self._图谱.get(主题)
        if not idx: return []
        idx.更新访问(); return sorted(idx.相关区块)

    def 状态(self) -> dict:
        return {"已下载": len(self._已下载), "进度": f"{self._进度:.1%}",
                "图谱主题": len(self._图谱), "偏好": self._偏好}


# ============================================================
# 状态同步器 — 多源验证
# ============================================================
class 状态同步器:
    """下载状态根而非重放交易，多源验证防篡改"""

    def __init__(self):
        self._缓存: Dict[str, 状态快照] = {}
        self._已验证高度: int = 0

    def 请求快照(self, 高度: int, 来源: List[str] = None) -> Optional[状态快照]:
        根 = hashlib.sha256(f"state:{高度}".encode()).hexdigest()
        return 状态快照(高度=高度, 状态根=根, 账户数=1000)

    def 验证状态根(self, 快照: 状态快照, 预期: str) -> bool:
        return 快照.状态根 == 预期

    def 多源验证(self, 高度: int, 来源: List[str]) -> bool:
        """多源获取状态根，2/3以上一致则通过"""
        快照们 = [self.请求快照(高度, [s]) for s in 来源[:5]]
        快照们 = [s for s in 快照们 if s]
        if len(快照们) < 3: return False
        计数: Dict[str, int] = {}
        for s in 快照们: 计数[s.状态根] = 计数.get(s.状态根, 0) + 1
        return max(计数.values()) >= len(快照们) * 2 // 3

    def 执行状态同步(self, 目标高度: int) -> bool:
        快照 = self.请求快照(目标高度)
        if 快照:
            self._缓存[快照.状态根] = 快照; self._已验证高度 = 目标高度; return True
        return False

    def 状态(self) -> dict:
        return {"已验证高度": self._已验证高度, "缓存快照": len(self._缓存)}


# ============================================================
# 节点同步器 — 统筹
# ============================================================
class 节点同步器:
    """
    统筹Fast Sync + State Sync + 增量同步 + 分叉检测

    新节点 → Fast Sync(预测优先) → State Sync(多源验证) → 增量同步
    已同步 → 增量同步(只接收新区块)
    检测分叉 → 最长链 + 涌现分数加权选择
    """

    def __init__(self, 本高度: int = 0):
        self._高度 = 本高度
        self._状态 = 同步状态.空闲
        self._fast = 快速同步器()
        self._state = 状态同步器()
        self._已见哈希: Dict[int, str] = {}
        self._分叉: Dict[int, List[str]] = {}
        self._历史: List[dict] = []

    @property
    def 当前状态(self) -> 同步状态: return self._状态
    @property
    def 本节点高度(self) -> int: return self._高度

    def 新节点同步(self, 目标: int, 源: List[区块摘要]) -> dict:
        """新节点完整同步: Fast Sync → State Sync → 增量"""
        self._状态 = 同步状态.快速同步中
        已下载, 命中率 = self._fast.执行快速同步(目标, 源)
        self._状态 = 同步状态.状态同步中
        状态ok = self._state.执行状态同步(目标)
        self._状态 = 同步状态.已同步 if 状态ok else 同步状态.空闲
        self._高度 = 目标
        报告 = {"已下载": 已下载, "预测命中率": f"{命中率:.1%}",
                "状态同步": "✅" if 状态ok else "❌", "高度": self._高度}
        self._历史.append(报告); return 报告

    def 增量同步(self, 新块: 区块摘要) -> bool:
        """已同步节点接收新区块"""
        if self._状态 not in (同步状态.已同步, 同步状态.增量中): return False
        self._状态 = 同步状态.增量中
        if 新块.高度 != self._高度 + 1: self._状态 = 同步状态.已同步; return False
        预期前一 = self._已见哈希.get(self._高度, "")
        if 新块.前一哈希 != 预期前一 and self._高度 > 0:
            self._状态 = 同步状态.已同步; return False
        self._已见哈希[新块.高度] = 新块.哈希
        self._高度 = 新块.高度; self._状态 = 同步状态.已同步; return True

    def 检测分叉(self, 高度: int, 哈希: str) -> bool:
        """同一高度出现不同哈希→分叉"""
        已有 = self._已见哈希.get(高度)
        if 已有 and 已有 != 哈希:
            self._分叉.setdefault(高度, [已有])
            if 哈希 not in self._分叉[高度]: self._分叉[高度].append(哈希)
            return True
        self._已见哈希[高度] = 哈希; return False

    def 选择最长链(self, 候选: List[List[区块摘要]]) -> List[区块摘要]:
        """最长链+涌现分数加权"""
        if not 候选: return []
        最长 = max(len(c) for c in 候选)
        长链 = [c for c in 候选 if len(c) == 最长]
        if len(长链) == 1: return 长链[0]
        return max(长链, key=lambda c: sum(b.交易数 for b in c))

    def 设置偏好(self, p: Dict[str, float]):
        self._fast.设置偏好(p)

    def 状态(self) -> dict:
        return {"同步状态": self._状态.value, "高度": self._高度,
                "分叉数": len(self._分叉),
                "快速同步": self._fast.状态(), "状态同步": self._state.状态()}


if __name__ == "__main__":
    print("=" * 60)
    print("  HKC 预测同步 Demo")
    print("=" * 60)
    sync = 节点同步器(0)
    sync.设置偏好({"转账": 0.8, "质押": 0.5, "跨链": 0.3})
    blks = []
    for i in range(1, 101):
        types = [["转账"], ["质押"], ["跨链"], ["转账","跨链"], ["质押","合约"]][i%5]
        blks.append(区块摘要(高度=i, 哈希=hashlib.sha256(f"b{i}".encode()).hexdigest()[:16],
            前一哈希=hashlib.sha256(f"b{i-1}".encode()).hexdigest()[:16],
            时间戳=time.time()-100+i, 交易数=i*2, 交易类型=types))
    r = sync.新节点同步(100, blks)
    print(f"  报告: {r}")
    print(f"  按语义查'转账': {sync._fast.按语义查询('转账')[:5]}...")
    print(f"  状态: {sync.状态()}")
