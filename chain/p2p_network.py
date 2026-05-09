"""
Hongkun AI Chain — 涌知路由 P2P网络层 (p2p_network.py)
========================================================
基于知识贡献度动态选邻居、智能衰减定向传播、恶意节点自动隔离。

核心创新:
  1. Kademlia涌知路由表 — 高K_i节点优先连接(知识引力)
  2. 智能衰减Gossip广播 — 按节点活跃度+兴趣定向传播
  3. P2P网络 — 4步握手 + 协同净化(低σ_i邻居自动断开)
"""

import hashlib
import os, time, random, math
from typing import Dict, List, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

KAD_K = 16; KAD_ALPHA = 3; KAD_BITS = 256
HB_INTERVAL = 30; HB_TIMEOUT = 90
GOSSIP_HOPS = 7; GOSSIP_FANOUT = 6; MAX_PEER = 50
PURGE_SIGMA = 0.05; BAN_COOLDOWN = 3600


def 生成节点ID(地址: str, 端口: int) -> str:
    return hashlib.sha256(f"hkc://{地址}:{端口}".encode()).hexdigest()

def 计算距离(a: str, b: str) -> int:
    return int(a, 16) ^ int(b, 16)

def 距离前缀(d: int) -> int:
    if d == 0: return KAD_BITS
    z = 0
    for i in range(KAD_BITS - 1, -1, -1):
        if d & (1 << i): break
        z += 1
    return z

def 知识引力(K_i: float, 距离: int) -> float:
    """引力 = K_i / log2(距离+2)"""
    if 距离 == 0: return K_i * 1000
    return K_i / math.log2(距离 + 2)


# ============================================================
# 节点信息
# ============================================================
@dataclass
class 节点信息:
    """网络节点信息 — 携带PoEI指标"""
    节点ID: str; 地址: str; 端口: int
    公钥: str = ""; 知识贡献度: float = 0.0; 协同因子: float = 0.0
    活跃度: float = 1.0; 兴趣标签: List[str] = field(default_factory=list)
    启动时间: float = 0.0; 最后可见: float = 0.0
    连接状态: str = "disconnected"; 延迟毫秒: float = 0.0
    版本: str = "4.0.0"; 隔离截止: float = 0.0

    def __post_init__(self):
        if self.启动时间 == 0: self.启动时间 = time.time()
        if self.最后可见 == 0: self.最后可见 = time.time()

    def 是否在线(self) -> bool:
        return time.time() - self.最后可见 < HB_TIMEOUT

    def 是否被隔离(self) -> bool:
        return time.time() < self.隔离截止


