"""
Hongkun AI Chain — 智能CLI (cli.py)
=====================================
hkc命令行工具，支持自然语言模式、AI诊断、风险提示、配置子命令。

用法:
    hkc start              启动节点
    hkc stop               停止节点
    hkc status             查看状态
    hkc balance <地址>      查询余额
    hkc send <从> <到> <金额>  转账
    hkc stake <金额>       质押
    hkc bridge send <链> <金额>  跨链
    hkc query "<自然语言>"   AI语义查询
    hkc diagnose            AI自动诊断
    hkc config show         显示配置
    hkc config set <键> <值> 设置配置
    hkc config ai           AI自动优化配置
    hkc explorer <关键词>    链上语义搜索
    hkc monitor             实时监控
    hkc testnet start       启动测试网
    hkc testnet attack      运行攻击测试
"""

import sys
import os
import hashlib
import time
import json
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class CLI模式(Enum):
    标准 = "standard"
    自然语言 = "nl"
    交互式 = "interactive"


class 严重等级(Enum):
    信息 = "info"
    警告 = "warn"
    危险 = "danger"
    致命 = "fatal"


@dataclass
class 诊断报告:
    """AI诊断报告"""
    节点状态: str = "未知"
    网络连通: bool = False
    同步进度: float = 0.0
    共识参与: bool = False
    问题列表: List[dict] = field(default_factory=list)
    建议列表: List[str] = field(default_factory=list)
    风险评分: float = 0.0  # 0-100, 越高越危险

    def 摘要(self) -> str:
        线 = [
            "=" * 50,
            "  HKC AI诊断报告",
            "=" * 50,
            f"  节点状态: {self.节点状态}",
            f"  网络连通: {'✅' if self.网络连通 else '❌'}",
            f"  同步进度: {self.同步进度:.1%}",
            f"  共识参与: {'✅' if self.共识参与 else '❌'}",
            f"  风险评分: {self.风险评分:.1f}/100",
        ]
        if self.问题列表:
            线.append("  ⚠️ 发现问题:")
            for p in self.问题列表:
                等级图标 = {"info": "ℹ️", "warn": "⚠️", "danger": "🔴", "fatal": "💀"}.get(
                    p.get("等级", "info"), "ℹ️"
                )
                线.append(f"    {等级图标} [{p.get('等级','')}] {p.get('描述','')}")
        if self.建议列表:
            线.append("  💡 建议:")
            for s in self.建议列表:
                线.append(f"    → {s}")
        线.append("=" * 50)
        return "\n".join(线)


class 风险评估器:
    """AI风险评估——交易前自动检测风险"""

    # 已知高风险地址模式
    _高风险模式 = [
        "mixer", "tornado", "darknet", "sanctioned"
    ]

    def 评估交易(self, 发送者: str, 接收者: str, 金额: float,
                  余额: float = 0) -> Tuple[float, List[str]]:
        """返回(风险评分0-100, 风险因素列表)"""
        风险 = 0.0
        因素 = []

        # 余额不足风险
        if 余额 > 0 and 金额 > 余额:
            风险 += 60
            因素.append("余额不足")
        elif 余额 > 0 and 金额 > 余额 * 0.8:
            风险 += 20
            因素.append("大额交易(超过余额80%)")

        # 大额交易
        if 金额 > 10000:
            风险 += 15
            因素.append("超大额交易(>10000 HKAIC)")
        elif 金额 > 1000:
            风险 += 5
            因素.append("大额交易(>1000 HKAIC)")

        # 接收者风险
        接收者低 = 接收者.lower()
        for 模式 in self._高风险模式:
            if 模式 in 接收者低:
                风险 += 40
                因素.append(f"接收者匹配高风险模式: {模式}")

        # 新地址风险
        if len(接收者) < 20:
            风险 += 10
            因素.append("接收者地址格式异常")

        return min(风险, 100), 因素

    def 评估跨链(self, 源链: str, 目标链: str, 金额: float) -> Tuple[float, List[str]]:
        """跨链风险评估"""
        风险 = 10.0  # 基础跨链风险
        因素 = ["跨链交易存在固有风险"]

        # 未知链风险
        已知链 = {"HKC", "EVM", "SVM", "BTC", "COSMOS"}
        if 源链 not in 已知链:
            风险 += 30
            因素.append(f"源链 '{源链}' 不在已知列表中")
        if 目标链 not in 已知链:
            风险 += 30
            因素.append(f"目标链 '{目标链}' 不在已知列表中")

        # 大额跨链
        if 金额 > 5000:
            风险 += 20
            因素.append("大额跨链(>5000 HKAIC)")

        return min(风险, 100), 因素


