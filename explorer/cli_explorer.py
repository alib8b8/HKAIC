"""
Hongkun AI Chain — AI语义浏览器 (cli_explorer.py)
===================================================
不是传统的区块/交易浏览器，而是AI语义搜索引擎。
用户用自然语言描述想找的内容，AI理解意图并返回结果。

示例查询:
  "最近有大额转账吗"
  "地址abc的所有跨链交易"
  "质押收益最高的节点"
  "过去1小时的网络健康度"
"""

import hashlib
import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class 查询类型(Enum):
    余额查询 = "balance"
    交易搜索 = "tx_search"
    区块搜索 = "block_search"
    节点排名 = "node_rank"
    网络状态 = "network"
    跨链追踪 = "cross_chain"
    安全审计 = "security"
    经济分析 = "economy"
    模式发现 = "pattern"


@dataclass
class 链上实体:
    """链上实体(地址/合约/节点)"""
    标识: str
    类型: str  # address/contract/node
    标签: List[str] = field(default_factory=list)
    交互数: int = 0
    总量: float = 0.0
    首次出现: float = 0.0
    最近活跃: float = 0.0
    涌现分数: float = 0.0
    信誉评分: float = 50.0

    def 风险等级(self) -> str:
        if self.信誉评分 < 20:
            return "🔴 高风险"
        elif self.信誉评分 < 50:
            return "🟡 中风险"
        return "🟢 低风险"


@dataclass
class 搜索结果:
    """语义搜索结果"""
    查询: str
    类型: 查询类型
    命中: int = 0
    实体: List[链上实体] = field(default_factory=list)
    摘要: str = ""
    AI洞察: List[str] = field(default_factory=list)
    耗时_ms: float = 0.0


class 语义索引:
    """链上语义索引——按主题/标签/关系组织"""

    def __init__(self):
        self._实体: Dict[str, 链上实体] = {}
        self._标签索引: Dict[str, List[str]] = {}     # 标签→实体ID列表
        self._类型索引: Dict[str, List[str]] = {}      # 类型→实体ID列表
        self._关系图: Dict[str, Dict[str, str]] = {}    # 实体ID→{相关实体:关系类型}

    def 添加实体(self, 实体: 链上实体):
        self._实体[实体.标识] = 实体
        for 标签 in 实体.标签:
            self._标签索引.setdefault(标签, []).append(实体.标识)
        self._类型索引.setdefault(实体.类型, []).append(实体.标识)

    def 添加关系(self, 实体A: str, 实体B: str, 关系: str):
        self._关系图.setdefault(实体A, {})[实体B] = 关系
        self._关系图.setdefault(实体B, {})[实体A] = 关系

    def 按标签搜索(self, 标签: str) -> List[链上实体]:
        ids = self._标签索引.get(标签, [])
        return [self._实体[i] for i in ids if i in self._实体]

    def 按类型搜索(self, 类型: str) -> List[链上实体]:
        ids = self._类型索引.get(类型, [])
        return [self._实体[i] for i in ids if i in self._实体]

    def 相关实体(self, 实体ID: str, 深度: int = 1) -> List[Tuple[链上实体, str]]:
        """获取相关实体(关系追踪)"""
        结果 = []
        已访问 = {实体ID}
        当前层 = [实体ID]
        for _ in range(深度):
            下一层 = []
            for eid in 当前层:
                for 相关, 关系 in self._关系图.get(eid, {}).items():
                    if 相关 not in 已访问 and 相关 in self._实体:
                        结果.append((self._实体[相关], 关系))
                        已访问.add(相关)
                        下一层.append(相关)
            当前层 = 下一层
        return 结果

    def 统计(self) -> dict:
        return {
            "实体数": len(self._实体),
            "标签数": len(self._标签索引),
            "关系边": sum(len(v) for v in self._关系图.values()) // 2,
        }


