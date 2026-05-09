"""
HKC 安全排行榜 (security_leaderboard.py)
==========================================
对抗安全游戏的荣誉系统。
排行维度：攻击成功率、防御拦截率、创新贡献、综合评分。
称号系统从学徒到大师，激励持续参与。

排行维度：
  - 攻击成功率：攻击成功次数/总攻击次数
  - 防御拦截率：防御成功次数/总防御次数
  - 创新贡献：发现新攻击/防御模式的数量和质量
  - 综合评分：加权综合分

称号系统：
  攻击者：黑客学徒→渗透专家→零日猎手→涌现攻师
  防御者：哨兵→铁壁→守护者→涌现守师

排行榜周期：日榜/周榜/月榜/总榜

纯Python标准库，零外部依赖。
"""

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class 排行周期(Enum):
    """排行榜周期"""
    日榜 = "daily"
    周榜 = "weekly"
    月榜 = "monthly"
    总榜 = "all_time"


class 称号等级(Enum):
    """称号等级"""
    # 攻击者称号
    黑客学徒 = "hacker_apprentice"
    渗透专家 = "penetration_expert"
    零日猎手 = "zeroday_hunter"
    涌现攻师 = "emergence_attacker"
    # 防御者称号
    哨兵 = "sentinel"
    铁壁 = "iron_wall"
    守护者 = "guardian"
    涌现守师 = "emergence_defender"


@dataclass
class 参与者战绩:
    """参与者战绩统计"""
    地址: str
    名称: str = ""
    角色: str = "both"          # "attacker" / "defender" / "both"
    # 攻击统计
    攻击次数: int = 0
    攻击成功次数: int = 0
    攻击得分: float = 0.0
    发现漏洞数: int = 0
    # 防御统计
    防御次数: int = 0
    防御成功次数: int = 0
    防御得分: float = 0.0
    零漏洞天数: int = 0
    # 创新统计
    创新贡献数: int = 0
    创新质量分: float = 0.0
    # 涌现分数
    涌现分数: float = 1.0
    # 称号
    攻击称号: 称号等级 = 称号等级.黑客学徒
    防御称号: 称号等级 = 称号等级.哨兵
    # 综合评分
    综合评分: float = 0.0
    # 最后活跃
    最后活跃: float = 0.0

    @property
    def 攻击成功率(self) -> float:
        if self.攻击次数 == 0:
            return 0.0
        return self.攻击成功次数 / self.攻击次数

    @property
    def 防御拦截率(self) -> float:
        if self.防御次数 == 0:
            return 0.0
        return self.防御成功次数 / self.防御次数

    def 计算综合评分(self) -> float:
        """计算综合评分

        权重：
          攻击成功率: 25%
          防御拦截率: 25%
          创新贡献: 30%
          涌现分数: 20%
        """
        攻击分 = self.攻击成功率 * 100
        防御分 = self.防御拦截率 * 100
        创新分 = min(100, self.创新质量分)
        涌现分 = min(100, self.涌现分数 * 10)

        self.综合评分 = 攻击分 * 0.25 + 防御分 * 0.25 + 创新分 * 0.30 + 涌现分 * 0.20
        return self.综合评分

    def 更新攻击称号(self):
        """根据攻击成绩更新攻击者称号"""
        成功率 = self.攻击成功率
        漏洞数 = self.发现漏洞数
        综合分 = self.综合评分

        if 成功率 >= 0.8 and 漏洞数 >= 5 and 综合分 >= 80:
            self.攻击称号 = 称号等级.涌现攻师
        elif 成功率 >= 0.6 and 漏洞数 >= 2 and 综合分 >= 60:
            self.攻击称号 = 称号等级.零日猎手
        elif 成功率 >= 0.4 and 综合分 >= 40:
            self.攻击称号 = 称号等级.渗透专家
        else:
            self.攻击称号 = 称号等级.黑客学徒

    def 更新防御称号(self):
        """根据防御成绩更新防御者称号"""
        拦截率 = self.防御拦截率
        零漏洞天 = self.零漏洞天数
        综合分 = self.综合评分

        if 拦截率 >= 0.9 and 零漏洞天 >= 30 and 综合分 >= 80:
            self.防御称号 = 称号等级.涌现守师
        elif 拦截率 >= 0.7 and 零漏洞天 >= 7 and 综合分 >= 60:
            self.防御称号 = 称号等级.守护者
        elif 拦截率 >= 0.5 and 综合分 >= 40:
            self.防御称号 = 称号等级.铁壁
        else:
            self.防御称号 = 称号等级.哨兵


@dataclass
class 挑战请求:
    """挑战请求"""
    挑战者: str
    被挑战者: str
    挑战者排名: int
    被挑战者排名: int
    时间: float = 0.0
    状态: str = "pending"    # pending / accepted / rejected / completed

    def __post_init__(self):
        if self.时间 == 0:
            self.时间 = time.time()