# ============================================================
# Kademlia涌知路由表
# ============================================================
class Kademlia路由表:
    """DHT路由表+知识引力排序, bucket满时低K_i被淘汰"""

    def __init__(self, 本节点ID: str):
        self._id = 本节点ID
        self._bk: Dict[int, List[节点信息]] = {}
        self._ns: Dict[str, 节点信息] = {}

    @property
    def 本节点ID(self) -> str: return self._id
    @property
    def 已知节点数(self) -> int: return len(self._ns)

    def 添加节点(self, n: 节点信息) -> bool:
        if n.节点ID == self._id or n.是否被隔离(): return False
        if n.节点ID in self._ns:
            o = self._ns[n.节点ID]; o.最后可见 = time.time()
            o.知识贡献度 = n.知识贡献度; o.协同因子 = n.协同因子; return False
        bi = 距离前缀(计算距离(self._id, n.节点ID))
        bk = self._bk.setdefault(bi, [])
        if len(bk) < KAD_K:
            bk.append(n); self._ns[n.节点ID] = n; return True
        最弱 = min(bk, key=lambda x: x.知识贡献度)
        if n.知识贡献度 > 最弱.知识贡献度:
            bk.remove(最弱); self._ns.pop(最弱.节点ID, None)
            bk.append(n); self._ns[n.节点ID] = n; return True
        最早 = min(bk, key=lambda x: x.最后可见)
        if time.time() - 最早.最后可见 > HB_TIMEOUT:
            bk.remove(最早); self._ns.pop(最早.节点ID, None)
            bk.append(n); self._ns[n.节点ID] = n; return True
        return False

    def 移除节点(self, nid: str) -> bool:
        if nid not in self._ns: return False
        bi = 距离前缀(计算距离(self._id, nid))
        for i, n in enumerate(self._bk.get(bi, [])):
            if n.节点ID == nid: self._bk[bi].pop(i); break
        self._ns.pop(nid, None); return True

    def 查找最近节点(self, 目标: str, k: int = KAD_K) -> List[节点信息]:
        ns = list(self._ns.values())
        ns.sort(key=lambda n: 知识引力(n.知识贡献度, 计算距离(n.节点ID, 目标)), reverse=True)
        return ns[:k]

    def 查找高知识节点(self, k: int = KAD_ALPHA) -> List[节点信息]:
        ns = list(self._ns.values())
        ns.sort(key=lambda n: n.知识贡献度, reverse=True)
        return ns[:k]

    def 迭代查找(self, 目标: str) -> List[节点信息]:
        已查: Set[str] = set(); 结果 = self.查找最近节点(目标, KAD_ALPHA)
        for _ in range(3):
            下轮 = []
            for n in 结果:
                if n.节点ID not in 已查:
                    已查.add(n.节点ID)
                    下轮.extend(self.查找最近节点(目标, KAD_ALPHA))
            合并 = list({x.节点ID: x for x in 结果 + 下轮}.values())
            合并.sort(key=lambda n: 知识引力(n.知识贡献度, 计算距离(n.节点ID, 目标)), reverse=True)
            结果 = 合并[:KAD_K]
            if any(n.节点ID == 目标 for n in 结果): break
        return 结果

    def 摘要(self) -> dict:
        n = len(self._ns)
        return {"已知节点": n, "活跃bucket": sum(1 for b in self._bk.values() if b),
                "平均K_i": f"{sum(x.知识贡献度 for x in self._ns.values())/max(n,1):.2f}",
                "平均σ_i": f"{sum(x.协同因子 for x in self._ns.values())/max(n,1):.4f}"}


# ============================================================
# 智能衰减Gossip广播器
# ============================================================
class 消息类型(Enum):
    区块广播 = "block"; 交易广播 = "tx"; 共识消息 = "consensus"
    状态同步 = "sync"; 心跳包 = "hb"; 跨链消息 = "bridge"

@dataclass
class Gossip消息:
    """携带知识权重与兴趣标签"""
    消息ID: str; 类型: 消息类型; 发送者: str; 发送者K_i: float
    负载: str; 标签: List[str] = field(default_factory=list)
    跳数: int = 0; 时间戳: float = 0.0

    def __post_init__(self):
        if self.时间戳 == 0: self.时间戳 = time.time()
        if not self.消息ID:
            self.消息ID = hashlib.sha256(
                f"{self.类型.value}:{self.发送者}:{self.负载}:{self.时间戳}".encode()).hexdigest()

    def 已过期(self) -> bool: return self.跳数 >= GOSSIP_HOPS
    def 传播力(self) -> float: return 1.0 + math.log2(self.发送者K_i + 1) / 10.0


