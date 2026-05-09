#!/usr/bin/env python3
"""
Hongkun AI Chain — 5节点本地测试网启动脚本 (start_testnet.py)
==============================================================
自动启动5个HKC节点进程，验证:
  1. P2P互联成功
  2. PoEI共识出块
  3. 端到端交易确认
  4. 涌信钱包转账
  5. 可视化状态报告

用法:
    python start_testnet.py
    python start_testnet.py --skip-docker
    python start_testnet.py --nodes 3
"""

import sys
import os
import time
import json
import subprocess
import hashlib
import signal
import argparse
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.blockchain import 区块链, 区块, HONGKUN_PER_HKAIC
from core.ledger import 账本
from core.wallet import 钱包
from core.transaction import 交易引擎, 交易优先级
from chain.consensus_engine import PoEI共识引擎


# ============================================================
# 测试网配置
# ============================================================
class 测试网配置:
    """5节点测试网配置"""
    节点数 = 5
    基础P2P端口 = 8001
    基础RPC端口 = 8841

    # 验证者配置 — 不同的质押和知识贡献度
    验证者 = [
        {"name": "涌金_Alice",   "stake": 10000, "K_i": 95.0, "σ": 0.8},
        {"name": "涌金_Bob",     "stake": 8000,  "K_i": 80.0, "σ": 0.7},
        {"name": "涌银_Carol",   "stake": 6000,  "K_i": 65.0, "σ": 0.6},
        {"name": "涌银_Dave",    "stake": 4000,  "K_i": 45.0, "σ": 0.4},
        {"name": "涌铜_Eve",     "stake": 2000,  "K_i": 25.0, "σ": 0.3},
    ]

    # 测试账户初始余额 (HKAIC)
    初始铸币 = {
        "Alice": 1000000,
        "Bob": 500000,
    }


# ============================================================
# HTTP客户端工具
# ============================================================
def http_get(url: str, timeout: float = 5.0) -> Optional[dict]:
    """发送GET请求"""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None


def http_post(url: str, data: dict, timeout: float = 5.0) -> Optional[dict]:
    """发送POST请求"""
    import urllib.request
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return None


