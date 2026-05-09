"""
安全审计漏洞修复验证测试 (test_security_fixes.py)
====================================================
验证全部14个Medium/Low级别漏洞的修复效果。
"""
import sys, os, time, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest


class TestM01_跨链桥验证组降级策略(unittest.TestCase):
    """M-01: 验证组合格节点不足时暂停跨链而非降级"""
    def setUp(self):
        from hongkun_ai_lab.chain.etb_bridge import 涌信桥, 跨链意图, 验证等级
        self.bridge = 涌信桥()
        from hongkun_ai_lab.chain.etb_bridge import Solver信息
        self.bridge.solver管理器.注册Solver("solver_0", 资金池=10**21, ATH验证=True)

    def test_合格节点不足时暂停跨链(self):
        """合格验证节点不足时返回空验证组，而非降级"""
        from hongkun_ai_lab.chain.etb_bridge import 跨链意图, 验证等级
        意图 = 跨链意图(意图ID="test_1", 源链="HKC", 目标链="EVM",
                      发送者="A", 接收者="B", 金额=50000*10**16)
        # 只提供低涌现分数节点
        低分节点 = [{"节点ID": f"low_{i}", "E_i": 0.01, "σ_i": 0.01, "epoch_age": 20} for i in range(5)]
        验证组 = self.bridge.生成动态验证组(意图, 低分节点, "epoch_42")
        self.assertEqual(验证组, [], "低分节点应返回空验证组，暂停跨链")

    def test_合格节点充足时正常生成验证组(self):
        """合格节点充足时正常生成验证组"""
        from hongkun_ai_lab.chain.etb_bridge import 跨链意图, 验证等级
        意图 = 跨链意图(意图ID="test_2", 源链="HKC", 目标链="EVM",
                      发送者="A", 接收者="B", 金额=50000*10**16)
        高分节点 = [{"节点ID": f"val_{i}", "E_i": 50+i*10, "σ_i": 0.3+i*0.05, "epoch_age": 20+i} for i in range(20)]
        验证组 = self.bridge.生成动态验证组(意图, 高分节点, "epoch_42")
        self.assertGreater(len(验证组), 0, "高分节点应正常生成验证组")


class TestM02_跨链意图ID不可预测(unittest.TestCase):
    """M-02: 跨链意图ID使用加密随机数"""
    def setUp(self):
        from hongkun_ai_lab.chain.etb_bridge import 涌信桥
        self.bridge = 涌信桥()

    def test_意图ID不可预测(self):
        """连续生成的意图ID应不可预测"""
        id1 = self.bridge.提交意图("HKC", "EVM", "A", "B", 1000)
        id2 = self.bridge.提交意图("HKC", "EVM", "A", "B", 1000)
        self.assertNotEqual(id1.意图ID, id2.意图ID, "连续意图ID应不同")

    def test_意图ID不含时间戳模式(self):
        """意图ID不应直接包含时间戳"""
        意图 = self.bridge.提交意图("HKC", "EVM", "A", "B", 1000)
        # 意图ID应为sha256哈希的前32字符，不含time.time_ns()原文
        now_ns = str(time.time_ns())
        self.assertNotIn(now_ns, 意图.意图ID, "意图ID不应包含明文时间戳")


class TestM03_跨链验证承诺和挑战期(unittest.TestCase):
    """M-03: 跨链验证承诺和挑战期机制"""
    def setUp(self):
        from hongkun_ai_lab.chain.etb_bridge import 涌信桥
        self.bridge = 涌信桥()
        from hongkun_ai_lab.chain.etb_bridge import Solver信息
        self.bridge.solver管理器.注册Solver("solver_0", 资金池=10**21, ATH验证=True)

    def test_跨链流程生成验证承诺(self):
        """跨链流程应生成验证承诺"""
        意图 = self.bridge.提交意图("HKC", "EVM", "A", "B", 50000*10**16)
        nodes = [{"节点ID": f"val_{i}", "E_i": 50+i*10, "σ_i": 0.3+i*0.05, "epoch_age": 20+i} for i in range(20)]
        self.bridge.执行跨链流程(意图, nodes, "epoch_42")
        self.assertGreater(len(意图.验证承诺), 0, "应生成验证承诺")
        self.assertGreater(意图.挑战期结束, 0, "应设置挑战期")

    def test_挑战机制存在(self):
        """应存在挑战提交接口"""
        self.assertTrue(hasattr(self.bridge, '提交挑战'), "涌信桥应有提交挑战方法")