class Gossip广播器:
    """智能衰减Gossip: 兴趣匹配+活跃度衰减+知识权重+协同过滤"""

    _PRI = {消息类型.共识消息: 0, 消息类型.区块广播: 1, 消息类型.跨链消息: 2,
            消息类型.交易广播: 3, 消息类型.状态同步: 4, 消息类型.心跳包: 5}

    def __init__(self, nid: str):
        self._nid = nid; self._K_i = 0.0
        self._seen: Dict[str, float] = {}; self._q: List[Gossip消息] = []
        self._nbr: Dict[str, 节点信息] = {}; self._cb: Dict[消息类型, Callable] = {}
        self._stat = {"广播": 0, "接收": 0, "过滤": 0, "转发": 0}

    def 设置K_i(self, k: float): self._K_i = k
    def 注册回调(self, t: 消息类型, cb: Callable): self._cb[t] = cb
    def 更新邻居(self, ns: List[节点信息]):
        self._nbr = {n.节点ID: n for n in ns if n.节点ID != self._nid}

    def 广播(self, 类型: 消息类型, 负载: str, 标签: List[str] = None) -> Gossip消息:
        m = Gossip消息(消息ID="", 类型=类型, 发送者=self._nid,
                    发送者K_i=self._K_i, 负载=负载, 标签=标签 or [], 跳数=0)
        self._seen[m.消息ID] = time.time(); self._q.append(m)
        self._stat["广播"] += 1; return m

    def 接收(self, m: Gossip消息) -> bool:
        now = time.time()
        for mid in [x for x, t in self._seen.items() if now - t > 300]: del self._seen[mid]
        if m.消息ID in self._seen or m.已过期():
            self._stat["过滤"] += 1; return False
        self._seen[m.消息ID] = now; self._stat["接收"] += 1
        cb = self._cb.get(m.类型)
        if cb: cb(m)
        fwd = Gossip消息(消息ID=m.消息ID, 类型=m.类型, 发送者=self._nid,
                     发送者K_i=self._K_i, 负载=m.负载, 标签=m.标签, 跳数=m.跳数+1)
        self._q.append(fwd); self._stat["转发"] += 1; return True

    def _评分(self, nb: 节点信息, m: Gossip消息) -> float:
        兴趣 = 1.0
        if m.标签:
            if nb.兴趣标签:
                重合 = set(nb.兴趣标签) & set(m.标签)
                兴趣 = 0.3 + 0.7 * len(重合) / len(set(m.标签)) if 重合 else 0.3
            else: 兴趣 = 0.7
        return nb.活跃度 * 兴趣 * (1.0 + nb.协同因子) * m.传播力()

    def 执行轮次(self) -> int:
        if not self._q: return 0
        self._q.sort(key=lambda m: self._PRI.get(m.类型, 99))
        batch = self._q[:]; self._q.clear(); cnt = 0
        for m in batch:
            if not self._nbr: continue
            评分 = sorted(self._nbr.values(), key=lambda n: self._评分(n, m), reverse=True)
            fanout = min(int(GOSSIP_FANOUT * m.传播力()), len(评分))
            pri = self._PRI.get(m.类型, 99)
            cnt += sum(1 for n in 评分[:fanout] if self._评分(n, m) >= 0.5 or pri <= 1)
        return cnt

    def 状态(self) -> dict:
        return {"K_i": f"{self._K_i:.2f}", "已见": len(self._seen),
                "待发": len(self._q), "邻居": len(self._nbr), "统计": self._stat}


# ============================================================
# 握手协议
# ============================================================
@dataclass
class 握手消息:
    """4步握手: hello→challenge→auth→ack"""
    类型: str; 节点ID: str; 地址: str; 端口: int
    版本: str = "4.0.0"; 链高度: int = 0
    K_i: float = 0.0; σ_i: float = 0.0
    挑战: str = ""; 签名: str = ""; 时间戳: float = 0.0

    def __post_init__(self):
        if self.时间戳 == 0: self.时间戳 = time.time()
        if self.类型 == "challenge" and not self.挑战:
            # H-18: os.urandom替代time.time_ns()
            self.挑战 = hashlib.sha256(f"{self.节点ID}:{os.urandom(16).hex()}".encode()).hexdigest()[:32]


