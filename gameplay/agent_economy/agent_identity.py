"""
HKC Agent身份系统 (agent_identity.py)
======================================
AI Agent是一等公民，拥有5级身份体系，从新手到传奇。
身份等级决定了Agent在链上的权限和收益比例。

核心概念：
  - 身份等级（Identity Level）：5级递进——新手→学徒→行家→大师→传奇
  - 身份凭证（Identity Credential）：ATH签发的可验证凭证
  - 身份升级（Level Up）：通过贡献度和信誉升级

纯Python标准库，零外部依赖。
"""

import math
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 身份等级(Enum):
    """Agent身份等级"""
    新手 = 1
    学徒 = 2
    行家 = 3
    大师 = 4
    传奇 = 5


@dataclass
class 升级条件:
    """升级所需的条件"""
    目标等级: 身份等级
    最低信誉分: float
    最低贡献度: float
    最低持有量: float
    最低活跃天数: int


# 预设升级条件
升级条件表 = {
    身份等级.学徒: 升级条件(身份等级.学徒, 10.0, 100.0, 500.0, 7),
    身份等级.行家: 升级条件(身份等级.行家, 30.0, 1000.0, 5000.0, 30),
    身份等级.大师: 升级条件(身份等级.大师, 60.0, 5000.0, 50000.0, 90),
    身份等级.传奇: 升级条件(身份等级.传奇, 90.0, 20000.0, 500000.0, 365),
}


@dataclass
class 身份凭证:
    """ATH签发的身份凭证"""
    凭证ID: str = ""
    AgentID: str = ""
    等级: 身份等级 = 身份等级.新手
    签发者: str = "ATH"
    签发时间: float = 0.0
    过期时间: float = 0.0
    签名: str = ""

    def __post_init__(self):
        if not self.凭证ID:
            self.凭证ID = hashlib.sha256(
                f"cred_{self.AgentID}_{time.time()}".encode()
            ).hexdigest()[:16]
        if self.签发时间 == 0.0:
            self.签发时间 = time.time()
        if self.过期时间 == 0.0:
            self.过期时间 = self.签发时间 + 86400 * 30  # 30天有效期

    def 是否有效(self) -> bool:
        """检查凭证是否有效"""
        return time.time() < self.过期时间 and bool(self.签名)


@dataclass
class Agent身份:
    """Agent完整身份信息"""
    AgentID: str = ""
    DID: str = ""
    名称: str = ""
    等级: 身份等级 = 身份等级.新手
    信誉分: float = 0.0
    贡献度: float = 0.0
    活跃天数: int = 0
    凭证: Optional[身份凭证] = None
    注册时间: float = 0.0
    最后活跃: float = 0.0
    元数据: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.AgentID:
            self.AgentID = hashlib.sha256(
                f"agent_{time.time()}".encode()
            ).hexdigest()[:16]
        if not self.DID:
            self.DID = f"did:hkc:{self.AgentID}"
        if self.注册时间 == 0.0:
            self.注册时间 = time.time()
        if self.最后活跃 == 0.0:
            self.最后活跃 = time.time()


