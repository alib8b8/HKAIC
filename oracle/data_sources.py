"""
HKC 数据源管理 (data_sources.py)
=================================
数据源类型、注册、健康监控、轮换、黑名单。
纯Python标准库，零外部依赖。
中文代码风格。
"""

import time
import math
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum
import random

from oracle.oracle_core import 数据点, 价格数据点, 数据源类型, 数据类型


class 数据源状态(Enum):
    """数据源状态"""
    正常 = "healthy"
    可疑 = "suspicious"
    异常 = "unhealthy"
    下线 = "offline"
    黑名单 = "blacklisted"


@dataclass
class 数据源健康报告:
    """数据源健康报告"""
    数据源: str = ""
    状态: 数据源状态 = 数据源状态.正常
    响应时间: float = 0.0              # 毫秒
    可用率: float = 1.0                # 0-1
    数据新鲜度: float = 1.0            # 0-1
    最后更新时间: float = 0.0
    最后成功时间: float = 0.0
    连续失败次数: int = 0
    总更新次数: int = 0
    健康评分: float = 100.0             # 0-100


@dataclass
class 数据源配置:
    """数据源配置"""
    名称: str = ""
    类型: 数据源类型 = 数据源类型.DEX链上
    权重: float = 1.0                   # 基础权重
    超时毫秒: float = 5000              # 超时时间
    最大重试: int = 3                   # 最大重试次数
    冷却时间秒: float = 60              # 故障后冷却时间
    最小可用率: float = 0.8              # 最低可用率要求
    最低健康评分: float = 60.0          # 最低健康评分
    自定义参数: Dict[str, Any] = field(default_factory=dict)