class 自然语言查询引擎:
    """自然语言→结构化查询"""

    _意图映射 = {
        r"余额|多少币|有多少|balance": 查询类型.余额查询,
        r"交易|转账|tx|发送": 查询类型.交易搜索,
        r"区块|block|高度": 查询类型.区块搜索,
        r"节点|验证者|出块|排名": 查询类型.节点排名,
        r"网络|状态|健康|TPS": 查询类型.网络状态,
        r"跨链|bridge|ETB|涌信": 查询类型.跨链追踪,
        r"安全|风险|攻击|异常": 查询类型.安全审计,
        r"经济|代币|质押|收益": 查询类型.经济分析,
        r"模式|规律|趋势|发现": 查询类型.模式发现,
    }

    def 解析(self, 文本: str) -> dict:
        """解析自然语言查询"""
        import re
        结果 = {
            "原文": 文本,
            "查询类型": 查询类型.交易搜索,
            "地址": "",
            "时间范围": 0,
            "数量限制": 10,
            "排序": "时间",
            "过滤条件": [],
        }

        # 识别意图
        for 模式, 类型 in self._意图映射.items():
            if re.search(模式, 文本):
                结果["查询类型"] = 类型
                break

        # 提取地址
        addr = re.search(r'(0x[a-fA-F0-9]{8,}|HKAIC_[a-zA-Z0-9]{8,})', 文本)
        if addr:
            结果["地址"] = addr.group(1)

        # 时间范围
        天 = re.search(r'(\d+)天', 文本)
        if 天:
            结果["时间范围"] = int(天.group(1))
        小时 = re.search(r'(\d+)小时', 文本)
        if 小时:
            结果["时间范围"] = int(小时.group(1)) / 24

        # 数量
        num = re.search(r'最近(\d+)', 文本)
        if num:
            结果["数量限制"] = int(num.group(1))

        # 排序
        if re.search(r'最多|最大|最高|top', 文本, re.IGNORECASE):
            结果["排序"] = "金额降序"
        elif re.search(r'最少|最小|最低', 文本):
            结果["排序"] = "金额升序"

        return 结果


