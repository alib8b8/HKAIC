"""
Hongkun AI Chain — 配置加载与校验 (config_loader.py)
=====================================================
YAML配置文件加载、环境检测、热重载、配置校验。
纯Python实现，无外部依赖。
"""

import os
import time
import hashlib
import copy
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class 配置项:
    """配置项元数据"""
    键: str
    值: Any
    类型: str  # int/float/str/bool/list/dict
    默认: Any = None
    描述: str = ""
    可热重载: bool = True
    最小值: Optional[float] = None
    最大值: Optional[float] = None


class 配置校验器:
    """配置值校验"""

    # 已知配置模式
    _模式 = {
        "链.版本": {"类型": str, "正则": r"^\d+\.\d+\.\d+$"},
        "共识.alpha": {"类型": float, "最小": 0.1, "最大": 1.0},
        "共识.beta": {"类型": float, "最小": 0.5, "最大": 3.0},
        "共识.epoch时长_秒": {"类型": int, "最小": 10, "最大": 600},
        "代币.总量": {"类型": int, "最小": 1},
        "代币.精度": {"类型": int, "最小": 0, "最大": 18},
        "P2P.默认端口": {"类型": int, "最小": 1024, "最大": 65535},
        "RPC.REST端口": {"类型": int, "最小": 1024, "最大": 65535},
        "跨链桥.保险费率": {"类型": float, "最小": 0.0, "最大": 0.1},
        "ATH.握手步骤": {"类型": int, "最小": 1, "最大": 20},
    }

    def 校验(self, 键: str, 值: Any) -> Tuple[bool, str]:
        """校验单个配置项"""
        模式 = self._模式.get(键)
        if not 模式:
            return True, "未知配置项(允许)"

        # 类型检查
        if not isinstance(值, 模式["类型"]):
            return False, f"类型错误: 期望{模式['类型'].__name__}, 实际{type(值).__name__}"

        # 范围检查
        if "最小" in 模式 and 值 < 模式["最小"]:
            return False, f"值过小: 最小{模式['最小']}, 实际{值}"
        if "最大" in 模式 and 值 > 模式["最大"]:
            return False, f"值过大: 最大{模式['最大']}, 实际{值}"

        return True, ""

    def 批量校验(self, 配置: dict) -> List[Tuple[str, bool, str]]:
        """批量校验配置"""
        结果 = []
        self._扁平遍历(配置, "", 结果)
        return 结果

    def _扁平遍历(self, d: dict, 前缀: str, 结果: list):
        for k, v in d.items():
            完整键 = f"{前缀}.{k}" if 前缀 else k
            if isinstance(v, dict):
                self._扁平遍历(v, 完整键, 结果)
            else:
                ok, msg = self.校验(完整键, v)
                结果.append((完整键, ok, msg))


