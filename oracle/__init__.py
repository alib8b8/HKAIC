"""
HKC AI原生预言机系统
====================

包含模块：
- oracle_core: 预言机核心
- aggregation_engine: 涌现聚合引擎
- data_sources: 数据源管理
- manipulation_guard: 操纵防护引擎
- volatility_oracle: 波动率预言机
- event_oracle: 事件预言机
- oracle_guardian: 预言机守护者
- oracle_api: 预言机API

纯Python标准库，零外部依赖。
中文代码风格。
AI原生创新。
"""

from oracle.oracle_core import (
    预言机核心,
    数据类型,
    数据源类型,
    更新周期,
    数据点,
    价格数据点,
    聚合结果,
    订阅记录,
)

from oracle.aggregation_engine import (
    涌现聚合引擎,
    涌现聚合配置,
    数据源可信度,
)

from oracle.data_sources import (
    数据源管理器,
    数据源配置,
    数据源状态,
    数据源健康报告,
    模拟数据源,
)

from oracle.manipulation_guard import (
    操纵防护引擎,
    操纵防护配置,
    操纵类型,
    操纵告警级别,
    操纵事件,
)

from oracle.volatility_oracle import (
    波动率预言机,
    波动率预言机配置,
    波动率数据,
    波动率曲面点,
)

from oracle.event_oracle import (
    事件预言机,
    事件预言机配置,
    事件类型,
    事件严重级别,
    事件状态,
    事件数据,
)

from oracle.oracle_guardian import (
    预言机守护者,
    守护者配置,
    守护者状态,
    告警级别,
    守护者告警,
)

from oracle.oracle_api import (
    预言机API,
    预言机查询结果,
    获取预言机API,
    重置预言机API,
)


__all__ = [
    # 核心
    "预言机核心",
    "数据类型",
    "数据源类型",
    "更新周期",
    "数据点",
    "价格数据点",
    "聚合结果",
    "订阅记录",
    # 聚合
    "涌现聚合引擎",
    "涌现聚合配置",
    "数据源可信度",
    # 数据源
    "数据源管理器",
    "数据源配置",
    "数据源状态",
    "数据源健康报告",
    "模拟数据源",
    # 操纵防护
    "操纵防护引擎",
    "操纵防护配置",
    "操纵类型",
    "操纵告警级别",
    "操纵事件",
    # 波动率
    "波动率预言机",
    "波动率预言机配置",
    "波动率数据",
    "波动率曲面点",
    # 事件
    "事件预言机",
    "事件预言机配置",
    "事件类型",
    "事件严重级别",
    "事件状态",
    "事件数据",
    # 守护者
    "预言机守护者",
    "守护者配置",
    "守护者状态",
    "告警级别",
    "守护者告警",
    # API
    "预言机API",
    "预言机查询结果",
    "获取预言机API",
    "重置预言机API",
]