class AI语义浏览器:
    """
    HKC AI语义浏览器
    
    传统浏览器: 区块号→区块→交易列表
    AI浏览器: 自然语言→语义理解→智能搜索→AI洞察
    
    特性:
      - 自然语言查询
      - 语义索引(标签/关系/主题)
      - 关系图谱追踪
      - AI洞察生成
      - 风险评估
    """

    def __init__(self):
        self._索引 = 语义索引()
        self._查询引擎 = 自然语言查询引擎()
        self._查询历史: List[dict] = []
        self._热门查询: Dict[str, int] = {}

    @property
    def 索引(self): return self._索引

    def 添加实体(self, 实体: 链上实体):
        """添加链上实体到索引"""
        self._索引.添加实体(实体)

    def 添加关系(self, 实体A: str, 实体B: str, 关系: str):
        """添加实体间关系"""
        self._索引.添加关系(实体A, 实体B, 关系)

    def 语义搜索(self, 查询文本: str) -> 搜索结果:
        """AI语义搜索"""
        开始 = time.time()
        解析 = self._查询引擎.解析(查询文本)

        # 记录查询
        self._查询历史.append(解析)
        关键词 = 解析["查询类型"].value
        self._热门查询[关键词] = self._热门查询.get(关键词, 0) + 1

        # 执行搜索
        命中实体 = []
        类型 = 解析["查询类型"]

        if 类型 == 查询类型.余额查询 and 解析["地址"]:
            实体 = self._索引._实体.get(解析["地址"])
            if 实体:
                命中实体.append(实体)
        elif 类型 == 查询类型.节点排名:
            命中实体 = sorted(
                self._索引.按类型搜索("node"),
                key=lambda e: e.涌现分数, reverse=True
            )[:解析["数量限制"]]
        elif 类型 == 查询类型.安全审计:
            命中实体 = [e for e in self._索引._实体.values() if e.信誉评分 < 30]
        else:
            # 通用搜索:按标签匹配
            for 标签 in [类型.value, 查询文本[:4]]:
                命中实体.extend(self._索引.按标签搜索(标签))
            # 去重
            已见 = set()
            去重 = []
            for e in 命中实体:
                if e.标识 not in 已见:
                    去重.append(e)
                    已见.add(e.标识)
            命中实体 = 去重[:解析["数量限制"]]

        # 生成AI洞察
        洞察 = self._生成洞察(命中实体, 类型)

        耗时 = (time.time() - 开始) * 1000

        return 搜索结果(
            查询=查询文本,
            类型=类型,
            命中=len(命中实体),
            实体=命中实体,
            摘要=self._生成摘要(命中实体, 类型),
            AI洞察=洞察,
            耗时_ms=耗时,
        )

    def 关系追踪(self, 实体ID: str, 深度: int = 2) -> dict:
        """追踪实体关系网络"""
        相关 = self._索引.相关实体(实体ID, 深度)
        实体 = self._索引._实体.get(实体ID)
        if not 实体:
            return {"错误": "实体不存在"}

        结果 = {
            "中心实体": 实体.标识,
            "关系深度": 深度,
            "相关实体数": len(相关),
            "关系网络": [],
        }
        for 相关实体, 关系 in 相关:
            结果["关系网络"].append({
                "实体": 相关实体.标识,
                "关系": 关系,
                "信誉": 相关实体.信誉评分,
                "风险": 相关实体.风险等级(),
            })
        return 结果

    def _生成洞察(self, 实体: List[链上实体], 类型: 查询类型) -> List[str]:
        """AI生成搜索洞察"""
        洞察 = []
        if not 实体:
            洞察.append("未找到匹配结果,试试不同的关键词")
            return 洞察

        # 风险洞察
        高风险 = [e for e in 实体 if e.信誉评分 < 30]
        if 高风险:
            洞察.append(f"⚠️ 发现{len(高风险)}个高风险实体")

        # 活跃度洞察
        活跃 = [e for e in 实体 if time.time() - e.最近活跃 < 3600]
        if 活跃:
            洞察.append(f"🔥 {len(活跃)}个实体最近1小时活跃")

        # 涌现分数洞察
        if 类型 == 查询类型.节点排名:
            top = 实体[:3] if len(实体) >= 3 else 实体
            avg_e = sum(e.涌现分数 for e in top) / max(len(top), 1)
            洞察.append(f"🏆 Top节点平均涌现分数: {avg_e:.4f}")

        # 经济洞察
        if 类型 == 查询类型.经济分析:
            总量 = sum(e.总量 for e in 实体)
            洞察.append(f"💰 涉及总量: {总量:.2f} HKAIC")

        return 洞察

    def _生成摘要(self, 实体: List[链上实体], 类型: 查询类型) -> str:
        """生成搜索结果摘要"""
        if not 实体:
            return "无匹配结果"
        类型名 = {
            查询类型.余额查询: "余额",
            查询类型.交易搜索: "交易",
            查询类型.节点排名: "节点",
            查询类型.安全审计: "安全",
        }.get(类型, "实体")
        return f"找到{len(实体)}个{类型名}相关结果"

    def 热门搜索(self, n: int = 5) -> List[Tuple[str, int]]:
        """热门搜索"""
        排序 = sorted(self._热门查询.items(), key=lambda x: -x[1])
        return 排序[:n]

    def 状态(self) -> dict:
        return {
            "索引": self._索引.统计(),
            "查询历史": len(self._查询历史),
            "热门搜索": self.热门搜索(3),
        }


if __name__ == "__main__":
    print("  HKC AI语义浏览器 Demo")
    explorer = AI语义浏览器()
    # 添加示例数据
    for i in range(10):
        e = 链上实体(
            标识=f"addr_{i}",
            类型=random.choice(["address", "node"]),
            标签=[random.choice(["大额", "质押", "跨链", "活跃"])],
            交互数=random.randint(10, 1000),
            总量=random.uniform(100, 50000),
            涌现分数=random.uniform(0.1, 5.0),
            信誉评分=random.uniform(10, 95),
        )
        explorer.添加实体(e)
    # 搜索
    for q in ["质押收益最高的节点", "最近有大额转账吗", "安全风险"]:
        r = explorer.语义搜索(q)
        print(f"  🔍 {q}")
        print(f"    命中: {r.命中}, 摘要: {r.摘要}")
        for d in r.AI洞察:
            print(f"    {d}")
    print(f"  {explorer.状态()}")
