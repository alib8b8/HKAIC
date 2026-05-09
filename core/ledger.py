"""
HKAIC 核心账本 (ledger.py)
==========================
UTXO + 账户混合模型，支持转账/铸币/销毁/Merkle验证。
金额单位：鸿坤 (1 HKAIC = 10^16 鸿坤)
"""

import hashlib
import time
import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

HKAIC_DECIMALS = 16
HKAIC_TOTAL_SUPPLY = 21_000_000
HONGKUN_PER_HKAIC = 10 ** 16


class 交易类型(Enum):
    转账 = "transfer"; 铸币 = "mint"; 销毁 = "burn"
    质押 = "stake"; 解除质押 = "unstake"; 合约 = "contract"; 手续费 = "fee"

class 交易状态(Enum):
    待确认 = "pending"; 已确认 = "confirmed"; 已失败 = "failed"; 已回滚 = "rolled_back"

@dataclass
class UTXO:
    交易ID: str; 输出索引: int; 金额: int; 接收地址: str
    脚本哈希: str = ""; 块高: int = 0; 已花费: bool = False
    def 唯一标识(self) -> str: return f"{self.交易ID}:{self.输出索引}"
    def 到字典(self) -> dict:
        return {"交易ID": self.交易ID, "输出索引": self.输出索引,
                "金额": self.金额, "接收地址": self.接收地址,
                "脚本哈希": self.脚本哈希, "块高": self.块高, "已花费": self.已花费}

@dataclass
class 交易输入:
    引用交易ID: str; 引用输出索引: int; 解锁脚本: str = ""; 公钥: str = ""
    def 到字典(self) -> dict:
        return {"引用交易ID": self.引用交易ID, "引用输出索引": self.引用输出索引,
                "解锁脚本": self.解锁脚本, "公钥": self.公钥}

@dataclass
class 交易输出:
    金额: int; 接收地址: str; 锁定脚本: str = ""
    def 到字典(self) -> dict:
        return {"金额": self.金额, "接收地址": self.接收地址, "锁定脚本": self.锁定脚本}

@dataclass
class 交易记录:
    交易ID: str; 类型: 交易类型; 输入列表: List[交易输入]
    输出列表: List[交易输出]; 时间戳: float; 手续费: int = 0
    状态: 交易状态 = 交易状态.待确认; 块高: int = -1; 备注数据: str = ""
    def 计算交易ID(self) -> str:
        内容 = json.dumps({"输入": [i.到字典() for i in self.输入列表],
                           "输出": [o.到字典() for o in self.输出列表],
                           "时间戳": self.时间戳, "类型": self.类型.value}, sort_keys=True)
        return hashlib.sha256(内容.encode()).hexdigest()
    def 输出总额(self) -> int: return sum(o.金额 for o in self.输出列表)
    def 到字典(self) -> dict:
        return {"交易ID": self.交易ID, "类型": self.类型.value,
                "输入": [i.到字典() for i in self.输入列表],
                "输出": [o.到字典() for o in self.输出列表],
                "时间戳": self.时间戳, "手续费": self.手续费,
                "状态": self.状态.value, "块高": self.块高}


