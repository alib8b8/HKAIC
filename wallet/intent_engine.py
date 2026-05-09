"""
意图驱动引擎 (intent_engine.py)
================================
涌信钱包核心创新——与涌信桥ETB联动的意图驱动交易。
用户表达"想要什么"而非"怎么做"，Solver竞争执行。
纯Python标准库，零外部依赖。
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class 意图状态(Enum):
    """意图执行状态"""
    已提交 = "submitted"
    匹配中 = "matching"
    执行中 = "executing"
    已完成 = "completed"
    已失败 = "failed"
    已取消 = "cancelled"


class 意图类型(Enum):
    """意图类型"""
    跨链兑换 = "cross_chain_swap"
    质押收益优化 = "staking_optimize"
    资产分散 = "asset_diversify"
    跨链转移 = "cross_chain_transfer"
    自定义 = "custom"


@dataclass
class Solver信息:
    """竞争执行意图的Solver"""
    SolverID: str
    资金池: float = 0.0
    履约率: float = 1.0
    响应速度: float = 0.0
    信誉评分: float = 50.0
    ATH验证: bool = False

    def 竞争分数(self) -> float:
        """计算Solver竞争分数"""
        ath_bonus = 1.3 if self.ATH验证 else 1.0
        return self.信誉评分 * self.履约率 * (1 + self.响应速度) * ath_bonus


@dataclass
class 执行方案:
    """Solver提出的执行方案"""
    SolverID: str
    预计耗时秒: float = 0.0
    预计费用: float = 0.0
    路径描述: str = ""
    竞争分数: float = 0.0


@dataclass
class 用户意图:
    """用户意图"""
    意图ID: str = ""
    类型: 意图类型 = 意图类型.自定义
    自然语言描述: str = ""
    发起者: str = ""
    状态: 意图状态 = 意图状态.已提交
    # 意图参数
    源资产: str = ""
    目标资产: str = ""
    金额: float = 0.0
    期望收益率: float = 0.0
    目标链列表: List[str] = field(default_factory=list)
    # 执行信息
    匹配的Solver: str = ""
    执行方案: Optional[执行方案] = None
    # 时间
    提交时间: float = 0.0
    匹配时间: float = 0.0
    完成时间: float = 0.0
    超时秒: float = 1800.0
    # AI播报
    播报历史: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.提交时间 == 0:
            self.提交时间 = time.time()
        if not self.意图ID:
            # H-02修复: 使用os.urandom加密随机数，替代可预测的time.time_ns()
            import os as _os
            self.意图ID = hashlib.sha256(
                f"{self.发起者}{self.自然语言描述}{_os.urandom(16).hex()}".encode()
            ).hexdigest()[:16]

    def 是否超时(self) -> bool:
        return time.time() - self.提交时间 > self.超时秒


class 意图驱动引擎:
    """
    意图驱动引擎 - 与涌信桥ETB联动

    核心理念：
      用户不需要知道"怎么做"，只需表达"想要什么"
      AI解析意图 -> Solver竞争执行 -> 全程AI播报

    示例：
      "我想把手里的ETH换成HKAIC" -> 自动走ETB跨链
      "我想年化8%以上" -> AI推荐质押方案
      "我想把资产分散到3条链" -> AI生成跨链分配方案
    """

    def __init__(self):
        # Solver注册池
        self._Solver池: Dict[str, Solver信息] = {}
        # 活跃意图
        self._活跃意图: Dict[str, 用户意图] = {}
        # 意图历史
        self._意图历史: List[用户意图] = []
        # 质押方案缓存
        self._质押方案: List[Dict] = []

    # ========== Solver管理 ==========

    def 注册Solver(self, SolverID: str, 资金池: float = 0.0,
                   ATH验证: bool = False, 信誉评分: float = 50.0):
        """注册Solver到竞争池"""
        self._Solver池[SolverID] = Solver信息(
            SolverID=SolverID,
            资金池=资金池,
            ATH验证=ATH验证,
            信誉评分=信誉评分,
        )

    def 更新Solver表现(self, SolverID: str, 成功: bool = True, 延迟: float = 0.0):
        """更新Solver表现数据"""
        solver = self._Solver池.get(SolverID)
        if not solver:
            return
        if 成功:
            solver.信誉评分 = min(100, solver.信誉评分 + 1)
        else:
            solver.信誉评分 = max(0, solver.信誉评分 - 5)
            solver.履约率 = max(0, solver.履约率 - 0.01)
        solver.响应速度 = (solver.响应速度 + 1.0 / max(延迟, 0.1)) / 2

    # ========== 意图解析 ==========

    def 解析意图(self, 自然语言: str, 发起者: str = "") -> 用户意图:
        """
        AI解析用户自然语言意图
        识别意图类型和关键参数
        """
        文本 = 自然语言.lower().strip()
        意图 = 用户意图(
            自然语言描述=自然语言,
            发起者=发起者,
            状态=意图状态.已提交,
        )
        意图.播报历史.append(f"[{self._时间戳()}] 意图已提交：{自然语言}")

        # 跨链兑换
        if ("换" in 文本 or "兑换" in 文本 or "swap" in 文本) and \
           any(k in 文本 for k in ["eth", "hkaic", "usdt", "btc"]):
            意图.类型 = 意图类型.跨链兑换
            意图.源资产, 意图.目标资产, 意图.金额 = self._解析兑换参数(文本)
            意图.播报历史.append(f"[{self._时间戳()}] 识别为跨链兑换意图：{意图.源资产} -> {意图.目标资产}")

        # 质押收益优化
        elif "年化" in 文本 or "收益率" in 文本 or "收益" in 文本 and "质押" in 文本:
            意图.类型 = 意图类型.质押收益优化
            意图.期望收益率 = self._解析期望收益率(文本)
            意图.播报历史.append(f"[{self._时间戳()}] 识别为质押收益优化意图，期望年化{意图.期望收益率}%")

        # 资产分散
        elif "分散" in 文本 or "分配" in 文本 and "链" in 文本:
            意图.类型 = 意图类型.资产分散
            意图.目标链列表 = self._解析目标链(文本)
            意图.播报历史.append(f"[{self._时间戳()}] 识别为资产分散意图，目标链：{意图.目标链列表}")

        # 跨链转移
        elif "跨链" in 文本 or "桥" in 文本:
            意图.类型 = 意图类型.跨链转移
            意图.源资产, 意图.目标资产, 意图.金额 = self._解析兑换参数(文本)
            意图.播报历史.append(f"[{self._时间戳()}] 识别为跨链转移意图")

        # 默认自定义
        else:
            意图.类型 = 意图类型.自定义
            意图.播报历史.append(f"[{self._时间戳()}] 识别为自定义意图，将进入Solver匹配")

        self._活跃意图[意图.意图ID] = 意图
        return 意图

    def _解析兑换参数(self, 文本: str) -> Tuple[str, str, float]:
        """解析兑换参数"""
        源 = 目标 = ""
        金额 = 0.0
        代币列表 = ["eth", "hkaic", "usdt", "btc", "usdc"]
        找到的 = [t for t in 代币列表 if t in 文本]
        if len(找到的) >= 2:
            if "换" in 文本:
                idx = 文本.index("换")
                for t in 找到的:
                    if 文本.index(t) < idx:
                        源 = t.upper()
                    else:
                        目标 = t.upper()
            else:
                源 = 找到的[0].upper()
                目标 = 找到的[1].upper()
        elif len(找到的) == 1:
            # 根据上下文推断
            if "换成" in 文本:
                源 = 找到的[0].upper()
            else:
                目标 = 找到的[0].upper()
        # 解析金额
        import re
        金额匹配 = re.search(r'(\d+(?:\.\d+)?)', 文本)
        if 金额匹配:
            金额 = float(金额匹配.group(1))
        return 源, 目标, 金额

    def _解析期望收益率(self, 文本: str) -> float:
        """解析期望收益率"""
        import re
        匹配 = re.search(r'(\d+(?:\.\d+)?)\s*%', 文本)
        if 匹配:
            return float(匹配.group(1))
        匹配 = re.search(r'年化\s*(\d+(?:\.\d+)?)', 文本)
        if 匹配:
            return float(匹配.group(1))
        return 0.0

    def _解析目标链(self, 文本: str) -> List[str]:
        """解析目标链"""
        链名映射 = {"eth": "Ethereum", "以太坊": "Ethereum",
                    "btc": "Bitcoin", "比特币": "Bitcoin",
                    "hkc": "Hongkun AI Chain", "鸿坤": "Hongkun AI Chain",
                    "bsc": "BSC", "币安": "BSC"}
        找到的链 = []
        for 关键词, 链名 in 链名映射.items():
            if 关键词 in 文本.lower() and 链名 not in 找到的链:
                找到的链.append(链名)
        # 数字指定
        import re
        数字匹配 = re.search(r'(\d+)\s*条链', 文本)
        if 数字匹配:
            数量 = int(数字匹配.group(1))
            while len(找到的链) < 数量:
                找到的链.append(f"链{len(找到的链) + 1}")
        return 找到的链

    # ========== Solver匹配 ==========

    def 匹配Solver(self, 意图ID: str) -> Tuple[Optional[执行方案], str]:
        """
        为意图匹配最佳Solver
        Solver竞争执行，最优者获胜
        """
        意图 = self._活跃意图.get(意图ID)
        if not 意图:
            return None, "意图不存在"

        意图.状态 = 意图状态.匹配中
        意图.播报历史.append(f"[{self._时间戳()}] 开始匹配Solver...")

        if not self._Solver池:
            意图.状态 = 意图状态.已失败
            意图.播报历史.append(f"[{self._时间戳()}] 无可用Solver，意图失败")
            return None, "无可用Solver"

        # Solver竞争排序
        候选 = sorted(self._Solver池.values(), key=lambda s: s.竞争分数(), reverse=True)

        # 选择最佳Solver
        最佳 = 候选[0]

        # 生成执行方案
        方案 = 执行方案(
            SolverID=最佳.SolverID,
            预计耗时秒=self._估算执行时间(意图),
            预计费用=self._估算费用(意图),
            路径描述=self._生成路径描述(意图, 最佳),
            竞争分数=最佳.竞争分数(),
        )

        意图.匹配的Solver = 最佳.SolverID
        意图.执行方案 = 方案
        意图.匹配时间 = time.time()
        意图.状态 = 意图状态.执行中

        意图.播报历史.append(
            f"[{self._时间戳()}] Solver {最佳.SolverID} 胜出 "
            f"(竞争分数:{最佳.竞争分数():.1f}，ATH验证:{'是' if 最佳.ATH验证 else '否'})"
        )
        意图.播报历史.append(f"[{self._时间戳()}] 执行方案：{方案.路径描述}")

        return 方案, f"已匹配Solver {最佳.SolverID}，预计{方案.预计耗时秒:.0f}秒完成"

    def _估算执行时间(self, 意图: 用户意图) -> float:
        """估算意图执行时间"""
        基础时间 = {
            意图类型.跨链兑换: 120.0,
            意图类型.质押收益优化: 30.0,
            意图类型.资产分散: 180.0,
            意图类型.跨链转移: 90.0,
            意图类型.自定义: 60.0,
        }
        return 基础时间.get(意图.类型, 60.0)

    def _估算费用(self, 意图: 用户意图) -> float:
        """估算执行费用"""
        if 意图.金额 > 0:
            return 意图.金额 * 0.001  # 0.1%手续费
        return 0.5  # 固定费用

    def _生成路径描述(self, 意图: 用户意图, solver: Solver信息) -> str:
        """AI生成执行路径描述"""
        if 意图.类型 == 意图类型.跨链兑换:
            return f"通过涌信桥ETB将{意图.源资产}兑换为{意图.目标资产}，Solver垫付后验证结算"
        elif 意图.类型 == 意图类型.质押收益优化:
            return f"AI推荐最优质押方案，目标年化{意图.期望收益率}%+"
        elif 意图.类型 == 意图类型.资产分散:
            链列表 = "、".join(意图.目标链列表) if 意图.目标链列表 else "多条链"
            return f"通过ETB将资产分散到{链列表}，AI优化分配比例"
        elif 意图.类型 == 意图类型.跨链转移:
            return f"通过涌信桥ETB跨链转移，动态验证组保障安全"
        return "自定义执行路径"

    # ========== 意图执行 ==========

    def 确认执行(self, 意图ID: str) -> Tuple[bool, str]:
        """用户确认执行意图"""
        意图 = self._活跃意图.get(意图ID)
        if not 意图:
            return False, "意图不存在"
        if 意图.状态 != 意图状态.执行中:
            return False, f"意图当前状态为{意图.状态.value}，无法确认执行"
        意图.播报历史.append(f"[{self._时间戳()}] 用户确认执行，意图进入执行阶段")
        return True, "意图执行已确认"

    def 完成意图(self, 意图ID: str, 成功: bool = True) -> Tuple[bool, str]:
        """标记意图完成"""
        意图 = self._活跃意图.get(意图ID)
        if not 意图:
            return False, "意图不存在"

        意图.完成时间 = time.time()
        if 成功:
            意图.状态 = 意图状态.已完成
            意图.播报历史.append(f"[{self._时间戳()}] ✅ 意图执行完成！")
            # 更新Solver表现
            if 意图.匹配的Solver:
                self.更新Solver表现(意图.匹配的Solver, 成功=True,
                                    延迟=意图.完成时间 - 意图.匹配时间)
        else:
            意图.状态 = 意图状态.已失败
            意图.播报历史.append(f"[{self._时间戳()}] ❌ 意图执行失败")
            if 意图.匹配的Solver:
                self.更新Solver表现(意图.匹配的Solver, 成功=False)

        self._意图历史.append(意图)
        del self._活跃意图[意图ID]
        return True, f"意图已{'完成' if 成功 else '失败'}"

    def 取消意图(self, 意图ID: str) -> Tuple[bool, str]:
        """取消意图"""
        意图 = self._活跃意图.get(意图ID)
        if not 意图:
            return False, "意图不存在"
        意图.状态 = 意图状态.已取消
        意图.播报历史.append(f"[{self._时间戳()}] 意图已取消")
        self._意图历史.append(意图)
        del self._活跃意图[意图ID]
        return True, "意图已取消"

    # ========== 状态查询 ==========

    def 获取意图状态(self, 意图ID: str) -> Optional[用户意图]:
        """获取意图当前状态"""
        return self._活跃意图.get(意图ID)

    def 获取播报(self, 意图ID: str) -> List[str]:
        """获取意图的AI播报历史"""
        意图 = self._活跃意图.get(意图ID)
        if 意图:
            return 意图.播报历史
        # 查历史
        for h in self._意图历史:
            if h.意图ID == 意图ID:
                return h.播报历史
        return []

    def 意图完成率(self, 地址: str = "") -> Dict:
        """统计意图完成率"""
        历史 = self._意图历史
        if 地址:
            历史 = [i for i in 历史 if i.发起者 == 地址]
        if not 历史:
            return {"总数": 0, "完成": 0, "失败": 0, "取消": 0, "完成率": 0.0}
        完成 = sum(1 for i in 历史 if i.状态 == 意图状态.已完成)
        失败 = sum(1 for i in 历史 if i.状态 == 意图状态.已失败)
        取消 = sum(1 for i in 历史 if i.状态 == 意图状态.已取消)
        return {
            "总数": len(历史),
            "完成": 完成,
            "失败": 失败,
            "取消": 取消,
            "完成率": 完成 / len(历史) if 历史 else 0.0,
        }

    def _时间戳(self) -> str:
        """获取简短时间戳"""
        return time.strftime("%H:%M:%S")
