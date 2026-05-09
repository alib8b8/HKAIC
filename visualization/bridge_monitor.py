"""
Hongkun AI Chain — 跨链桥监控面板 (bridge_monitor.py)
======================================================
可视化ETB涌信桥数据：跨链流量、验证组轮换、保险池、Solver排行。
纯Python零依赖，生成自包含HTML。
"""

import math as _math
import random as _random
from typing import Dict, List, Optional, Any

from .html_template import (
    wrap_html, escape_js, save_html,
    BRAND_GOLD, BRAND_GREEN, BRAND_RED, BRAND_ORANGE, BRAND_CYAN
)

SUPPORTED_CHAINS = ["Ethereum", "BSC", "Polygon", "Arbitrum", "Optimism", "HKC"]


def _模拟跨链数据(交易数: int = 50) -> Dict:
    """生成模拟跨链桥数据"""
    flows = []
    for src in SUPPORTED_CHAINS:
        for dst in SUPPORTED_CHAINS:
            if src != dst:
                flows.append({
                    "source": src, "target": dst,
                    "volume": round(_random.uniform(10000, 500000), 0),
                    "tx_count": _random.randint(5, 100)
                })

    solvers = []
    for i in range(8):
        solvers.append({
            "id": f"Solver-{i+1:02d}",
            "reputation": round(_random.uniform(60, 99), 1),
            "fulfill_rate": round(_random.uniform(0.85, 0.99), 3),
            "speed": round(_random.uniform(0.5, 2.0), 2),
            "ath_verified": _random.choice([True, True, False]),
            "completed": _random.randint(100, 2000),
            "capital": round(_random.uniform(100000, 5000000), 0)
        })
    solvers.sort(key=lambda x: -x["reputation"])

    pool_history = []
    balance = 500000
    for d in range(60):
        balance += _random.uniform(-20000, 30000)
        balance = max(100000, balance)
        pool_history.append({
            "day": d+1,
            "balance": round(balance, 0),
            "claim": _random.choice([0, 0, 0, round(_random.uniform(5000, 30000), 0)])
        })

    events = []
    event_types = ["挑战提交", "交易回滚", "异常检测", "验证超时", "签名恢复"]
    for i in range(15):
        events.append({
            "time": f"{(i//24)+1}d {(i%24):02d}h",
            "type": _random.choice(event_types),
            "severity": _random.choice(["安全", "注意", "警告", "危险"]),
            "detail": f"跨链意图INT-{_random.randint(1000,9999)}触发"
        })

    intents = []
    states = ["意图提交", "Solver选定", "验证中", "已确认", "已结算"]
    for i in range(10):
        src = _random.choice(SUPPORTED_CHAINS)
        dst = _random.choice([c for c in SUPPORTED_CHAINS if c != src])
        cur_state = _random.randint(0, 4)
        intents.append({
            "id": f"INT-{9000+i}",
            "src": src,
            "dst": dst,
            "amount": round(_random.uniform(100, 10000), 2),
            "state": states[cur_state],
            "solver": f"Solver-{_random.randint(1,8):02d}"
        })

    return {"flows": flows, "solvers": solvers, "pool_history": pool_history,
            "events": events, "intents": intents}