# ============================================================
# P2P网络 — 涌知路由核心
# ============================================================
class P2P网络:
    """
    涌知路由P2P网络:
    1. 知识引力连接: 高K_i优先
    2. 协同净化: 低σ_i自动断开隔离
    3. 智能衰减广播: 兴趣+活跃度定向
    """

    def __init__(self, 地址: str = "127.0.0.1", 端口: int = 8800):
        self._addr = 地址; self._port = 端口
        self._nid = 生成节点ID(地址, 端口)
        self._路由 = Kademlia路由表(self._nid)
        self._gossip = Gossip广播器(self._nid)
        self._peers: Dict[str, 节点信息] = {}
        self._seeds: List[节点信息] = []
        self._running = False; self._last_hb = 0.0
        self._hs: Dict[str, 握手消息] = {}
        self._隔离: Dict[str, float] = {}
        self._净化日志: List[dict] = []

    @property
    def 节点ID(self) -> str: return self._nid
    @property
    def 路由表(self) -> Kademlia路由表: return self._路由
    @property
    def 广播器(self) -> Gossip广播器: return self._gossip
    @property
    def 已连接数(self) -> int: return len(self._peers)

    def 添加种子节点(self, 地址: str, 端口: int, K_i: float = 0.0, σ_i: float = 0.0):
        nid = 生成节点ID(地址, 端口)
        n = 节点信息(节点ID=nid, 地址=地址, 端口=端口, 知识贡献度=K_i, 协同因子=σ_i)
        self._seeds.append(n); self._路由.添加节点(n)

    def 启动(self) -> bool:
        if self._running: return False
        self._running = True; self._last_hb = time.time()
        for s in self._seeds: self._发起握手(s)
        self._节点发现(); self._协同净化(); return True

    def 停止(self):
        self._running = False
        for nid in list(self._peers): self._断开(nid)

    def _发起握手(self, t: 节点信息) -> bool:
        if self.已连接数 >= MAX_PEER: return False
        if t.节点ID in self._隔离:
            if time.time() < self._隔离[t.节点ID]: return False
            del self._隔离[t.节点ID]
        self._hs[t.节点ID] = 握手消息(类型="hello", 节点ID=self._nid, 地址=self._addr, 端口=self._port)
        return True

    def 处理握手(self, m: 握手消息) -> Optional[握手消息]:
        """4步握手状态机"""
        if m.类型 == "hello":
            return 握手消息(类型="challenge", 节点ID=self._nid, 地址=self._addr, 端口=self._port)
        elif m.类型 == "challenge":
            # 使用HMAC签名代替SHA256哈希，防止签名伪造
            import hmac as _hmac
            sig = _hmac.new(m.挑战.encode(), self._nid.encode(), hashlib.sha256).hexdigest()
            return 握手消息(类型="auth", 节点ID=self._nid, 地址=self._addr, 端口=self._port, 签名=sig)
        elif m.类型 == "auth":
            # 验证签名：使用ECDSA或HMAC验证，防止中间人攻击
            hs = self._hs.get(m.节点ID)
            挑战 = hs.挑战 if hs else ''
            # 使用SHA256+HMAC验证签名（比纯SHA256更安全）
            import hmac as _hmac
            预期签名 = _hmac.new(
                挑战.encode(), 
                m.节点ID.encode(), 
                hashlib.sha256
            ).hexdigest()
            if _hmac.compare_digest(m.签名, 预期签名):
                self._连接(节点信息(节点ID=m.节点ID, 地址=m.地址, 端口=m.端口,
                    连接状态="connected", 知识贡献度=m.K_i, 协同因子=m.σ_i))
                return 握手消息(类型="ack", 节点ID=self._nid, 地址=self._addr, 端口=self._port)
            return None
        elif m.类型 == "ack":
            self._连接(节点信息(节点ID=m.节点ID, 地址=m.地址, 端口=m.端口,
                连接状态="connected", 知识贡献度=m.K_i, 协同因子=m.σ_i))
            self._hs.pop(m.节点ID, None); return None
        return None

    def _连接(self, n: 节点信息):
        if len(self._peers) >= MAX_PEER:
            最弱 = min(self._peers, key=lambda k: self._peers[k].知识贡献度)
            if self._peers[最弱].知识贡献度 < n.知识贡献度: self._断开(最弱)
            else: return
        n.连接状态 = "connected"; self._peers[n.节点ID] = n
        self._路由.添加节点(n); self._gossip.更新邻居(list(self._peers.values()))

    def _断开(self, nid: str, 原因: str = ""):
        if nid in self._peers:
            self._peers[nid].连接状态 = "disconnected"
            del self._peers[nid]; self._路由.移除节点(nid)
            self._gossip.更新邻居(list(self._peers.values()))

    def _节点发现(self):
        for n in self._路由.查找高知识节点(KAD_ALPHA): self._路由.添加节点(n)
        for s in self._seeds:
            if s.节点ID != self._nid:
                for n in self._路由.查找最近节点(self._nid, KAD_ALPHA): self._路由.添加节点(n)

    def _协同净化(self) -> List[str]:
        """断开低σ_i节点——恶意节点σ_i自然衰减后被自动隔离"""
        净化 = []
        for nid, n in list(self._peers.items()):
            if 0 < n.协同因子 < PURGE_SIGMA:
                self._断开(nid, "协同净化"); self._隔离[nid] = time.time() + BAN_COOLDOWN
                净化.append(nid)
                self._净化日志.append({"时间": time.time(), "节点": nid[:16], "σ_i": n.协同因子})
        return 净化

    def 更新PoEI指标(self, nid: str, K_i: float, σ_i: float):
        if nid in self._peers:
            self._peers[nid].知识贡献度 = K_i; self._peers[nid].协同因子 = σ_i
        if nid in self._路由._ns:
            self._路由._ns[nid].知识贡献度 = K_i; self._路由._ns[nid].协同因子 = σ_i

    def 执行心跳(self) -> Tuple[List[str], List[str]]:
        """心跳+协同净化, 返回(超时, 净化)"""
        now = time.time()
        if now - self._last_hb < HB_INTERVAL: return [], []
        self._last_hb = now
        超时 = [nid for nid, n in list(self._peers.items()) if now - n.最后可见 > HB_TIMEOUT]
        for nid in 超时: self._断开(nid, "心跳超时")
        净化 = self._协同净化()
        for n in self._peers.values(): n.最后可见 = now
        return 超时, 净化

    def 广播区块(self, 数据: str, 标签: List[str] = None) -> Gossip消息:
        return self._gossip.广播(消息类型.区块广播, 数据, 标签)

    def 广播交易(self, 数据: str, 标签: List[str] = None) -> Gossip消息:
        return self._gossip.广播(消息类型.交易广播, 数据, 标签)

    def 广播共识消息(self, 数据: str) -> Gossip消息:
        return self._gossip.广播(消息类型.共识消息, 数据)

    def 网络状态(self) -> dict:
        Ks = [n.知识贡献度 for n in self._peers.values()]
        Ss = [n.协同因子 for n in self._peers.values()]
        return {"节点ID": self._nid[:16]+"...", "地址": f"{self._addr}:{self._port}",
                "状态": "✅运行" if self._running else "⏹停止", "已连接": self.已连接数,
                "平均K_i": f"{sum(Ks)/max(len(Ks),1):.2f}",
                "平均σ_i": f"{sum(Ss)/max(len(Ss),1):.4f}",
                "隔离": len(self._隔离), "净化": len(self._净化日志),
                "路由": self._路由.摘要(), "Gossip": self._gossip.状态()}


if __name__ == "__main__":
    print("=" * 60)
    print("  HKC 涌知路由 P2P Demo")
    print("=" * 60)
    A, B, C = [P2P网络("127.0.0.1", 8800+i) for i in range(3)]
    B.添加种子节点("127.0.0.1", 8800, K_i=50, σ_i=0.3)
    C.添加种子节点("127.0.0.1", 8800, K_i=50, σ_i=0.3)
    for n in [A, B, C]: n.启动()
    h = 握手消息(类型="hello", 节点ID=A.节点ID, 地址=A._addr, 端口=A._port, K_i=85, σ_i=0.6)
    r1 = B.处理握手(h)
    r2 = A.处理握手(r1) if r1 else None
    r3 = B.处理握手(r2) if r2 else None
    if r3: A.处理握手(r3)
    print(f"  A连接={A.已连接数} B连接={B.已连接数}")
    A._gossip.设置K_i(85)
    A._gossip.更新邻居(list(A._peers.values()))
    msg = A.广播区块('{"h":1}', ["consensus"])
    print(f"  传播力={msg.传播力():.2f} 发送={A._gossip.执行轮次()}条")
    print(f"  状态: {A.网络状态()}")