class TestM04_PoEI共识K0节点排除(unittest.TestCase):
    """M-04: K=0节点不得参与出块"""
    def setUp(self):
        from hongkun_ai_lab.core.blockchain import PoEI共识
        self.consensus = PoEI共识()

    def test_K0节点不出块(self):
        """K=0的节点不应被选为出块者"""
        # 注册K=0的节点
        self.consensus.更新质押("zero_K_node", 10000)
        # 不更新知识贡献，K默认为0
        # 注册正常节点
        self.consensus.更新质押("normal_node", 10000)
        self.consensus.更新知识贡献("normal_node", 50.0)
        self.consensus.记录协同("normal_node", "other", 0.5)

        # 多次选举，K=0节点不应被选
        出块者列表 = []
        for i in range(10):
            出块者 = self.consensus.判定出块权(["zero_K_node", "normal_node"], f"epoch_{i}")
            if 出块者:
                出块者列表.append(出块者)
        # zero_K_node不应出现在出块者列表中
        self.assertNotIn("zero_K_node", 出块者列表, "K=0节点不应被选为出块者")

    def test_共识引擎K0排除(self):
        """共识引擎的选举器也应排除K=0节点"""
        from hongkun_ai_lab.chain.consensus_engine import PoEI共识引擎
        engine = PoEI共识引擎()
        engine.更新质押("zero_K", 10000)
        engine.更新质押("normal", 10000)
        engine.更新知识贡献("normal", 50.0)
        engine.记录协同("normal", "other", 0.5)
        
        出块者列表 = []
        for i in range(10):
            ep = engine.开始新epoch()
            出块者 = engine.判定出块权(["zero_K", "normal"], ep.种子)
            if 出块者:
                出块者列表.append(出块者)
        self.assertNotIn("zero_K", 出块者列表, "K=0节点不应在共识引擎中被选")


class TestM05_共识参数范围校验(unittest.TestCase):
    """M-05: 共识参数修改需在安全范围内"""
    def setUp(self):
        from hongkun_ai_lab.core.blockchain import PoEI共识
        self.consensus = PoEI共识()

    def test_正常范围内参数可修改(self):
        """正常范围内的参数应能修改"""
        原ALPHA = self.consensus.ALPHA
        self.consensus.调整参数({"alpha": 0.5})
        self.assertEqual(self.consensus.ALPHA, 0.5)

    def test_超出范围参数被拒绝(self):
        """超出安全范围的参数修改应被拒绝"""
        原ALPHA = self.consensus.ALPHA
        # alpha=5.0 超出范围(0.1~1.0)
        self.consensus.调整参数({"alpha": 5.0})
        self.assertEqual(self.consensus.ALPHA, 原ALPHA, "超范围参数应被拒绝")

        # alpha=-0.1 超出范围
        self.consensus.调整参数({"alpha": -0.1})
        self.assertEqual(self.consensus.ALPHA, 原ALPHA, "负数参数应被拒绝")

    def test_slash_rate为零被拒绝(self):
        """slash_rate=0应被拒绝"""
        原SLASH = self.consensus.SLASH_RATE
        self.consensus.调整参数({"slash_rate": 0})
        self.assertEqual(self.consensus.SLASH_RATE, 原SLASH, "slash_rate=0应被拒绝")

    def test_beta超范围被拒绝(self):
        """beta=10.0超出范围应被拒绝"""
        原BETA = self.consensus.BETA
        self.consensus.调整参数({"beta": 10.0})
        self.assertEqual(self.consensus.BETA, 原BETA, "beta超范围应被拒绝")


class TestM06_社交恢复阈值提升(unittest.TestCase):
    """M-06: 社交恢复最低5守护者3/5阈值"""
    def setUp(self):
        from hongkun_ai_lab.wallet.social_recovery import 社交恢复引擎
        self.engine = 社交恢复引擎()

    def test_少于5守护者不可恢复(self):
        """3个守护者应无法发起恢复"""
        for i in range(3):
            self.engine.添加守护者("wallet_1", f"guardian_{i}", PoEI分数=60.0)
        请求, 消息 = self.engine.发起恢复("wallet_1", "new_addr")
        self.assertIsNone(请求, "3个守护者应无法发起恢复")
        self.assertIn("5", 消息)

    def test_5守护者可恢复(self):
        """5个守护者应可发起恢复"""
        for i in range(5):
            self.engine.添加守护者("wallet_2", f"guardian_{i+10}", PoEI分数=60.0)
        请求, 消息 = self.engine.发起恢复("wallet_2", "new_addr")
        self.assertIsNotNone(请求, "5个守护者应可发起恢复")

    def test_所需确认数至少3(self):
        """5守护者时所需确认数应至少为3"""
        for i in range(5):
            self.engine.添加守护者("wallet_3", f"guardian_{i+20}", PoEI分数=60.0)
        请求, _ = self.engine.发起恢复("wallet_3", "new_addr")
        self.assertGreaterEqual(请求.所需确认数, 3, "所需确认数应至少为3")


