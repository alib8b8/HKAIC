"""
Hongkun AI Chain — AI守护者大屏 (guardian_dashboard.py)
=======================================================
可视化AI守护者数据：风险事件流、威胁统计、守护状态、地址风险热力图。
纯Python零依赖，生成自包含HTML。
"""

import math as _math
import random as _random
from typing import Dict, List, Optional, Any

from .html_template import (
    wrap_html, escape_js, save_html,
    BRAND_GOLD, BRAND_GREEN, BRAND_RED, BRAND_ORANGE, BRAND_CYAN
)


def _模拟守护者数据() -> Dict:
    """生成模拟AI守护者数据"""
    risk_levels = ["安全", "注意", "警告", "危险"]
    categories = ["合约风险", "地址风险", "金额异常", "频率异常", "授权风险"]

    events = []
    for i in range(30):
        level = _random.choices(risk_levels, weights=[50, 25, 18, 7])[0]
        cat = _random.choice(categories)
        events.append({
            "time": f"{i+1}分钟前",
            "level": level, "category": cat,
            "detail": f"检测到{cat}事件 — 交易0x{_random.randint(0,0xFFFF):04x}...",
            "action": "已拦截" if level == "危险" else ("需确认" if level == "警告" else "已放行")
        })

    threats = [
        {"type": "合约风险", "count": _random.randint(10, 50), "trend": _random.choice(["up", "down", "flat"])},
        {"type": "地址风险", "count": _random.randint(5, 30), "trend": _random.choice(["up", "down", "flat"])},
        {"type": "金额异常", "count": _random.randint(3, 20), "trend": _random.choice(["up", "down"])},
        {"type": "频率异常", "count": _random.randint(2, 15), "trend": _random.choice(["down", "flat"])},
        {"type": "授权风险", "count": _random.randint(1, 10), "trend": _random.choice(["flat", "down"])}
    ]

    guardian_level = _random.choice(["标准", "增强", "最高"])
    intercepts_today = _random.randint(5, 30)

    addr_labels = [f"0x{_random.randint(0,0xFFFF):04x}" for _ in range(8)]
    addr_matrix = [[round(_random.uniform(0, 1), 2) for _ in range(8)] for _ in range(8)]

    lock_events = []
    for i in range(10):
        lock_type = _random.choice(["自动锁定", "主动锁定", "异常锁定"])
        lock_events.append({
            "time": f"{i+1}小时前",
            "type": lock_type,
            "duration": f"{_random.randint(1, 60)}分钟",
            "reason": f"{lock_type} — {_random.choice(['异常IP登录', '大额转账', '用户手动', '频率异常', '可疑合约交互'])}"
        })

    return {
        "events": events, "threats": threats,
        "guardian_level": guardian_level,
        "intercepts_today": intercepts_today,
        "addr_labels": addr_labels, "addr_matrix": addr_matrix,
        "lock_events": lock_events
    }


