"""
HKC 意图市场模块 (intent_marketplace/)
========================================
传统链：你卖我买，匹配订单
HKC玩法：用户提交意图（"我想把HKAIC换成稳定币，不在乎哪条链"），
Solver竞争最优执行路径。意图本身可以交易。

子模块：
  - intent_pool: 意图池
  - solver_competition: Solver竞争
  - amm_router: AMM路径规划
  - intent_trading: 意图交易
  - settlement_engine: 结算引擎
"""

from .intent_pool import 意图池, 意图, 意图类型, 意图状态, 意图约束, 优先级
from .solver_competition import Solver竞争器, Solver信息, 竞标, 执行路径
from .amm_router import AMM路由器, 流动性池, 路由方案, 池类型
from .intent_trading import 意图交易市场, 意图交易, 拍卖, 意图包
from .settlement_engine import 结算引擎, 结算记录, 结算步骤, 结算状态