class TestM07_私钥内存加密(unittest.TestCase):
    """M-07: 私钥使用时解密，不使用时加密存储"""
    def test_钱包账户私钥加密存储(self):
        """创建钱包账户后私钥hex应为空（已加密存储）"""
        from hongkun_ai_lab.wallet.emergent_wallet import 钱包账户
        账户 = 钱包账户(索引=0, EVM地址="0xabc", 鸿坤地址="HKC_abc", 私钥hex="a"*64)
        # M-07: 私钥hex应被清除（加密存储在_加密私钥中）
        self.assertEqual(账户.私钥hex, "", "明文私钥应被清除")

    def test_解密私钥可正确获取(self):
        """解密私钥应能正确获取原始值"""
        from hongkun_ai_lab.wallet.emergent_wallet import 钱包账户
        原始私钥 = "a" * 64
        账户 = 钱包账户(索引=0, EVM地址="0xabc", 鸿坤地址="HKC_abc", 私钥hex=原始私钥)
        解密私钥 = 账户._获取解密私钥()
        self.assertEqual(解密私钥, 原始私钥, "解密私钥应与原始私钥一致")

    def test_加密私钥字段存在(self):
        """钱包账户应有加密存储字段"""
        from hongkun_ai_lab.wallet.emergent_wallet import 钱包账户
        账户 = 钱包账户(索引=0, EVM地址="0xabc", 鸿坤地址="HKC_abc", 私钥hex="b"*64)
        self.assertTrue(hasattr(账户, '_加密私钥'), "应有加密私钥字段")
        self.assertTrue(hasattr(账户, '_混淆密钥'), "应有混淆密钥字段")
        self.assertGreater(len(账户._加密私钥), 0, "加密私钥不应为空")


class TestM08_保险池赔付上限(unittest.TestCase):
    """M-08: 保险池单笔赔付上限和日赔付上限"""
    def setUp(self):
        from hongkun_ai_lab.chain.etb_bridge import 涌信保险池
        self.pool = 涌信保险池()
        # 充入保险池
        for i in range(100):
            self.pool.收取保费(1000*10**16, f"tx_{i}")

    def test_单笔赔付上限(self):
        """单笔赔付不应超过池余额的10%"""
        池余额 = self.pool._池余额
        超限金额 = int(池余额 * 0.11)  # 11%，超过10%上限
        结果 = self.pool.申请理赔("claim_1", 超限金额, "测试")
        self.assertFalse(结果, "单笔超限赔付应被拒绝")

    def test_正常赔付可执行(self):
        """低于单笔上限的赔付应可执行"""
        池余额 = self.pool._池余额
        正常金额 = int(池余额 * 0.05)  # 5%，低于10%上限
        结果 = self.pool.申请理赔("claim_2", 正常金额, "测试")
        self.assertTrue(结果, "正常赔付应可执行")


class TestL01_Solver选择随机性(unittest.TestCase):
    """L-01: Solver选择添加随机性因子"""
    def test_使用secrets_choice(self):
        """Solver竞争器应使用secrets.choice而非random.choice"""
        import inspect
        from hongkun_ai_lab.chain.etb_bridge import Solver竞争器
        源码 = inspect.getsource(Solver竞争器.选择Solver)
        self.assertIn("secrets", 源码, "应使用secrets模块")
        # 检查return语句使用secrets.choice而非random.choice
        代码行 = [l.strip() for l in 源码.split("\n") if l.strip().startswith("return")]
        self.assertTrue(any("secrets.choice" in l for l in 代码行), "return应使用secrets.choice")


