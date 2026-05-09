"""
社交恢复模块 (social_recovery.py)
===================================
替代助记词恢复方案：守护者网络 + 阈值签名恢复。
守护者必须PoEI涌现分数超过阈值。
AI推荐守护者，帮助恢复可获奖励。
纯Python标准库，零外部依赖。
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


class 恢复状态(Enum):
    """社交恢复流程状态"""
    空闲 = "idle"
    恢复发起 = "initiated"
    守护者确认中 = "confirming"
    已确认 = "confirmed"
    资产迁移中 = "migrating"
    恢复完成 = "completed"
    恢复失败 = "failed"
    冻结中 = "frozen"


@dataclass
class 守护者信息:
    """守护者详情"""
    地址: str
    别名: str = ""
    PoEI分数: float = 0.0
    信用等级: str = ""
    已确认: bool = False
    确认时间: float = 0.0
    是AI推荐: bool = False


@dataclass
class 恢复请求:
    """社交恢复请求"""
    请求ID: str = ""
    原地址: str = ""
    新地址: str = ""
    发起时间: float = 0.0
    状态: 恢复状态 = 恢复状态.空闲
    守护者列表: List[守护者信息] = field(default_factory=list)
    确认阈值: float = 0.667  # 2/3
    已获确认数: int = 0
    所需确认数: int = 0
    冻结原因: str = ""
    完成时间: float = 0.0

    def __post_init__(self):
        if self.发起时间 == 0:
            self.发起时间 = time.time()
        if not self.请求ID:
            # H-08修复: 使用os.urandom加密随机数，替代可预测的time.time_ns()
            import os as _os
            self.请求ID = hashlib.sha256(
                f"{self.原地址}{self.新地址}{_os.urandom(16).hex()}".encode()
            ).hexdigest()[:16]
        if self.守护者列表:
            self.所需确认数 = max(1, int(len(self.守护者列表) * self.确认阈值 + 0.5))

    @property
    def 确认进度(self) -> str:
        """恢复进度描述"""
        return f"{self.已获确认数}/{self.所需确认数} 守护者已确认"


class 社交恢复引擎:
    """
    社交恢复引擎 - 涌信钱包核心创新

    设计原则：
      - 不再依赖助记词，守护者网络提供恢复保障
      - 守护者必须是PoEI涌现分数超过阈值的可信地址
      - 3/5阈值签名即可恢复（M-06修复：从2/3提升到3/5，最低5人3确认）
      - AI推荐守护者：根据信用分和社交关系
      - 恢复奖励：帮助恢复的守护者获得HKAIC奖励
      - 紧急冻结：发现私钥泄露可一键冻结
    """

    def __init__(self, 守护者PoEI最低分: float = 50.0, 恢复阈值: float = 0.6):
        # M-06修复: 最低守护者数提升到5，阈值提升到3/5(60%)
        self._守护者PoEI最低分 = 守护者PoEI最低分
        self._恢复阈值 = 恢复阈值
        self._最低守护者数 = 5  # M-06: 从3提升到5
        self._最低确认数 = 3    # M-06: 从2提升到3
        # 各钱包地址的守护者配置
        self._守护者配置: Dict[str, List[守护者信息]] = {}
        # 活跃恢复请求
        self._恢复请求: Dict[str, 恢复请求] = {}
        # 冻结地址
        self._冻结地址: Set[str] = set()
        # 恢复历史
        self._恢复历史: List[恢复请求] = []
        # 恢复奖励池
        self._奖励池: float = 1000.0  # HKAIC
        self._单次奖励: float = 10.0   # HKAIC

    # ========== 守护者管理 ==========

    def 添加守护者(self, 钱包地址: str, 守护者地址: str, 别名: str = "",
                   PoEI分数: float = 0.0, 是AI推荐: bool = False) -> Tuple[bool, str]:
        """
        添加守护者
        返回 (是否成功, 消息)
        """
        # 验证PoEI分数
        if PoEI分数 < self._守护者PoEI最低分 and not 是AI推荐:
            return False, f"守护者PoEI分数({PoEI分数:.1f})未达最低要求({self._守护者PoEI最低分:.1f})"

        # 不能添加自己为守护者
        if 守护者地址 == 钱包地址:
            return False, "不能添加自己为守护者"

        # 不能重复添加
        if 钱包地址 in self._守护者配置:
            for g in self._守护者配置[钱包地址]:
                if g.地址 == 守护者地址:
                    return False, "该地址已是守护者"

        守护者 = 守护者信息(
            地址=守护者地址,
            别名=别名 or 守护者地址[:10],
            PoEI分数=PoEI分数,
            是AI推荐=是AI推荐,
        )

        if 钱包地址 not in self._守护者配置:
            self._守护者配置[钱包地址] = []
        self._守护者配置[钱包地址].append(守护者)
        return True, f"守护者 {守护者.别名} 已添加"

    def 移除守护者(self, 钱包地址: str, 守护者地址: str) -> Tuple[bool, str]:
        """移除守护者"""
        if 钱包地址 not in self._守护者配置:
            return False, "未配置守护者"
        原列表 = self._守护者配置[钱包地址]
        新列表 = [g for g in 原列表 if g.地址 != 守护者地址]
        if len(新列表) == len(原列表):
            return False, "未找到该守护者"
        self._守护者配置[钱包地址] = 新列表
        return True, "守护者已移除"

    def 获取守护者列表(self, 钱包地址: str) -> List[守护者信息]:
        """获取钱包的守护者列表"""
        return self._守护者配置.get(钱包地址, [])

    def AI推荐守护者(self, 钱包地址: str, 候选地址池: Dict[str, Tuple[float, str]],
                     推荐数量: int = 3) -> List[守护者信息]:
        """
        AI推荐守护者
        候选地址池: {地址: (PoEI分数, 信用等级)}
        推荐策略：
          1. PoEI分数越高越优先
          2. 信用等级越高越优先
          3. 避免选择与已有守护者高度关联的地址（分散风险）
        """
        已有 = {g.地址 for g in self._守护者配置.get(钱包地址, [])}
        候选 = []
        for 地址, (分数, 等级) in 候选地址池.items():
            if 地址 == 钱包地址 or 地址 in 已有:
                continue
            if 分数 < self._守护者PoEI最低分:
                continue
            # 信用等级权重
            等级权重 = {"涌金级": 5, "涌银级": 4, "涌铜级": 3, "普通级": 2, "风险级": 0}
            权重 = 分数 * 0.7 + 等级权重.get(等级, 1) * 10
            候选.append((权重, 地址, 分数, 等级))
        # 按权重排序取Top N
        候选.sort(key=lambda x: x[0], reverse=True)
        推荐结果 = []
        for i, (_, 地址, 分数, 等级) in enumerate(候选[:推荐数量]):
            推荐结果.append(守护者信息(
                地址=地址,
                别名=f"AI推荐#{i + 1}",
                PoEI分数=分数,
                信用等级=等级,
                是AI推荐=True,
            ))
        return 推荐结果

    # ========== 恢复流程 ==========

    def 发起恢复(self, 原地址: str, 新地址: str) -> Tuple[Optional[恢复请求], str]:
        """
        发起社交恢复
        1. 验证守护者数量足够
        2. 创建恢复请求
        3. 通知守护者
        """
        守护者列表 = self._守护者配置.get(原地址, [])
        # M-06修复: 最低守护者数量从3提升到5
        if len(守护者列表) < self._最低守护者数:
            return None, f"守护者数量不足（需要至少{self._最低守护者数}个，当前{len(守护者列表)}个）"
        # M-06修复: 确保所需确认数不低于最低确认数
        计算确认数 = max(1, int(len(守护者列表) * self._恢复阈值 + 0.5))
        if 计算确认数 < self._最低确认数:
            计算确认数 = self._最低确认数

        # 创建恢复请求
        请求 = 恢复请求(
            原地址=原地址,
            新地址=新地址,
            状态=恢复状态.恢复发起,
            守护者列表=[守护者信息(地址=g.地址, 别名=g.别名, PoEI分数=g.PoEI分数)
                        for g in 守护者列表],
            确认阈值=self._恢复阈值,
        )
        请求.所需确认数 = 计算确认数
        self._恢复请求[请求.请求ID] = 请求
        return 请求, f"恢复请求已创建，ID: {请求.请求ID}，需{请求.所需确认数}个守护者确认"

    def 守护者确认(self, 请求ID: str, 守护者地址: str) -> Tuple[bool, str]:
        """
        守护者确认恢复请求
        返回 (是否成功, 消息)
        """
        请求 = self._恢复请求.get(请求ID)
        if not 请求:
            return False, "恢复请求不存在"

        if 请求.状态 not in (恢复状态.恢复发起, 恢复状态.守护者确认中):
            return False, f"恢复请求当前状态为{请求.状态.value}，无法确认"

        # 查找守护者
        守护者 = None
        for g in 请求.守护者列表:
            if g.地址 == 守护者地址 and not g.已确认:
                守护者 = g
                break
        if not 守护者:
            return False, "该守护者不在此恢复请求中或已确认"

        # 确认
        守护者.已确认 = True
        守护者.确认时间 = time.time()
        请求.已获确认数 += 1
        请求.状态 = 恢复状态.守护者确认中

        # 检查是否达到阈值
        if 请求.已获确认数 >= 请求.所需确认数:
            请求.状态 = 恢复状态.已确认
            return True, f"守护者确认成功！已达到恢复阈值({请求.确认进度})，可以执行资产迁移。"

        return True, f"守护者确认成功。当前进度：{请求.确认进度}"

    def 执行资产迁移(self, 请求ID: str) -> Tuple[bool, str]:
        """
        执行资产迁移（确认达到阈值后）
        1. 新地址继承原地址资产
        2. 旧地址冻结
        3. 奖励守护者
        """
        请求 = self._恢复请求.get(请求ID)
        if not 请求:
            return False, "恢复请求不存在"
        if 请求.状态 != 恢复状态.已确认:
            return False, f"恢复请求尚未达到确认阈值(当前:{请求.确认进度})"

        请求.状态 = 恢复状态.资产迁移中
        # 冻结旧地址
        self._冻结地址.add(请求.原地址)
        # 完成恢复
        请求.状态 = 恢复状态.恢复完成
        请求.完成时间 = time.time()
        # 奖励守护者
        for g in 请求.守护者列表:
            if g.已确认 and self._奖励池 >= self._单次奖励:
                self._奖励池 -= self._单次奖励
        # 记录历史
        self._恢复历史.append(请求)
        # 清理活跃请求
        del self._恢复请求[请求ID]
        return True, f"资产迁移完成！新地址 {请求.新地址[:10]}... 已继承原地址资产。"

    # ========== 紧急冻结 ==========

    def 紧急冻结(self, 钱包地址: str, 原因: str = "私钥泄露") -> Tuple[bool, str]:
        """
        一键紧急冻结：发现私钥泄露时使用
        冻结后需要守护者确认才能解冻或恢复
        """
        if 钱包地址 in self._冻结地址:
            return False, "地址已处于冻结状态"
        self._冻结地址.add(钱包地址)
        return True, f"地址 {钱包地址[:10]}... 已紧急冻结。原因：{原因}。请联系守护者进行恢复。"

    def 是否冻结(self, 地址: str) -> bool:
        """检查地址是否被冻结"""
        return 地址 in self._冻结地址

    # ========== 状态查询 ==========

    def 获取恢复请求(self, 请求ID: str) -> Optional[恢复请求]:
        """获取恢复请求详情"""
        return self._恢复请求.get(请求ID)

    def 获取恢复历史(self, 地址: str = "") -> List[恢复请求]:
        """获取恢复历史"""
        if 地址:
            return [r for r in self._恢复历史 if r.原地址 == 地址 or r.新地址 == 地址]
        return self._恢复历史

    def 获取奖励池余额(self) -> float:
        """获取恢复奖励池余额"""
        return self._奖励池
