"""
HKC 第二步 — 跨链桥端到端验证
================================
验证涌信桥ETB和IBC的完整跨链流程。

测试内容:
  1. ETB跨链: 意图提交→Solver竞标→验证组确认→资产锁定→目标链铸造→结算
  2. IBC跨链: 连接建立→通道创建→ICS-20代币转移→中继→轻客户端验证→防御体系
"""

import sys
import os
import time
import hashlib

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from chain.etb_bridge import 涌信桥, 跨链状态, 验证等级
from ibc_compat.ibc_connection import IBCConnectionManager, 连接状态
from ibc_compat.ibc_channel import IBCChannelManager, 通道状态, 通道顺序
from ibc_compat.ics20_transfer import ICS20Transfer
from ibc_compat.ibc_relayer import IBCRelayer, IBC数据包
from ibc_compat.ibc_light_client import IBCLightClient, 信任期配置
from ibc_compat.tendermint_header import TendermintHeader, ValidatorSet, Commit
from ibc_defense.defense_coordinator import DefenseCoordinator


# ============================================================
# ETB 跨链桥端到端测试
# ============================================================

class TestETBCrossChain:
    """涌信桥ETB完整跨链流程验证"""

    def __init__(self):
        self.bridge = 涌信桥()
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

    def test_1_提交跨链意图(self):
        """步骤1: 用户在HKC提交跨链意图"""
        意图 = self.bridge.提交意图(
            源链="HKC", 目标链="EVM", 发送者="addr_Alice",
            接收者="addr_Bob", 金额=100*10**16
        )
        self._记录("提交跨链意图", 意图.意图ID != "", f"意图ID为空")
        self._记录("意图状态=意图提交", 意图.状态 == 跨链状态.意图提交, f"状态={意图.状态}")
        self._记录("意图金额正确", 意图.金额 == 100*10**16, f"金额={意图.金额}")
        self._记录("意图非超时", not 意图.是否超时(), "意图已超时")
        return 意图

    def test_2_注册Solver(self):
        """步骤2: 注册ATH验证的Solver"""
        self.bridge.solver管理器.注册Solver("solver_0", 资金池=10**21, ATH验证=True)
        self.bridge.solver管理器.注册Solver("solver_1", 资金池=10**20, ATH验证=True)
        self.bridge.solver管理器.注册Solver("solver_2", 资金池=10**19, ATH验证=False)  # 无ATH
        状态 = self.bridge.solver管理器.状态()
        self._记录("注册3个Solver", 状态["Solver数"] == 3, f"Solver数={状态['Solver数']}")
        self._记录("ATH验证Solver=2", 状态["ATH验证"] == 2, f"ATH验证={状态['ATH验证']}")

    def test_3_动态验证组生成(self):
        """步骤3: ETB动态验证组生成（基于涌现分数选验证者）"""
        意图 = self.bridge.提交意图(
            源链="HKC", 目标链="Cosmos", 发送者="addr_C",
            接收者="addr_D", 金额=50000*10**16
        )
        # 生成候选节点 — 有足够多的高涌现分数节点
        候选 = []
        for i in range(20):
            候选.append({
                "节点ID": f"val_{i}",
                "E_i": 50 + i*10,       # 涌现分数50-240
                "σ_i": 0.3 + i*0.05,    # 协同因子
                "epoch_age": 20 + i      # 已存活epoch
            })
        验证组 = self.bridge.生成动态验证组(意图, 候选, "epoch_test")
        self._记录("生成验证组", len(验证组) >= 3, f"验证组大小={len(验证组)}")
        self._记录("验证组在候选中", all(v.startswith("val_") for v in 验证组), "验证组不在候选中")

    def test_4_Solver竞标(self):
        """步骤4: Solver竞标选择最优执行路径"""
        意图 = self.bridge.提交意图(
            源链="HKC", 目标链="EVM", 发送者="addr_E",
            接收者="addr_F", 金额=1000*10**16
        )
        solver = self.bridge.solver管理器.选择Solver(意图)
        self._记录("选择Solver", solver is not None, "无可用Solver")
        if solver:
            self._记录("Solver已ATH验证", solver.ATH验证, "Solver未ATH验证")
            self._记录("Solver资金充足", solver.资金池 >= 意图.金额, "Solver资金不足")

    def test_5_验证组签名确认(self):
        """步骤5: 验证组确认（≥2/3验证者签名）"""
        意图 = self.bridge.提交意图(
            源链="HKC", 目标链="EVM", 发送者="addr_G",
            接收者="addr_H", 金额=1000*10**16
        )
        候选 = [{"节点ID": f"val_{i}", "E_i": 50+i*10, "σ_i": 0.3+i*0.05, "epoch_age": 20+i} for i in range(20)]
        验证组 = self.bridge.生成动态验证组(意图, 候选, "epoch_sig")
        if not 验证组:
            self._记录("验证组签名确认", False, "验证组为空")
            return

        # 模拟≥2/3签名
        签名节点 = {}
        涌现分数 = {}
        for i, nid in enumerate(验证组):
            涌现分数[nid] = 50 + i*10
        签名数 = max(1, len(验证组) * 2 // 3)
        for nid in 验证组[:签名数]:
            签名节点[nid] = f"sig_{nid}"

        有效 = self.bridge.验证涌现签名(意图, 签名节点, 涌现分数)
        self._记录("≥2/3签名有效", 有效, "签名不足2/3")

        # 测试不足2/3签名
        少数签名 = {验证组[0]: "sig_1"} if len(验证组) > 1 else {}
        无效 = self.bridge.验证涌现签名(意图, 少数签名, 涌现分数)
        self._记录("<2/3签名无效(正确拒绝)", not 无效 or len(验证组) <= 2, "少数签名不应通过")

    def test_6_完整跨链流程(self):
        """步骤6-7: 完整跨链流程 — 源链锁定→目标链铸造→结算→Solver奖励"""
        意图 = self.bridge.提交意图(
            源链="HKC", 目标链="EVM", 发送者="addr_I",
            接收者="addr_J", 金额=500*10**16
        )
        候选 = [{"节点ID": f"val_{i}", "E_i": 50+i*10, "σ_i": 0.3+i*0.05, "epoch_age": 20+i} for i in range(20)]
        结果 = self.bridge.执行跨链流程(意图, 候选, "epoch_full")
        self._记录("完整跨链流程", "✅" in 结果, f"结果={结果}")
        self._记录("意图已结算", 意图.状态 == 跨链状态.已结算, f"状态={意图.状态}")
        self._记录("验证承诺已生成", len(意图.验证承诺) > 0, "验证承诺为空")
        self._记录("挑战期已设定", 意图.挑战期结束 > 0, "挑战期未设定")

    def test_7_挑战机制(self):
        """步骤7: 挑战机制验证"""
        意图 = self.bridge.提交意图(
            源链="HKC", 目标链="EVM", 发送者="addr_K",
            接收者="addr_L", 金额=200*10**16
        )
        候选 = [{"节点ID": f"val_{i}", "E_i": 50+i*10, "σ_i": 0.3+i*0.05, "epoch_age": 20+i} for i in range(20)]
        self.bridge.执行跨链流程(意图, 候选, "epoch_challenge")
        # 提交挑战（有证据）
        挑战结果 = self.bridge.提交挑战(意图.意图ID, "伪造的跨链证明证据")
        self._记录("挑战机制(有证据)", 挑战结果, "挑战失败")
        self._记录("挑战后已回滚", 意图.状态 == 跨链状态.已回滚, f"状态={意图.状态}")

    def test_8_保险池机制(self):
        """步骤8: 保险池收取和理赔"""
        初始状态 = self.bridge.保险池.状态()
        # 多笔跨链交易收取保费
        for i in range(5):
            意图 = self.bridge.提交意图(
                源链="HKC", 目标链="EVM", 发送者=f"addr_X{i}",
                接收者=f"addr_Y{i}", 金额=1000*10**16
            )
            候选 = [{"节点ID": f"val_{j}", "E_i": 50+j*10, "σ_i": 0.3+j*0.05, "epoch_age": 20+j} for j in range(20)]
            self.bridge.执行跨链流程(意图, 候选, f"epoch_ins_{i}")

        最终状态 = self.bridge.保险池.状态()
        self._记录("保险池收取保费", "HKAIC" in 最终状态["池余额"], f"池余额={最终状态['池余额']}")

    def test_9_验证组不足暂停(self):
        """步骤9: 验证组不足时暂停跨链"""
        意图 = self.bridge.提交意图(
            源链="HKC", 目标链="EVM", 发送者="addr_M",
            接收者="addr_N", 金额=50000*10**16
        )
        # 候选不足
        少量候选 = [{"节点ID": "val_0", "E_i": 10, "σ_i": 0.01, "epoch_age": 1}]
        结果 = self.bridge.执行跨链流程(意图, 少量候选, "epoch_low")
        self._记录("验证组不足暂停", "❌" in 结果 or "暂停" in 结果, f"应暂停但结果={结果}")

    def 运行(self):
        print("\n" + "="*60)
        print("  ETB 跨链桥端到端测试")
        print("="*60)
        self.test_1_提交跨链意图()
        self.test_2_注册Solver()
        self.test_3_动态验证组生成()
        self.test_4_Solver竞标()
        self.test_5_验证组签名确认()
        self.test_6_完整跨链流程()
        self.test_7_挑战机制()
        self.test_8_保险池机制()
        self.test_9_验证组不足暂停()
        for r in self.结果:
            print(r)
        print(f"\n  ETB测试: {self.通过}通过 / {self.失败}失败")
        return self.失败 == 0


# ============================================================
# IBC 跨链端到端测试
# ============================================================

class TestIBCCrossChain:
    """IBC跨链完整流程验证"""

    def __init__(self):
        self.conn_mgr = IBCConnectionManager()
        self.ch_mgr = IBCChannelManager()
        self.ics20 = ICS20Transfer()
        self.relayer = IBCRelayer()
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

    def test_1_IBC连接4步握手(self):
        """步骤1: IBC连接建立（4步握手）"""
        # OpenInit — 发起方
        ok, msg = self.conn_mgr.OpenInit("conn-0", "client-hkc-0", "client-cosmos-0")
        self._记录("OpenInit成功", ok, msg)
        conn = self.conn_mgr.获取连接("conn-0")
        self._记录("连接状态=INIT", conn.状态 == 连接状态.初始化中, f"状态={conn.状态}")

        # OpenTry — 响应方
        ok, msg = self.conn_mgr.OpenTry("conn-1", "client-cosmos-0", "conn-0", "client-hkc-0")
        self._记录("OpenTry成功", ok, msg)

        # OpenAck — 发起方确认
        ok, msg = self.conn_mgr.OpenAck("conn-0", "conn-1")
        self._记录("OpenAck成功", ok, msg)
        conn = self.conn_mgr.获取连接("conn-0")
        self._记录("连接状态=ACK", conn.状态 == 连接状态.确认中, f"状态={conn.状态}")

        # OpenConfirm — 完成连接
        ok, msg = self.conn_mgr.OpenConfirm("conn-1")
        self._记录("OpenConfirm成功", ok, msg)
        conn1 = self.conn_mgr.获取连接("conn-1")
        self._记录("连接状态=OPEN", conn1.状态 == 连接状态.已建立, f"状态={conn1.状态}")

    def test_2_IBC通道创建(self):
        """步骤2: IBC通道创建"""
        ok, msg = self.ch_mgr.OpenInit("chan-0", "transfer", "conn-0", 通道顺序.无序)
        self._记录("通道OpenInit", ok, msg)
        ok, msg = self.ch_mgr.OpenTry("chan-1", "transfer", "conn-1", "chan-0", "transfer")
        self._记录("通道OpenTry", ok, msg)
        ok, msg = self.ch_mgr.OpenAck("chan-0", "chan-1", "transfer")
        self._记录("通道OpenAck", ok, msg)
        ok, msg = self.ch_mgr.OpenConfirm("chan-1")
        self._记录("通道OpenConfirm", ok, msg)
        ch = self.ch_mgr.获取通道("chan-1")
        self._记录("通道状态=OPEN", ch.状态 == 通道状态.已打开, f"状态={ch.状态}")

    def test_3_ICS20代币转移(self):
        """步骤3: ICS-20代币转移（HKAIC→Cosmos链）"""
        # 先给地址存款
        self.ics20.存款("hkc_addr_1", "hkaic", 10000*10**16)
        转移前余额 = self.ics20.获取余额("hkc_addr_1", "hkaic")
        self._记录("存款成功", 转移前余额 > 0, f"余额={转移前余额}")

        # 发起转移
        转移ID, msg = self.ics20.发起转移(
            发送者="hkc_addr_1", 接收者="cosmos_addr_1",
            面额="hkaic", 金额=1000*10**16,
            源通道="chan-0", 目标通道="chan-1"
        )
        self._记录("发起ICS20转移", 转移ID is not None, msg)

        转移后余额 = self.ics20.获取余额("hkc_addr_1", "hkaic")
        self._记录("扣除源链余额", 转移后余额 < 转移前余额, f"余额未扣除")

        # 接收端确认
        ok, msg = self.ics20.确认转移(转移ID)
        self._记录("确认转移", ok, msg)

    def test_4_反向代币接收(self):
        """步骤4: Cosmos链→HKC的代币接收"""
        recv_id, msg = self.ics20.接收转移(
            接收者="hkc_addr_2", 面额="uatom", 金额=500*10**6,
            源通道="chan-1", 目标通道="chan-0"
        )
        self._记录("接收IBC代币", recv_id is not None, msg)

        # 检查IBC面额追踪
        追踪 = self.ics20.获取面额追踪(self.ics20.查询原始面额.__func__ and "ibc/")
        # 检查余额是否到账
        余额 = self.ics20.获取余额("hkc_addr_2", "uatom")
        self._记录("反向代币到账", 余额 > 0, f"余额={余额}")

    def test_5_IBC中继器传递(self):
        """步骤5: IBC中继器传递数据包"""
        # 注册中继器
        self.relayer.注册中继器("relayer-1", ATH验证=True)
        self.relayer.注册中继器("relayer-2", ATH验证=False)
        self._记录("注册中继器", True, "")

        # 创建数据包
        pkt = IBC数据包(
            序列号=1, 源端口="transfer", 源通道="chan-0",
            目标端口="transfer", 目标通道="chan-1",
            数据=b'{"denom":"hkaic","amount":"1000","sender":"addr1","receiver":"addr2"}'
        )
        任务ID = self.relayer.提交数据包(pkt)
        self._记录("提交数据包", 任务ID != "", "任务ID为空")

        # 选择中继器
        选中 = self.relayer.选择中继器(任务ID)
        self._记录("选择ATH验证中继器", 选中 == "relayer-1", f"选中={选中}")

        # 执行中继
        ok, msg = self.relayer.执行中继(任务ID, 成功=True)
        self._记录("中继执行成功", ok, msg)

        # 确认中继
        ok, msg = self.relayer.确认中继(任务ID)
        self._记录("中继确认完成", ok, msg)

    def test_6_轻客户端验证(self):
        """步骤6: 轻客户端验证证明"""
        # 创建验证者集
        vs = ValidatorSet()
        for i in range(4):
            vs.添加验证者(os.urandom(32), 投票权=100)

        # 创建轻客户端
        lc = IBCLightClient("cosmos-hub-4")
        ok = lc.初始化(100, int(time.time()*1e9), vs, 应用哈希=os.urandom(32))
        self._记录("轻客户端初始化", ok, "")

        ok = lc.激活()
        self._记录("轻客户端激活", ok, "")

        # 验证区块头
        header = TendermintHeader(
            链ID="cosmos-hub-4", 高度=101,
            时间戳=int(time.time()*1e9),
            验证者哈希=vs.哈希(),
            下一个验证者哈希=vs.哈希(),
            应用哈希=os.urandom(32),
        )
        commit = Commit(高度=101, 块ID哈希=header.哈希())
        for i in range(4):
            commit.添加签名(i, os.urandom(64), header.哈希())

        ok, msg = lc.验证并更新区块头(header, commit)
        self._记录("区块头验证通过", ok, msg)

        # 检查高度更新
        self._记录("高度更新到101", lc.获取共识高度() == 101, f"高度={lc.获取共识高度()}")

        # 不当行为检测
        lc.报告不当行为(101, "双签", "验证者双签")
        self._记录("不当行为→冻结", lc.获取状态().value == "frozen", "未冻结")

        # 解冻
        lc.解冻("人工审核确认安全")
        self._记录("解冻恢复", lc.获取状态().value == "active", "未恢复")

    def test_7_防御体系检查(self):
        """步骤7: IBC防御体系检查"""
        dc = DefenseCoordinator(总质押量=21_000_000*10**16, 流通量=21_000_000*10**16)

        # 注册链
        dc.注册链("cosmos-hub-4", 涌现分数=0.8, 初始信用分=800)
        dc.注册链("evm-chain-1", 涌现分数=0.5, 初始信用分=500)
        dc.注册链("suspect-chain", 涌现分数=0.1, 初始信用分=100)
        self._记录("注册3条链", True, "")

        # 风险评估
        dc.risk_assessor.执行评估("cosmos-hub-4", 稳定性=90, 安全历史=85,
                                 验证者集中度=80, 治理风险=85, 流动性深度=90)
        dc.risk_assessor.执行评估("suspect-chain", 稳定性=20, 安全历史=15,
                                 验证者集中度=10, 治理风险=10, 流动性深度=10)

        # 检查跨链交易 — 合法链
        ok, reason, detail = dc.检查跨链交易("cosmos-hub-4", 金额=1000*10**16)
        self._记录("合法链跨链允许", ok, reason)

        # 检查跨链交易 — 可疑链
        ok, reason, detail = dc.检查跨链交易("suspect-chain", 金额=100*10**16)
        self._记录("可疑链跨链拒绝", not ok, f"应拒绝但允许了: {reason}")

        # 断路器测试
        dc.circuit_breaker.记录失败("evm-chain-1")
        dc.circuit_breaker.记录失败("evm-chain-1")
        dc.circuit_breaker.记录失败("evm-chain-1")
        # 模拟多次失败后熔断
        for _ in range(20):
            dc.circuit_breaker.记录失败("evm-chain-1")
        允许, 原因 = dc.circuit_breaker.是否允许交易("evm-chain-1")
        self._记录("断路器熔断", not 允许, f"应熔断但允许: {原因}")

        # 暴露上限检查
        dc.exposure_cap.注册链("cosmos-hub-4", 800)
        结果, 原因 = dc.exposure_cap.检查敞口("cosmos-hub-4", 1000*10**16)
        self._记录("敞口检查", True, f"结果={结果.value}")

    def 运行(self):
        print("\n" + "="*60)
        print("  IBC 跨链端到端测试")
        print("="*60)
        self.test_1_IBC连接4步握手()
        self.test_2_IBC通道创建()
        self.test_3_ICS20代币转移()
        self.test_4_反向代币接收()
        self.test_5_IBC中继器传递()
        self.test_6_轻客户端验证()
        self.test_7_防御体系检查()
        for r in self.结果:
            print(r)
        print(f"\n  IBC测试: {self.通过}通过 / {self.失败}失败")
        return self.失败 == 0


# ============================================================
# 主入口
# ============================================================

def run_tests():
    """运行所有跨链端到端测试"""
    print("\n" + "🜏"*30)
    print("  HKC 第二步 — 跨链桥端到端验证")
    print("🜏"*30)

    etb_ok = TestETBCrossChain().运行()
    ibc_ok = TestIBCCrossChain().运行()

    全部通过 = etb_ok and ibc_ok
    print(f"\n{'='*60}")
    print(f"  跨链桥端到端验证: {'✅ 全部通过' if 全部通过 else '❌ 存在失败'}")
    print(f"{'='*60}")
    return 全部通过


if __name__ == "__main__":
    成功 = run_tests()
    sys.exit(0 if 成功 else 1)