class 环境检测器:
    """检测运行环境"""

    def 检测(self) -> dict:
        """检测当前环境"""
        结果 = {
            "Python版本": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            "平台": os.name,
            "CPU核心": os.cpu_count() or 1,
            "内存_GB": self._估算内存(),
            "磁盘可用": True,
            "网络": True,
            "端口可用": self._检测端口(8843),
        }
        return 结果

    def _估算内存(self) -> float:
        """估算可用内存(GB)"""
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        return int(line.split()[1]) / 1024 / 1024
        except (FileNotFoundError, ValueError, IndexError):
            pass
        return 4.0  # 默认4GB

    def _检测端口(self, 端口: int) -> bool:
        """检测端口是否可用"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.bind(("127.0.0.1", 端口))
            s.close()
            return True
        except OSError:
            return False

    def 推荐(self) -> dict:
        """根据环境推荐配置"""
        环境 = self.检测()
        推荐 = {}
        if 环境["CPU核心"] >= 8:
            推荐["同步.并行下载"] = 16
        elif 环境["CPU核心"] >= 4:
            推荐["同步.并行下载"] = 8
        else:
            推荐["同步.并行下载"] = 4

        if 环境["内存_GB"] >= 16:
            推荐["P2P.最大连接"] = 100
        elif 环境["内存_GB"] >= 8:
            推荐["P2P.最大连接"] = 50
        else:
            推荐["P2P.最大连接"] = 20

        return 推荐


class 配置加载器:
    """
    HKC配置加载器
    
    功能:
      - YAML配置文件解析(纯Python实现)
      - 环境检测与配置推荐
      - 配置校验
      - 热重载(文件变更检测)
      - 配置合并(默认→文件→环境变量)
    """

    def __init__(self, 配置目录: str = ""):
        self._目录 = 配置目录 or os.path.join(os.path.dirname(__file__), "")
        self._配置: Dict[str, Any] = {}
        self._校验器 = 配置校验器()
        self._环境 = 环境检测器()
        self._文件哈希: Dict[str, str] = {}
        self._变更回调: List[callable] = []
        self._最后加载: float = 0.0

    def 加载默认(self) -> dict:
        """加载默认配置"""
        self._配置 = {
            "链": {"名称": "Hongkun AI Chain", "代号": "HKC", "版本": "4.0.0"},
            "共识": {"算法": "PoEI", "alpha": 0.6, "beta": 1.2, "epoch时长_秒": 60},
            "代币": {"总量": 21000000, "精度": 16},
            "P2P": {"端口": 8845, "最大连接": 50},
            "RPC": {"端口": 8843, "WS端口": 8844},
        }
        return self._配置

    def 解析YAML(self, 文本: str) -> dict:
        """简易YAML解析器(纯Python)"""
        结果 = {}
        当前路径 = []
        当前缩进 = -1

        for line in 文本.split("\n"):
            # 跳过空行和注释
            去除 = line.strip()
            if not 去除 or 去除.startswith("#"):
                continue

            # 计算缩进
            缩进 = len(line) - len(line.lstrip())
            内容 = 去除.split("#")[0].strip()  # 去除行内注释

            if ":" in 内容:
                键, 值部分 = 内容.split(":", 1)
                键 = 键.strip()
                值部分 = 值部分.strip()

                # 确定层级
                while 当前路径 and 缩进 <= 当前缩进:
                    当前路径.pop()

                # 解析值
                if 值部分:
                    值 = self._解析值(值部分)
                    # 设置值到嵌套字典
                    目标 = 结果
                    for p in 当前路径:
                        目标 = 目标.setdefault(p, {})
                    目标[键] = 值
                else:
                    目标 = 结果
                    for p in 当前路径:
                        目标 = 目标.setdefault(p, {})
                    目标.setdefault(键, {})
                    当前路径.append(键)
                    当前缩进 = 缩进

        return 结果

    def _解析值(self, 值文本: str) -> Any:
        """解析YAML值"""
        值文本 = 值文本.strip().strip('"').strip("'")

        # 列表
        if 值文本.startswith("[") and 值文本.endswith("]"):
            内容 = 值文本[1:-1]
            return [self._解析值(v.strip()) for v in 内容.split(",") if v.strip()]

        # 布尔
        if 值文本.lower() in ("true", "yes"):
            return True
        if 值文本.lower() in ("false", "no"):
            return False

        # 整数
        try:
            return int(值文本)
        except ValueError:
            pass

        # 浮点
        try:
            return float(值文本)
        except ValueError:
            pass

        return 值文本

    def 加载文件(self, 文件名: str) -> dict:
        """从文件加载配置"""
        路径 = os.path.join(self._目录, 文件名)
        try:
            with open(路径, "r", encoding="utf-8") as f:
                文本 = f.read()
            self._文件哈希[文件名] = hashlib.sha256(文本.encode()).hexdigest()[:16]
            return self.解析YAML(文本)
        except FileNotFoundError:
            return {}

    def 加载全部(self) -> dict:
        """加载所有配置文件"""
        for fn in ["genesis.yaml", "node.yaml", "network.yaml"]:
            文件配置 = self.加载文件(fn)
            self._合并配置(self._配置, 文件配置)
        # 环境变量覆盖
        self._加载环境变量()
        self._最后加载 = time.time()
        return self._配置

    def _合并配置(self, 基础: dict, 覆盖: dict):
        """深度合并配置"""
        for k, v in 覆盖.items():
            if k in 基础 and isinstance(基础[k], dict) and isinstance(v, dict):
                self._合并配置(基础[k], v)
            else:
                基础[k] = v

    def _加载环境变量(self):
        """从环境变量覆盖配置(前缀HKC_)"""
        for key, value in os.environ.items():
            if key.startswith("HKC_"):
                配置键 = key[4:].replace("_", ".").lower()
                self._设置嵌套(self._配置, 配置键, value)

    def _设置嵌套(self, d: dict, 键: str, 值: str):
        """设置嵌套字典值"""
        部分 = 键.split(".")
        当前 = d
        for p in 部分[:-1]:
            当前 = 当前.setdefault(p, {})
        当前[部分[-1]] = self._解析值(值)

    def 校验(self) -> List[Tuple[str, bool, str]]:
        """校验当前配置"""
        return self._校验器.批量校验(self._配置)

    def 检测变更(self) -> List[str]:
        """检测配置文件是否变更(热重载)"""
        变更 = []
        for fn in ["genesis.yaml", "node.yaml", "network.yaml"]:
            路径 = os.path.join(self._目录, fn)
            try:
                with open(路径, "r", encoding="utf-8") as f:
                    哈希 = hashlib.sha256(f.read().encode()).hexdigest()[:16]
                if fn in self._文件哈希 and 哈希 != self._文件哈希[fn]:
                    变更.append(fn)
            except FileNotFoundError:
                pass
        return 变更

    def 热重载(self) -> bool:
        """热重载变更的配置"""
        变更 = self.检测变更()
        if not 变更:
            return False
        for fn in 变更:
            文件配置 = self.加载文件(fn)
            self._合并配置(self._配置, 文件配置)
        # 触发回调
        for cb in self._变更回调:
            try:
                cb(变更)
            except Exception:
                pass
        return True

    def 注册变更回调(self, 回调: callable):
        """注册配置变更回调"""
        self._变更回调.append(回调)

    def 获取(self, 键: str, 默认: Any = None) -> Any:
        """获取配置值(支持点号分隔)"""
        当前 = self._配置
        for 部分 in 键.split("."):
            if isinstance(当前, dict) and 部分 in 当前:
                当前 = 当前[部分]
            else:
                return 默认
        return 当前

    def 设置(self, 键: str, 值: Any) -> bool:
        """设置配置值"""
        ok, msg = self._校验器.校验(键, 值)
        if not ok:
            return False
        部分 = 键.split(".")
        当前 = self._配置
        for p in 部分[:-1]:
            当前 = 当前.setdefault(p, {})
        当前[部分[-1]] = 值
        return True

    def 环境推荐(self) -> dict:
        """环境检测推荐"""
        return self._环境.推荐()

    def 状态(self) -> dict:
        return {
            "配置项数": len(str(self._配置)),
            "最后加载": time.strftime("%H:%M:%S", time.localtime(self._最后加载)),
            "文件哈希": self._文件哈希,
            "校验问题": sum(1 for _, ok, _ in self.校验() if not ok),
        }


if __name__ == "__main__":
    print("  HKC 配置加载器 Demo")
    loader = 配置加载器()
    loader.加载默认()
    配置 = loader.加载全部()
    校验 = loader.校验()
    print(f"  配置: {len(str(配置))}字节")
    print(f"  校验: {sum(1 for _,ok,_ in 校验 if ok)}/{len(校验)}通过")
    print(f"  环境: {loader.环境推荐()}")
    print(f"  状态: {loader.状态()}")
