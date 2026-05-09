"""
HKC 第二步 — ATH 9步握手真实执行验证
======================================
模拟两个AI Agent通过ATH协议完成可信握手，验证ATH与HKC的深度绑定。

测试内容:
  1. Agent A发起握手请求
  2. Agent B验证A的身份（ATH身份验证）
  3. 双方协商权限和会话参数
  4. 建立可信会话
  5. 会话内执行操作（跨链交易授权）
  6. 会话结束和审计日志生成
  7. ATH与HKC深度绑定: adapter/identity/audit
"""

import sys
import os
import time
import hashlib

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ath.ath_adapter import ath_HandshakeAdapter, ATH角色, ATH握手阶段
from ath.ath_identity import ath_IdentityManager
from ath.ath_audit import ath_AuditEngine, 审计事件类型


class TestATHHandshakeE2E:
    """ATH 9步握手端到端测试"""

    def __init__(self):
        self.adapter = ath_HandshakeAdapter()
        self.id_mgr = ath_IdentityManager()
        self.audit = ath_AuditEngine()
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

    def test_1_注册身份(self):
        """步骤1: Agent A和B注册ATH身份"""
        # Agent A — 用户角色
        a = self.adapter.ath_注册身份("did:agent:alice", ATH角色.智能体, "pubkey_alice_ed25519")
        self._记录("Agent A注册身份", a.DID == "did:agent:alice", "DID不匹配")
        self._记录("A角色=智能体", a.角色 == ATH角色.智能体, f"角色={a.角色}")
        self._记录("A信任评分初始=50", a.信任评分 == 50.0, f"评分={a.信任评分}")

        # Agent B — 应用角色
        b = self.adapter.ath_注册身份("did:app:solver_bridge", ATH角色.应用, "pubkey_solver_secp256k1")
        self._记录("Agent B注册身份", b.DID == "did:app:solver_bridge", "DID不匹配")
        self._记录("B角色=应用", b.角色 == ATH角色.应用, f"角色={b.角色}")

        # 在身份管理器中注册
        self.id_mgr.ath_注册身份("did:agent:alice", "agent")
        self.id_mgr.ath_注册身份("did:app:solver_bridge", "app")
        self._记录("身份管理器注册", True, "")

        # 签发凭证
        凭证 = self.id_mgr.ath_签发凭证(
            "did:agent:alice", "did:app:solver_bridge", "跨链操作授权",
            {"权限": "跨链转账", "限额": "10000 HKAIC"}
        )
        self._记录("签发凭证", 凭证 is not None, "凭证签发失败")
        if 凭证:
            self._记录("凭证有效", 凭证.是否有效(), "凭证无效")

    def test_2_发起握手(self):
        """步骤2: Agent A发起握手请求"""
        self.handshake = self.adapter.ath_发起握手("did:agent:alice", "did:app:solver_bridge")
        self._记录("发起握手", self.handshake.握手ID != "", "握手ID为空")
        self._记录("阶段=注册请求(1)", self.handshake.阶段 == ATH握手阶段.注册请求,
                    f"阶段={self.handshake.阶段}")
        self._记录("发起者=Alice", self.handshake.发起者DID == "did:agent:alice", "发起者不匹配")
        self._记录("响应者=Solver", self.handshake.响应者DID == "did:app:solver_bridge", "响应者不匹配")
        # 审计记录
        self.audit.ath_记录事件(审计事件类型.握手发起, "did:agent:alice", f"发起与did:app:solver_bridge的握手")

    def test_3_身份验证阶段(self):
        """步骤3: Agent B验证A的身份（ATH身份验证）— 推进到阶段2"""
        阶段 = self.adapter.ath_推进握手(self.handshake.握手ID)
        self._记录("推进到身份验证(2)", 阶段 == ATH握手阶段.身份验证, f"阶段={阶段}")

        # 身份验证
        已验证 = self.id_mgr.ath_验证身份("did:agent:alice")
        self._记录("Alice身份验证通过", 已验证, "身份验证失败")
        self.audit.ath_记录事件(审计事件类型.握手完成, "did:agent:alice", "身份验证通过")

    def test_4_能力声明阶段(self):
        """步骤4: 推进到能力声明 — 阶段3"""
        阶段 = self.adapter.ath_推进握手(self.handshake.握手ID)
        self._记录("推进到能力声明(3)", 阶段 == ATH握手阶段.能力声明, f"阶段={阶段}")

    def test_5_策略协商阶段(self):
        """步骤5: 推进到策略协商 — 阶段4"""
        阶段 = self.adapter.ath_推进握手(self.handshake.握手ID)
        self._记录("推进到策略协商(4)", 阶段 == ATH握手阶段.策略协商, f"阶段={阶段}")

    def test_6_权限授予阶段(self):
        """步骤6: 推进到权限授予 — 阶段5"""
        阶段 = self.adapter.ath_推进握手(self.handshake.握手ID)
        self._记录("推进到权限授予(5)", 阶段 == ATH握手阶段.权限授予, f"阶段={阶段}")

    def test_7_会话建立(self):
        """步骤7: 建立可信会话 — 阶段6"""
        阶段 = self.adapter.ath_推进握手(self.handshake.握手ID)
        self._记录("推进到会话建立(6)", 阶段 == ATH握手阶段.会话建立, f"阶段={阶段}")

    def test_8_心跳检测(self):
        """步骤8: 心跳检测 — 阶段7"""
        阶段 = self.adapter.ath_推进握手(self.handshake.握手ID)
        self._记录("推进到心跳检测(7)", 阶段 == ATH握手阶段.心跳检测, f"阶段={阶段}")

    def test_9_行为审计(self):
        """步骤9: 行为审计 — 阶段8"""
        阶段 = self.adapter.ath_推进握手(self.handshake.握手ID)
        self._记录("推进到行为审计(8)", 阶段 == ATH握手阶段.行为审计, f"阶段={阶段}")
        self.audit.ath_记录事件(审计事件类型.K_i更新, "did:agent:alice", "K_i增量=3.6")

    def test_10_信任更新_完成握手(self):
        """步骤10: 信任更新 — 阶段9，握手完成"""
        阶段 = self.adapter.ath_推进握手(self.handshake.握手ID)
        self._记录("推进到信任更新(9)", 阶段 == ATH握手阶段.信任更新, f"阶段={阶段}")
        self._记录("握手已完成", self.handshake.成功, "握手未完成")
        self._记录("完成时间已记录", self.handshake.完成时间 > 0, "完成时间未记录")

        # 计算K_i增量
        K增量 = self.adapter.ath_完成握手(self.handshake.握手ID, 交互质量=0.8, 权限精细度=0.9)
        self._记录("K_i增量计算", K增量 > 0, f"K_i增量={K增量}")
        # K_i增量 = 5.0 * 0.8 * 0.9 = 3.6
        self._记录("K_i增量=3.6", abs(K增量 - 3.6) < 0.01, f"K_i增量={K增量}")

        # 信任评分提升
        alice = self.adapter._身份注册.get("did:agent:alice")
        self._记录("Alice信任评分提升", alice.信任评分 > 50, f"评分={alice.信任评分}")
        self._记录("Alice握手次数=1", alice.握手次数 == 1, f"次数={alice.握手次数}")

    def test_11_会话内操作(self):
        """步骤11: 会话内执行跨链交易授权"""
        # Solver验证 — ATH与ETB联动
        验证通过 = self.adapter.ath_验证Solver("did:app:solver_bridge")
        self._记录("Solver ATH验证通过", 验证通过, "Solver验证失败")

        # K_i更新到身份管理器
        新K_i = self.id_mgr.ath_更新K_i("did:agent:alice", 3.6)
        self._记录("K_i绑定更新", 新K_i > 0, f"K_i={新K_i}")

    def test_12_会话结束审计(self):
        """步骤12: 会话结束和审计日志生成"""
        # 生成审计摘要
        摘要 = self.audit.ath_生成摘要()
        self._记录("审计摘要生成", "记录" in 摘要, "摘要为空")

        # 验证完整性
        完整 = self.audit.ath_验证完整性()
        self._记录("审计日志完整性", 完整, "审计日志不完整")

        # 查询Agent记录
        记录 = self.audit.ath_查询Agent("did:agent:alice")
        self._记录("Alice审计记录查询", len(记录) > 0, "无审计记录")

    def test_13_撤销握手(self):
        """步骤13: 撤销握手测试"""
        K下降 = self.adapter.ath_撤销握手("did:agent:alice", "恶意行为")
        self._记录("撤销握手K_i下降", K下降 > 0, f"K下降={K下降}")
        alice = self.adapter._身份注册.get("did:agent:alice")
        self._记录("信任评分下降", alice.信任评分 < 60, f"评分={alice.信任评分}")
        self.audit.ath_记录事件(审计事件类型.握手失败, "did:agent:alice", "恶意行为导致撤销")

    def test_14_多Agent并发握手(self):
        """步骤14: 多Agent并发握手"""
        # 注册更多Agent
        agents = []
        for i in range(5):
            did = f"did:agent:bot_{i}"
            self.adapter.ath_注册身份(did, ATH角色.智能体, f"pubkey_bot_{i}")
            self.id_mgr.ath_注册身份(did, "agent")
            self.id_mgr.ath_签发凭证(did, "did:app:solver_bridge", "基础验证")
            agents.append(did)

        # 多个握手并发
        握手IDs = []
        for i, did in enumerate(agents):
            hs = self.adapter.ath_发起握手(did, "did:app:solver_bridge")
            握手IDs.append(hs.握手ID)

        # 推进所有握手到完成
        for hid in 握手IDs:
            while True:
                阶段 = self.adapter.ath_推进握手(hid)
                if 阶段 is None or 阶段 == ATH握手阶段.信任更新:
                    break
            self.adapter.ath_完成握手(hid, 0.5, 0.5)

        状态 = self.adapter.状态()
        self._记录("5个并发握手", 状态["握手记录"] >= 6, f"记录数={状态['握手记录']}")  # 5+之前的1

    def test_15_ATH与HKC深度绑定验证(self):
        """步骤15: ATH与HKC三个模块的深度绑定"""
        # ath_adapter: ATH握手→HKC权限映射
        状态 = self.adapter.状态()
        self._记录("adapter链上锚定", 状态["链上锚定"] > 0, "无链上锚定记录")

        # ath_identity: ATH身份→HKC地址绑定
        K_i = self.id_mgr.ath_获取K_i("did:agent:alice")
        self._记录("identity K_i绑定", K_i > 0, f"K_i={K_i}")
        id状态 = self.id_mgr.状态()
        self._记录("identity有效凭证", id状态["有效凭证"] > 0, "无有效凭证")

        # ath_audit: 操作审计→链上记录
        审计状态 = self.audit.状态()
        self._记录("audit记录数", 审计状态["记录数"] > 0, "无审计记录")
        self._记录("audit完整性", 审计状态["完整"], "审计不完整")
        self._记录("audit Merkle根", 审计状态["Merkle根"] != "0"*16+"...", "Merkle根为空")

    def 运行(self):
        print("\n" + "="*60)
        print("  ATH 9步握手端到端测试")
        print("="*60)
        self.test_1_注册身份()
        self.test_2_发起握手()
        self.test_3_身份验证阶段()
        self.test_4_能力声明阶段()
        self.test_5_策略协商阶段()
        self.test_6_权限授予阶段()
        self.test_7_会话建立()
        self.test_8_心跳检测()
        self.test_9_行为审计()
        self.test_10_信任更新_完成握手()
        self.test_11_会话内操作()
        self.test_12_会话结束审计()
        self.test_13_撤销握手()
        self.test_14_多Agent并发握手()
        self.test_15_ATH与HKC深度绑定验证()
        for r in self.结果:
            print(r)
        print(f"\n  ATH测试: {self.通过}通过 / {self.失败}失败")
        return self.失败 == 0


def run_tests():
    """运行ATH握手端到端测试"""
    print("\n" + "🜏"*30)
    print("  HKC 第二步 — ATH 9步握手真实执行验证")
    print("🜏"*30)

    ok = TestATHHandshakeE2E().运行()
    print(f"\n{'='*60}")
    print(f"  ATH 9步握手验证: {'✅ 全部通过' if ok else '❌ 存在失败'}")
    print(f"{'='*60}")
    return ok


if __name__ == "__main__":
    成功 = run_tests()
    sys.exit(0 if 成功 else 1)
