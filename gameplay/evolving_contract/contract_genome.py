"""
HKC 合约基因组 (contract_genome.py)
====================================
将合约参数编码为"基因组"，支持变异、交叉、版本管理。
合约的"基因"决定了合约的行为特征——利率曲线、手续费率、质押参数等。
好的基因被保留，坏的基因被淘汰，合约在链上环境中自然选择。

核心概念：
  - 基因座（Locus）：单个参数的基因位，如利率、手续费率
  - 基因组（Genome）：所有基因座的集合，决定合约完整参数
  - 基因型（Genotype）：基因座的类型定义（范围、变异模式）

纯Python标准库，零外部依赖。
"""

import hashlib
import math
import os
import time
import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class 变异模式(Enum):
    """基因变异模式"""
    高斯 = "gaussian"        # 高斯变异：以当前值为均值微调
    均匀 = "uniform"         # 均匀变异：在范围内随机取值
    增量 = "incremental"     # 增量变异：固定步长递增/递减
    翻转 = "flip"            # 翻转变异：布尔值专用


@dataclass
class 基因型:
    """基因型定义——单个参数的规范
    定义了参数的名称、取值范围、变异模式和默认值。
    相当于"基因的蓝图"，基因组是蓝图的具体实例。
    """
    名称: str                       # 参数名称，如"利率"
    最小值: float                   # 参数下界
    最大值: float                   # 参数上界
    默认值: float                   # 默认参数值
    变异: 变异模式 = 变异模式.高斯   # 变异方式
    变异幅度: float = 0.1           # 变异幅度（高斯: σ/范围比; 均匀: 不用; 增量: 步长）
    安全边界: Tuple[float, float] = (0.0, 0.0)  # (下界安全线, 上界安全线)，0表示与最值一致
    描述: str = ""                  # 参数说明

    def __post_init__(self):
        """初始化安全边界"""
        if self.安全边界 == (0.0, 0.0):
            self.安全边界 = (self.最小值, self.最大值)

    def 是否在安全边界内(self, 值: float) -> bool:
        """检查值是否在安全边界内"""
        return self.安全边界[0] <= 值 <= self.安全边界[1]

    def 钳位(self, 值: float) -> float:
        """将值限制在合法范围内"""
        return max(self.最小值, min(self.最大值, 值))


