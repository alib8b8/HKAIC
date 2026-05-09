"""
语义交易模块 (semantic_tx.py)
===============================
涌信钱包核心创新——自然语言驱动的交易系统。
将"转100个HKAIC给Bob"解析为结构化交易，
AI生成交易摘要用自然语言确认。
纯Python标准库，零外部依赖。
"""

import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class 交易类型(Enum):
    """交易类型"""
    转账 = "transfer"
    质押 = "stake"
    跨链 = "cross_chain"
    合约交互 = "contract"
    条件触发 = "conditional"
    定时转账 = "scheduled"
    定投 = "dca"


class Gas偏好(Enum):
    """Gas偏好"""
    尽快 = "fast"
    标准 = "standard"
    省钱 = "economical"


@dataclass
class 解析结果:
    """自然语言解析结果"""
    成功: bool = False
    交易类型: 交易类型 = 交易类型.转账
    金额: float = 0.0
    代币: str = "HKAIC"
    收款人: str = ""
    收款人地址: str = ""
    Gas偏好: Gas偏好 = Gas偏好.标准
    附加条件: str = ""
    错误信息: str = ""


@dataclass
class 交易摘要:
    """AI生成的自然语言交易确认摘要"""
    原文: str = ""
    摘要文本: str = ""
    结构化数据: Optional[解析结果] = None
    Gas估算: float = 0.0
    预计确认秒: float = 30.0
    风险提示: str = ""


@dataclass
class 交易模板:
    """常用交易模板"""
    名称: str
    描述: str
    模板文本: str


