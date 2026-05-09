"""
Hongkun AI Chain — 节点进程 (node_process.py)
==============================================
每个节点进程运行独立的:
  - HTTP RPC服务器 (真实网络I/O)
  - 区块链 + 账本 + 共识引擎
  - P2P通信客户端 (向其他节点发HTTP请求)
  - 交易池 + 出块逻辑

用法:
    python node_process.py --node-id 0 --p2p-port 8001 --rpc-port 8841 --seeds 8002,8003,8004,8005
"""

import sys
import os
import json
import hashlib
import time
import threading
import argparse
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List, Optional, Set
from copy import deepcopy

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.blockchain import 区块链, 区块, 区块头, HONGKUN_PER_HKAIC
from core.ledger import 账本, HONGKUN_PER_HKAIC as LEDGER_HONGKUN
from core.wallet import 钱包, 密钥对
from core.transaction import 交易引擎, 交易优先级, 待处理交易
from chain.consensus_engine import PoEI共识引擎
from chain.p2p_network import P2P网络, 消息类型


# ============================================================
# 节点状态 — 每个进程独立实例
# ============================================================
class 节点状态:
    """单节点完整状态"""
    def __init__(self, node_id: int, p2p_port: int, rpc_port: int):
        self.node_id = node_id
        self.name = f"hkc-node-{node_id}"
        self.p2p_port = p2p_port
        self.rpc_port = rpc_port
        self.address = "127.0.0.1"

        # 核心组件 — 每个节点独立实例
        self.blockchain = 区块链()
        self.ledger = 账本()
        self.consensus = PoEI共识引擎()
        self.tx_engine = 交易引擎()
        self.p2p = P2P网络(self.address, self.p2p_port)

        # 钱包管理
        self.wallets: Dict[str, 钱包] = {}

        # 已知节点列表 (node_id -> {host, p2p_port, rpc_port})
        self.known_nodes: Dict[int, dict] = {}

        # 出块锁 — 防止多个线程同时出块
        self.block_lock = threading.Lock()

        # 节点状态
        self.running = False
        self.is_validator = False
        self.validator_name = ""

        # 共识轮次追踪
        self.current_epoch = 0
        self.last_block_time = time.time()

        # 统计
        self.stats = {
            "blocks_produced": 0,
            "tx_processed": 0,
            "p2p_messages_sent": 0,
            "p2p_messages_recv": 0,
            "start_time": time.time()
        }

    def 注册验证者(self, 名称: str, 质押: float, 知识贡献: float):
        """注册本节点为验证者"""
        self.consensus.更新质押(名称, 质押)
        self.consensus.更新知识贡献(名称, 知识贡献)
        self.is_validator = True
        self.validator_name = 名称

    def 注册协同关系(self, 其他验证者: List[str], 强度: float = 0.5):
        """注册与其他验证者的协同关系"""
        for v in 其他验证者:
            if v != self.validator_name:
                self.consensus.记录协同(self.validator_name, v, 强度)

    def 创建钱包(self, 名称: str, seed: str = "") -> 钱包:
        """创建钱包"""
        w = 钱包(名称=名称, seed=seed or f"node{self.node_id}-{名称}")
        self.wallets[名称] = w
        return w

    def 铸币给钱包(self, 钱包名: str, 金额_HKAIC: float):
        """铸造代币给指定钱包"""
        w = self.wallets.get(钱包名)
        if not w:
            raise ValueError(f"钱包 {钱包名} 不存在")
        金额_鸿坤 = int(金额_HKAIC * HONGKUN_PER_HKAIC)
        self.ledger.铸币(w.地址, 金额_鸿坤)
        # 同时添加铸币交易到交易池(用于出块追踪)
        self.tx_engine.创建转账(
            "MINT", w.地址, 金额_鸿坤, 0, 交易优先级.高)

    def 提交交易(self, 发送钱包名: str, 接收地址: str, 金额_HKAIC: float, 手续费_HKAIC: float = 0.001):
        """提交交易到交易池"""
        w = self.wallets.get(发送钱包名)
        if not w:
            raise ValueError(f"钱包 {发送钱包名} 不存在")
        金额_鸿坤 = int(金额_HKAIC * HONGKUN_PER_HKAIC)
        手续费_鸿坤 = int(手续费_HKAIC * HONGKUN_PER_HKAIC)
        tx = self.tx_engine.创建转账(
            w.地址, 接收地址, 金额_鸿坤, 手续费_鸿坤, 交易优先级.高)
        return tx

    def 尝试出块(self) -> Optional[区块]:
        """尝试出块 — PoEI共识判定出块权
        
        测试网宽松模式: 
          - 每个有交易池交易的节点都可以出块
          - 出块权由PoEI共识判定，但测试网允许直接出块
        """
        if self.tx_engine.交易池.大小 == 0:
            return None  # 无交易不出块

        with self.block_lock:
            # 开启新epoch
            epoch = self.consensus.开始新epoch()
            self.current_epoch = epoch.编号

            # 推进共识阶段 — 测试网简化: 直接推进到提交阶段
            出块者 = self.consensus.推进共识()

            # 如果共识引擎未选出出块者，使用PoEI直接判定
            if 出块者 is None or isinstance(出块者, str) and "超时" in 出块者:
                候选 = list(self.consensus._S.keys())
                出块者 = self.consensus.判定出块权(候选, epoch.种子)

            # 测试网: 如果还是没有出块者，自己出块
            if 出块者 is None:
                出块者 = self.validator_name

            # 不检查出块权是否是自己 — 测试网中所有节点都可以出块
            # (生产环境需要严格检查)

            # 获得出块权 — 打包交易出块
            待打包 = self.tx_engine.交易池.获取最高费率(500)
            if not 待打包:
                return None

            # 在区块上添加待确认交易
            for tx in 待打包:
                self.blockchain.添加待确认交易({
                    "交易ID": tx.交易ID,
                    "发送": tx.发送地址,
                    "接收": tx.接收地址,
                    "金额": tx.金额,
                    "手续费": tx.手续费,
                    "类型": "铸币" if tx.发送地址 == "MINT" else "转账",
                    "优先级": tx.优先级.value
                })

            # 出块
            新区块 = self.blockchain.出块(出块者)

            if 新区块:
                # 确认交易并更新账本
                for tx in 待打包:
                    result = self.tx_engine.确认交易(tx.交易ID)
                    if result:
                        # 铸币交易已在账本中记录，跳过
                        if result["发送"] == "MINT":
                            self.stats["tx_processed"] += 1
                            continue
                        # 普通转账 — 更新账本余额
                        金额 = result["金额"]
                        发送 = result["发送"]
                        接收 = result["接收"]
                        手续费 = result["手续费"]
                        try:
                            if self.ledger.查询余额(发送) >= 金额 + 手续费:
                                self.ledger.转账(发送, 接收, 金额, 手续费)
                        except ValueError:
                            pass  # 余额不足跳过
                        self.stats["tx_processed"] += 1

                self.stats["blocks_produced"] += 1
                self.last_block_time = time.time()

            return 新区块

    def 状态摘要(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "p2p_port": self.p2p_port,
            "rpc_port": self.rpc_port,
            "running": self.running,
            "is_validator": self.is_validator,
            "validator_name": self.validator_name,
            "block_height": self.blockchain.高度,
            "tx_pool_size": self.tx_engine.交易池.大小,
            "tx_confirmed": self.tx_engine.已确认数,
            "wallets": list(self.wallets.keys()),
            "known_nodes": list(self.known_nodes.keys()),
            "current_epoch": self.current_epoch,
            "stats": self.stats,
            "uptime": f"{time.time() - self.stats['start_time']:.1f}s"
        }


