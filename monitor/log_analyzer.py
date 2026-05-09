"""
Hongkun AI Chain — AI日志分析器 (log_analyzer.py)
===================================================
AI驱动的日志分析:模式识别、根因分析、日志压缩。
"""

import hashlib
import time
import math
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class 日志级别(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass
class 日志条目:
    """日志条目"""
    时间: float
    级别: 日志级别
    模块: str
    消息: str
    原始: str = ""

    def 关键词(self) -> List[str]:
        """提取关键词"""
        # 简单关键词提取
        停用词 = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
        词 = re.findall(r'\b[a-zA-Z_]\w*\b', self.消息)
        return [w for w in 词 if w.lower() not in 停用词 and len(w) > 2]


class 日志模式:
    """识别到的日志模式"""
    def __init__(self, 模式ID: str, 示例: str, 频率: int, 级别: 日志级别):
        self.模式ID = 模式ID
        self.示例 = 示例
        self.频率 = 频率
        self.级别 = 级别
        self.首次出现: float = 0.0
        self.最近出现: float = 0.0
        self.关联模式: List[str] = []

    def 摘要(self) -> str:
        return f"[{self.级别.value}×{self.频率}] {self.示例[:60]}"


class AI日志分析器:
    """
    HKC AI日志分析器
    
    能力:
      1. 模式识别 — 自动聚类相似日志
      2. 根因分析 — 从错误日志回溯根因
      3. 日志压缩 — 合并重复日志
      4. 异常检测 — 识别异常日志模式
    """

    def __init__(self):
        self._日志: List[日志条目] = []
        self._模式: Dict[str, 日志模式] = {}
        self._模块索引: Dict[str, List[int]] = {}

    def 添加日志(self, 条目: 日志条目):
        """添加日志条目"""
        idx = len(self._日志)
        self._日志.append(条目)
        self._模块索引.setdefault(条目.模块, []).append(idx)
        # 尝试匹配已有模式
        模式键 = self._提取模式键(条目)
        if 模式键 in self._模式:
            self._模式[模式键].频率 += 1
            self._模式[模式键].最近出现 = 条目.时间
        else:
            self._模式[模式键] = 日志模式(
                模式ID=hashlib.sha256(模式键.encode()).hexdigest()[:8],
                示例=条目.消息,
                频率=1,
                级别=条目.级别,
            )
            self._模式[模式键].首次出现 = 条目.时间

    def _提取模式键(self, 条目: 日志条目) -> str:
        """提取日志模式键(替换变量为占位符)"""
        消息 = 条目.消息
        # 替换数字
        消息 = re.sub(r'\d+', '<N>', 消息)
        # 替换地址
        消息 = re.sub(r'0x[a-fA-F0-9]+', '<ADDR>', 消息)
        # 替换哈希
        消息 = re.sub(r'[a-fA-F0-9]{32,}', '<HASH>', 消息)
        return f"{条目.级别.value}:{条目.模块}:{消息}"

    def 根因分析(self, 错误: 日志条目) -> List[日志条目]:
        """从错误日志回溯根因"""
        候选 = []
        # 回溯同模块的最近WARN/INFO日志
        for idx in reversed(range(len(self._日志))):
            条目 = self._日志[idx]
            if 条目 == 错误:
                break
            if 条目.模块 == 错误.模块 or 条目.级别 == 日志级别.WARN:
                候选.append(条目)
        return 候选[-10:]  # 最近10条

    def 压缩日志(self) -> Dict[str, int]:
        """日志压缩统计"""
        结果 = {}
        for 模式键, 模式 in self._模式.items():
            if 模式.频率 > 1:
                结果[模式.示例[:40]] = 模式.频率
        return 结果

    def 异常模式(self) -> List[日志模式]:
        """识别异常日志模式"""
        异常 = []
        for 模式 in self._模式.values():
            # ERROR级别且频率高
            if 模式.级别 == 日志级别.ERROR and 模式.频率 > 3:
                异常.append(模式)
            # 频率突然增加
            if 模式.频率 > 10:
                异常.append(模式)
        return 异常

    def 摘要(self) -> str:
        """日志分析摘要"""
        总 = len(self._日志)
        按级别 = {}
        for 条 in self._日志:
            按级别[条.级别.value] = 按级别.get(条.级别.value, 0) + 1
        线 = [f"日志分析: {总}条"]
        for 级别, 数 in sorted(按级别.items()):
            线.append(f"  {级别}: {数}")
        线.append(f"  模式: {len(self._模式)}种")
        异常 = self.异常模式()
        if 异常:
            线.append(f"  异常模式: {len(异常)}种")
        return "\n".join(线)


if __name__ == "__main__":
    print("  HKC AI日志分析器 Demo")
    analyzer = AI日志分析器()
    模拟 = [
        (日志级别.INFO, "p2p", "连接建立: peer=0xabc, 延迟=50ms"),
        (日志级别.INFO, "p2p", "连接建立: peer=0xdef, 延迟=30ms"),
        (日志级别.WARN, "sync", "区块高度差=3, 开始同步"),
        (日志级别.ERROR, "consensus", "出块超时: epoch=42, 延迟=5000ms"),
        (日志级别.WARN, "consensus", "视图切换: epoch=42"),
        (日志级别.ERROR, "consensus", "出块超时: epoch=43, 延迟=6000ms"),
    ]
    for 级别, 模块, 消息 in 模拟:
        analyzer.添加日志(日志条目(time.time(), 级别, 模块, 消息))
    print(analyzer.摘要())
    压缩 = analyzer.压缩日志()
    print(f"  压缩: {压缩}")
    异常 = analyzer.异常模式()
    for m in 异常:
        print(f"  异常: {m.摘要()}")