class AI诊断器:
    """AI自动诊断节点问题"""

    def 诊断(self, 节点信息: dict = None) -> 诊断报告:
        """全面诊断"""
        报告 = 诊断报告()
        信息 = 节点信息 or {}

        # 节点状态
        报告.节点状态 = 信息.get("状态", "运行中")
        报告.网络连通 = 信息.get("网络连通", True)
        报告.同步进度 = 信息.get("同步进度", 1.0)
        报告.共识参与 = 信息.get("共识参与", True)

        # 检查问题
        if not 报告.网络连通:
            报告.问题列表.append({"等级": "danger", "描述": "网络连接断开"})
            报告.建议列表.append("检查网络连接和防火墙设置")

        if 报告.同步进度 < 0.9:
            报告.问题列表.append({
                "等级": "warn" if 报告.同步进度 > 0.5 else "danger",
                "描述": f"同步进度低: {报告.同步进度:.1%}"
            })
            报告.建议列表.append("尝试重新同步: hkc sync --fast")

        if not 报告.共识参与:
            报告.问题列表.append({"等级": "warn", "描述": "未参与共识"})
            报告.建议列表.append("检查质押是否足够: hkc stake <金额>")

        # 检查磁盘空间(模拟)
        磁盘使用 = 信息.get("磁盘使用", 0.3)
        if 磁盘使用 > 0.9:
            报告.问题列表.append({"等级": "danger", "描述": f"磁盘空间不足: {磁盘使用:.0%}"})
            报告.建议列表.append("清理旧数据: hkc prune --before <日期>")
        elif 磁盘使用 > 0.7:
            报告.问题列表.append({"等级": "warn", "描述": f"磁盘空间偏低: {磁盘使用:.0%}"})

        # 检查内存
        内存使用 = 信息.get("内存使用", 0.4)
        if 内存使用 > 0.9:
            报告.问题列表.append({"等级": "danger", "描述": f"内存不足: {内存使用:.0%}"})
            报告.建议列表.append("减少缓存或增加内存")

        # 计算风险评分
        等级分数 = {"info": 5, "warn": 20, "danger": 40, "fatal": 60}
        报告.风险评分 = sum(等级分数.get(p.get("等级", "info"), 5) for p in 报告.问题列表)
        报告.风险评分 = min(报告.风险评分, 100)

        return 报告


class 配置管理器:
    """CLI配置子命令管理"""

    def __init__(self):
        self._配置: Dict[str, Any] = {
            "节点名称": "hkc-node-1",
            "RPC端口": 8843,
            "WS端口": 8844,
            "P2P端口": 8845,
            "种子节点": ["hkc://seed1.hongkun.ai:8845", "hkc://seed2.hongkun.ai:8845"],
            "日志级别": "INFO",
            "数据目录": "~/.hkc/data",
            "AI诊断": True,
            "自动同步": True,
            "最大连接": 50,
            "最小质押": 1000,
        }

    def 显示(self) -> str:
        线 = ["  HKC 配置:"]
        for k, v in self._配置.items():
            线.append(f"    {k} = {v}")
        return "\n".join(线)

    def 设置(self, 键: str, 值: Any) -> bool:
        if 键 not in self._配置:
            return False
        # 类型转换
        当前值 = self._配置[键]
        if isinstance(当前值, int):
            值 = int(值)
        elif isinstance(当前值, float):
            值 = float(值)
        elif isinstance(当前值, bool):
            值 = str(值).lower() in ("true", "1", "yes")
        self._配置[键] = 值
        return True

    def AI优化(self) -> List[str]:
        """AI根据当前配置自动优化"""
        建议 = []
        if self._配置["最大连接"] < 30:
            self._配置["最大连接"] = 30
            建议.append("最大连接数提升至30,改善网络连通性")
        if not self._配置["AI诊断"]:
            self._配置["AI诊断"] = True
            建议.append("启用AI诊断,自动检测问题")
        if self._配置["日志级别"] == "DEBUG":
            self._配置["日志级别"] = "INFO"
            建议.append("日志级别从DEBUG调整为INFO,减少磁盘占用")
        return 建议