class Merkle树:
    """Merkle树 - 验证交易完整性"""
    def __init__(self, 交易列表: List[交易记录]):
        self.交易列表 = 交易列表; self.叶节点: List[str] = []
        self.树: List[List[str]] = []; self.根哈希: str = ""
        self._构建()

    def _哈希(self, 数据: str) -> str:
        return hashlib.sha256(数据.encode()).hexdigest()

    def _构建(self):
        if not self.交易列表:
            self.根哈希 = self._哈希("空树"); return
        self.叶节点 = [tx.交易ID for tx in self.交易列表]
        当前层 = self.叶节点[:]; self.树 = [当前层[:]]
        while len(当前层) > 1:
            上层 = []
            for i in range(0, len(当前层), 2):
                左 = 当前层[i]; 右 = 当前层[i+1] if i+1 < len(当前层) else 左
                上层.append(self._哈希(左 + 右))
            当前层 = 上层; self.树.append(当前层[:])
        self.根哈希 = 当前层[0]

    def 生成证明(self, idx: int) -> List[Tuple[str, str]]:
        if idx >= len(self.叶节点): return []
        路径 = []; 位置 = idx
        for 层 in self.树[:-1]:
            兄弟 = 位置 + 1 if 位置 % 2 == 0 else 位置 - 1
            if 兄弟 < len(层):
                路径.append((层[兄弟], '右' if 位置 % 2 == 0 else '左'))
            位置 //= 2
        return 路径

    def 验证证明(self, 哈希: str, 路径: List[Tuple[str, str]]) -> bool:
        当前 = 哈希
        for 兄弟, 方向 in 路径:
            当前 = self._哈希(兄弟 + 当前) if 方向 == '左' else self._哈希(当前 + 兄弟)
        return 当前 == self.根哈希

    def 验证完整性(self) -> bool:
        for li in range(len(self.树) - 1):
            for i in range(0, len(self.树[li]), 2):
                左 = self.树[li][i]; 右 = self.树[li][i+1] if i+1 < len(self.树[li]) else 左
                if self.树[li+1][i//2] != self._哈希(左 + 右): return False
        return True


class 账本:
    """HKAIC 核心账本 (UTXO + 账户混合模型)"""

    def __init__(self):
        self._utxo集合: Dict[str, UTXO] = {}
        self._账户余额: Dict[str, int] = {}
        self._交易历史: Dict[str, 交易记录] = {}
        self._地址交易: Dict[str, Set[str]] = {}
        self._已花费: Set[str] = set()
        self._总铸币: int = 0; self._总销毁: int = 0; self._当前块高: int = 0

    def 查询余额(self, 地址: str) -> int: return self._账户余额.get(地址, 0)
    def 查询余额_HKAIC(self, 地址: str) -> float:
        """查询余额(HKAIC单位)，修复显示精度"""
        余额鸿坤 = self.查询余额(地址)
        if 余额鸿坤 == 0:
            return 0.0
        return 余额鸿坤 / HONGKUN_PER_HKAIC
    def 查询UTXO列表(self, 地址: str) -> List[UTXO]:
        return [u for u in self._utxo集合.values() if u.接收地址 == 地址 and not u.已花费]
    def 查询交易历史(self, 地址: str) -> List[交易记录]:
        return [self._交易历史[tid] for tid in self._地址交易.get(地址, set()) if tid in self._交易历史]
    def 查询交易(self, 交易ID: str) -> Optional[交易记录]: return self._交易历史.get(交易ID)
    @property
    def 总铸币量(self) -> int: return self._总铸币
    @property
    def 总销毁量(self) -> int: return self._总销毁
    @property
    def 流通量(self) -> int: return self._总铸币 - self._总销毁
    @property
    def 当前块高(self) -> int: return self._当前块高
    def 设置块高(self, h: int): self._当前块高 = h

    def 铸币(self, 地址: str, 金额: int, 备注: str = "") -> 交易记录:
        if 金额 <= 0: raise ValueError("铸币金额必须大于0")
        上限 = HKAIC_TOTAL_SUPPLY * HONGKUN_PER_HKAIC
        if self._总铸币 + 金额 > 上限:
            raise ValueError(f"超过总量上限！剩余: {(上限 - self._总铸币)/HONGKUN_PER_HKAIC:.8f} HKAIC")
        输出 = 交易输出(金额=金额, 接收地址=地址)
        tx = 交易记录(交易ID="", 类型=交易类型.铸币, 输入列表=[], 输出列表=[输出],
                      时间戳=time.time(), 状态=交易状态.已确认, 块高=self._当前块高, 备注数据=备注)
        tx.交易ID = tx.计算交易ID()
        u = UTXO(交易ID=tx.交易ID, 输出索引=0, 金额=金额, 接收地址=地址, 块高=self._当前块高)
        self._utxo集合[u.唯一标识()] = u
        self._账户余额[地址] = self._账户余额.get(地址, 0) + 金额
        self._总铸币 += 金额; self._交易历史[tx.交易ID] = tx
        self._地址交易.setdefault(地址, set()).add(tx.交易ID)
        return tx

    def 销毁(self, 地址: str, 金额: int, 备注: str = "") -> 交易记录:
        if 金额 <= 0: raise ValueError("销毁金额必须大于0")
        if self.查询余额(地址) < 金额: raise ValueError("余额不足")
        已耗 = self._消耗UTXO(地址, 金额)
        输入 = [交易输入(引用交易ID=u.交易ID, 引用输出索引=u.输出索引) for u in 已耗]
        tx = 交易记录(交易ID="", 类型=交易类型.销毁, 输入列表=输入, 输出列表=[],
                      时间戳=time.time(), 状态=交易状态.已确认, 块高=self._当前块高, 备注数据=备注)
        tx.交易ID = tx.计算交易ID()
        self._账户余额[地址] -= 金额; self._总销毁 += 金额
        self._交易历史[tx.交易ID] = tx; self._地址交易.setdefault(地址, set()).add(tx.交易ID)
        return tx

    def 转账(self, 发送: str, 接收: str, 金额: int, 手续费: int = 0) -> 交易记录:
        总需 = 金额 + 手续费
        if 总需 <= 0: raise ValueError("转账金额必须大于0")
        if self.查询余额(发送) < 总需: raise ValueError("余额不足")
        已耗 = self._消耗UTXO(发送, 总需); 实耗 = sum(u.金额 for u in 已耗)
        找零 = 实耗 - 总需
        输入 = [交易输入(引用交易ID=u.交易ID, 引用输出索引=u.输出索引) for u in 已耗]
        输出 = [交易输出(金额=金额, 接收地址=接收)]
        if 找零 > 0: 输出.append(交易输出(金额=找零, 接收地址=发送))
        tx = 交易记录(交易ID="", 类型=交易类型.转账, 输入列表=输入, 输出列表=输出,
                      时间戳=time.time(), 手续费=手续费, 状态=交易状态.已确认, 块高=self._当前块高)
        tx.交易ID = tx.计算交易ID()
        for i, o in enumerate(输出):
            self._utxo集合[f"{tx.交易ID}:{i}"] = UTXO(
                交易ID=tx.交易ID, 输出索引=i, 金额=o.金额, 接收地址=o.接收地址, 块高=self._当前块高)
        self._账户余额[发送] = self._账户余额.get(发送, 0) - 实耗 + 找零
        self._账户余额[接收] = self._账户余额.get(接收, 0) + 金额
        self._交易历史[tx.交易ID] = tx
        for a in [发送, 接收]: self._地址交易.setdefault(a, set()).add(tx.交易ID)
        return tx

    def 构建Merkle树(self, 交易列表=None) -> Merkle树:
        return Merkle树(交易列表 or list(self._交易历史.values()))

    def 账本摘要(self) -> dict:
        return {"总铸币": f"{self._总铸币/HONGKUN_PER_HKAIC:.8f} HKAIC",
                "总销毁": f"{self._总销毁/HONGKUN_PER_HKAIC:.8f} HKAIC",
                "流通量": 格式化金额(self.流通量),
                "UTXO数": len([u for u in self._utxo集合.values() if not u.已花费]),
                "交易数": len(self._交易历史), "地址数": len(self._账户余额)}

    def _消耗UTXO(self, 地址: str, 金额: int) -> List[UTXO]:
        已耗 = []; 累计 = 0
        可用 = sorted([u for u in self._utxo集合.values() if u.接收地址 == 地址 and not u.已花费],
                      key=lambda u: u.金额)
        for u in 可用:
            if 累计 >= 金额: break
            if u.唯一标识() in self._已花费: raise ValueError(f"双花检测！UTXO {u.唯一标识()} 已花费")
            u.已花费 = True; self._已花费.add(u.唯一标识()); 已耗.append(u); 累计 += u.金额
        if 累计 < 金额:
            for u in 已耗: u.已花费 = False; self._已花费.discard(u.唯一标识())
            raise ValueError("UTXO不足")
        return 已耗


def 鸿坤转HKAIC(v: int) -> float: return v / HONGKUN_PER_HKAIC
def HKAIC转鸿坤(v: float) -> int: return int(v * HONGKUN_PER_HKAIC)
def 格式化金额(v: int) -> str:
    """格式化金额显示，修复精度问题"""
    if v == 0:
        return "0 HKAIC"
    h = v / HONGKUN_PER_HKAIC
    # 使用高精度格式化，避免浮点截断导致0.00000000
    if h == int(h):
        return f"{int(h)} HKAIC"
    # 对于小数，使用足够的精度显示
    格式化 = f"{h:.16f}".rstrip("0").rstrip(".")
    return f"{格式化} HKAIC"


if __name__ == "__main__":
    print("=" * 60)
    print("  HKAIC 核心账本 Demo")
    print("=" * 60)
    L = 账本(); A, B, C = "addr_A", "addr_B", "addr_C"
    L.铸币(A, HKAIC转鸿坤(100)); L.铸币(B, HKAIC转鸿坤(50))
    print(f"A: {L.查询余额_HKAIC(A)} | B: {L.查询余额_HKAIC(B)}")
    L.转账(A, C, HKAIC转鸿坤(30), 手续费=HKAIC转鸿坤(0.001))
    L.销毁(B, HKAIC转鸿坤(10))
    print(f"A: {L.查询余额_HKAIC(A):.8f} | B: {L.查询余额_HKAIC(B):.8f} | C: {L.查询余额_HKAIC(C):.8f}")
    树 = L.构建Merkle树()
    print(f"Merkle完整性: {'✅' if 树.验证完整性() else '❌'}")
    for k, v in L.账本摘要().items(): print(f"  {k}: {v}")