# ============================================================
# 全局节点实例
# ============================================================
_node: Optional[节点状态] = None


def get_node() -> 节点状态:
    global _node
    return _node


# ============================================================
# P2P通信客户端 — HTTP向其他节点发送消息
# ============================================================
class P2P客户端:
    """通过HTTP向其他节点发送P2P消息"""

    @staticmethod
    def 广播区块(区块数据: dict, 排除节点: int = -1):
        """向所有已知节点广播新区块"""
        node = get_node()
        if not node:
            return
        for nid, info in node.known_nodes.items():
            if nid == 排除节点:
                continue
            try:
                P2P客户端._post(f"http://{info['host']}:{info['rpc_port']}/p2p/block",
                                 {"block": 区块数据, "from_node": node.node_id})
                node.stats["p2p_messages_sent"] += 1
            except Exception:
                pass

    @staticmethod
    def 广播交易(交易数据: dict, 排除节点: int = -1):
        """向所有已知节点广播新交易"""
        node = get_node()
        if not node:
            return
        for nid, info in node.known_nodes.items():
            if nid == 排除节点:
                continue
            try:
                P2P客户端._post(f"http://{info['host']}:{info['rpc_port']}/p2p/tx",
                                 {"tx": 交易数据, "from_node": node.node_id})
                node.stats["p2p_messages_sent"] += 1
            except Exception:
                pass

    @staticmethod
    def 请求区块(目标节点: int, 高度: int) -> Optional[dict]:
        """向指定节点请求特定高度的区块"""
        node = get_node()
        if not node or 目标节点 not in node.known_nodes:
            return None
        info = node.known_nodes[目标节点]
        try:
            resp = P2P客户端._get(
                f"http://{info['host']}:{info['rpc_port']}/p2p/block/{高度}")
            return resp
        except Exception:
            return None

    @staticmethod
    def ping(目标节点: int) -> bool:
        """检查节点是否在线"""
        node = get_node()
        if not node or 目标节点 not in node.known_nodes:
            return False
        info = node.known_nodes[目标节点]
        try:
            resp = P2P客户端._get(
                f"http://{info['host']}:{info['rpc_port']}/p2p/ping")
            return resp is not None
        except Exception:
            return False

    @staticmethod
    def _post(url: str, data: dict) -> dict:
        """发送POST请求"""
        import urllib.request
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST')
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode('utf-8'))

    @staticmethod
    def _get(url: str) -> Optional[dict]:
        """发送GET请求"""
        import urllib.request
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode('utf-8'))


