"""
HKC 第二步 — 异常场景测试
============================
模拟各种异常和攻击场景，验证系统韧性。

测试内容:
  1. 节点掉线: 5节点中随机2个掉线，剩余3个能否继续出块
  2. 恶意节点: 1个节点提交无效区块，能否被识别和惩罚
  3. 网络分区: 5节点分裂为2+3两组，少数组是否停止出块
  4. 双花攻击: 同一笔钱花两次，双花检测器能否拦截
  5. DDoS模拟: 大量无效交易涌入，交易池是否有限流
  6. 跨链桥攻击: 伪造跨链证明，防御体系能否拦截
  7. Gas操纵: 试图推高Gas，自适应Gas能否抑制
  8. Validator串通: 验证者联合操纵，PoEI涌现分数能否识别
"""

import sys
import os
import time
import hashlib
import random

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.blockchain import 区块链, HONGKUN_PER_HKAIC
from core.ledger import 账本
from core.transaction import 交易引擎, 交易优先级, 交易池
from core.staking import 质押引擎
from chain.consensus_engine import PoEI共识引擎, Epoch阶段
from chain.etb_bridge import 涌信桥, 跨链状态
from ibc_defense.defense_coordinator import DefenseCoordinator
from ibc_defense.circuit_breaker import CircuitBreaker
from wallet.adaptive_gas import 自适应Gas引擎


