"""
Hongkun AI Chain — AI配置大脑 (adaptive_config.py)
====================================================
AI驱动的自适应配置系统。

核心能力:
  1. AI创世配置生成器 — 根据目标场景自动生成最优创世配置
  2. 实时自适应调整 — 根据网络状态动态调整参数
  3. 冲突检测 — 检测配置间矛盾并自动解决
  4. 变更预测 — 预测配置变更影响
  5. 环境检测 — 根据运行环境推荐配置
"""

import hashlib
import time
import math
import copy
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class 配置场景(Enum):
    开发 = "dev"
    测试网 = "testnet"
    主网 = "mainnet"
    高吞吐 = "high_tps"
    高安全 = "high_security"
    低资源 = "low_resource"


class 调整策略(Enum):
    保守 = "conservative"    # 小幅调整
    适度 = "moderate"        # 中幅调整
    激进 = "aggressive"      # 大幅调整


@dataclass
class 配置变更:
    """配置变更记录"""
    变更ID: str
    键: str
    旧值: Any
    新值: Any
    原因: str = ""
    时间戳: float = 0.0
    影响: float = 0.0  # 预测影响评分0-1
    def __post_init__(self):
        if self.时间戳 == 0:
            self.时间戳 = time.time()


@dataclass
class 冲突记录:
    """配置冲突"""
    键A: str
    键B: str
    值A: Any
    值B: Any
    冲突原因: str
    建议值: Any = None


class AI创世配置生成器:
    """
    根据目标场景自动生成最优创世配置
    
    场景→参数映射:
      高吞吐: 短epoch,大区块,高并行
      高安全: 大验证组,长冷却,高质押
      低资源: 小连接数,少并行,低内存
    """

    # 场景模板
    _模板 = {
        配置场景.开发: {
            "共识.epoch时长_秒": 10,
            "共识.最小验证者": 1,
            "共识.目标验证者": 3,
            "P2P.最大连接": 10,
            "RPC.限流_每分钟": 1000,
            "同步.并行下载": 2,
            "跨链桥.最小验证组": 1,
            "ATH.信任评分阈值": 10,
        },
        配置场景.测试网: {
            "共识.epoch时长_秒": 30,
            "共识.最小验证者": 2,
            "共识.目标验证者": 5,
            "P2P.最大连接": 20,
            "RPC.限流_每分钟": 500,
            "同步.并行下载": 4,
            "跨链桥.最小验证组": 2,
            "ATH.信任评分阈值": 20,
        },
        配置场景.主网: {
            "共识.epoch时长_秒": 60,
            "共识.最小验证者": 3,
            "共识.目标验证者": 21,
            "P2P.最大连接": 50,
            "RPC.限流_每分钟": 100,
            "同步.并行下载": 8,
            "跨链桥.最小验证组": 3,
            "ATH.信任评分阈值": 30,
        },
        配置场景.高吞吐: {
            "共识.epoch时长_秒": 15,
            "共识.最小验证者": 3,
            "共识.目标验证者": 11,
            "P2P.最大连接": 100,
            "RPC.限流_每分钟": 500,
            "同步.并行下载": 16,
            "跨链桥.最小验证组": 3,
            "ATH.信任评分阈值": 30,
        },
        配置场景.高安全: {
            "共识.epoch时长_秒": 120,
            "共识.最小验证者": 7,
            "共识.目标验证者": 51,
            "P2P.最大连接": 30,
            "RPC.限流_每分钟": 50,
            "同步.并行下载": 4,
            "跨链桥.最小验证组": 7,
            "跨链桥.冷却epochs": 50,
            "ATH.信任评分阈值": 50,
        },
        配置场景.低资源: {
            "共识.epoch时长_秒": 120,
            "共识.最小验证者": 1,
            "共识.目标验证者": 3,
            "P2P.最大连接": 10,
            "RPC.限流_每分钟": 30,
            "同步.并行下载": 2,
            "跨链桥.最小验证组": 1,
            "ATH.信任评分阈值": 20,
        },
    }

    def 生成(self, 场景: 配置场景, 自定义: dict = None) -> dict:
        """根据场景生成配置"""
        基础 = copy.deepcopy(self._模板.get(场景, self._模板[配置场景.主网]))
        if 自定义:
            基础.update(自定义)
        # AI微调: 根据自定义参数调整关联参数
        if "共识.epoch时长_秒" in 基础:
            时长 = 基础["共识.epoch时长_秒"]
            基础.setdefault("跨链桥.超时秒数", 时长 * 30)
        return 基础

    def 推荐场景(self, 环境信息: dict) -> 配置场景:
        """根据环境推荐场景"""
        cpu = 环境信息.get("CPU核心", 1)
        mem = 环境信息.get("内存_GB", 2)
        if cpu >= 8 and mem >= 16:
            return 配置场景.主网
        elif cpu >= 4 and mem >= 8:
            return 配置场景.测试网
        elif cpu >= 2:
            return 配置场景.低资源
        return 配置场景.开发