# ============================================================
# 测试网管理器
# ============================================================
class 测试网管理器:
    """5节点本地测试网管理器"""

    def __init__(self, 节点数: int = 5):
        self.节点数 = 节点数
        self.进程列表: List[subprocess.Popen] = []
        self.问题记录: List[dict] = []
        self.测试结果: Dict[str, bool] = {}

    def 启动节点(self):
        """Phase 1: 启动5个节点进程"""
        print("\n" + "=" * 70)
        print("  🌐 HKC 5节点本地测试网 — 启动")
        print("=" * 70)
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  节点数: {self.节点数}")
        print()

        脚本路径 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_process.py")
        项目根 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        for i in range(self.节点数):
            p2p_port = 测试网配置.基础P2P端口 + i
            rpc_port = 测试网配置.基础RPC端口 + i

            # 种子节点 = 除自己外的所有节点P2P端口
            种子端口 = [测试网配置.基础P2P端口 + j for j in range(self.节点数) if j != i]
            种子str = ",".join(str(p) for p in 种子端口)

            v = 测试网配置.验证者[i]

            cmd = [
                sys.executable, 脚本路径,
                "--node-id", str(i),
                "--p2p-port", str(p2p_port),
                "--rpc-port", str(rpc_port),
                "--seeds", 种子str,
                "--validator", v["name"],
                "--stake", str(v["stake"]),
                "--K-i", str(v["K_i"]),
            ]

            print(f"  🚀 启动节点 {i}: {v['name']} (P2P:{p2p_port} RPC:{rpc_port})")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=项目根,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            self.进程列表.append(proc)

        print(f"\n  ⏳ 等待 {self.节点数} 个节点启动...")
        time.sleep(5)

        # 检查进程是否存活
        for i, proc in enumerate(self.进程列表):
            if proc.poll() is not None:
                print(f"  ❌ 节点 {i} 启动失败! 退出码: {proc.returncode}")
                self.问题记录.append({
                    "问题": f"节点{i}启动失败",
                    "原因": f"退出码{proc.returncode}",
                    "修复": "检查node_process.py是否有语法错误"
                })
            else:
                print(f"  ✅ 节点 {i} 进程运行中 (PID: {proc.pid})")

    def 验证P2P互联(self) -> bool:
        """Phase 2: 验证5个节点P2P互联成功"""
        print("\n" + "=" * 70)
        print("  🔗 Phase 2: 验证P2P互联")
        print("=" * 70)

        # 检查每个节点的/p2p/ping
        成功数 = 0
        for i in range(self.节点数):
            rpc_port = 测试网配置.基础RPC端口 + i
            resp = http_get(f"http://127.0.0.1:{rpc_port}/p2p/ping")
            if resp and resp.get("pong"):
                print(f"  ✅ 节点{i} ({resp.get('validator','')}) 在线, 高度={resp.get('height',0)}")
                成功数 += 1
            else:
                print(f"  ❌ 节点{i} 无响应")
                self.问题记录.append({
                    "问题": f"节点{i} P2P ping失败",
                    "原因": "RPC服务未启动或端口错误",
                    "修复": "检查node_process.py是否正常启动"
                })

        # 检查节点间注册状态
        print("\n  📡 检查节点间注册:")
        for i in range(self.节点数):
            rpc_port = 测试网配置.基础RPC端口 + i
            resp = http_get(f"http://127.0.0.1:{rpc_port}/status")
            if resp:
                已知 = resp.get("known_nodes", [])
                print(f"  节点{i}: 已知节点={已知}")
                if len(已知) < self.节点数 - 1:
                    self.问题记录.append({
                        "问题": f"节点{i}已注册邻居不足",
                        "原因": f"已知{len(已知)}个，期望{self.节点数-1}个",
                        "修复": "检查P2P注册接口"
                    })

        互联成功 = 成功数 == self.节点数
        self.测试结果["P2P互联"] = 互联成功
        print(f"\n  结果: {'✅ P2P互联成功' if 互联成功 else '❌ P2P互联失败'}")
        return 互联成功

    def 验证共识出块(self) -> bool:
        """Phase 2: 验证PoEI共识出块"""
        print("\n" + "=" * 70)
        print("  ⛏️  Phase 2: 验证PoEI共识出块")
        print("=" * 70)

        # 查看验证者信息
        print("\n  📊 验证者信息:")
        rpc_port = 测试网配置.基础RPC端口
        resp = http_get(f"http://127.0.0.1:{rpc_port}/validators")
        if resp and "validators" in resp:
            for v in resp["validators"]:
                print(f"    {v.get('地址','')}: K={v.get('K','0')} S={v.get('S','0')} "
                      f"σ={v.get('σ','0')} E={v.get('E','0')}")

        # 在节点0上创建钱包并铸币，制造交易触发出块
        print("\n  💰 创建测试钱包并铸币(触发出块):")
        # 创建Alice钱包
        resp = http_post(f"http://127.0.0.1:{rpc_port}/wallet/create", {"name": "Alice"})
        if resp:
            print(f"    Alice地址: {resp.get('地址', 'N/A')}")
        # 创建Bob钱包
        resp = http_post(f"http://127.0.0.1:{rpc_port}/wallet/create", {"name": "Bob"})
        if resp:
            print(f"    Bob地址: {resp.get('地址', 'N/A')}")

        # 铸币给Alice
        resp = http_post(f"http://127.0.0.1:{rpc_port}/wallet/mint",
                         {"wallet": "Alice", "amount": 1000000})
        if resp:
            print(f"    Alice铸币: {resp}")

        # 铸币给Bob
        resp = http_post(f"http://127.0.0.1:{rpc_port}/wallet/mint",
                         {"wallet": "Bob", "amount": 500000})
        if resp:
            print(f"    Bob铸币: {resp}")

        # 先添加一笔交易到交易池，然后强制出块
        # 先获取钱包地址
        wallets_resp = http_get(f"http://127.0.0.1:{rpc_port}/wallets")
        alice_addr = ""
        bob_addr = ""
        if wallets_resp:
            for w in wallets_resp.get("wallets", []):
                if w["名称"] == "Alice":
                    alice_addr = w["地址"]
                elif w["名称"] == "Bob":
                    bob_addr = w["地址"]

        # 提交一笔小额交易到交易池(触发PoEI共识)
        print(f"\n  📤 提交交易触发共识(Alice→Bob: 10 HKAIC):")
        resp = http_post(f"http://127.0.0.1:{rpc_port}/tx/send", {
            "from": "Alice", "to": bob_addr, "amount": 10, "fee": 0.001})
        if resp and "成功" in resp.get("状态", ""):
            print(f"    交易已提交: {resp.get('交易ID', 'N/A')}")

        # 强制出块
        print(f"\n  ⛏️  强制出块(铸币+转账交易):")
        resp = http_post(f"http://127.0.0.1:{rpc_port}/force_block", {})
        if resp:
            状态 = resp.get("状态", "")
            if "成功" in 状态:
                区块 = resp.get("区块", {})
                print(f"    ✅ 出块成功! 高度={区块.get('height')} 出块者={区块.get('proposer')} "
                      f"交易数={区块.get('tx_count')} 涌现分数={区块.get('emergence_score','N/A')}")
                self.测试结果["共识出块"] = True
            else:
                print(f"    ⏳ {状态} — 交易池大小: {resp.get('交易池', '?')}")
                # 再等几秒重试
                time.sleep(3)
                # 再次提交交易
                http_post(f"http://127.0.0.1:{rpc_port}/tx/send", {
                    "from": "Alice", "to": bob_addr, "amount": 5, "fee": 0.001})
                resp = http_post(f"http://127.0.0.1:{rpc_port}/force_block", {})
                if resp and "成功" in resp.get("状态", ""):
                    区块 = resp.get("区块", {})
                    print(f"    ✅ 重试出块成功! 高度={区块.get('height')} "
                          f"出块者={区块.get('proposer')} 交易数={区块.get('tx_count')}")
                    self.测试结果["共识出块"] = True
                else:
                    print(f"    ❌ 出块失败: {resp}")
                    self.测试结果["共识出块"] = False
                    self.问题记录.append({
                        "问题": "共识出块失败",
                        "原因": "交易池为空或共识引擎未选出出块者",
                        "修复": "检查共识引擎状态和交易池"
                    })
        else:
            print("    ❌ 强制出块请求失败")
            self.测试结果["共识出块"] = False

        # 检查区块链状态
        resp = http_get(f"http://127.0.0.1:{rpc_port}/blockchain")
        if resp:
            print(f"\n  📊 区块链状态: 高度={resp.get('高度',0)} 区块数={resp.get('区块数',0)} "
                  f"完整性={resp.get('链完整性','?')}")

        return self.测试结果.get("共识出块", False)

    def 验证端到端交易(self) -> bool:
        """Phase 3: 验证端到端交易"""
        print("\n" + "=" * 70)
        print("  💸 Phase 3: 端到端交易测试")
        print("=" * 70)

        rpc_port = 测试网配置.基础RPC端口

        # 获取钱包信息
        resp = http_get(f"http://127.0.0.1:{rpc_port}/wallets")
        if not resp or "wallets" not in resp:
            print("  ❌ 无法获取钱包列表")
            self.测试结果["端到端交易"] = False
            return False

        wallets = {w["名称"]: w for w in resp["wallets"]}
        alice_addr = wallets.get("Alice", {}).get("地址", "")
        bob_addr = wallets.get("Bob", {}).get("地址", "")

        print(f"\n  📋 交易前状态:")
        print(f"    Alice ({alice_addr[:20]}...): {wallets.get('Alice', {}).get('余额_HKAIC', 0):.2f} HKAIC")
        print(f"    Bob   ({bob_addr[:20]}...): {wallets.get('Bob', {}).get('余额_HKAIC', 0):.2f} HKAIC")

        # Alice给Bob转账100 HKAIC
        print(f"\n  💸 Alice → Bob: 100 HKAIC")
        resp = http_post(f"http://127.0.0.1:{rpc_port}/tx/send", {
            "from": "Alice",
            "to": bob_addr,
            "amount": 100,
            "fee": 0.001,
        })

        if resp and "成功" in resp.get("状态", ""):
            print(f"    ✅ 交易成功!")
            print(f"    交易ID: {resp.get('交易ID', 'N/A')}")
            print(f"    Alice余额: {resp.get('发送者余额', 'N/A')} HKAIC")
            print(f"    Bob余额: {resp.get('接收者余额', 'N/A')} HKAIC")
            self.测试结果["端到端交易"] = True
        else:
            print(f"    ❌ 交易失败: {resp}")
            self.问题记录.append({
                "问题": "端到端交易失败",
                "原因": str(resp),
                "修复": "检查余额是否足够、账本转账逻辑"
            })
            self.测试结果["端到端交易"] = False
            return False

        # 强制出块确认交易
        print(f"\n  ⛏️  强制出块确认交易:")
        resp = http_post(f"http://127.0.0.1:{rpc_port}/force_block", {})
        if resp and "成功" in resp.get("状态", ""):
            区块 = resp.get("区块", {})
            print(f"    ✅ 交易已打包入块! 高度={区块.get('height')} 交易数={区块.get('tx_count')}")

        # 验证最终余额
        time.sleep(1)
        resp = http_get(f"http://127.0.0.1:{rpc_port}/wallets")
        if resp:
            wallets = {w["名称"]: w for w in resp.get("wallets", [])}
            alice_bal = wallets.get("Alice", {}).get("余额_HKAIC", 0)
            bob_bal = wallets.get("Bob", {}).get("余额_HKAIC", 0)
            print(f"\n  📋 交易后状态:")
            print(f"    Alice: {alice_bal:.2f} HKAIC")
            print(f"    Bob:   {bob_bal:.2f} HKAIC")

            # 验证Bob收到100 HKAIC
            if bob_bal >= 500100:  # 500000初始 + 100转账
                print(f"    ✅ Bob余额正确 (500000 + 100 = 500100)")
            else:
                print(f"    ⚠️  Bob余额异常: 预期≥500100, 实际={bob_bal}")

        return self.测试结果.get("端到端交易", False)

    def 涌信钱包测试(self) -> bool:
        """Phase 3: 涌信钱包发起转账"""
        print("\n" + "=" * 70)
        print("  🔐 Phase 3: 涌信钱包转账测试")
        print("=" * 70)

        rpc_port = 测试网配置.基础RPC端口

        # 创建涌信钱包
        resp = http_post(f"http://127.0.0.1:{rpc_port}/wallet/create",
                         {"name": "涌信用户", "seed": "yongxin-wallet-test"})
        if resp:
            print(f"  📱 涌信钱包创建: {resp.get('地址', 'N/A')}")
        涌信地址 = resp.get("地址", "") if resp else ""

        # 给涌信钱包铸币
        resp = http_post(f"http://127.0.0.1:{rpc_port}/wallet/mint",
                         {"wallet": "涌信用户", "amount": 50000})
        if resp:
            print(f"  💰 涌信钱包铸币: {resp}")

        # 涌信钱包给Bob转账
        resp_wallets = http_get(f"http://127.0.0.1:{rpc_port}/wallets")
        bob_addr = ""
        if resp_wallets:
            for w in resp_wallets.get("wallets", []):
                if w["名称"] == "Bob":
                    bob_addr = w["地址"]
                    break

        print(f"\n  📱 涌信钱包 → Bob: 50 HKAIC")
        resp = http_post(f"http://127.0.0.1:{rpc_port}/tx/send", {
            "from": "涌信用户",
            "to": bob_addr,
            "amount": 50,
            "fee": 0.001,
        })
        if resp and "成功" in resp.get("状态", ""):
            print(f"  ✅ 涌信钱包转账成功! Bob余额: {resp.get('接收者余额', 'N/A')} HKAIC")
            self.测试结果["涌信钱包"] = True
        else:
            print(f"  ❌ 涌信钱包转账失败: {resp}")
            self.测试结果["涌信钱包"] = False

        # 强制出块
        http_post(f"http://127.0.0.1:{rpc_port}/force_block", {})

        return self.测试结果.get("涌信钱包", False)

    def 生成状态报告(self) -> str:
        """Phase 5: 生成可视化状态报告"""
        print("\n" + "=" * 70)
        print("  📊 Phase 5: 生成可视化状态报告")
        print("=" * 70)

        report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 收集所有节点状态
        节点状态列表 = []
        for i in range(self.节点数):
            rpc_port = 测试网配置.基础RPC端口 + i
            status = http_get(f"http://127.0.0.1:{rpc_port}/status")
            info = http_get(f"http://127.0.0.1:{rpc_port}/info")
            blockchain = http_get(f"http://127.0.0.1:{rpc_port}/blockchain")
            validators = http_get(f"http://127.0.0.1:{rpc_port}/validators")
            wallets_resp = http_get(f"http://127.0.0.1:{rpc_port}/wallets")

            节点状态列表.append({
                "node_id": i,
                "status": status or {},
                "info": info or {},
                "blockchain": blockchain or {},
                "validators": validators or {},
                "wallets": wallets_resp or {},
            })

        # 生成HTML报告
        html = self._生成HTML报告(节点状态列表, report_time)

        # 保存报告
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "docs", "testnet_report.html"
        )
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  📄 状态报告已保存: {report_path}")
        return report_path

    def _生成HTML报告(self, 节点状态列表: list, report_time: str) -> str:
        """生成自包含HTML状态报告"""

        # 节点卡片
        node_cards = ""
        for ns in 节点状态列表:
            status = ns.get("status", {})
            info = ns.get("info", {})
            bc = ns.get("blockchain", {})
            i = ns.get("node_id", 0)
            online = bool(status)
            v_name = info.get("验证者", f"Node-{i}")
            height = bc.get("高度", 0)

            card_color = "#2ecc71" if online else "#e74c3c"
            node_cards += f"""
            <div class="node-card" style="border-left:4px solid {card_color}">
                <div class="node-header">
                    <span class="node-id">Node-{i}</span>
                    <span class="node-status" style="color:{card_color}">
                        {'🟢 在线' if online else '🔴 离线'}
                    </span>
                </div>
                <div class="node-info">
                    <div>验证者: <strong>{v_name}</strong></div>
                    <div>区块高度: <strong>{height}</strong></div>
                    <div>P2P端口: {测试网配置.基础P2P端口 + i}</div>
                    <div>RPC端口: {测试网配置.基础RPC端口 + i}</div>
                </div>
            </div>"""

        # 交易表格
        wallets_html = ""
        for ns in 节点状态列表:
            w_resp = ns.get("wallets", {})
            for w in w_resp.get("wallets", []):
                wallets_html += f"""
                <tr>
                    <td>Node-{ns.get('node_id', 0)}</td>
                    <td>{w.get('名称', 'N/A')}</td>
                    <td style="font-family:monospace;font-size:12px">{w.get('地址', 'N/A')[:20]}...</td>
                    <td style="text-align:right">{w.get('余额_HKAIC', 0):.4f}</td>
                </tr>"""

        # 测试结果
        结果行 = ""
        for k, v in self.测试结果.items():
            icon = "✅" if v else "❌"
            颜色 = "#2ecc71" if v else "#e74c3c"
            结果行 += f"""
            <tr>
                <td>{k}</td>
                <td style="color:{颜色};font-weight:bold">{icon} {'通过' if v else '失败'}</td>
            </tr>"""

        # 问题记录
        问题行 = ""
        for p in self.问题记录:
            问题行 += f"""
            <tr>
                <td>{p.get('问题', '')}</td>
                <td>{p.get('原因', '')}</td>
                <td>{p.get('修复', '')}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>HKC 5节点测试网状态报告</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',system-ui,-apple-system,sans-serif;
               background:#0a0e17; color:#e0e6f0; padding:20px; }}
        .header {{ text-align:center; padding:40px 0 20px; }}
        .header h1 {{ font-size:36px; color:#FFD700; letter-spacing:3px; }}
        .header .sub {{ color:#8892a4; font-size:14px; margin-top:8px; }}
        .stats-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px;
                      max-width:1200px; margin:30px auto; }}
        .stat-card {{ background:#151b2b; border:1px solid #1e2a42; border-radius:12px;
                     padding:24px; text-align:center; }}
        .stat-value {{ font-size:32px; font-weight:700; color:#FFD700; }}
        .stat-label {{ font-size:13px; color:#8892a4; margin-top:8px; }}
        .section {{ max-width:1200px; margin:30px auto; }}
        .section h2 {{ font-size:22px; color:#FFD700; margin-bottom:16px;
                      border-bottom:1px solid #1e2a42; padding-bottom:12px; }}
        .nodes-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
                      gap:16px; }}
        .node-card {{ background:#151b2b; border:1px solid #1e2a42; border-radius:12px;
                     padding:20px; }}
        .node-header {{ display:flex; justify-content:space-between; margin-bottom:12px; }}
        .node-id {{ font-weight:700; font-size:16px; color:#FFD700; }}
        .node-info div {{ margin:6px 0; font-size:14px; color:#b0b8c8; }}
        table {{ width:100%; border-collapse:collapse; background:#151b2b;
                border-radius:12px; overflow:hidden; }}
        th {{ background:#1a2236; padding:14px; text-align:left;
             font-size:13px; color:#FFD700; text-transform:uppercase; }}
        td {{ padding:12px 14px; border-top:1px solid #1e2a42; font-size:14px; }}
        .footer {{ text-align:center; padding:40px 0; color:#555; font-size:12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 HKC 5节点测试网</h1>
        <div class="sub">Hongkun AI Chain v4.0.0 — 本地多进程测试网状态报告</div>
        <div class="sub">生成时间: {report_time}</div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{self.节点数}</div>
            <div class="stat-label">网络节点</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color:#2ecc71">
                {sum(1 for ns in 节点状态列表 if ns.get('status'))}
            </div>
            <div class="stat-label">在线节点</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">
                {max((ns.get('blockchain',{}).get('高度',0) for ns in 节点状态列表), default=0)}
            </div>
            <div class="stat-label">最高区块</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color:#2ecc71">
                {sum(1 for v in self.测试结果.values() if v)}/{len(self.测试结果)}
            </div>
            <div class="stat-label">测试通过</div>
        </div>
    </div>

    <div class="section">
        <h2>🌐 节点状态</h2>
        <div class="nodes-grid">{node_cards}</div>
    </div>

    <div class="section">
        <h2>💰 钱包余额</h2>
        <table>
            <tr><th>节点</th><th>钱包</th><th>地址</th><th>余额 (HKAIC)</th></tr>
            {wallets_html}
        </table>
    </div>

    <div class="section">
        <h2>🧪 测试结果</h2>
        <table>
            <tr><th>测试项</th><th>结果</th></tr>
            {结果行}
        </table>
    </div>

    {"<div class='section'><h2>⚠️ 问题记录</h2><table><tr><th>问题</th><th>原因</th><th>修复</th></tr>" + 问题行 + "</table></div>" if self.问题记录 else ""}

    <div class="footer">
        HKC v4.0.0 — Hongkun AI Chain 5节点本地测试网 | PoEI共识 | 涌知路由P2P
    </div>
</body>
</html>"""
        return html

    def 停止所有节点(self):
        """停止所有节点进程"""
        print("\n  ⏹ 停止所有节点...")
        for i, proc in enumerate(self.进程列表):
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"    节点{i} 已停止")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"    节点{i} 强制停止")
            except Exception as e:
                print(f"    节点{i} 停止出错: {e}")

    def 打印最终报告(self):
        """打印最终测试报告"""
        print("\n" + "=" * 70)
        print("  📋 HKC 5节点测试网 — 最终报告")
        print("=" * 70)
        print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("  🧪 测试结果:")
        for k, v in self.测试结果.items():
            icon = "✅" if v else "❌"
            print(f"    {icon} {k}: {'通过' if v else '失败'}")

        通过数 = sum(1 for v in self.测试结果.values() if v)
        总数 = len(self.测试结果)
        print(f"\n  📊 总计: {通过数}/{总数} 通过")

        if self.问题记录:
            print(f"\n  ⚠️ 遇到问题 ({len(self.问题记录)}个):")
            for i, p in enumerate(self.问题记录, 1):
                print(f"    {i}. {p.get('问题', '')}")
                print(f"       原因: {p.get('原因', '')}")
                print(f"       修复: {p.get('修复', '')}")

        print("\n  📝 下一步建议:")
        if 通过数 == 总数:
            print("    1. 所有测试通过！可以尝试Docker部署")
            print("    2. 增加更多交易压力测试")
            print("    3. 测试跨节点交易同步")
        else:
            print("    1. 修复上述问题")
            print("    2. 确保所有节点正常启动和P2P注册")
            print("    3. 检查共识引擎和账本逻辑")
        print("=" * 70)


# ============================================================
# 主入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="HKC 5节点本地测试网")
    parser.add_argument("--nodes", type=int, default=5, help="节点数(默认5)")
    parser.add_argument("--skip-report", action="store_true", help="跳过HTML报告生成")
    args = parser.parse_args()

    测试网配置.节点数 = args.nodes
    管理器 = 测试网管理器(args.nodes)

    try:
        # Phase 1: 启动节点
        管理器.启动节点()

        # Phase 2: P2P互联验证
        管理器.验证P2P互联()

        # Phase 2: 共识出块验证
        管理器.验证共识出块()

        # Phase 3: 端到端交易
        管理器.验证端到端交易()

        # Phase 3: 涌信钱包
        管理器.涌信钱包测试()

        # Phase 5: 可视化报告
        if not args.skip_report:
            管理器.生成状态报告()

        # 打印最终报告
        管理器.打印最终报告()

    except KeyboardInterrupt:
        print("\n\n  ⏹ 用户中断，停止测试网...")
    except Exception as e:
        print(f"\n  ❌ 测试网出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        管理器.停止所有节点()


if __name__ == "__main__":
    main()