def generate_bridge_monitor(
    bridge_data: Optional[Dict] = None,
    output_path: str = "bridge_monitor.html"
) -> str:
    """生成跨链桥监控面板HTML"""
    if bridge_data is None:
        bridge_data = _模拟跨链数据()

    total_volume = sum(f["volume"] for f in bridge_data["flows"])
    total_tx = sum(f["tx_count"] for f in bridge_data["flows"])
    active_solvers = len([s for s in bridge_data["solvers"] if s["ath_verified"]])
    pool_balance = bridge_data["pool_history"][-1]["balance"]

    top_flows = sorted(bridge_data["flows"], key=lambda x: -x["volume"])[:12]
    radar_labels = ["信誉评分", "履约率", "响应速度", "ATH验证", "资金规模", "完成量"]

    # 预计算JS数据
    js_chains = escape_js(SUPPORTED_CHAINS)
    js_top_flows = escape_js(top_flows)
    
    top3_solvers = bridge_data["solvers"][:3]
    radar_datasets = []
    for s in top3_solvers:
        radar_datasets.append({
            "name": s["id"],
            "values": [s["reputation"], s["fulfill_rate"]*100, s["speed"]*50,
                       100 if s["ath_verified"] else 40, min(s["capital"]/50000, 100),
                       min(s["completed"]/20, 100)]
        })
    js_radar = escape_js(radar_datasets)
    js_radar_labels = escape_js(radar_labels)
    
    pool_days = [str(p["day"]) for p in bridge_data["pool_history"]]
    pool_vals = [p["balance"] for p in bridge_data["pool_history"]]
    js_pool_days = escape_js(pool_days)
    js_pool_vals = escape_js(pool_vals)

    # 构建意图表格
    intent_rows = ""
    for it in bridge_data["intents"]:
        state_cls = "badge-green" if it["state"]=="已结算" else ("badge-cyan" if it["state"]=="已确认" else ("badge-orange" if it["state"]=="验证中" else "badge-gold"))
        intent_rows += f'<tr><td>{it["id"]}</td><td>{it["src"]}</td><td>{it["dst"]}</td>'
        intent_rows += f'<td>{it["amount"]}</td>'
        intent_rows += f'<td><span class="badge {state_cls}">{it["state"]}</span></td>'
        intent_rows += f'<td>{it["solver"]}</td></tr>\n'

    # 安全事件
    event_html = ""
    for e in bridge_data["events"]:
        sev_cls = "badge-red" if e["severity"]=="危险" else ("badge-orange" if e["severity"]=="警告" else ("badge-gold" if e["severity"]=="注意" else "badge-green"))
        event_html += f'<div style="padding:6px 12px;border-bottom:1px solid #2A3F5F;font-size:13px">'
        event_html += f'<span style="color:#8899AA">{e["time"]}</span> '
        event_html += f'<span class="badge {sev_cls}">{e["severity"]}</span> '
        event_html += f'<span style="color:#E0E6ED">{e["type"]}</span> '
        event_html += f'<span style="color:#8899AA;font-size:12px">— {e["detail"]}</span></div>\n'

    body = f"""
    <div class="hkc-page-title"><span class="icon">🌉</span> ETB 跨链桥监控</div>
    <div class="hkc-subtitle">涌信桥 Emergent Trust Bridge — 跨链流量/Solver/保险池/安全事件</div>

    <div class="hkc-grid hkc-grid-4 animate-slide">
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{total_volume/1e6:.1f}M</div><div class="stat-label">跨链总量(HKAIC)</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{total_tx}</div><div class="stat-label">跨链交易数</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:{BRAND_GREEN}">{active_solvers}</div><div class="stat-label">ATH验证Solver</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{pool_balance/1e6:.2f}M</div><div class="stat-label">保险池余额</div>
        </div></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 跨链流量图（箭头粗细=流量）</div>
        <div class="chart-container" style="height:400px"><canvas id="flowChart"></canvas></div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> Solver排行雷达图</div>
            <div class="chart-container" style="height:350px"><canvas id="solverRadar"></canvas></div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 保险池水位</div>
            <div class="chart-container" style="height:350px"><canvas id="poolChart"></canvas></div>
        </div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 意图状态流转</div>
        <div style="overflow-x:auto">
        <table class="hkc-table" id="intentTable">
            <thead><tr><th>意图ID</th><th>源链</th><th>目标链</th><th>金额</th><th>状态</th><th>Solver</th></tr></thead>
            <tbody>{intent_rows}</tbody>
        </table>
        </div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 安全事件日志</div>
        <div style="max-height:300px;overflow-y:auto">{event_html}</div>
    </div>
    """

    extra_js = f"""
    (function(){{
        var c = initCanvas('flowChart');
        if (!c) return;
        var ctx = c.ctx, w = c.w, h = c.h;
        var chains = {js_chains};
        var n = chains.length;
        var cx = w/2, cy = h/2, r = Math.min(w,h)/2 - 70;
        var positions = {{}};
        chains.forEach(function(ch, i) {{
            var a = 2*Math.PI*i/n - Math.PI/2;
            positions[ch] = {{x: cx+r*Math.cos(a), y: cy+r*Math.sin(a)}};
            ctx.beginPath(); ctx.arc(positions[ch].x, positions[ch].y, 22, 0, Math.PI*2);
            ctx.fillStyle = '#1B2838'; ctx.fill();
            ctx.strokeStyle = '#FFD700'; ctx.lineWidth = 2; ctx.stroke();
            ctx.fillStyle = '#E0E6ED'; ctx.font = '9px sans-serif';
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(ch.slice(0,4), positions[ch].x, positions[ch].y);
            ctx.fillStyle = '#8899AA'; ctx.font = '10px sans-serif';
            ctx.fillText(ch, positions[ch].x, positions[ch].y + 32);
        }});
        var flows = {js_top_flows};
        var maxV = Math.max.apply(null, flows.map(function(f){{return f.volume}}));
        flows.forEach(function(f) {{
            var s = positions[f.source], t = positions[f.target];
            if (!s || !t) return;
            ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(t.x, t.y);
            ctx.strokeStyle = 'rgba(255,215,0,' + (0.2 + 0.6*f.volume/maxV) + ')';
            ctx.lineWidth = 1 + 5 * f.volume / maxV;
            ctx.stroke();
            var angle = Math.atan2(t.y-s.y, t.x-s.x);
            var mx = (s.x+t.x)/2, my = (s.y+t.y)/2;
            ctx.beginPath();
            ctx.moveTo(mx+8*Math.cos(angle), my+8*Math.sin(angle));
            ctx.lineTo(mx-6*Math.cos(angle-0.5), my-6*Math.sin(angle-0.5));
            ctx.lineTo(mx-6*Math.cos(angle+0.5), my-6*Math.sin(angle+0.5));
            ctx.closePath();
            ctx.fillStyle = 'rgba(255,215,0,' + (0.4+0.5*f.volume/maxV) + ')';
            ctx.fill();
        }});
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center'; ctx.fillText('跨链流量拓扑', cx, 20);
    }})();

    drawRadarChart('solverRadar', {js_radar}, {{
        title: 'Solver Top-3 雷达图',
        sides: 6, labels: {js_radar_labels},
        maxVal: 100
    }});

    drawLineChart('poolChart', [
        {{name: '池余额', values: {js_pool_vals}, labels: {js_pool_days}}}
    ], {{ title: '保险池余额趋势', lineColors: ['#00BCD4'], fillArea: true }});

    setupTableSort('intentTable');
    """

    html_content = wrap_html(
        title="HKC 跨链桥监控",
        nav_active="bridge",
        body_content=body,
        extra_js=extra_js
    )
    return save_html(html_content, output_path)