class 实时自适应器:
    """
    根据网络运行指标实时调整配置参数
    
    调整逻辑:
      - TPS低 → 缩短epoch时长
      - 延迟高 → 减少验证者数量
      - 分叉多 → 提高质押门槛
      - 协同质量低 → 调整α/β
    """

    def __init__(self, 策略: 调整策略 = 调整策略.适度):
        self._策略 = 策略
        self._调整历史: List[配置变更] = []
        self._指标: Dict[str, float] = {}

        # 策略对应的调整幅度
        self._幅度 = {
            调整策略.保守: 0.05,
            调整策略.适度: 0.15,
            调整策略.激进: 0.30,
        }

    def 更新指标(self, 指标: dict):
        """更新网络运行指标"""
        self._指标.update(指标)

    def 自适应调整(self) -> List[配置变更]:
        """根据指标调整配置"""
        变更列表 = []
        幅度 = self._幅度[self._策略]

        # TPS调整
        tps = self._指标.get("TPS", 100)
        目标tps = self._指标.get("目标TPS", 200)
        if tps < 目标tps * 0.5:
            变更 = self._创建变更(
                "共识.epoch时长_秒",
                self._指标.get("epoch时长", 60),
                max(15, self._指标.get("epoch时长", 60) * (1 - 幅度)),
                f"TPS({tps:.0f})远低于目标({目标tps:.0f}),缩短epoch"
            )
            变更列表.append(变更)

        # 延迟调整
        延迟 = self._指标.get("平均延迟_ms", 100)
        if 延迟 > 500:
            变更 = self._创建变更(
                "P2P.最大连接",
                self._指标.get("最大连接", 50),
                max(10, self._指标.get("最大连接", 50) * (1 - 幅度)),
                f"延迟({延迟:.0f}ms)过高,减少连接"
            )
            变更列表.append(变更)

        # 分叉调整
        分叉率 = self._指标.get("分叉率", 0.01)
        if 分叉率 > 0.05:
            变更 = self._创建变更(
                "共识.最小质押",
                self._指标.get("最小质押", 1000),
                self._指标.get("最小质押", 1000) * (1 + 幅度),
                f"分叉率({分叉率:.1%})过高,提高质押门槛"
            )
            变更列表.append(变更)

        # 协同质量调整
        协同质量 = self._指标.get("协同质量", 0.5)
        if 协同质量 > 0.5:
            变更 = self._创建变更(
                "共识.beta",
                self._指标.get("beta", 1.2),
                min(2.0, self._指标.get("beta", 1.2) * (1 + 幅度 * 0.3)),
                f"协同质量({协同质量:.2f})高,放大涌现激励"
            )
            变更列表.append(变更)

        self._调整历史.extend(变更列表)
        return 变更列表

    def _创建变更(self, 键: str, 旧值: Any, 新值: Any, 原因: str) -> 配置变更:
        # H-19: os.urandom替代time.time_ns()
        import os as _os
        变更ID = hashlib.sha256(f"{键}:{_os.urandom(16).hex()}".encode()).hexdigest()[:12]
        return 配置变更(
            变更ID=变更ID, 键=键, 旧值=旧值, 新值=新值,
            原因=原因, 影响=min(abs(新值 - 旧值) / max(abs(旧值), 1), 1.0)
        )

    def 历史摘要(self) -> str:
        """调整历史摘要"""
        if not self._调整历史:
            return "  无调整记录"
        线 = [f"  自适应调整历史({len(self._调整历史)}条):"]
        for c in self._调整历史[-5:]:
            线.append(f"    {c.键}: {c.旧值} → {c.新值} ({c.原因})")
        return "\n".join(线)


