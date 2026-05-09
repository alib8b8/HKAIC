"""
HKC 语义跨链生态模块 (semantic_crosschain/)
=============================================
传统链：跨链就是锁铸造
HKC玩法：涌信桥ETB让跨链变成"我想要什么"而不是"怎么搬过去"。
用户说"我要在Cosmos上用DeFi"，ETB自动找最优路径、自动桥接、自动管理风险。

子模块：
  - intent_parser: 语义意图解析器
  - path_finder: 跨链路径寻找器
  - bridge_coordinator: 多桥协调器
  - etb_integration: ETB集成层
  - crosschain_security: 跨链安全层
"""

from .intent_parser import 语义解析器, 解析结果, 意图类别, 子意图
from .path_finder import 路径寻找器, 跨链路径, 跨链桥, 桥类型
from .bridge_coordinator import 桥协调器, 协调转账, 分片, 桥状态
from .etb_integration import ETB集成层, ETB事务, 验证组
from .crosschain_security import 跨链安全层, 安全事件, 敞口限制, 安全事件等级