class HKC_CLI:
    """
    Hongkun AI Chain 智能CLI
    
    特性:
      - 标准命令模式
      - 自然语言查询模式
      - AI诊断模式
      - 风险提示
      - 配置AI化
    """

    def __init__(self):
        self._模式 = CLI模式.标准
        self._诊断器 = AI诊断器()
        self._风险评估 = 风险评估器()
        self._配置 = 配置管理器()
        self._运行中 = False
        self._命令历史: List[dict] = []

    def 解析命令(self, 输入: str) -> dict:
        """解析CLI输入为结构化命令"""
        部分 = 输入.strip().split()
        if not 部分:
            return {"命令": "help", "参数": {}}

        命令 = 部分[0]
        参数 = {}

        # hkc query "自然语言"
        if 命令 == "query" and len(部分) > 1:
            参数["查询"] = " ".join(部分[1:]).strip('"').strip("'")
        # hkc send <从> <到> <金额>
        elif 命令 == "send" and len(部分) >= 4:
            参数["发送者"] = 部分[1]
            参数["接收者"] = 部分[2]
            try:
                参数["金额"] = float(部分[3])
            except ValueError:
                参数["金额"] = 0
        # hkc balance <地址>
        elif 命令 == "balance" and len(部分) > 1:
            参数["地址"] = 部分[1]
        # hkc stake <金额>
        elif 命令 == "stake" and len(部分) > 1:
            try:
                参数["金额"] = float(部分[1])
            except ValueError:
                参数["金额"] = 0
        # hkc bridge send <链> <金额>
        elif 命令 == "bridge" and len(部分) >= 4 and 部分[1] == "send":
            参数["目标链"] = 部分[2]
            try:
                参数["金额"] = float(部分[3])
            except ValueError:
                参数["金额"] = 0
        # hkc config set <键> <值>
        elif 命令 == "config":
            if len(部分) >= 2:
                子命令 = 部分[1]
                if 子命令 == "set" and len(部分) >= 4:
                    参数["键"] = 部分[2]
                    参数["值"] = 部分[3]
                elif 子命令 == "ai":
                    参数["AI优化"] = True
        # hkc explorer <关键词>
        elif 命令 == "explorer" and len(部分) > 1:
            参数["关键词"] = " ".join(部分[1:])
        # hkc testnet <子命令>
        elif 命令 == "testnet" and len(部分) > 1:
            参数["子命令"] = 部分[1]

        记录 = {"命令": 命令, "参数": 参数, "时间": time.time()}
        self._命令历史.append(记录)
        return 记录

    def 执行命令(self, 输入: str) -> str:
        """执行CLI命令并返回输出"""
        解析 = self.解析命令(输入)
        命令 = 解析["命令"]
        参数 = 解析["参数"]

        if 命令 == "help":
            return self._帮助信息()
        elif 命令 == "start":
            self._运行中 = True
            return "🟢 HKC节点已启动"
        elif 命令 == "stop":
            self._运行中 = False
            return "🔴 HKC节点已停止"
        elif 命令 == "status":
            状态 = "运行中" if self._运行中 else "已停止"
            return f"  节点状态: {状态}\n  链: Hongkun AI Chain (HKC)\n  版本: v4.0.0\n  共识: PoEI"
        elif 命令 == "balance":
            地址 = 参数.get("地址", "未知")
            return f"  地址: {地址}\n  余额: 1000.00000000 HKAIC\n  质押: 0 HKAIC"
        elif 命令 == "send":
            return self._执行转账(参数)
        elif 命令 == "stake":
            金额 = 参数.get("金额", 0)
            return f"  ✅ 质押成功: {金额} HKAIC\n  当前质押收益年化: 5.2%"
        elif 命令 == "bridge":
            return self._执行跨链(参数)
        elif 命令 == "query":
            return f"  🔍 AI语义查询: {参数.get('查询', '')}\n  解析结果: 操作=查询, 目标=全部"
        elif 命令 == "diagnose":
            报告 = self._诊断器.诊断()
            return 报告.摘要()
        elif 命令 == "config":
            return self._执行配置(参数)
        elif 命令 == "explorer":
            return f"  🔎 链上搜索: {参数.get('关键词', '')}\n  找到3条相关记录"
        elif 命令 == "monitor":
            return "  📊 HKC实时监控\n  区块高度: 12345 | TPS: 150 | 活跃验证者: 21"
        elif 命令 == "testnet":
            子 = 参数.get("子命令", "")
            if 子 == "start":
                return "  🧪 测试网已启动(5节点小世界拓扑)"
            elif 子 == "attack":
                return "  ⚔️ 进化沙盒启动: AI生成攻击→评估防御→进化攻击"
            return "  用法: hkc testnet <start|attack>"
        else:
            return f"  ❌ 未知命令: {命令}\n  输入 'help' 查看帮助"

    def _帮助信息(self) -> str:
        return """
  ╔══════════════════════════════════════════╗
  ║   Hongkun AI Chain (HKC) v4.0.0 CLI    ║
  ║   全球首条AI原生区块链                   ║
  ╚══════════════════════════════════════════╝

  基础命令:
    hkc start                 启动节点
    hkc stop                  停止节点
    hkc status                节点状态
    hkc balance <地址>         查询余额
    hkc send <从> <到> <金额>  转账
    hkc stake <金额>          质押

  跨链命令:
    hkc bridge send <链> <金额>  跨链转账

  AI命令:
    hkc query "<自然语言>"    AI语义查询
    hkc diagnose              AI自动诊断
    hkc explorer <关键词>     链上语义搜索
    hkc monitor               实时监控

  配置命令:
    hkc config show           显示配置
    hkc config set <键> <值>  设置配置
    hkc config ai             AI自动优化配置

  测试网:
    hkc testnet start         启动测试网
    hkc testnet attack        运行攻击测试
"""

    def _执行转账(self, 参数: dict) -> str:
        发送者 = 参数.get("发送者", "")
        接收者 = 参数.get("接收者", "")
        金额 = 参数.get("金额", 0)
        # 风险评估
        风险, 因素 = self._风险评估.评估交易(发送者, 接收者, 金额)
        输出 = [f"  📤 转账: {金额} HKAIC → {接收者}"]
        if 风险 > 30:
            输出.append(f"  ⚠️ 风险评分: {风险:.0f}/100")
            for f in 因素:
                输出.append(f"    - {f}")
            if 风险 > 60:
                输出.append("  🔴 高风险交易,请确认!")
                return "\n".join(输出)
        # H-22: os.urandom替代time.time_ns()
        import os as _os
        tx_hash = hashlib.sha256(f"{发送者}:{接收者}:{金额}:{_os.urandom(16).hex()}".encode()).hexdigest()[:16]
        输出.append(f"  ✅ 交易已提交: {tx_hash}")
        return "\n".join(输出)

    def _执行跨链(self, 参数: dict) -> str:
        目标链 = 参数.get("目标链", "未知")
        金额 = 参数.get("金额", 0)
        风险, 因素 = self._风险评估.评估跨链("HKC", 目标链, 金额)
        输出 = [f"  🌉 跨链: {金额} HKAIC → {目标链}"]
        if 风险 > 20:
            输出.append(f"  ⚠️ 跨链风险: {风险:.0f}/100")
            for f in 因素:
                输出.append(f"    - {f}")
        输出.append(f"  ✅ 意图已提交(ETB涌信桥)")
        return "\n".join(输出)

    def _执行配置(self, 参数: dict) -> str:
        if 参数.get("AI优化"):
            建议 = self._配置.AI优化()
            线 = ["  🤖 AI配置优化:"]
            for s in 建议:
                线.append(f"    ✅ {s}")
            线.append(self._配置.显示())
            return "\n".join(线)
        elif "键" in 参数:
            ok = self._配置.设置(参数["键"], 参数["值"])
            if ok:
                return f"  ✅ {参数['键']} = {参数['值']}"
            return f"  ❌ 未知配置项: {参数['键']}"
        else:
            return self._配置.显示()

    @property
    def 历史命令数(self) -> int:
        return len(self._命令历史)


if __name__ == "__main__":
    print("=" * 50)
    print("  HKC CLI v4.0.0 Demo")
    print("=" * 50)
    cli = HKC_CLI()
    # 测试各种命令
    命令列表 = [
        "help",
        "start",
        "status",
        "balance HKAIC_abc123",
        "send addr_A addr_B 100",
        "bridge send EVM 500",
        'query "查一下最近5笔跨链交易"',
        "diagnose",
        "config show",
        "config ai",
    ]
    for cmd in 命令列表:
        print(f"\n  > hkc {cmd}")
        print(cli.执行命令(cmd))
    print(f"\n  命令历史: {cli.历史命令数}条")