# ============================================================
# RPC服务器 — HTTP请求处理器
# ============================================================
class 节点RPCHandler(BaseHTTPRequestHandler):
    """HKC节点RPC接口"""

    def log_message(self, format, *args):
        """自定义日志 — 添加节点标识"""
        node = get_node()
        prefix = f"[Node-{node.node_id}]" if node else "[???]"
        sys.stdout.write(f"{prefix} RPC: {format % args}\n")
        sys.stdout.flush()

    def _send_json(self, data: dict, code: int = 200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode('utf-8'))

    def _read_body(self) -> dict:
        length = int(self.headers.get('Content-Length', 0))
        if length:
            return json.loads(self.rfile.read(length).decode('utf-8'))
        return {}

    def do_GET(self):
        node = get_node()
        if not node:
            self._send_json({"error": "节点未初始化"}, 500)
            return

        try:
            if self.path == '/status':
                self._send_json(node.状态摘要())

            elif self.path == '/info':
                self._send_json({
                    "链名": "Hongkun AI Chain",
                    "代号": "HKC",
                    "版本": "4.0.0",
                    "共识": "PoEI",
                    "节点ID": node.node_id,
                    "区块高度": node.blockchain.高度,
                    "验证者": node.validator_name,
                })

            elif self.path.startswith('/balance/'):
                地址 = self.path.split('/balance/')[-1]
                余额鸿坤 = node.ledger.查询余额(地址)
                余额HKAIC = 余额鸿坤 / HONGKUN_PER_HKAIC
                self._send_json({"地址": 地址, "余额_鸿坤": 余额鸿坤, "余额_HKAIC": 余额HKAIC})

            elif self.path == '/blockchain':
                链摘要 = node.blockchain.链摘要()
                self._send_json(链摘要)

            elif self.path.startswith('/block/'):
                高度 = int(self.path.split('/block/')[-1])
                区块 = node.blockchain.获取区块(高度)
                if 区块:
                    self._send_json({
                        "高度": 区块.头.区块高度,
                        "哈希": 区块.区块哈希()[:32],
                        "前一哈希": 区块.头.前一区块哈希[:32],
                        "出块者": 区块.头.出块者,
                        "涌现分数": 区块.头.涌现分数证明,
                        "交易数": len(区块.交易列表),
                        "时间戳": 区块.头.时间戳,
                        "交易列表": 区块.交易列表,
                    })
                else:
                    self._send_json({"error": f"区块 {高度} 不存在"}, 404)

            elif self.path == '/validators':
                # 获取所有验证者信息
                验证者列表 = []
                for v_name in node.consensus._S:
                    报告 = node.consensus.节点报告(v_name)
                    验证者列表.append(报告)
                self._send_json({"validators": 验证者列表})

            elif self.path == '/txpool':
                交易列表 = []
                for tx in node.tx_engine.交易池.获取全部():
                    交易列表.append({
                        "交易ID": tx.交易ID[:16],
                        "发送": tx.发送地址,
                        "接收": tx.接收地址,
                        "金额_HKAIC": tx.金额 / HONGKUN_PER_HKAIC,
                        "手续费": tx.手续费,
                        "优先级": tx.优先级.value,
                    })
                self._send_json({"pool_size": len(交易列表), "transactions": 交易列表})

            elif self.path == '/wallets':
                钱包列表 = []
                for name, w in node.wallets.items():
                    余额 = node.ledger.查询余额(w.地址) / HONGKUN_PER_HKAIC
                    钱包列表.append({
                        "名称": name,
                        "地址": w.地址,
                        "余额_HKAIC": 余额,
                    })
                self._send_json({"wallets": 钱包列表})

            elif self.path == '/consensus':
                self._send_json({
                    "network": node.consensus.网络摘要(),
                    "epoch": node.current_epoch,
                    "validator": node.validator_name,
                })

            # ---- P2P接口 ----
            elif self.path == '/p2p/ping':
                node.stats["p2p_messages_recv"] += 1
                self._send_json({"pong": True, "node_id": node.node_id,
                                 "height": node.blockchain.高度,
                                 "validator": node.validator_name})

            elif self.path.startswith('/p2p/block/'):
                高度 = int(self.path.split('/p2p/block/')[-1])
                区块 = node.blockchain.获取区块(高度)
                if 区块:
                    self._send_json({
                        "height": 区块.头.区块高度,
                        "hash": 区块.区块哈希(),
                        "proposer": 区块.头.出块者,
                        "tx_count": len(区块.交易列表),
                    })
                else:
                    self._send_json({"error": "not found"}, 404)

            else:
                self._send_json({"error": f"未知路由: {self.path}"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_POST(self):
        node = get_node()
        if not node:
            self._send_json({"error": "节点未初始化"}, 500)
            return

        try:
            body = self._read_body()

            if self.path == '/wallet/create':
                名称 = body.get("name", f"wallet-{len(node.wallets)}")
                seed = body.get("seed", "")
                w = node.创建钱包(名称, seed)
                self._send_json({
                    "名称": 名称, "地址": w.地址, "公钥": w.密钥对.公钥[:16] + "..."
                })

            elif self.path == '/wallet/mint':
                钱包名 = body.get("wallet", "")
                金额 = float(body.get("amount", 0))
                if 钱包名 and 金额 > 0:
                    node.铸币给钱包(钱包名, 金额)
                    余额 = node.ledger.查询余额(node.wallets[钱包名].地址) / HONGKUN_PER_HKAIC
                    self._send_json({"状态": "铸币成功", "钱包": 钱包名, "余额_HKAIC": 余额})
                else:
                    self._send_json({"error": "参数错误"}, 400)

            elif self.path == '/tx/send':
                """提交交易 — 涌信钱包转账"""
                发送者 = body.get("from", "")
                接收地址 = body.get("to", "")
                金额 = float(body.get("amount", 0))
                手续费 = float(body.get("fee", 0.001))

                # 检查是否使用钱包名称
                if 发送者 in node.wallets:
                    发送地址 = node.wallets[发送者].地址
                else:
                    发送地址 = 发送者

                # 检查余额
                余额 = node.ledger.查询余额(发送地址) / HONGKUN_PER_HKAIC
                if 余额 < 金额 + 手续费:
                    self._send_json({"error": f"余额不足: {余额} HKAIC"}, 400)
                    return

                # 直接通过账本转账
                try:
                    金额_鸿坤 = int(金额 * HONGKUN_PER_HKAIC)
                    手续费_鸿坤 = int(手续费 * HONGKUN_PER_HKAIC)
                    tx_record = node.ledger.转账(发送地址, 接收地址, 金额_鸿坤, 手续费_鸿坤)

                    # 同时添加到交易引擎(用于出块追踪)
                    node.tx_engine.创建转账(发送地址, 接收地址, 金额_鸿坤, 手续费_鸿坤, 交易优先级.高)

                    # 广播交易给其他节点
                    tx_data = {
                        "交易ID": tx_record.交易ID,
                        "发送": 发送地址,
                        "接收": 接收地址,
                        "金额_HKAIC": 金额,
                        "手续费_HKAIC": 手续费,
                        "type": "转账"
                    }
                    threading.Thread(
                        target=P2P客户端.广播交易,
                        args=(tx_data, node.node_id),
                        daemon=True
                    ).start()

                    发送余额 = node.ledger.查询余额(发送地址) / HONGKUN_PER_HKAIC
                    接收余额 = node.ledger.查询余额(接收地址) / HONGKUN_PER_HKAIC
                    self._send_json({
                        "状态": "✅ 交易成功",
                        "交易ID": tx_record.交易ID[:16],
                        "发送者余额": 发送余额,
                        "接收者余额": 接收余额,
                    })
                except ValueError as e:
                    self._send_json({"error": str(e)}, 400)

            elif self.path == '/force_block':
                """强制出块(测试网管理员命令)"""
                区块 = node.尝试出块()
                if 区块:
                    # 广播区块
                    区块数据 = {
                        "height": 区块.头.区块高度,
                        "hash": 区块.区块哈希()[:32],
                        "proposer": 区块.头.出块者,
                        "tx_count": len(区块.交易列表),
                        "emergence_score": 区块.头.涌现分数证明,
                    }
                    threading.Thread(
                        target=P2P客户端.广播区块,
                        args=(区块数据, node.node_id),
                        daemon=True
                    ).start()
                    self._send_json({"状态": "✅ 出块成功", "区块": 区块数据})
                else:
                    self._send_json({"状态": "⏳ 无交易可出块", "交易池": node.tx_engine.交易池.大小})

            # ---- P2P消息接收 ----
            elif self.path == '/p2p/block':
                """接收其他节点广播的区块"""
                node.stats["p2p_messages_recv"] += 1
                区块数据 = body.get("block", {})
                来源 = body.get("from_node", -1)
                # 简化: 记录收到区块(测试网中每个节点独立出块)
                self._send_json({"status": "received", "height": 区块数据.get("height")})

            elif self.path == '/p2p/tx':
                """接收其他节点广播的交易"""
                node.stats["p2p_messages_recv"] += 1
                交易数据 = body.get("tx", {})
                来源 = body.get("from_node", -1)
                # 将交易添加到本地交易池
                if 交易数据:
                    已有 = node.tx_engine.交易池.是否已知(交易数据.get("交易ID", ""))
                    if not 已有:
                        try:
                            node.tx_engine.创建转账(
                                交易数据.get("发送", ""),
                                交易数据.get("接收", ""),
                                int(交易数据.get("金额_HKAIC", 0) * HONGKUN_PER_HKAIC),
                                int(交易数据.get("手续费_HKAIC", 0.001) * HONGKUN_PER_HKAIC),
                                交易优先级.中
                            )
                        except Exception:
                            pass
                self._send_json({"status": "received"})

            elif self.path == '/p2p/register':
                """其他节点注册到本节点"""
                node.stats["p2p_messages_recv"] += 1
                nid = body.get("node_id")
                host = body.get("host", "127.0.0.1")
                p2p_port = body.get("p2p_port")
                rpc_port = body.get("rpc_port")
                validator = body.get("validator", "")
                if nid is not None:
                    node.known_nodes[nid] = {
                        "host": host, "p2p_port": p2p_port,
                        "rpc_port": rpc_port, "validator": validator
                    }
                    # 同时注册到共识引擎
                    if validator:
                        质押 = body.get("stake", 5000)
                        K_i = body.get("K_i", 50)
                        node.consensus.更新质押(validator, 质押)
                        node.consensus.更新知识贡献(validator, K_i)
                        # 建立协同关系
                        if node.validator_name:
                            node.consensus.记录协同(node.validator_name, validator, 0.5)
                self._send_json({"status": "registered", "node_id": node.node_id})

            else:
                self._send_json({"error": f"未知路由: {self.path}"}, 404)

        except Exception as e:
            traceback.print_exc()
            self._send_json({"error": str(e)}, 500)


# ============================================================
# 共识循环线程 — 定期尝试出块
# ============================================================
class 共识循环线程(threading.Thread):
    """定期执行共识流程"""

    def __init__(self, interval: float = 3.0):
        super().__init__(daemon=True)
        self.interval = interval
        self._stop = threading.Event()

    def run(self):
        node = get_node()
        if not node:
            return
        while not self._stop.is_set():
            self._stop.wait(self.interval)
            if not node.running:
                continue
            try:
                # 尝试出块
                区块 = node.尝试出块()
                if 区块:
                    print(f"\n  ⛏️  [Node-{node.node_id} {node.validator_name}] "
                          f"出块成功! 高度={区块.头.区块高度} "
                          f"交易数={len(区块.交易列表)} "
                          f"涌现分数={区块.头.涌现分数证明:.6f}")
                    # 广播区块
                    区块数据 = {
                        "height": 区块.头.区块高度,
                        "hash": 区块.区块哈希()[:32],
                        "proposer": 区块.头.出块者,
                        "tx_count": len(区块.交易列表),
                        "emergence_score": 区块.头.涌现分数证明,
                    }
                    P2P客户端.广播区块(区块数据, node.node_id)
            except Exception as e:
                print(f"  ❌ [Node-{node.node_id}] 共识错误: {e}")

    def stop(self):
        self._stop.set()


# ============================================================
# 节点发现线程 — 定期检查其他节点在线状态
# ============================================================
class 节点发现线程(threading.Thread):
    """定期与其他节点交换状态"""

    def __init__(self, interval: float = 5.0):
        super().__init__(daemon=True)
        self.interval = interval
        self._stop = threading.Event()

    def run(self):
        node = get_node()
        if not node:
            return
        while not self._stop.is_set():
            self._stop.wait(self.interval)
            if not node.running:
                continue
            # 检查已知节点是否在线
            for nid, info in list(node.known_nodes.items()):
                if P2P客户端.ping(nid):
                    pass  # 在线
                # 不移除离线节点(可能临时断开)

    def stop(self):
        self._stop.set()


# ============================================================
# 启动节点
# ============================================================
def 启动节点(node_id: int, p2p_port: int, rpc_port: int,
            seed_ports: List[int], validator_name: str,
            stake: float, K_i: float):
    """启动一个完整的HKC节点"""
    global _node

    # 初始化节点
    _node = 节点状态(node_id, p2p_port, rpc_port)
    node = _node

    # 注册验证者
    node.注册验证者(validator_name, stake, K_i)

    # 启动P2P网络
    node.p2p.启动()

    # 注册种子节点
    for seed_port in seed_ports:
        seed_id = seed_port - 8001  # 推算node_id
        node.known_nodes[seed_id] = {
            "host": "127.0.0.1", "p2p_port": seed_port,
            "rpc_port": seed_port + 840,  # rpc_port = p2p_port + 840
            "validator": f"Validator_{seed_id}"
        }

    node.running = True

    # 启动RPC服务器
    server = HTTPServer(('0.0.0.0', rpc_port), 节点RPCHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    # 启动共识循环
    consensus_thread = 共识循环线程(interval=3.0)
    consensus_thread.start()

    # 启动节点发现
    discovery_thread = 节点发现线程(interval=5.0)
    discovery_thread.start()

    print(f"\n  🚀 [Node-{node_id}] {validator_name} 已启动")
    print(f"     P2P端口: {p2p_port}  RPC端口: {rpc_port}")
    print(f"     种子节点: {seed_ports}")

    # 等待其他节点上线(3秒)
    time.sleep(3)

    # 向其他节点注册自己
    for nid, info in node.known_nodes.items():
        try:
            P2P客户端._post(f"http://{info['host']}:{info['rpc_port']}/p2p/register", {
                "node_id": node_id,
                "host": "127.0.0.1",
                "p2p_port": p2p_port,
                "rpc_port": rpc_port,
                "validator": validator_name,
                "stake": stake,
                "K_i": K_i,
            })
        except Exception:
            pass

    # 注册完种子后，建立所有验证者的协同关系
    所有验证者 = [node.validator_name]
    for nid, info in node.known_nodes.items():
        v = info.get("validator", "")
        if v and v not in 所有验证者:
            所有验证者.append(v)

    # 建立全连接协同关系
    node.注册协同关系(所有验证者, 0.5)

    print(f"  ✅ [Node-{node_id}] P2P互联完成, 已知节点: {list(node.known_nodes.keys())}")
    print(f"  ✅ [Node-{node_id}] 验证者协同: {所有验证者}")

    # 主循环 — 保持进程运行
    try:
        while node.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n  ⏹ [Node-{node_id}] 停止中...")
        node.running = False
        server.shutdown()
        consensus_thread.stop()
        discovery_thread.stop()


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HKC节点进程")
    parser.add_argument("--node-id", type=int, required=True)
    parser.add_argument("--p2p-port", type=int, required=True)
    parser.add_argument("--rpc-port", type=int, required=True)
    parser.add_argument("--seeds", type=str, default="", help="逗号分隔的种子节点P2P端口")
    parser.add_argument("--validator", type=str, default="")
    parser.add_argument("--stake", type=float, default=5000)
    parser.add_argument("--K-i", type=float, default=50)
    args = parser.parse_args()

    seed_ports = [int(p) for p in args.seeds.split(",") if p.strip()]

    启动节点(
        node_id=args.node_id,
        p2p_port=args.p2p_port,
        rpc_port=args.rpc_port,
        seed_ports=seed_ports,
        validator_name=args.validator or f"Validator_{args.node_id}",
        stake=args.stake,
        K_i=args.K_i,
    )