class 冲突检测器:
    """检测配置间矛盾并自动解决"""

    # 冲突规则
    _规则 = [
        {
            "条件": lambda c: c.get("共识.最小验证者", 3) > c.get("共识.目标验证者", 21),
            "冲突": "最小验证者不能大于目标验证者",
            "建议": lambda c: {"共识.目标验证者": c.get("共识.最小验证者", 3) * 3},
        },
        {
            "条件": lambda c: c.get("P2P.默认端口", 8845) == c.get("RPC.REST端口", 8843),
            "冲突": "P2P端口与RPC端口冲突",
            "建议": lambda c: {"RPC.REST端口": 8843},
        },
        {
            "条件": lambda c: c.get("共识.alpha", 0.6) + c.get("共识.beta", 1.2) > 3.0,
            "冲突": "α+β过大可能导致涌现分数爆炸",
            "建议": lambda c: {"共识.beta": 3.0 - c.get("共识.alpha", 0.6)},
        },
        {
            "条件": lambda c: c.get("跨链桥.保险费率", 0.001) > 0.05,
            "冲突": "保险费率过高影响跨链意愿",
            "建议": lambda c: {"跨链桥.保险费率": 0.005},
        },
        {
            "条件": lambda c: c.get("ATH.信任评分阈值", 30) > 80,
            "冲突": "ATH信任阈值过高,新参与者难以加入",
            "建议": lambda c: {"ATH.信任评分阈值": 50},
        },
    ]

    def 检测(self, 配置: dict) -> List[冲突记录]:
        """检测配置冲突"""
        扁平 = self._扁平化(配置)
        冲突列表 = []
        for 规则 in self._规则:
            try:
                if 规则["条件"](扁平):
                    建议 = 规则["建议"](扁平)
                    for 键, 值 in 建议.items():
                        冲突列表.append(冲突记录(
                            键A=list(建议.keys())[0],
                            键B="",
                            值A=扁平.get(键),
                            值B=值,
                            冲突原因=规则["冲突"],
                            建议值=值
                        ))
            except (KeyError, TypeError):
                pass
        return 冲突列表

    def 自动解决(self, 配置: dict) -> Tuple[dict, List[冲突记录]]:
        """自动解决冲突"""
        冲突 = self.检测(配置)
        解决后 = copy.deepcopy(配置)
        for c in 冲突:
            if c.建议值 is not None:
                self._设置嵌套(解决后, c.键A, c.建议值)
        return 解决后, 冲突

    def _扁平化(self, d: dict, 前缀: str = "") -> dict:
        结果 = {}
        for k, v in d.items():
            完整键 = f"{前缀}.{k}" if 前缀 else k
            if isinstance(v, dict):
                结果.update(self._扁平化(v, 完整键))
            else:
                结果[完整键] = v
        return 结果

    def _设置嵌套(self, d: dict, 键: str, 值: Any):
        部分 = 键.split(".")
        当前 = d
        for p in 部分[:-1]:
            当前 = 当前.setdefault(p, {})
        当前[部分[-1]] = 值


class 变更预测器:
    """预测配置变更的影响"""

    _影响模型 = {
        "共识.epoch时长_秒": {"影响TPS": 0.8, "影响延迟": 0.6, "影响安全": 0.3},
        "共识.alpha": {"影响安全": 0.9, "影响涌现": 0.8, "影响出块": 0.4},
        "共识.beta": {"影响涌现": 0.9, "影响协同": 0.8, "影响出块": 0.5},
        "P2P.最大连接": {"影响网络": 0.7, "影响延迟": 0.5, "影响内存": 0.6},
        "共识.最小验证者": {"影响安全": 0.9, "影响去中心化": 0.7},
    }

    def 预测(self, 键: str, 旧值: Any, 新值: Any) -> dict:
        """预测变更影响"""
        模型 = self._影响模型.get(键, {"影响未知": 0.5})
        变化率 = abs(新值 - 旧值) / max(abs(旧值), 1e-6) if isinstance(新值, (int, float)) else 0.5

        预测结果 = {}
        for 维度, 敏感度 in 模型.items():
            影响 = min(变化率 * 敏感度, 1.0)
            预测结果[维度] = round(影响, 4)

        总体风险 = sum(预测结果.values()) / max(len(预测结果), 1)
        预测结果["总体风险"] = round(总体风险, 4)

        if 总体风险 > 0.5:
            预测结果["建议"] = "⚠️ 高风险变更,建议先在测试网验证"
        elif 总体风险 > 0.2:
            预测结果["建议"] = "💡 中等风险,建议逐步调整"
        else:
            预测结果["建议"] = "✅ 低风险,可直接应用"

        return 预测结果


