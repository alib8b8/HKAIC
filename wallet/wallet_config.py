"""
涌信钱包配置 (wallet_config.py)
================================
Emergent Wallet 全局配置：HKC主网/测试网、安全策略、AI参数、多语言。
纯Python标准库，零外部依赖。
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class 网络配置:
    """RPC与链网络配置"""
    名称: str = "HKC主网"
    chain_id: int = 2888
    rpc_url: str = "https://rpc.hongkunaichain.io"
    浏览器_url: str = "https://explorer.hongkunaichain.io"
    etb_bridge_url: str = "https://bridge.hongkunaichain.io"
    区块时间秒: float = 6.0
    币种代号: str = "HKAIC"
    币种精度: int = 16


@dataclass
class 安全配置:
    """安全与风控配置"""
    自动锁定分钟: int = 5
    单笔限额: float = 10000.0
    日累计限额: float = 100000.0
    高风险二次确认: bool = True
    守护者最少人数: int = 3
    守护者恢复阈值: float = 0.667
    守护者PoEI最低分: float = 50.0


@dataclass
class AI配置:
    """AI增强功能配置"""
    守护者灵敏度: float = 0.8
    信用分更新频率秒: float = 6.0
    Gas策略: str = "标准"
    语义解析严格模式: bool = False
    意图超时秒: float = 1800.0
    批量合并窗口秒: float = 300.0
    异常标准差阈值: float = 3.0
    频率异常窗口秒: float = 60.0


@dataclass
class 语言配置:
    """多语言配置"""
    界面语言: str = "zh"
    中文: Dict = field(default_factory=lambda: {
        "welcome": "涌信钱包 Emergent Wallet v4.0.0",
        "locked": "钱包已锁定，请输入密码解锁",
        "insufficient": "余额不足",
        "confirm": "确认交易？",
        "cancelled": "交易已取消",
        "sent": "交易已提交",
        "high_risk": "⚠ AI守护者检测到高风险！",
        "credit_low": "⚠ 目标地址信用分较低",
    })
    英文: Dict = field(default_factory=lambda: {
        "welcome": "Emergent Wallet v4.0.0",
        "locked": "Wallet locked, enter password to unlock",
        "insufficient": "Insufficient balance",
        "confirm": "Confirm transaction?",
        "cancelled": "Transaction cancelled",
        "sent": "Transaction submitted",
        "high_risk": "⚠ AI Guardian: High risk detected!",
        "credit_low": "⚠ Target address has low credit score",
    })

    def 获取(self, key: str) -> str:
        """根据当前语言获取提示文本"""
        字典 = self.中文 if self.界面语言 == "zh" else self.英文
        return 字典.get(key, key)


# ========== 预设网络 ==========

HKC主网 = 网络配置(
    名称="HKC主网",
    chain_id=2888,
    rpc_url="https://rpc.hongkunaichain.io",
    浏览器_url="https://explorer.hongkunaichain.io",
    etb_bridge_url="https://bridge.hongkunaichain.io",
)

HKC测试网 = 网络配置(
    名称="HKC测试网",
    chain_id=2889,
    rpc_url="https://testnet-rpc.hongkunaichain.io",
    浏览器_url="https://testnet-explorer.hongkunaichain.io",
    etb_bridge_url="https://testnet-bridge.hongkunaichain.io",
)

本地开发网 = 网络配置(
    名称="HKC本地开发网",
    chain_id=31337,
    rpc_url="http://127.0.0.1:8545",
    浏览器_url="http://127.0.0.1:8080",
    etb_bridge_url="http://127.0.0.1:8081",
    区块时间秒=2.0,
)

预设网络列表 = [HKC主网, HKC测试网, 本地开发网]


class 涌信钱包配置:
    """涌信钱包全局配置管理"""

    def __init__(self, 配置路径: str = ""):
        self.网络 = HKC主网
        self.安全 = 安全配置()
        self.AI = AI配置()
        self.语言 = 语言配置()
        self.守护者列表: List[str] = []
        self.地址本: Dict[str, str] = {}
        self._配置路径 = 配置路径 or os.path.join(
            os.path.expanduser("~"), ".emergent_wallet", "config.json"
        )
        if os.path.exists(self._配置路径):
            self.加载()

    def 切换网络(self, 网络: 网络配置):
        """切换到指定网络"""
        self.网络 = 网络

    def 切换语言(self, 语言: str):
        """切换界面语言 zh/en"""
        self.语言.界面语言 = 语言

    def 保存(self):
        """保存配置到文件"""
        数据 = {
            "网络": {
                "名称": self.网络.名称,
                "chain_id": self.网络.chain_id,
                "rpc_url": self.网络.rpc_url,
            },
            "安全": {
                "自动锁定分钟": self.安全.自动锁定分钟,
                "单笔限额": self.安全.单笔限额,
                "日累计限额": self.安全.日累计限额,
                "高风险二次确认": self.安全.高风险二次确认,
                "守护者最少人数": self.安全.守护者最少人数,
                "守护者PoEI最低分": self.安全.守护者PoEI最低分,
            },
            "AI": {
                "守护者灵敏度": self.AI.守护者灵敏度,
                "信用分更新频率秒": self.AI.信用分更新频率秒,
                "Gas策略": self.AI.Gas策略,
                "语义解析严格模式": self.AI.语义解析严格模式,
                "意图超时秒": self.AI.意图超时秒,
                "批量合并窗口秒": self.AI.批量合并窗口秒,
                "异常标准差阈值": self.AI.异常标准差阈值,
                "频率异常窗口秒": self.AI.频率异常窗口秒,
            },
            "语言": self.语言.界面语言,
            "守护者列表": self.守护者列表,
            "地址本": self.地址本,
        }
        目录 = os.path.dirname(self._配置路径)
        if 目录:
            os.makedirs(目录, exist_ok=True)
        with open(self._配置路径, "w", encoding="utf-8") as f:
            json.dump(数据, f, ensure_ascii=False, indent=2)

    def 加载(self):
        """从文件加载配置"""
        if not os.path.exists(self._配置路径):
            return
        try:
            with open(self._配置路径, "r", encoding="utf-8") as f:
                数据 = json.load(f)
            网络数据 = 数据.get("网络", {})
            for 预设 in 预设网络列表:
                if 预设.名称 == 网络数据.get("名称"):
                    self.网络 = 预设
                    break
            else:
                self.网络 = 网络配置(**网络数据)
            安全数据 = 数据.get("安全", {})
            for k, v in 安全数据.items():
                if hasattr(self.安全, k):
                    setattr(self.安全, k, v)
            AI数据 = 数据.get("AI", {})
            for k, v in AI数据.items():
                if hasattr(self.AI, k):
                    setattr(self.AI, k, v)
            self.语言.界面语言 = 数据.get("语言", "zh")
            self.守护者列表 = 数据.get("守护者列表", [])
            self.地址本 = 数据.get("地址本", {})
        except (json.JSONDecodeError, KeyError):
            pass

    def 获取提示(self, key: str) -> str:
        """获取当前语言的提示文本"""
        return self.语言.获取(key)
