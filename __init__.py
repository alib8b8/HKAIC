"""
Hongkun AI Chain (HKC) — 全球首条AI原生区块链
================================================

基于 PoEI 涌智证明共识的AI原生区块链，深度融合 ATH 信任框架。

链规格:
    链名称: Hongkun AI Chain
    链代号: HKC
    币种名称: Hongkun AI Coin
    币种代号: HKAIC
    总发行量: 21,000,000 枚 (全部预铸，永不增发)
    最小精度: 小数点后16位
    最小单位: 鸿坤 (hongkun), 1 HKAIC = 10^16 鸿坤
    共识机制: PoEI — 涌智证明 (Proof of Emergent Intelligence)
    跨链协议: ETB — 涌信桥 (Emergent Trust Bridge)
    身份框架: ATH — 自主信任握手 (Autonomous Trust Handshake)

核心模块 (core/):
    core.ledger      - 核心账本 (UTXO + 账户混合模型)
    core.tokenomics  - 代币经济学 (固定供给/内循环/手续费驱动)
    core.wallet      - 钱包系统 (地址生成/签名/多签)
    core.transaction - 交易引擎 (转账/交易池/双花检测)
    core.contract    - 智能合约 (条件支付/时间锁/多签)
    core.staking     - 质押与治理 (质押获交易费分成/投票/提案)
    core.market      - 市场与定价 (订单簿/K线/深度)
    core.blockchain  - 区块链核心 (PoEI共识/按需出块/浏览器)

链模块 (chain/):
    chain.p2p_network    - 涌知路由P2P网络 (知识引力路由/智能Gossip/协同净化)
    chain.node_sync      - 预测同步 (AI预判区块/知识图谱索引)
    chain.rpc_api        - 语义接口 (自然语言查询/AI限流/智能推送)
    chain.etb_bridge     - 涌信桥ETB (意图驱动/Solver竞争/动态验证组)
    chain.consensus_engine - PoEI共识引擎 (自适应参数/Epoch管理/Slashing)
    chain.testnet        - 进化沙盒 (AI攻防进化/压力测试/安全评估)

ATH模块 (ath/):
    ath.ath_adapter    - ATH握手适配器 (9步握手/PoEI融合/链上锚定)
    ath.ath_identity   - ATH身份管理 (DID/凭证/K_i绑定)
    ath.ath_audit      - ATH行为审计 (Merkle存储/完整性验证)

AI增强模块:
    explorer   - AI语义浏览器 (链上语义搜索/AI分析引擎)
    faucet     - 智能水龙头 (信誉评估/反女巫/动态配额)
    monitor    - AI运维大脑 (异常检测/日志分析/自愈)
    sdk        - Python SDK (智能路由/交易优化/ATH集成)
    simulation - HKAIC经济仿真 (蒙特卡洛/参数寻优/可视化)

配置系统 (config/):
    config.adaptive_config - AI配置大脑 (自动生成/自适应/冲突检测/预测)
    config.config_loader   - 配置加载与校验 (YAML/环境检测/热重载)
"""

__version__ = "4.0.0"
__chain_name__ = "Hongkun AI Chain"
__chain_symbol__ = "HKC"
__author__ = "HongKun AI Lab"
__coin_name__ = "Hongkun AI Coin"
__coin_symbol__ = "HKAIC"
__coin_supply__ = 21_000_000
__coin_decimals__ = 16
__coin_min_unit__ = "hongkun"
__consensus__ = "PoEI"
__bridge_protocol__ = "ETB"
__identity_framework__ = "ATH"