class 语义交易引擎:
    """
    语义交易引擎 - 涌信钱包核心创新

    功能：
      1. 自然语言解析：将"转100个HKAIC给Bob"解析为结构化交易
      2. 交易确认对话：AI生成自然语言摘要
      3. 交易模板：常用交易一键发
      4. 语义查询：用自然语言查余额、查交易、查质押收益
    """

    def __init__(self):
        self._地址本: Dict[str, str] = {}   # 别名 -> 地址
        self._交易历史: List[Dict] = []
        self._条件交易: List[Dict] = []      # 条件触发的待执行交易
        self._定投计划: List[Dict] = []

        # 预置交易模板
        self._模板列表 = [
            交易模板("定投质押", "每周定投100 HKAIC质押", "每周质押100个HKAIC"),
            交易模板("定期转账", "每月1号转50 HKAIC给Bob", "每月1号转50个HKAIC给{收款人}"),
            交易模板("条件卖出", "HKAIC涨到500时卖出100个", "HKAIC涨到{价格}时转{金额}个给{收款人}"),
        ]

        # 代币别名映射
        self._代币别名 = {
            "hkaic": "HKAIC",
            "hk": "HKAIC",
            "币": "HKAIC",
            "eth": "ETH",
            "usdt": "USDT",
            "usdc": "USDC",
        }

        # 中文数字映射
        self._中文数字 = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
            "百": 100, "千": 1000, "万": 10000,
        }

    def 设置地址本(self, 地址本: Dict[str, str]):
        """设置地址本"""
        self._地址本 = 地址本

    def 添加地址(self, 别名: str, 地址: str):
        """添加地址本条目"""
        self._地址本[别名.lower()] = 地址

    # ========== 自然语言解析 ==========

    def 解析(self, 输入: str) -> 解析结果:
        """
        将自然语言交易指令解析为结构化数据

        支持的格式示例：
          - "转100个HKAIC给Bob"
          - "转账500 HKAIC到0x3a2f..."
          - "给Alice转50个币"
          - "质押200 HKAIC"
          - "跨链转100 HKAIC到ETH链"
          - "如果HKAIC涨到500就转100个给Bob"
          - "明天下午3点转50给Alice"
          - "尽快转100给Bob"
          - "省钱模式转200给Charlie"
        """
        原文 = 输入.strip()
        if not 原文:
            return 解析结果(成功=False, 错误信息="输入为空")

        结果 = 解析结果()

        # 1. 检测交易类型
        结果.交易类型 = self._检测交易类型(原文)

        # 2. 解析金额
        金额, 代币 = self._解析金额(原文)
        结果.金额 = 金额
        结果.代币 = 代币
        if 金额 <= 0 and 结果.交易类型 in (交易类型.转账, 交易类型.跨链, 交易类型.质押):
            return 解析结果(成功=False, 错误信息="无法识别金额，请明确指定转账金额")

        # 3. 解析收款人
        收款人, 地址 = self._解析收款人(原文)
        结果.收款人 = 收款人
        结果.收款人地址 = 地址

        # 4. 解析Gas偏好
        结果.Gas偏好 = self._解析Gas偏好(原文)

        # 5. 解析附加条件
        结果.附加条件 = self._解析附加条件(原文)

        结果.成功 = True
        return 结果

    def _检测交易类型(self, 文本: str) -> 交易类型:
        """检测交易类型"""
        文本l = 文本.lower()
        if "跨链" in 文本 or "桥" in 文本 or "到" in 文本 and any(c in 文本 for c in ["eth链", "以太坊", "btc链", "比特币链"]):
            return 交易类型.跨链
        if "质押" in 文本 or "stake" in 文本l or "抵押" in 文本:
            return 交易类型.质押
        if "合约" in 文本 or "approve" in 文本l or "授权" in 文本:
            return 交易类型.合约交互
        if "如果" in 文本 or "涨到" in 文本 or "跌到" in 文本:
            if "转" in 文本 or "卖" in 文本:
                return 交易类型.条件触发
        if "每天" in 文本 or "每周" in 文本 or "每月" in 文本 or "定投" in 文本:
            return 交易类型.定投
        if "明天" in 文本 or "定时" in 文本 or "点" in 文本 and re.search(r'\d+点', 文本):
            return 交易类型.定时转账
        return 交易类型.转账

    def _解析金额(self, 文本: str) -> Tuple[float, str]:
        """解析金额和代币"""
        代币 = "HKAIC"
        # 检测代币
        文本l = 文本.lower()
        for 别名, 代币名 in self._代币别名.items():
            if 别名 in 文本l:
                代币 = 代币名
                break

        # 尝试提取数字金额
        # 匹配 "转100个"、"100 hkaic"、"500币"
        模式列表 = [
            r'转\s*(\d+(?:\.\d+)?)\s*个',           # 转100个
            r'转\s*(\d+(?:\.\d+)?)\s*' + re.escape(代币.lower()),  # 转100hkaic
            r'(\d+(?:\.\d+)?)\s*' + re.escape(代币.lower()),       # 100 HKAIC
            r'(\d+(?:\.\d+)?)\s*个\s*币',             # 100个币
            r'转\s*(\d+(?:\.\d+)?)\s*币',             # 转100币
            r'转\s*(\d+(?:\.\d+)?)',                   # 转100
            r'质押\s*(\d+(?:\.\d+)?)',                 # 质押200
            r'(\d+(?:\.\d+)?)\s*个',                   # 100个
        ]
        for 模式 in 模式列表:
            匹配 = re.search(模式, 文本l)
            if 匹配:
                return float(匹配.group(1)), 代币

        return 0.0, 代币

    def _解析收款人(self, 文本: str) -> Tuple[str, str]:
        """解析收款人（从地址本匹配或直接使用地址）"""
        # 先尝试匹配0x地址
        地址匹配 = re.search(r'0x[0-9a-fA-F]{40}', 文本)
        if 地址匹配:
            地址 = 地址匹配.group(0)
            # 反查地址本
            for 别名, addr in self._地址本.items():
                if addr.lower() == 地址.lower():
                    return 别名, 地址
            return 地址[:10] + "...", 地址

        # 尝试从地址本匹配别名
        for 别名, 地址 in self._地址本.items():
            if 别名.lower() in 文本.lower():
                return 别名, 地址

        # 尝试匹配"给XXX"
        给匹配 = re.search(r'给\s*(\S+)', 文本)
        if 给匹配:
            名字 = 给匹配.group(1)
            # 清理名字后的标点
            名字 = re.sub(r'[的个了啊吗，。！？\s]+$', '', 名字)
            if 名字.lower() in self._地址本:
                return 名字, self._地址本[名字.lower()]
            return 名字, ""

        return "", ""

    def _解析Gas偏好(self, 文本: str) -> Gas偏好:
        """解析Gas偏好"""
        文本l = 文本.lower()
        if "尽快" in 文本 or "快速" in 文本 or "加急" in 文本 or "urgent" in 文本l:
            return Gas偏好.尽快
        if "省钱" in 文本 or "便宜" in 文本 or "不急" in 文本 or "慢" in 文本:
            return Gas偏好.省钱
        return Gas偏好.标准

    def _解析附加条件(self, 文本: str) -> str:
        """解析附加条件"""
        条件 = ""
        # 条件触发
        if "如果" in 文本:
            if匹配 = re.search(r'如果(.+?)(就|则|，)', 文本)
            if if匹配:
                条件 = if匹配.group(1)
        # 价格条件
        涨匹配 = re.search(r'涨到\s*(\d+)', 文本)
        if 涨匹配:
            条件 = f"HKAIC价格达到{涨匹配.group(1)}"
        跌匹配 = re.search(r'跌到\s*(\d+)', 文本)
        if 跌匹配:
            条件 = f"HKAIC价格跌至{跌匹配.group(1)}"
        # 定时条件
        时间匹配 = re.search(r'(明天|后天|下周|每月|每周|每天).+?(\d+点|\d+号|\d+日)', 文本)
        if 时间匹配:
            条件 = 时间匹配.group(0)
        return 条件

    # ========== 交易确认对话 ==========

    def 生成确认摘要(self, 原文: str, 解析: 解析结果,
                     Gas估算: float = 0.5, 预计确认秒: float = 30.0,
                     风险提示: str = "") -> 交易摘要:
        """
        AI生成交易确认摘要
        用自然语言而非hex数据确认交易
        """
        if not 解析.成功:
            return 交易摘要(
                原文=原文,
                摘要文本=f"无法理解交易指令：{解析.错误信息}",
                风险提示="请重新描述您的交易意图。",
            )

        # 构建自然语言摘要
        部分 = []
        if 解析.交易类型 == 交易类型.转账:
            部分.append("你即将")
            if 解析.收款人地址:
                部分.append(f"向{解析.收款人}({解析.收款人地址[:8]}...{解析.收款人地址[-4:]})")
            elif 解析.收款人:
                部分.append(f"向{解析.收款人}")
            部分.append(f"转账{解析.金额} {解析.代币}")
        elif 解析.交易类型 == 交易类型.质押:
            部分.append(f"你即将质押{解析.金额} {解析.代币}")
        elif 解析.交易类型 == 交易类型.跨链:
            部分.append(f"你即将跨链转{解析.金额} {解析.代币}")
        elif 解析.交易类型 == 交易类型.条件触发:
            部分.append(f"当{解析.附加条件}时，将自动转账{解析.金额} {解析.代币}")
            if 解析.收款人:
                部分.append(f"给{解析.收款人}")
        elif 解析.交易类型 == 交易类型.定投:
            部分.append(f"将设置定投：{解析.附加条件 or '定期'}{解析.金额} {解析.代币}")
        else:
            部分.append(f"交易{解析.金额} {解析.代币}")

        # Gas信息
        部分.append(f"，当前Gas费约{Gas估算} {解析.代币}")
        部分.append(f"，预计{预计确认秒:.0f}秒确认")

        # 附加条件
        if 解析.附加条件 and 解析.交易类型 not in (交易类型.条件触发, 交易类型.定投):
            部分.append(f"。触发条件：{解析.附加条件}")

        部分.append("。确认？")

        return 交易摘要(
            原文=原文,
            摘要文本="".join(部分),
            结构化数据=解析,
            Gas估算=Gas估算,
            预计确认秒=预计确认秒,
            风险提示=风险提示,
        )

    # ========== 语义查询 ==========

    def 解析查询(self, 输入: str) -> Dict:
        """
        解析语义查询
        支持：
          - "我还有多少HKAIC？"
          - "我上个月跨链花了多少Gas？"
          - "最近5笔交易"
          - "质押收益多少？"
        """
        文本 = 输入.lower()
        查询类型 = "未知"
        参数 = {}

        # 余额查询
        if "余额" in 文本 or "还有多少" in 文本 or "有多少" in 文本:
            查询类型 = "余额"
            if "eth" in 文本:
                参数["代币"] = "ETH"
            elif "usdt" in 文本:
                参数["代币"] = "USDT"
            else:
                参数["代币"] = "HKAIC"

        # 交易查询
        elif "交易" in 文本 or "转账" in 文本:
            查询类型 = "交易历史"
            # 解析数量
            数量匹配 = re.search(r'(\d+)\s*笔', 文本)
            if 数量匹配:
                参数["数量"] = int(数量匹配.group(1))
            else:
                参数["数量"] = 10
            # 解析时间范围
            if "上个月" in 文本 or "上月" in 文本:
                参数["时间范围"] = "上月"
            elif "本周" in 文本 or "这周" in 文本:
                参数["时间范围"] = "本周"
            elif "今天" in 文本:
                参数["时间范围"] = "今天"

        # Gas查询
        elif "gas" in 文本 or "手续费" in 文本 or "矿工费" in 文本:
            查询类型 = "Gas"
            if "上个月" in 文本 or "上月" in 文本:
                参数["时间范围"] = "上月"
            elif "本周" in 文本:
                参数["时间范围"] = "本周"

        # 质押查询
        elif "质押" in 文本 or "收益" in 文本:
            查询类型 = "质押"
            if "收益" in 文本:
                参数["详情"] = "收益"

        # 跨链查询
        elif "跨链" in 文本 or "桥" in 文本:
            查询类型 = "跨链"

        return {"查询类型": 查询类型, "参数": 参数}

    # ========== 交易模板 ==========

    def 获取模板列表(self) -> List[交易模板]:
        """获取可用交易模板"""
        return self._模板列表

    def 应用模板(self, 模板名称: str, 参数: Dict[str, str] = None) -> str:
        """应用交易模板，填充参数"""
        参数 = 参数 or {}
        for 模板 in self._模板列表:
            if 模板.名称 == 模板名称:
                文本 = 模板.模板文本
                for k, v in 参数.items():
                    文本 = 文本.replace(f"{{{k}}}", v)
                return 文本
        return ""

    # ========== 交易记录 ==========

    def 记录交易(self, 交易哈希: str, 交易类型: 交易类型, 金额: float,
                代币: str, 收款人: str = "", Gas费用: float = 0.0):
        """记录交易到本地历史，AI标注类型"""
        self._交易历史.append({
            "交易哈希": 交易哈希,
            "类型": 交易类型.value,
            "类型标签": self._交易类型标签(交易类型),
            "金额": 金额,
            "代币": 代币,
            "收款人": 收款人,
            "Gas费用": Gas费用,
            "时间": time.time(),
        })

    def _交易类型标签(self, 类型: 交易类型) -> str:
        """AI标注交易类型的中文标签"""
        标签 = {
            交易类型.转账: "💸 转账",
            交易类型.质押: "🔒 质押",
            交易类型.跨链: "🌉 跨链",
            交易类型.合约交互: "📜 合约交互",
            交易类型.条件触发: "⚡ 条件触发",
            交易类型.定时转账: "⏰ 定时转账",
            交易类型.定投: "📅 定投",
        }
        return 标签.get(类型, "❓ 未知")

    def 查询交易历史(self, 数量: int = 10, 类型过滤: Optional[交易类型] = None) -> List[Dict]:
        """查询交易历史"""
        历史 = self._交易历史
        if 类型过滤:
            历史 = [t for t in 历史 if t["类型"] == 类型过滤.value]
        return 历史[-数量:]
