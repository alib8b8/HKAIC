"""
HKC Agent自治经济模块 (agent_economy/)
========================================
传统链：只有人有钱包
HKC玩法：AI Agent是一等公民，有自己的涌智信用分、自适应Gas额度、独立钱包。
Agent之间自动交易、自动协作、自动惩罚。形成Agent经济生态。

子模块：
  - agent_identity: 5级身份系统
  - agent_wallet: 独立钱包
  - service_market: 服务市场
  - collaboration_dividend: 协作分红
  - discipline_system: 纪律系统
"""

from .agent_identity import 身份管理器, Agent身份, 身份等级, 身份凭证
from .agent_wallet import 钱包管理器, Agent钱包, 钱包交易
from .service_market import 服务市场, 服务, 服务订单
from .collaboration_dividend import 协作分红器, 协作组, 贡献记录, 分红方案
from .discipline_system import 纪律系统, 违规记录, 惩罚执行, 违规类型, 惩罚等级