class 安全排行榜:
    """
    安全排行榜——对抗安全游戏的荣誉系统

    功能：
      - 多维度排行：攻击成功率、防御拦截率、创新贡献、综合评分
      - 称号系统：从学徒到大师
      - 多周期排行：日榜/周榜/月榜/总榜
      - 挑战机制：低排名可挑战高排名
      - 历史战绩：完整对战记录和统计

    与奖励分配器联动：
      - 排行榜排名影响奖励加成
      - 称号升级触发额外奖励
    """

    # 挑战规则：只能挑战排名在自己前面3位以内的
    挑战跨度 = 3

    def __init__(self):
        """初始化安全排行榜"""
        self._参与者: Dict[str, 参与者战绩] = {}
        self._排行缓存: Dict[排行周期, List[Tuple[str, float]]] = {}
        self._挑战请求: List[挑战请求] = []
        self._排行更新时间: Dict[排行周期, float] = {}

    def 注册参与者(self, 地址: str, 名称: str = "", 角色: str = "both") -> 参与者战绩:
        """注册参与者"""
        if 地址 in self._参与者:
            return self._参与者[地址]

        战绩 = 参与者战绩(地址=地址, 名称=名称, 角色=角色)
        self._参与者[地址] = 战绩
        return 战绩

    def 记录攻击结果(self, 地址: str, 成功: bool, 得分: float = 0.0,
                       是新漏洞: bool = False, 创新质量: float = 0.0):
        """记录攻击结果"""
        战绩 = self._参与者.get(地址)
        if not 战绩:
            战绩 = self.注册参与者(地址)

        战绩.攻击次数 += 1
        if 成功:
            战绩.攻击成功次数 += 1
            战绩.攻击得分 += 得分
        if 是新漏洞:
            战绩.发现漏洞数 += 1
            战绩.创新贡献数 += 1
            战绩.创新质量分 += 创新质量
        战绩.最后活跃 = time.time()
        战绩.计算综合评分()
        战绩.更新攻击称号()

    def 记录防御结果(self, 地址: str, 成功: bool, 得分: float = 0.0,
                       创新质量: float = 0.0):
        """记录防御结果"""
        战绩 = self._参与者.get(地址)
        if not 战绩:
            战绩 = self.注册参与者(地址)

        战绩.防御次数 += 1
        if 成功:
            战绩.防御成功次数 += 1
            战绩.防御得分 += 得分
        战绩.创新贡献数 += (1 if 创新质量 > 0.5 else 0)
        战绩.创新质量分 += 创新质量
        战绩.最后活跃 = time.time()
        战绩.计算综合评分()
        战绩.更新防御称号()

    def 更新零漏洞天数(self, 地址: str, 天数: int):
        """更新零漏洞连续天数"""
        战绩 = self._参与者.get(地址)
        if 战绩:
            战绩.零漏洞天数 = 天数
            战绩.计算综合评分()
            战绩.更新防御称号()

    def 获取排行(self, 周期: 排行周期 = 排行周期.总榜,
                  维度: str = "综合评分", 限制: int = 50) -> List[dict]:
        """获取排行榜

        参数:
            周期: 排行周期
            维度: 排行维度（"综合评分"/"攻击成功率"/"防御拦截率"/"创新贡献"）
            限制: 返回数量
        """
        # 计算排行
        参与者列表 = list(self._参与者.values())

        if 维度 == "攻击成功率":
            参与者列表.sort(key=lambda x: x.攻击成功率, reverse=True)
        elif 维度 == "防御拦截率":
            参与者列表.sort(key=lambda x: x.防御拦截率, reverse=True)
        elif 维度 == "创新贡献":
            参与者列表.sort(key=lambda x: x.创新质量分, reverse=True)
        else:
            参与者列表.sort(key=lambda x: x.综合评分, reverse=True)

        排行列表 = []
        for i, 战绩 in enumerate(参与者列表[:限制]):
            排行列表.append({
                "排名": i + 1,
                "地址": 战绩.地址,
                "名称": 战绩.名称,
                "综合评分": f"{战绩.综合评分:.2f}",
                "攻击成功率": f"{战绩.攻击成功率:.2%}",
                "防御拦截率": f"{战绩.防御拦截率:.2%}",
                "攻击称号": 战绩.攻击称号.value,
                "防御称号": 战绩.防御称号.value,
                "创新贡献": 战绩.创新贡献数,
            })

        return 排行列表

    def 获取排名(self, 地址: str, 维度: str = "综合评分") -> int:
        """获取指定参与者的排名"""
        排行 = self.获取排行(维度=维度, 限制=1000)
        for i, 条目 in enumerate(排行):
            if 条目["地址"] == 地址:
                return i + 1
        return -1  # 未上榜

    def 提交挑战(self, 挑战者地址: str, 被挑战者地址: str) -> Optional[挑战请求]:
        """提交挑战请求

        规则：只能挑战排名在自己前面3位以内的
        """
        挑战者排名 = self.获取排名(挑战者地址)
        被挑战者排名 = self.获取排名(被挑战者地址)

        if 挑战者排名 <= 0 or 被挑战者排名 <= 0:
            return None

        # 挑战者排名必须低于被挑战者
        if 挑战者排名 <= 被挑战者排名:
            return None

        # 挑战跨度检查
        if 挑战者排名 - 被挑战者排名 > self.挑战跨度:
            return None

        请求 = 挑战请求(
            挑战者=挑战者地址,
            被挑战者=被挑战者地址,
            挑战者排名=挑战者排名,
            被挑战者排名=被挑战者排名,
        )

        self._挑战请求.append(请求)
        return 请求

    def 获取参与者战绩(self, 地址: str) -> Optional[参与者战绩]:
        """获取参与者详细战绩"""
        return self._参与者.get(地址)

    def 排行榜摘要(self) -> dict:
        """获取排行榜摘要"""
        参与者列表 = list(self._参与者.values())

        # 称号分布
        攻击称号分布 = {}
        防御称号分布 = {}
        for p in 参与者列表:
            攻击称号分布[p.攻击称号.value] = 攻击称号分布.get(p.攻击称号.value, 0) + 1
            防御称号分布[p.防御称号.value] = 防御称号分布.get(p.防御称号.value, 0) + 1

        return {
            "参与者总数": len(参与者列表),
            "攻击称号分布": 攻击称号分布,
            "防御称号分布": 防御称号分布,
            "挑战请求数": len(self._挑战请求),
        }