class AI配置大脑:
    """
    HKC AI配置大脑
    
    整合: 创世生成器 + 实时自适应 + 冲突检测 + 变更预测 + 环境检测
    
    使用:
      brain = AI配置大脑()
      brain.生成创世配置(配置场景.主网)
      brain.更新运行指标({"TPS": 50, "延迟": 300})
      brain.自适应调整()
      brain.检测冲突()
    """

    def __init__(self, 策略: 调整策略 = 调整策略.适度):
        self._生成器 = AI创世配置生成器()
        self._自适应 = 实时自适应器(策略)
        self._冲突检测 = 冲突检测器()
        self._预测器 = 变更预测器()
        self._配置: dict = {}
        self._变更日志: List[配置变更] = []

    @property
    def 创世生成器(self): return self._生成器
    @property
    def 自适应器(self): return self._自适应
    @property
    def 冲突检测(self): return self._冲突检测
    @property
    def 预测器(self): return self._预测器

    def 生成创世配置(self, 场景: 配置场景, 自定义: dict = None) -> dict:
        """生成创世配置"""
        self._配置 = self._生成器.生成(场景, 自定义)
        return self._配置

    def 更新运行指标(self, 指标: dict):
        """更新网络运行指标"""
        self._自适应.更新指标(指标)

    def 自适应调整(self) -> List[配置变更]:
        """实时自适应调整"""
        变更 = self._自适应.自适应调整()
        for c in 变更:
            self._变更日志.append(c)
            # 应用变更
            部分 = c.键.split(".")
            当前 = self._配置
            for p in 部分[:-1]:
                当前 = 当前.setdefault(p, {})
            当前[部分[-1]] = c.新值
        return 变更

    def 检测冲突(self) -> List[冲突记录]:
        """检测配置冲突"""
        return self._冲突检测.检测(self._配置)

    def 自动解决冲突(self) -> Tuple[dict, List[冲突记录]]:
        """自动解决冲突"""
        self._配置, 冲突 = self._冲突检测.自动解决(self._配置)
        return self._配置, 冲突

    def 预测变更(self, 键: str, 新值: Any) -> dict:
        """预测配置变更影响"""
        旧值 = self._获取值(键)
        return self._预测器.预测(键, 旧值, 新值)

    def _获取值(self, 键: str) -> Any:
        当前 = self._配置
        for p in 键.split("."):
            if isinstance(当前, dict) and p in 当前:
                当前 = 当前[p]
            else:
                return 0
        return 当前

    def 推荐场景(self, 环境: dict) -> 配置场景:
        """推荐场景"""
        return self._生成器.推荐场景(环境)

    def 状态(self) -> dict:
        return {
            "配置": len(str(self._配置)),
            "变更日志": len(self._变更日志),
            "冲突": len(self.检测冲突()),
            "自适应历史": len(self._自适应._调整历史),
        }


if __name__ == "__main__":
    print("  HKC AI配置大脑 Demo")
    brain = AI配置大脑()
    配置 = brain.生成创世配置(配置场景.测试网)
    print(f"  创世配置: {配置}")
    brain.更新运行指标({"TPS": 50, "目标TPS": 200, "平均延迟_ms": 600,
                          "epoch时长": 30, "最大连接": 20})
    变更 = brain.自适应调整()
    for c in 变更:
        print(f"  变更: {c.键} {c.旧值}→{c.新值} ({c.原因})")
    冲突 = brain.检测冲突()
    print(f"  冲突: {len(冲突)}")
    预测 = brain.预测变更("共识.alpha", 0.9)
    print(f"  预测: {预测}")
    print(f"  状态: {brain.状态()}")