class TestL02_交易池大小限制(unittest.TestCase):
    """L-02: 交易池大小限制"""
    def test_交易池默认上限(self):
        """交易池默认上限应为10000"""
        from hongkun_ai_lab.core.transaction import 交易池
        pool = 交易池()
        self.assertEqual(pool._最大容量, 10000, "默认上限应为10000")

    def test_交易池满时拒绝(self):
        """交易池满时应拒绝新交易"""
        from hongkun_ai_lab.core.transaction import 交易池, 待处理交易, 交易优先级
        pool = 交易池(最大容量=5)
        for i in range(5):
            tx = 待处理交易(交易ID=f"tx_{i}", 发送地址="A", 接收地址="B",
                          金额=100, 手续费=1, 时间戳=time.time(), 优先级=交易优先级.中)
            pool.添加(tx)
        # 第6笔应被拒绝
        tx = 待处理交易(交易ID="tx_overflow", 发送地址="A", 接收地址="B",
                      金额=100, 手续费=1, 时间戳=time.time(), 优先级=交易优先级.中)
        结果 = pool.添加(tx)
        self.assertFalse(结果, "池满应拒绝新交易")


class TestL03_区块大小限制(unittest.TestCase):
    """L-03: 区块交易数上限和区块大小上限"""
    def test_区块最大交易数限制(self):
        """区块链应设置区块最大交易数"""
        from hongkun_ai_lab.core.blockchain import 区块链
        chain = 区块链()
        self.assertTrue(hasattr(chain, '_区块最大交易数'), "应有区块最大交易数属性")
        self.assertEqual(chain._区块最大交易数, 500, "区块最大交易数应为500")

    def test_区块最大字节数限制(self):
        """区块链应设置区块最大字节数"""
        from hongkun_ai_lab.core.blockchain import 区块链
        chain = 区块链()
        self.assertTrue(hasattr(chain, '_区块最大字节数'), "应有区块最大字节数属性")
        self.assertEqual(chain._区块最大字节数, 2*1024*1024, "区块最大应为2MB")


class TestL04_日志脱敏(unittest.TestCase):
    """L-04: 日志脱敏处理"""
    def test_私钥脱敏(self):
        """日志中64位hex私钥应被替换"""
        from hongkun_ai_lab.chain.rpc_api import 日志脱敏
        私钥 = "0x" + "a" * 64
        结果 = 日志脱敏(f"私钥是{私钥}")
        self.assertNotIn(私钥, 结果, "私钥应被脱敏")
        self.assertIn("***", 结果)

    def test_地址脱敏(self):
        """日志中地址应显示前6后4位"""
        from hongkun_ai_lab.chain.rpc_api import 日志脱敏
        地址 = "0x1234567890abcdef1234567890abcdef12345678"
        结果 = 日志脱敏(f"发送到{地址}")
        self.assertNotIn(地址, 结果, "完整地址应被脱敏")
        self.assertIn("0x1234", 结果[:10], "应保留前6位")

    def test_普通文本不变(self):
        """普通文本不应被修改"""
        from hongkun_ai_lab.chain.rpc_api import 日志脱敏
        文本 = "这是一条普通日志消息"
        self.assertEqual(日志脱敏(文本), 文本)


class TestL05_请求频率限制(unittest.TestCase):
    """L-05: 请求频率限制"""
    def test_限流器默认限制(self):
        """AI限流器默认限制应为60次/分钟"""
        from hongkun_ai_lab.chain.rpc_api import AI限流器
        limiter = AI限流器()
        self.assertEqual(limiter._限制, 60, "默认限制应为60次/分钟")


class TestL06_错误信息不泄露(unittest.TestCase):
    """L-06: RPC接口只返回通用错误信息"""
    def test_JSONRPC内部错误不泄露(self):
        """JSON-RPC内部错误应返回通用消息"""
        from hongkun_ai_lab.chain.rpc_api import 以太坊RPC处理器
        rpc = 以太坊RPC处理器()
        # 调用会触发异常的方法
        响应 = rpc.处理JSONRPC("eth_getBalance", [])  # 空参数可能异常
        if "error" in 响应:
            self.assertNotIn("Traceback", str(响应), "错误信息不应包含堆栈")
            self.assertNotIn("File", str(响应), "错误信息不应包含文件路径")

    def test_REST内部错误通用化(self):
        """REST API内部错误应返回500通用消息"""
        from hongkun_ai_lab.chain.rpc_api import RESTful处理器, API请求, HTTP方法, API响应
        rest = RESTful处理器()
        # 注册一个会抛异常的路由
        rest.注册路由("GET", "/error", lambda r: 1/0)
        响应 = rest.处理请求(API请求(方法=HTTP方法.GET, 路径="/error"))
        # 应返回通用错误，不泄露内部信息
        if 响应.状态码 == 500:
            self.assertNotIn("ZeroDivision", 响应.消息, "不应泄露异常类型")


if __name__ == "__main__":
    unittest.main(verbosity=2)