class 数据源管理器:
    """
    HKC 数据源管理器
    
    职责：
    1. 数据源注册和配置
    2. 健康监控（响应时间、可用率、新鲜度）
    3. 自动轮换（切换到最健康的数据源）
    4. 黑名单管理（持续异常自动加入）
    
    支持的数据源类型：
    - DEX链上价格：从HKC DEX流动性池读取
    - 跨链价格：通过ETB桥和IBC获取
    - 模拟外部API：提供接口（生产接CoinGecko等）
    - 链上推导价格：通过链上交易数据推算
    """

    def __init__(self):
        # 数据源配置: {名称: 配置}
        self._数据源配置: Dict[str, 数据源配置] = {}
        
        # 健康报告: {名称: 健康报告}
        self._健康报告: Dict[str, 数据源健康报告] = {}
        
        # 黑名单: {名称: (加入时间, 原因)}
        self._黑名单: Dict[str, Tuple[float, str]] = {}
        
        # 冷却中的数据源: {名称: 冷却结束时间}
        self._冷却中: Dict[str, float] = {}
        
        # 数据拉取回调: {类型: [回调函数]}
        self._拉取回调: Dict[str, List[Callable]] = {}
        
        # 统计数据
        self._总拉取次数: int = 0
        self._成功拉取次数: int = 0
        self._失败拉取次数: int = 0

    # ==================== 注册与管理 ====================

    def 注册数据源(self, 配置: 数据源配置) -> bool:
        """
        注册新的数据源
        
        参数:
            配置: 数据源配置
            
        返回:
            是否注册成功
        """
        名称 = 配置.名称
        
        self._数据源配置[名称] = 配置
        
        # 初始化健康报告
        self._健康报告[名称] = 数据源健康报告(
            数据源=名称,
            状态=数据源状态.正常,
            健康评分=100.0
        )
        
        return True

    def 注销数据源(self, 名称: str) -> bool:
        """注销数据源"""
        if 名称 in self._数据源配置:
            del self._数据源配置[名称]
        if 名称 in self._健康报告:
            del self._健康报告[名称]
        # 从黑名单移除
        if 名称 in self._黑名单:
            del self._黑名单[名称]
        return True

    def 获取数据源列表(
        self,
        状态过滤: Optional[数据源状态] = None,
        类型过滤: Optional[数据源类型] = None
    ) -> List[数据源配置]:
        """获取数据源列表（可过滤）"""
        结果 = []
        for 名称, 配置 in self._数据源配置.items():
            # 黑名单过滤
            if 名称 in self._黑名单:
                continue
            
            # 状态过滤
            if 状态过滤:
                报告 = self._健康报告.get(名称)
                if 报告 and 报告.状态 != 状态过滤:
                    continue
            
            # 类型过滤
            if 类型过滤 and 配置.类型 != 类型过滤:
                continue
            
            结果.append(配置)
        
        return 结果

    # ==================== 健康监控 ====================

    def 更新健康状态(
        self,
        名称: str,
        成功: bool,
        响应时间毫秒: float = 0,
        数据新鲜度: float = 1.0
    ) -> None:
        """
        更新数据源健康状态
        
        参数:
            名称: 数据源名称
            成功: 是否成功获取数据
            响应时间毫秒: 响应时间
            数据新鲜度: 数据新鲜度 0-1
        """
        if 名称 not in self._健康报告:
            self._健康报告[名称] = 数据源健康报告(数据源=名称)
        
        报告 = self._健康报告[名称]
        报告.最后更新时间 = time.time()
        报告.总更新次数 += 1
        报告.响应时间 = 响应时间毫秒
        报告.数据新鲜度 = 数据新鲜度

        if 成功:
            报告.最后成功时间 = time.time()
            报告.连续失败次数 = 0
            
            # 更新可用率（指数移动平均）
            alpha = 0.1
            报告.可用率 = 报告.可用率 * (1 - alpha) + alpha * 1.0
        else:
            报告.连续失败次数 += 1
            
            # 更新可用率
            alpha = 0.1
            报告.可用率 = 报告.可用率 * (1 - alpha) + alpha * 0.0

        # 计算健康评分
        self._计算健康评分(名称)
        
        # 检查是否需要加入黑名单
        self._检查黑名单(名称)

    def _计算健康评分(self, 名称: str) -> float:
        """计算数据源健康评分"""
        if 名称 not in self._健康报告:
            return 0.0
        
        报告 = self._健康报告[名称]
        配置 = self._数据源配置.get(名称)
        
        if not 配置:
            return 0.0
        
        评分 = 100.0
        
        # 可用率权重 40%
        可用率得分 = 报告.可用率 * 40
        评分 = 评分 - 40 + 可用率得分
        
        # 响应时间权重 30%
        # 低于500ms为满分，高于5000ms为0分
        响应时间得分 = max(0, 30 - (报告.响应时间 - 500) / 150 * 30)
        评分 = 评分 - 30 + 响应时间得分
        
        # 数据新鲜度权重 20%
        新鲜度得分 = 报告.数据新鲜度 * 20
        评分 = 评分 - 20 + 新鲜度得分
        
        # 连续失败惩罚
        失败惩罚 = min(20, 报告.连续失败次数 * 4)
        评分 -= 失败惩罚
        
        # 限制范围
        评分 = max(0, min(100, 评分))
        报告.健康评分 = 评分
        
        # 更新状态
        if 评分 >= 80:
            报告.状态 = 数据源状态.正常
        elif 评分 >= 60:
            报告.状态 = 数据源状态.可疑
        elif 评分 >= 40:
            报告.状态 = 数据源状态.异常
        else:
            报告.状态 = 数据源状态.下线
        
        return 评分

    def _检查黑名单(self, 名称: str) -> None:
        """检查是否需要加入黑名单"""
        报告 = self._健康报告.get(名称)
        配置 = self._数据源配置.get(名称)
        
        if not 报告 or not 配置:
            return
        
        # 加入黑名单条件
        加入黑名单 = False
        原因 = ""
        
        # 条件1：连续失败超过阈值
        if 报告.连续失败次数 >= 配置.最大重试:
            加入黑名单 = True
            原因 = f"连续失败{报告.连续失败次数}次"
        
        # 条件2：可用率低于最低要求
        if 报告.可用率 < 配置.最小可用率:
            加入黑名单 = True
            原因 = f"可用率{报告.可用率:.1%}低于要求"
        
        # 条件3：健康评分低于最低要求
        if 报告.健康评分 < 配置.最低健康评分:
            加入黑名单 = True
            原因 = f"健康评分{报告.健康评分:.1f}低于要求"
        
        if 加入黑名单:
            self._加入黑名单(名称, 原因)

    def _加入黑名单(self, 名称: str, 原因: str) -> None:
        """加入黑名单"""
        self._黑名单[名称] = (time.time(), 原因)
        if 名称 in self._健康报告:
            self._健康报告[名称].状态 = 数据源状态.黑名单

    def 获取健康报告(self, 名称: str) -> Optional[数据源健康报告]:
        """获取数据源健康报告"""
        return self._健康报告.get(名称)

    def 获取所有健康报告(self) -> List[数据源健康报告]:
        """获取所有健康报告"""
        return list(self._健康报告.values())

    # ==================== 黑名单管理 ====================

    def 获取黑名单(self) -> List[Tuple[str, str, float]]:
        """
        获取黑名单
        
        返回: [(名称, 原因, 加入时间), ...]
        """
        return [
            (名称, 信息[1], 信息[0])
            for 名称, 信息 in self._黑名单.items()
        ]

    def 移出黑名单(self, 名称: str) -> bool:
        """
        移出黑名单
        
        需要等待冷却时间
        """
        if 名称 not in self._黑名单:
            return False
        
        配置 = self._数据源配置.get(名称)
        if not 配置:
            return False
        
        # 设置冷却时间
        self._冷却中[名称] = time.time() + 配置.冷却时间秒
        
        # 清除黑名单记录
        del self._黑名单[名称]
        
        # 重置信度
        if 名称 in self._健康报告:
            报告 = self._健康报告[名称]
            报告.连续失败次数 = 0
            报告.状态 = 数据源状态.正常
        
        return True

    def 是否在黑名单(self, 名称: str) -> bool:
        """检查是否在黑名单"""
        return 名称 in self._黑名单

    # ==================== 数据拉取 ====================

    def 拉取数据(self, 名称: str, 数据键: str) -> Optional[数据点]:
        """
        拉取数据
        
        参数:
            名称: 数据源名称
            数据键: 数据键
            
        返回:
            数据点或None
        """
        self._总拉取次数 += 1
        
        # 检查黑名单
        if self.是否在黑名单(名称):
            self._失败拉取次数 += 1
            return None
        
        # 检查冷却
        if 名称 in self._冷却中:
            if time.time() < self._冷却中[名称]:
                self._失败拉取次数 += 1
                return None
            else:
                del self._冷却中[名称]
        
        配置 = self._数据源配置.get(名称)
        if not 配置:
            self._失败拉取次数 += 1
            return None
        
        # 调用拉取回调
        回调列表 = self._拉取回调.get(名称, [])
        for 回调 in 回调列表:
            try:
                开始时间 = time.time()
                结果 = 回调(数据键, 配置)
                响应时间 = (time.time() - 开始时间) * 1000
                
                if 结果 is not None:
                    self._成功拉取次数 += 1
                    self.更新健康状态(名称, True, 响应时间)
                    return 结果
            except Exception:
                pass
        
        self._失败拉取次数 += 1
        self.更新健康状态(名称, False)
        return None

    def 注册拉取回调(self, 名称: str, 回调: Callable) -> None:
        """注册数据拉取回调"""
        if 名称 not in self._拉取回调:
            self._拉取回调[名称] = []
        self._拉取回调[名称].append(回调)

    # ==================== 数据源轮换 ====================

    def 获取最健康数据源(
        self,
        数据键: str,
        类型: Optional[数据源类型] = None
    ) -> Optional[str]:
        """
        获取最健康的数据源
        
        参数:
            数据键: 数据键
            类型: 数据源类型过滤
            
        返回:
            最健康的数据源名称
        """
        数据源列表 = self.获取数据源列表(类型过滤=类型)
        
        if not 数据源列表:
            return None
        
        # 按健康评分排序
        排序列表 = sorted(
            数据源列表,
            key=lambda x: self._健康报告.get(x.名称, 数据源健康报告(数据源=x.名称)).健康评分,
            reverse=True
        )
        
        # 返回评分最高的数据源
        for 配置 in 排序列表:
            if not self.是否在黑名单(配置.名称):
                return 配置.名称
        
        return None

    def 获取加权随机数据源(
        self,
        数据键: str,
        类型: Optional[数据源类型] = None
    ) -> Optional[str]:
        """
        获取加权随机的数据源
        
        健康评分高的数据源被选中的概率更高
        
        返回:
            选中的数据源名称
        """
        数据源列表 = self.获取数据源列表(类型过滤=类型)
        
        if not 数据源列表:
            return None
        
        # 计算权重
        权重列表: List[Tuple[str, float]] = []
        总权重 = 0.0
        
        for 配置 in 数据源列表:
            if self.是否在黑名单(配置.名称):
                continue
            
            报告 = self._健康报告.get(配置.名称)
            健康评分 = report.健康评分 if 报告 else 50.0
            
            # 权重 = 健康评分 * 基础权重
            权重 = 健康评分 * 配置.权重
            权重列表.append((配置.名称, 权重))
            总权重 += 权重
        
        if not 权重列表:
            return None
        
        # 加权随机选择
        随机值 = random.random() * 总权重
        累计 = 0.0
        
        for 名称, 权重 in 权重列表:
            累计 += 权重
            if 随机值 <= 累计:
                return 名称
        
        return 权重列表[-1][0]

    # ==================== 统计 ====================

    def 获取统计信息(self) -> Dict:
        """获取统计信息"""
        黑名单数 = len(self._黑名单)
        冷却中数 = len(self._冷却中)
        
        健康分布 = {
            "正常": 0,
            "可疑": 0,
            "异常": 0,
            "下线": 0,
            "黑名单": 黑名单数
        }
        
        for 报告 in self._健康报告.values():
            if 报告.状态 == 数据源状态.正常:
                健康分布["正常"] += 1
            elif 报告.状态 == 数据源状态.可疑:
                健康分布["可疑"] += 1
            elif 报告.状态 == 数据源状态.异常:
                健康分布["异常"] += 1
            elif 报告.状态 == 数据源状态.下线:
                健康分布["下线"] += 1
        
        return {
            "注册数据源数": len(self._数据源配置),
            "健康报告数": len(self._健康报告),
            "黑名单数": 黑名单数,
            "冷却中数": 冷却中数,
            "健康分布": 健康分布,
            "总拉取次数": self._总拉取次数,
            "成功拉取次数": self._成功拉取次数,
            "失败拉取次数": self._失败拉取次数,
            "成功率": self._成功拉取次数 / max(1, self._总拉取次数),
        }


