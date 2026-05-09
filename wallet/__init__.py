"""
涌信钱包 Emergent Wallet (wallet/__init__.py)
===============================================
HKC AI原生态钱包 v4.0.0

涌信钱包不是"又一个MetaMask"，而是AI原生钱包：
传统钱包功能全有，但加入只有AI原生链才能做到的独特功能。

核心创新：
  🔤 语义交易 — 自然语言驱动交易，AI解析+确认
  🏆 涌智信用分 — PoEI涌现分数驱动的链上信用评估
  🎯 意图驱动 — 与涌信桥ETB联动，表达"想要什么"而非"怎么做"
  🛡️ AI守护者 — 五维交易安全检测，主动防御
  🔗 社交恢复 — 守护者网络替代助记词恢复
  ⛽ 自适应Gas — AI预测+3档建议+批量合并+对冲
  📊 AI组合分析 — 资产分布+收益追踪+风险评估

EVM兼容 + AI原生逻辑
纯Python标准库，零外部依赖
"""

__version__ = "4.0.0"
__wallet_name__ = "涌信钱包"
__wallet_name_en__ = "Emergent Wallet"
__wallet_code__ = "EW"
__chain__ = "Hongkun AI Chain"
__coin__ = "HKAIC"

# 核心模块
from .emergent_wallet import 涌信钱包
from .semantic_tx import 语义交易引擎, 交易类型, Gas偏好
from .credit_score import 涌智信用分引擎, 信用等级
from .intent_engine import 意图驱动引擎, 意图类型, 意图状态
from .ai_guardian import AI守护者, 风险等级
from .social_recovery import 社交恢复引擎, 恢复状态
from .adaptive_gas import 自适应Gas引擎, Gas档位
from .portfolio_analyzer import 投资组合分析器, 资产项
from .wallet_config import 涌信钱包配置, HKC主网, HKC测试网, 本地开发网
from .wallet_ui import 涌信钱包UI


def 创建钱包(助记词长度: int = 12, 密码: str = "") -> 涌信钱包:
    """快捷创建涌信钱包"""
    钱包 = 涌信钱包()
    钱包.创建钱包(助记词长度=助记词长度, 密码=密码)
    return 钱包


def 助记词导入(助记词: str, 密码: str = "") -> 涌信钱包:
    """快捷导入涌信钱包"""
    钱包 = 涌信钱包()
    钱包.助记词导入(助记词=助记词, 密码=密码)
    return 钱包


def 私钥导入(私钥hex: str) -> 涌信钱包:
    """快捷私钥导入"""
    钱包 = 涌信钱包()
    钱包.私钥导入(私钥hex=私钥hex)
    return 钱包