def generate_guardian_dashboard(
    guardian_data: Optional[Dict] = None,
    output_path: str = "guardian_dashboard.html"
) -> str:
    """生成AI守护者大屏HTML"""
    if guardian_data is None:
        guardian_data = _模拟守护者数据()

    level_colors = {"标准": BRAND_GREEN, "增强": BRAND_ORANGE, "最高": BRAND_RED}
    gl_color = level_colors.get(guardian_data["guardian_level"], BRAND_GOLD)

    # 预计算JS数据
    js_threats_pie = escape_js([{"label": t["type"], "value": t["count"]} for t in guardian_data["threats"]])
    js_threats_bar = escape_js([{"label": t["type"][:4], "value": t["count"],
        "color": BRAND_RED if t["trend"]=="up" else (BRAND_GREEN if t["trend"]=="down" else BRAND_ORANGE)}
        for t in guardian_data["threats"]])
    js_addr_matrix = escape_js(guardian_data["addr_matrix"])
    js_addr_labels = escape_js(guardian_data["addr_labels"])

    # 风险事件流
    event_html = ""
    for e in guardian_data["events"][:15]:
        level_cls = "badge-green" if e["level"]=="安全" else ("badge-orange" if e["level"]=="注意" else ("badge-red" if e["level"]=="危险" else "badge-gold"))
        action_cls = "badge-red" if e["action"]=="已拦截" else ("badge-gold" if e["action"]=="需确认" else "badge-green")
        event_html += f'<div style="padding:6px 12px;border-bottom:1px solid #2A3F5F;font-size:13px;display:flex;align-items:center;gap:8px">'
        event_html += f'<span style="color:#8899AA;min-width:70px">{e["time"]}</span>'
        event_html += f'<span class="badge {level_cls}">{e["level"]}</span>'
        event_html += f'<span style="color:#E0E6ED">{e["category"]}</span>'
        event_html += f'<span style="color:#8899AA;font-size:12px;flex:1">{e["detail"]}</span>'
        event_html += f'<span class="badge {action_cls}">{e["action"]}</span>'
        event_html += f'</div>\n'

    # 锁事件
    lock_html = ""
    for l in guardian_data["lock_events"]:
        lock_color = "#FF5252" if l["type"]=="异常锁定" else ("#FFD700" if l["type"]=="主动锁定" else "#00E676")
        lock_html += f'<div style="padding:8px 12px;border-left:3px solid {lock_color};margin:4px 0;background:rgba(27,40,56,.5);border-radius:0 6px 6px 0;font-size:13px">'
        lock_html += f'<span style="color:#8899AA">{l["time"]}</span> '
        lock_html += f'<span style="color:#E0E6ED;font-weight:600">{l["type"]}</span> '
        lock_html += f'<span style="color:#8899AA">· {l["duration"]} · {l["reason"]}</span></div>\n'

    safe_count = sum(1 for e in guardian_data["events"] if e["level"]=="安全")

    body = f"""
    <div class="hkc-page-title"><span class="icon">🛡️</span> AI 守护者大屏</div>
    <div class="hkc-subtitle">交易安全实时检测 — 五维风险扫描/自动拦截/钱包锁</div>

    <div class="hkc-grid hkc-grid-4 animate-slide">
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:{gl_color}">{guardian_data["guardian_level"]}</div>
            <div class="stat-label">守护等级</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:{BRAND_RED}">{guardian_data["intercepts_today"]}</div>
            <div class="stat-label">今日拦截</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{len(guardian_data["events"])}</div>
            <div class="stat-label">检测事件</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:{BRAND_GREEN}">{safe_count}</div>
            <div class="stat-label">安全放行</div>
        </div></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot" style="background:{BRAND_RED};animation:pulse 1s infinite"></span> 风险事件实时流</div>
        <div style="max-height:250px;overflow-y:auto">{event_html}</div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 威胁类型分布</div>
            <div class="chart-container" style="height:300px"><canvas id="threatPie"></canvas></div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 威胁趋势</div>
            <div class="chart-container" style="height:300px"><canvas id="threatBar"></canvas></div>
        </div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 地址风险热力图</div>
        <div class="chart-container" style="height:320px"><canvas id="addrHeatmap"></canvas></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 钱包锁状态时间线</div>
        <div style="overflow-x:auto">{lock_html}</div>
    </div>
    """

    extra_js = f"""
    drawPieChart('threatPie', {js_threats_pie}, {{
        title: '威胁类型分布', donut: true
    }});

    drawBarChart('threatBar', {js_threats_bar}, {{
        title: '威胁数量(↑上升 ↓下降 →平稳)',
        showValues: true
    }});

    drawHeatmap('addrHeatmap', {js_addr_matrix}, {{
        title: '近期交互地址风险矩阵',
        rowLabels: {js_addr_labels}, colLabels: {js_addr_labels},
        colorHigh: '#FF5252'
    }});
    """

    html_content = wrap_html(
        title="HKC AI守护者",
        nav_active="guardian",
        body_content=body,
        extra_js=extra_js
    )
    return save_html(html_content, output_path)