class 身份管理器:
    """
    Agent身份管理器
    
    管理Agent的注册、凭证签发、等级升降。
    """

    def __init__(self):
        self._Agents: Dict[str, Agent身份] = {}
        self._凭证: Dict[str, 身份凭证] = {}
        self._等级统计: Dict[身份等级, int] = {lv: 0 for lv in 身份等级}

    def 注册Agent(self, 名称: str = "", 元数据: Optional[Dict] = None) -> Agent身份:
        """注册新Agent"""
        Agent = Agent身份(
            名称=名称,
            等级=身份等级.新手,
            元数据=元数据 or {},
        )
        self._Agents[Agent.AgentID] = Agent
        self._等级统计[身份等级.新手] += 1
        return Agent

    def 签发凭证(self, AgentID: str) -> Optional[身份凭证]:
        """签发身份凭证"""
        Agent = self._Agents.get(AgentID)
        if not Agent:
            return None

        凭证 = 身份凭证(
            AgentID=AgentID,
            等级=Agent.等级,
            签名=hashlib.sha256(
                f"sig_{AgentID}_{Agent.等级.value}_{time.time()}".encode()
            ).hexdigest()[:32],
        )
        Agent.凭证 = 凭证
        self._凭证[凭证.凭证ID] = 凭证
        return 凭证

    def 检查升级(self, AgentID: str) -> Tuple[bool, Optional[身份等级], str]:
        """
        检查Agent是否满足升级条件
        
        Returns:
            (是否可升级, 目标等级, 原因)
        """
        Agent = self._Agents.get(AgentID)
        if not Agent:
            return False, None, "Agent不存在"

        当前等级值 = Agent.等级.value
        if 当前等级值 >= 5:
            return False, None, "已达到最高等级"

        目标等级 = 身份等级(当前等级值 + 1)
        条件 = 升级条件表.get(目标等级)
        if not 条件:
            return False, None, "无升级条件定义"

        不满足 = []
        if Agent.信誉分 < 条件.最低信誉分:
            不满足.append(f"信誉分{Agent.信誉分:.0f}<{条件.最低信誉分:.0f}")
        if Agent.贡献度 < 条件.最低贡献度:
            不满足.append(f"贡献度{Agent.贡献度:.0f}<{条件.最低贡献度:.0f}")
        if Agent.活跃天数 < 条件.最低活跃天数:
            不满足.append(f"活跃天数{Agent.活跃天数}<{条件.最低活跃天数}")

        if 不满足:
            return False, 目标等级, "不满足: " + "; ".join(不满足)

        return True, 目标等级, "满足所有条件"

    def 执行升级(self, AgentID: str) -> Tuple[bool, str]:
        """执行Agent升级"""
        可升级, 目标等级, 原因 = self.检查升级(AgentID)
        if not 可升级:
            return False, 原因

        Agent = self._Agents[AgentID]
        旧等级 = Agent.等级
        self._等级统计[旧等级] -= 1
        Agent.等级 = 目标等级
        self._等级统计[目标等级] += 1

        # 重新签发凭证
        self.签发凭证(AgentID)

        return True, f"升级成功: {旧等级.name} → {目标等级.name}"

    def 更新Agent属性(
        self, AgentID: str, 信誉分: Optional[float] = None,
        贡献度: Optional[float] = None, 活跃天数: Optional[int] = None,
    ) -> bool:
        """更新Agent属性"""
        Agent = self._Agents.get(AgentID)
        if not Agent:
            return False
        if 信誉分 is not None:
            Agent.信誉分 = 信誉分
        if 贡献度 is not None:
            Agent.贡献度 = 贡献度
        if 活跃天数 is not None:
            Agent.活跃天数 = 活跃天数
        Agent.最后活跃 = time.time()
        return True

    def 获取Agent(self, AgentID: str) -> Optional[Agent身份]:
        """获取Agent信息"""
        return self._Agents.get(AgentID)

    def 验证凭证(self, 凭证ID: str) -> bool:
        """验证凭证有效性"""
        凭证 = self._凭证.get(凭证ID)
        if not 凭证:
            return False
        if not 凭证.是否有效():
            return False
        # 检查凭证等级与Agent当前等级一致
        Agent = self._Agents.get(凭证.AgentID)
        if not Agent or Agent.等级 != 凭证.等级:
            return False
        return True

    def 列出Agent(self, 等级过滤: Optional[身份等级] = None) -> List[Agent身份]:
        """列出所有Agent"""
        结果 = list(self._Agents.values())
        if 等级过滤:
            结果 = [a for a in 结果 if a.等级 == 等级过滤]
        return sorted(结果, key=lambda a: (a.等级.value, a.信誉分), reverse=True)

    def 获取等级统计(self) -> Dict[str, int]:
        """获取各等级Agent数量"""
        return {lv.name: self._等级统计[lv] for lv in 身份等级}