@dataclass
class 基因座:
    """基因座——基因组中单个参数的实际值
    包含基因型定义和当前值，是基因组的基本组成单元。
    """
    基因型定义: 基因型
    当前值: float = 0.0
    变异历史: List[dict] = field(default_factory=list)

    def __post_init__(self):
        """初始化时使用默认值"""
        if self.当前值 == 0.0:
            self.当前值 = self.基因型定义.默认值

    def 变异(self, 变异率: float = 0.1, 随机源: Optional[bytes] = None) -> float:
        """执行基因变异

        参数:
            变异率: 变异概率（0-1）
            随机源: 可选的随机源，用于确定性测试
        返回:
            变异后的新值
        """
        # 决定是否变异
        if 随机源:
            决定 = int(hashlib.sha256(随机源 + self.基因型定义.名称.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        else:
            决定 = int.from_bytes(os.urandom(4), 'big') / 0xFFFFFFFF

        if 决定 > 变异率:
            return self.当前值  # 不变异

        旧值 = self.当前值
        定义 = self.基因型定义
        范围 = 定义.最大值 - 定义.最小值

        if 定义.变异 == 变异模式.高斯:
            # 高斯变异：以当前值为均值，σ=变异幅度*范围
            σ = 定义.变异幅度 * 范围
            # 使用Box-Muller变换生成高斯随机数
            if 随机源:
                u1 = int(hashlib.sha256(随机源 + b"u1" + str(旧值).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
                u2 = int(hashlib.sha256(随机源 + b"u2" + str(旧值).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
            else:
                u1 = int.from_bytes(os.urandom(4), 'big') / 0xFFFFFFFF
                u2 = int.from_bytes(os.urandom(4), 'big') / 0xFFFFFFFF
            u1 = max(u1, 1e-10)  # 避免log(0)
            z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
            新值 = 旧值 + z0 * σ

        elif 定义.变异 == 变异模式.均匀:
            # 均匀变异：在范围内随机取值
            if 随机源:
                r = int(hashlib.sha256(随机源 + b"u" + str(旧值).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
            else:
                r = int.from_bytes(os.urandom(4), 'big') / 0xFFFFFFFF
            新值 = 定义.最小值 + r * 范围

        elif 定义.变异 == 变异模式.增量:
            # 增量变异：固定步长方向随机
            if 随机源:
                方向 = 1 if int(hashlib.sha256(随机源 + b"d" + str(旧值).encode()).hexdigest()[:2], 16) % 2 == 0 else -1
            else:
                方向 = 1 if int.from_bytes(os.urandom(1), 'big') % 2 == 0 else -1
            新值 = 旧值 + 方向 * 定义.变异幅度

        elif 定义.变异 == 变异模式.翻转:
            # 翻转变异：布尔值专用
            新值 = 1.0 if 旧值 < 0.5 else 0.0

        else:
            新值 = 旧值

        # 钳位到合法范围
        新值 = 定义.钳位(新值)

        # 记录变异历史
        self.变异历史.append({
            "时间": time.time(),
            "旧值": 旧值,
            "新值": 新值,
            "变异率": 变异率,
            "模式": 定义.变异.value,
        })

        self.当前值 = 新值
        return 新值


class 合约基因组:
    """
    合约基因组——合约参数的完整编码

    将合约的所有可调参数编码为基因座集合，每个基因座对应一个参数。
    基因组可以被复制、变异、交叉，构成合约进化的遗传基础。

    典型基因座：
      - 利率曲线参数（基准利率、斜率）
      - 手续费率
      - 质押参数（最低质押、锁定期）
      - 清算阈值
      - 奖励分配比例
      - 涌现分数权重
    """

    # 预设基因型模板
    默认基因型模板: List[基因型] = [
        基因型(名称="基准利率", 最小值=0.001, 最大值=0.5, 默认值=0.05,
               变异=变异模式.高斯, 变异幅度=0.15, 安全边界=(0.005, 0.3),
               描述="借贷基准年化利率"),
        基因型(名称="利率斜率", 最小值=0.1, 最大值=10.0, 默认值=2.0,
               变异=变异模式.高斯, 变异幅度=0.1, 安全边界=(0.5, 5.0),
               描述="利率曲线斜率，控制利率随利用率增长的速度"),
        基因型(名称="手续费率", 最小值=0.0001, 最大值=0.05, 默认值=0.003,
               变异=变异模式.高斯, 变异幅度=0.1, 安全边界=(0.0005, 0.02),
               描述="交易手续费率"),
        基因型(名称="最低质押", 最小值=100, 最大值=100000, 默认值=1000,
               变异=变异模式.增量, 变异幅度=100, 安全边界=(500, 50000),
               描述="最低质押HKAIC数量"),
        基因型(名称="锁定期天数", 最小值=1, 最大值=365, 默认值=14,
               变异=变异模式.增量, 变异幅度=1, 安全边界=(7, 180),
               描述="质押锁定期天数"),
        基因型(名称="清算阈值", 最小值=0.5, 最大值=0.95, 默认值=0.8,
               变异=变异模式.高斯, 变异幅度=0.05, 安全边界=(0.6, 0.9),
               描述="抵押率低于此阈值触发清算"),
        基因型(名称="奖励分配比", 最小值=0.1, 最大值=0.9, 默认值=0.5,
               变异=变异模式.高斯, 变异幅度=0.1, 安全边界=(0.2, 0.8),
               描述="质押奖励分配比例（剩余归保险池）"),
        基因型(名称="涌现分数权重", 最小值=0.0, 最大值=2.0, 默认值=1.0,
               变异=变异模式.高斯, 变异幅度=0.15, 安全边界=(0.3, 1.5),
               描述="涌现分数在合约逻辑中的权重因子"),
        基因型(名称="自动复投", 最小值=0.0, 最大值=1.0, 默认值=0.0,
               变异=变异模式.翻转, 安全边界=(0.0, 1.0),
               描述="是否自动将收益复投（布尔）"),
        基因型(名称="保险池抽成", 最小值=0.0, 最大值=0.1, 默认值=0.01,
               变异=变异模式.高斯, 变异幅度=0.2, 安全边界=(0.001, 0.05),
               描述="每笔交易抽入保险池的比例"),
    ]

    def __init__(self, 基因型列表: Optional[List[基因型]] = None,
                 合约ID: str = "", 合约名称: str = ""):
        """初始化合约基因组

        参数:
            基因型列表: 自定义基因型，为空则使用默认模板
            合约ID: 关联的合约ID
            合约名称: 合约名称
        """
        self.合约ID = 合约ID
        self.合约名称 = 合约名称
        模板 = 基因型列表 or self.默认基因型模板
        self.基因座字典: Dict[str, 基因座] = {}
        for gt in 模板:
            self.基因座字典[gt.名称] = 基因座(基因型定义=gt)

        # 版本管理
        self.版本号: int = 1
        self.版本历史: List[dict] = [{
            "版本": 1,
            "时间": time.time(),
            "基因快照": {名称: locus.当前值 for 名称, locus in self.基因座字典.items()},
            "来源": "初始",
        }]

        # 适应度缓存
        self._适应度: float = 0.0
        self._评估时间: float = 0.0

    @property
    def 适应度(self) -> float:
        return self._适应度

    @适应度.setter
    def 适应度(self, 值: float):
        self._适应度 = 值
        self._评估时间 = time.time()

    def 获取参数(self, 名称: str) -> Optional[float]:
        """获取指定参数的当前值"""
        locus = self.基因座字典.get(名称)
        return locus.当前值 if locus else None

    def 设置参数(self, 名称: str, 值: float) -> bool:
        """手动设置参数值（需在合法范围内）"""
        locus = self.基因座字典.get(名称)
        if not locus:
            return False
        locus.当前值 = locus.基因型定义.钳位(值)
        return True

    def 基因表达(self) -> Dict[str, float]:
        """基因组→合约参数的映射（基因表达）
        返回所有参数的当前值字典
        """
        return {名称: locus.当前值 for 名称, locus in self.基因座字典.items()}

    def 变异(self, 变异率: float = 0.1, 随机源: Optional[bytes] = None) -> '合约基因组':
        """对基因组执行变异

        参数:
            变异率: 每个基因座的变异概率
            随机源: 可选随机源，用于确定性测试
        返回:
            变异后的新基因组（不修改当前基因组）
        """
        # 深拷贝创建新基因组
        新基因 = copy.deepcopy(self)
        新基因.版本号 = self.版本号 + 1

        # 对每个基因座执行变异
        for 名称, locus in 新基因.基因座字典.items():
            # 每个基因座使用不同的随机源
            座随机源 = (随机源 + 名称.encode()) if 随机源 else None
            locus.变异(变异率=变异率, 随机源=座随机源)

        # 记录版本
        新基因.版本历史 = list(self.版本历史)  # 保留历史引用
        新基因.版本历史.append({
            "版本": 新基因.版本号,
            "时间": time.time(),
            "基因快照": 新基因.基因表达(),
            "来源": "变异",
            "父版本": self.版本号,
            "变异率": 变异率,
        })

        return 新基因

    @staticmethod
    def 交叉(基因A: '合约基因组', 基因B: '合约基因组',
             交叉率: float = 0.5, 随机源: Optional[bytes] = None) -> '合约基因组':
        """两个优秀合约的基因组交叉组合

        参数:
            基因A: 父本A
            基因B: 父本B
            交叉率: 每个基因座从B继承的概率
            随机源: 可选随机源
        返回:
            交叉后的新基因组
        """
        # 以A为基底
        子代 = copy.deepcopy(基因A)
        子代.版本号 = max(基因A.版本号, 基因B.版本号) + 1
        子代.合约ID = ""  # 子代需要新合约ID
        子代.合约名称 = f"{基因A.合约名称}×{基因B.合约名称}"

        # 逐基因座交叉
        for 名称 in 子代.基因座字典:
            if 名称 not in 基因B.基因座字典:
                continue
            if 随机源:
                决定 = int(hashlib.sha256(随机源 + 名称.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
            else:
                决定 = int.from_bytes(os.urandom(4), 'big') / 0xFFFFFFFF

            if 决定 < 交叉率:
                # 从B继承该基因座
                子代.基因座字典[名称].当前值 = 基因B.基因座字典[名称].当前值

        # 记录版本
        子代.版本历史 = list(基因A.版本历史)
        子代.版本历史.append({
            "版本": 子代.版本号,
            "时间": time.time(),
            "基因快照": 子代.基因表达(),
            "来源": "交叉",
            "父本A版本": 基因A.版本号,
            "父本B版本": 基因B.版本号,
            "交叉率": 交叉率,
        })

        return 子代

    def 安全检查(self) -> Dict[str, bool]:
        """检查所有基因座是否在安全边界内

        返回:
            字典：参数名→是否安全
        """
        结果 = {}
        for 名称, locus in self.基因座字典.items():
            结果[名称] = locus.基因型定义.是否在安全边界内(locus.当前值)
        return 结果

    def 获取不安全参数(self) -> List[str]:
        """获取不在安全边界内的参数名列表"""
        检查结果 = self.安全检查()
        return [名称 for 名称, 安全 in 检查结果.items() if not 安全]

    def 基因组哈希(self) -> str:
        """计算基因组哈希（用于唯一标识和验证）"""
        表达 = self.基因表达()
        数据 = "|".join(f"{k}={v:.10f}" for k, v in sorted(表达.items()))
        return hashlib.sha256(数据.encode()).hexdigest()[:32]

    def 摘要(self) -> dict:
        """获取基因组摘要"""
        return {
            "合约ID": self.合约ID,
            "合约名称": self.合约名称,
            "版本": self.版本号,
            "基因数": len(self.基因座字典),
            "适应度": f"{self._适应度:.4f}",
            "基因哈希": self.基因组哈希(),
            "参数": self.基因表达(),
            "安全状态": self.安全检查(),
        }