# ==================== 模拟数据源 ====================

class 模拟数据源:
    """
    模拟数据源
    
    提供测试用数据源实现
    支持多种价格波动模式
    """

    def __init__(
        self,
        名称: str,
        基础价格: float = 100.0,
        波动率: float = 0.01,
        延迟毫秒: float = 100,
        故障率: float = 0.0
    ):
        self.名称 = 名称
        self.基础价格 = 基础价格
        self.波动率 = 波动率
        self.延迟毫秒 = 延迟毫秒
        self.故障率 = 故障率
        self.当前价格 = 基础价格
        self.更新次数 = 0

    def 模拟延迟(self) -> None:
        """模拟网络延迟"""
        if self.延迟毫秒 > 0:
            time.sleep(self.延迟毫秒 / 1000)

    def 更新价格(self) -> float:
        """更新模拟价格"""
        # 随机游走
        随机变化 = random.gauss(0, self.波动率)
        self.当前价格 *= (1 + 随机变化)
        self.更新次数 += 1
        return self.当前价格

    def 拉取价格(self, 数据键: str) -> Optional[价格数据点]:
        """
        模拟拉取价格
        
        参数:
            数据键: e.g., "HKAIC/USDT"
            
        返回:
            价格数据点
        """
        self.模拟延迟()
        
        # 模拟故障
        if random.random() < self.故障率:
            return None
        
        价格 = self.更新价格()
        
        return 价格数据点(
            数据源=self.名称,
            数据源类型=数据源类型.外部API,
            交易对=数据键,
            数值=价格,
            置信度=0.9,
            时间戳=time.time()
        )

    def 注入价格偏移(self, 偏移比例: float) -> None:
        """
        注入价格偏移（用于测试异常检测）
        
        参数:
            偏移比例: e.g., 0.2 表示20%偏移
        """
        self.当前价格 = self.基础价格 * (1 + 偏移比例)

    def 恢复正常(self) -> None:
        """恢复正常价格"""
        self.当前价格 = self.基础价格