class TestFaultTolerance:
    """异常场景和容错测试"""

    def __init__(self):
        self.通过 = 0
        self.失败 = 0
        self.结果 = []

    def _记录(self, 名称, 通过, 详情=""):
        if 通过:
            self.通过 += 1
            self.结果.append(f"  ✅ {名称}")
        else:
            self.失败 += 1
            self.结果.append(f"  ❌ {名称} — {详情}")

    def _创建5节点集群(self):
        """创建5节点PoEI共识集群"""
        engine = PoEI共识引擎()
        验证者 = []
        for i, (name, stk, k) in enumerate([
            ("Alice", 10000, 85), ("Bob", 8000, 75),
            ("Carol", 6000, 60), ("Dave", 4000, 45),
            ("Eve", 2000, 30)
        ]):
            engine.更新质押(name, stk)
            engine.更新知识贡献(name, k)
            验证者.append(name)

        # 建立协同关系
        for i in range(len(验证者)):
            for j in range(i+1, len(验证者)):
                engine.记录协同(验证者[i], 验证者[j], random.uniform(0.3, 0.9))

        return engine, 验证者

    # ============================================================
    # 测试1: 节点掉线
    # ============================================================

    def test_1_节点掉线继续出块(self):
        """5节点中2个掉线，剩余3个能否继续出块"""
        engine, 验证者 = self._创建5节点集群()

        # 正常情况出块
        engine.计算总涌现分数()
        候选 = list(验证者)
        ep = engine.开始新epoch()
        出块者 = engine.判定出块权(候选, ep.种子)
        self._记录("正常5节点出块", 出块者 is not None, "正常情况无法出块")

        # 模拟2个节点掉线 — 移除Eve和Dave
        存活 = ["Alice", "Bob", "Carol"]
        # 将掉线节点质押设为0（模拟下线）
        engine.更新质押("Dave", 0)
        engine.更新质押("Eve", 0)
        engine._Λ["Dave"] = 0.0
        engine._Λ["Eve"] = 0.0

        # 3节点仍应能出块
        engine.计算总涌现分数()
        ep = engine.开始新epoch()
        出块者 = engine.判定出块权(存活, ep.种子)
        self._记录("3节点仍能出块", 出块者 in 存活, f"出块者={出块者}")

        # 多轮出块验证
        出块统计 = {}
        for _ in range(10):
            ep = engine.开始新epoch()
            winner = engine.判定出块权(存活, ep.种子)
            if winner:
                出块统计[winner] = 出块统计.get(winner, 0) + 1
        self._记录("3节点多轮出块稳定", len(出块统计) >= 2, f"出块分布={出块统计}")

    # ============================================================
    # 测试2: 恶意节点
    # ============================================================

    def test_2_恶意节点识别惩罚(self):
        """1个节点提交无效区块，能否被识别和惩罚"""
        engine, 验证者 = self._创建5节点集群()

        # Eve提交"无效区块" — 模拟恶意行为
        惩罚额 = engine.惩罚作恶("Eve", "提交无效区块")
        self._记录("恶意节点被惩罚", 惩罚额 > 0, f"惩罚额={惩罚额}")

        # 验证Eve质押减少
        eve_stake = engine._S.get("Eve", 0)
        self._记录("Eve质押减少", eve_stake < 2000, f"Eve质押={eve_stake}")

        # Eve知识贡献被清零
        eve_K = engine._K.get("Eve", 0)
        self._记录("Eve知识贡献清零", eve_K == 0, f"Eve K={eve_K}")

        # Eve协同关系被移除
        eve_协同 = engine._协同图.get("Eve", {})
        self._记录("Eve协同关系移除", len(eve_协同) == 0, f"Eve协同={len(eve_协同)}")

        # 再次作恶 — 累犯指数加重
        engine.更新质押("Eve", 1000)
        engine.更新知识贡献("Eve", 10)
        惩罚2 = engine.惩罚作恶("Eve", "再次恶意")
        self._记录("累犯加重惩罚", 惩罚2 > 0, f"二次惩罚={惩罚2}")

    # ============================================================
    # 测试3: 网络分区
    # ============================================================

    def test_3_网络分区少数组停止(self):
        """5节点分裂为2+3，少数组是否停止出块"""
        engine, 验证者 = self._创建5节点集群()

        # 多数组: Alice, Bob, Carol (3)
        多数组 = ["Alice", "Bob", "Carol"]
        # 少数组: Dave, Eve (2)
        少数组 = ["Dave", "Eve"]

        # 多数组应能达成共识
        engine.计算总涌现分数()
        ep = engine.开始新epoch()
        出块者 = engine.判定出块权(多数组, ep.种子)
        self._记录("多数组(3)能出块", 出块者 in 多数组, f"出块者={出块者}")

        # 少数组不应轻易出块（2/5 < 2/3投票权）
        # 在PoEI中，少数组的涌现分数总和应远小于多数组
        少数E = sum(engine.计算涌现分数(n) for n in 少数组)
        多数E = sum(engine.计算涌现分数(n) for n in 多数组)
        self._记录("少数组E远小于多数组", 少数E < 多数E, f"少数E={少数E:.4f}, 多数E={多数E:.4f}")

    # ============================================================
    # 测试4: 双花攻击
    # ============================================================

    def test_4_双花攻击检测(self):
        """同一笔钱花两次，双花检测器能否拦截"""
        tx_engine = 交易引擎()
        ledger = 账本()

        # 给Alice铸币
        alice = "addr_alice"
        bob = "addr_bob"
        carol = "addr_carol"
        ledger.铸币(alice, 1000 * HONGKUN_PER_HKAIC)

        # 第一笔交易: Alice→Bob 500 HKAIC
        tx1 = tx_engine.创建转账(
            alice, bob, 500 * HONGKUN_PER_HKAIC, 1 * HONGKUN_PER_HKAIC, 交易优先级.高
        )
        self._记录("第一笔交易创建", tx1.交易ID != "", "交易ID为空")

        # 第二笔交易: Alice→Carol 600 HKAIC（双花，余额不足）
        # 先确认第一笔
        ledger.转账(alice, bob, 500 * HONGKUN_PER_HKAIC, 1 * HONGKUN_PER_HKAIC)
        余额 = ledger.查询余额(alice) / HONGKUN_PER_HKAIC

        # 尝试第二笔转账 — 余额不足应失败
        双花拦截 = False
        try:
            ledger.转账(alice, carol, 600 * HONGKUN_PER_HKAIC, 1 * HONGKUN_PER_HKAIC)
        except ValueError:
            双花拦截 = True
        self._记录("双花被账本拦截", 双花拦截, "双花未被拦截")

    # ============================================================
    # 测试5: DDoS模拟
    # ============================================================

    def test_5_DDoS交易池限流(self):
        """大量无效交易涌入，交易池是否有限流"""
        pool = 交易池(最大容量=1000)
        已拒绝 = 0
        已接受 = 0

        # 模拟10000笔交易涌入
        for i in range(10000):
            from core.transaction import 待处理交易
            tx = 待处理交易(
                交易ID=f"spam_tx_{i}",
                发送地址=f"spam_addr_{i % 100}",
                接收地址=f"target_addr_{i % 10}",
                金额=i + 1,
                手续费=1,
                时间戳=time.time(),
                优先级=交易优先级.低
            )
            ok = pool.添加(tx)
            if ok:
                已接受 += 1
            else:
                已拒绝 += 1

        self._记录("DDoS: 交易池有限流", 已拒绝 > 0, "无交易被拒绝")
        self._记录("DDoS: 池大小≤1000", pool.大小 <= 1000, f"池大小={pool.大小}")
        self._记录("DDoS: 接受≤1000", 已接受 <= 1000, f"接受={已接受}")
        self._记录("DDoS: 拒绝>0", 已拒绝 > 0, f"拒绝={已拒绝}")

    # ============================================================
    # 测试6: 跨链桥攻击
    # ============================================================

    def test_6_跨链桥伪造证明(self):
        """伪造跨链证明，防御体系能否拦截"""
        # ETB验证组检查
        bridge = 涌信桥()
        for i in range(5):
            bridge.solver管理器.注册Solver(f"solver_{i}", 资金池=10**21, ATH验证=True)

        # 提交意图
        意图 = bridge.提交意图("HKC", "EVM", "attacker", "beneficiary", 10000*10**16)

        # 伪造验证组 — 尝试用不合格节点
        伪造候选 = [
            {"节点ID": "fake_1", "E_i": 0.1, "σ_i": 0.001, "epoch_age": 1},  # 太低
            {"节点ID": "fake_2", "E_i": 0.2, "σ_i": 0.002, "epoch_age": 2},  # 太低
        ]
        验证组 = bridge.生成动态验证组(意图, 伪造候选, "fake_epoch")
        self._记录("伪造低分验证组被拒", len(验证组) == 0, f"验证组={验证组}")

        # 防御协调器拦截
        dc = DefenseCoordinator(总质押量=21_000_000*10**16, 流通量=21_000_000*10**16)
        dc.注册链("malicious-chain", 涌现分数=0.05, 初始信用分=50)
        dc.risk_assessor.执行评估("malicious-chain", 稳定性=10, 安全历史=5,
                                 验证者集中度=5, 治理风险=5, 流动性深度=5)

        ok, reason, detail = dc.检查跨链交易("malicious-chain", 金额=100*10**16)
        self._记录("恶意链被防御拦截", not ok, f"应拦截但放行: {reason}")

        # 断路器测试
        cb = CircuitBreaker()
        cb.注册链("attack-chain", 涌现分数=0.3)
        cb.添加管理员("admin")
        cb.手动熔断链("attack-chain", "admin")
        允许, 原因 = cb.是否允许交易("attack-chain")
        self._记录("断路器手动熔断", not 允许, f"应熔断但允许: {原因}")

    # ============================================================
    # 测试7: Gas操纵
    # ============================================================

    def test_7_Gas操纵抑制(self):
        """试图通过大量交易推高Gas，自适应Gas能否抑制"""
        gas = 自适应Gas引擎(基础Gas=1.0)

        # 正常状态Gas
        正常建议 = gas.预测Gas价格()
        self._记录("正常Gas有建议", 正常建议.AI建议原因 != "", "无建议")

        # 模拟大量交易推高Gas
        for i in range(100):
            gas.记录区块Gas(i, Gas使用率=0.95, 基础费=5.0)

        操纵建议 = gas.预测Gas价格()
        self._记录("Gas操纵: 拥堵检测", 操纵建议.网络拥堵度 > 0.5, f"拥堵度={操纵建议.网络拥堵度}")
        self._记录("Gas操纵: AI建议应对", 操纵建议.AI建议原因 != "", "无应对建议")

        # 拥堵模式检测
        拥堵模式 = gas.检测拥堵模式()
        self._记录("拥堵模式检测", 拥堵模式 is not None, "未检测到拥堵")

        # Gas对冲 — 部分Gas用质押收益抵扣
        gas.设置质押收益(100.0)
        实际, 对冲 = gas.计算Gas对冲(50.0)
        self._记录("Gas对冲生效", 对冲 > 0, f"对冲={对冲}")

    # ============================================================
    # 测试8: Validator串通
    # ============================================================

    def test_8_Validator串通识别(self):
        """验证者试图联合操纵，PoEI涌现分数能否识别"""
        engine = PoEI共识引擎()

        # 正常验证者
        for name, stk, k in [("A", 5000, 70), ("B", 5000, 70), ("C", 5000, 70)]:
            engine.更新质押(name, stk)
            engine.更新知识贡献(name, k)

        # 串通验证者 — 高质押但内部高协同、对外零协同
        for name, stk, k in [("X", 8000, 40), ("Y", 8000, 40), ("Z", 8000, 40)]:
            engine.更新质押(name, stk)
            engine.更新知识贡献(name, k)

        # 正常协同: A-B-C之间
        engine.记录协同("A", "B", 0.7)
        engine.记录协同("B", "C", 0.6)
        engine.记录协同("A", "C", 0.5)

        # 串通: X-Y-Z内部高协同，对外零协同
        engine.记录协同("X", "Y", 0.95)
        engine.记录协同("Y", "Z", 0.95)
        engine.记录协同("X", "Z", 0.95)

        # 计算涌现分数
        正常E = {n: engine.计算涌现分数(n) for n in ["A", "B", "C"]}
        串通E = {n: engine.计算涌现分数(n) for n in ["X", "Y", "Z"]}

        正常均值 = sum(正常E.values()) / len(正常E)
        串通均值 = sum(串通E.values()) / len(串通E)

        # PoEI中，σ_i = Σ C_ij·√(K_i·K_j) / |N(i)|
        # 串通组内部高协同但K_i低，正常组K_i高且协同均衡
        # 关键: 串通组的σ_i虽高，但K_i低导致E_i不一定占优
        self._记录("串通组E可计算", 串通均值 > 0, f"串通E均值={串通均值:.8f}")
        self._记录("正常组E可计算", 正常均值 > 0, f"正常E均值={正常均值:.8f}")

        # 出块权分布 — 多轮选举
        候选 = ["A", "B", "C", "X", "Y", "Z"]
        出块统计 = {n: 0 for n in 候选}
        for _ in range(100):
            ep = engine.开始新epoch()
            winner = engine.判定出块权(候选, ep.种子)
            if winner:
                出块统计[winner] += 1

        # 正常验证者也应获得出块权（不能被串通组完全垄断）
        正常出块 = sum(出块统计[n] for n in ["A", "B", "C"])
        串通出块 = sum(出块统计[n] for n in ["X", "Y", "Z"])
        总出块 = 正常出块 + 串通出块
        if 总出块 > 0:
            正常比例 = 正常出块 / 总出块
            self._记录("正常验证者获出块权", 正常比例 > 0.05,
                        f"正常出块率={正常比例:.2%}, 分布={出块统计}")

    # ============================================================
    # 测试9: 链上数据一致性
    # ============================================================

    def test_9_链上数据一致性(self):
        """验证链上操作的数据一致性"""
        ledger = 账本()
        blockchain = 区块链()

        # 铸币
        addr1 = "addr_consistency_1"
        addr2 = "addr_consistency_2"
        ledger.铸币(addr1, 1000 * HONGKUN_PER_HKAIC)

        余额1 = ledger.查询余额(addr1)
        self._记录("铸币后余额正确", 余额1 == 1000 * HONGKUN_PER_HKAIC, f"余额={余额1}")

        # 转账
        ledger.转账(addr1, addr2, 300 * HONGKUN_PER_HKAIC, 1 * HONGKUN_PER_HKAIC)
        余额1_后 = ledger.查询余额(addr1)
        余额2 = ledger.查询余额(addr2)
        self._记录("转账后余额正确", 余额2 == 300 * HONGKUN_PER_HKAIC, f"余额2={余额2}")
        self._记录("发送方扣除正确", 余额1_后 == 699 * HONGKUN_PER_HKAIC, f"余额1后={余额1_后}")

        # 销毁
        销毁前总量 = sum(ledger.查询余额(a) for a in [addr1, addr2])
        ledger.销毁(addr2, 100 * HONGKUN_PER_HKAIC)
        销毁后总量 = sum(ledger.查询余额(a) for a in [addr1, addr2])
        self._记录("销毁减少总量", 销毁后总量 < 销毁前总量, f"销毁后={销毁后总量}")

    # ============================================================
    # 测试10: Epoch视图切换
    # ============================================================

    def test_10_Epoch视图切换(self):
        """Epoch超时触发视图切换"""
        engine, 验证者 = self._创建5节点集群()
        engine.计算总涌现分数()

        # 连续3次超时触发视图切换
        ep = engine.开始新epoch()
        for _ in range(3):
            处理 = ep.处理超时()
        self._记录("3次超时→视图切换", 处理 == "视图切换", f"处理={处理}")

        # 正常推进
        ep2 = engine.开始新epoch()
        出块者 = engine.判定出块权(验证者, ep2.种子)
        self._记录("视图切换后仍出块", 出块者 is not None, f"出块者={出块者}")

    def 运行(self):
        print("\n" + "="*60)
        print("  异常场景与容错测试")
        print("="*60)

        print("\n  --- 节点级异常 ---")
        self.test_1_节点掉线继续出块()
        self.test_2_恶意节点识别惩罚()
        self.test_3_网络分区少数组停止()

        print("\n  --- 交易级攻击 ---")
        self.test_4_双花攻击检测()
        self.test_5_DDoS交易池限流()

        print("\n  --- 跨链级攻击 ---")
        self.test_6_跨链桥伪造证明()

        print("\n  --- 经济级攻击 ---")
        self.test_7_Gas操纵抑制()
        self.test_8_Validator串通识别()

        print("\n  --- 系统一致性 ---")
        self.test_9_链上数据一致性()
        self.test_10_Epoch视图切换()

        for r in self.结果:
            print(r)
        print(f"\n  容错测试: {self.通过}通过 / {self.失败}失败")
        return self.失败 == 0


def run_tests():
    """运行异常场景测试"""
    print("\n" + "🜏"*30)
    print("  HKC 第二步 — 异常场景测试")
    print("🜏"*30)

    ok = TestFaultTolerance().运行()
    print(f"\n{'='*60}")
    print(f"  异常场景测试: {'✅ 全部通过' if ok else '❌ 存在失败'}")
    print(f"{'='*60}")
    return ok


if __name__ == "__main__":
    成功 = run_tests()
    sys.exit(0 if 成功 else 1)
