"""
Hongkun AI Chain — PoEI共识仪表盘 (consensus_dashboard.py)
============================================================
可视化PoEI共识数据：涌现分数、出块权分布、Epoch时间线、知识贡献热力图。
纯Python零依赖，生成自包含HTML。
"""

import time as _time
import math as _math
import random as _random
from typing import Dict, List, Optional, Any

from .html_template import (
    wrap_html, escape_js, save_html,
    BRAND_GOLD, BRAND_GREEN, BRAND_RED, BRAND_ORANGE, BRAND_CYAN
)


def _模拟节点数据(节点数: int = 21) -> List[Dict]:
    """生成模拟共识节点数据"""
    names = [f"HKC-Node-{i:02d}" for i in range(1, 节点数+1)]
    nodes = []
    for i, name in enumerate(names):
        K_i = _random.uniform(10, 100)
        S_i = _random.uniform(5000, 500000)
        sigma_i = _random.uniform(0.1, 0.95)
        E_i = (K_i * _math.sqrt(S_i))**0.6 * sigma_i**1.2
        tier = "涌金" if E_i > 800 else ("涌银" if E_i > 400 else "涌铜")
        nodes.append({
            "name": name, "K_i": round(K_i, 2),
            "S_i": round(S_i, 0), "sigma_i": round(sigma_i, 4),
            "E_i": round(E_i, 2), "tier": tier,
            "color": BRAND_GOLD if tier=="涌金" else ("#C0C0C0" if tier=="涌银" else "#CD7F32")
        })
    nodes.sort(key=lambda x: -x["E_i"])
    return nodes


def _模拟epoch历史(数量: int = 20) -> List[Dict]:
    """生成模拟Epoch历史"""
    epochs = []
    for i in range(数量):
        nodes = _模拟节点数据(21)
        proposer = nodes[0]["name"]
        participants = _random.randint(18, 21)
        slashing = _random.choice([0,0,0,0,1])
        epochs.append({
            "epoch": i+1, "proposer": proposer,
            "participants": participants, "slashing": slashing,
            "alpha": round(_random.uniform(0.5, 0.8), 2),
            "beta": round(_random.uniform(0.8, 1.5), 2),
            "gamma": round(_random.uniform(0.3, 0.6), 2)
        })
    return epochs


def generate_consensus_dashboard(
    nodes: Optional[List[Dict]] = None,
    epochs: Optional[List[Dict]] = None,
    alpha: float = 0.6, beta: float = 1.2, gamma: float = 0.5,
    output_path: str = "consensus_dashboard.html"
) -> str:
    """生成PoEI共识仪表盘HTML"""
    if nodes is None:
        nodes = _模拟节点数据()
    if epochs is None:
        epochs = _模拟epoch历史()

    # 预计算JS数据
    bar_data = escape_js([{"label": n["name"][-5:], "value": n["E_i"], "color": n["color"]} for n in nodes])
    bar_colors = escape_js([n["color"] for n in nodes])
    total_E = sum(n["E_i"] for n in nodes) or 1
    pie_items = [{"label": n["name"][-5:], "value": round(n["E_i"]/total_E*100, 2)} for n in nodes[:8]]
    pie_items.append({"label": "其他", "value": round(sum(n["E_i"] for n in nodes[8:])/total_E*100, 2)})
    pie_data = escape_js(pie_items)

    k_labels = [n["name"][-5:] for n in nodes[:10]]
    k_matrix = [[round(_random.uniform(0, n["K_i"]/100), 2) for _ in range(10)] for n in nodes[:10]]

    edges = []
    for i in range(min(len(nodes), 10)):
        for j in range(i+1, min(len(nodes), 10)):
            w = round(nodes[i]["sigma_i"] * nodes[j]["sigma_i"] * _random.uniform(0.5, 1.5), 3)
            if w > 0.3:
                edges.append({"source": i, "target": j, "weight": w})

    sigma_nodes = [{"name": n["name"][-5:], "sigma": n["sigma_i"], "E": n["E_i"]} for n in nodes[:10]]
    sigma_edges = edges

    涌金数 = sum(1 for n in nodes if n["tier"]=="涌金")
    涌银数 = sum(1 for n in nodes if n["tier"]=="涌银")
    涌铜数 = sum(1 for n in nodes if n["tier"]=="涌铜")

    # 构建Epoch表格行
    epoch_rows = ""
    for e in epochs:
        slash_cls = "badge-red" if e["slashing"] else "badge-green"
        slash_icon = "⚠" if e["slashing"] else "✓"
        epoch_rows += f'<tr><td>{e["epoch"]}</td><td>{e["proposer"]}</td><td>{e["participants"]}</td>'
        epoch_rows += f'<td><span class="badge {slash_cls}">{slash_icon}</span></td>'
        epoch_rows += f'<td>{e["alpha"]}</td><td>{e["beta"]}</td><td>{e["gamma"]}</td></tr>\n'

    body = f"""
    <div class="hkc-page-title"><span class="icon">⚡</span> PoEI 共识仪表盘</div>
    <div class="hkc-subtitle">涌智证明 Proof of Emergent Intelligence — 实时共识状态监控</div>

    <div class="hkc-grid hkc-grid-4 animate-slide">
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{len(nodes)}</div><div class="stat-label">活跃节点</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:{BRAND_GOLD}">{涌金数}</div><div class="stat-label">涌金节点</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:#C0C0C0">{涌银数}</div><div class="stat-label">涌银节点</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:#CD7F32">{涌铜数}</div><div class="stat-label">涌铜节点</div>
        </div></div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 节点涌现分数 E_i</div>
            <div class="chart-container" style="height:380px"><canvas id="barEmergence"></canvas></div>
            <div class="time-filter" id="tf-bar">
                <button data-range="all" class="active">全部</button>
                <button data-range="gold">涌金</button>
                <button data-range="silver">涌银</button>
                <button data-range="bronze">涌铜</button>
            </div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 出块权分布</div>
            <div class="chart-container" style="height:380px"><canvas id="pieBlock"></canvas></div>
        </div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 知识贡献热力图 K_i</div>
            <div class="chart-container" style="height:350px"><canvas id="heatKnowledge"></canvas></div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 协同因子网络 σ_i</div>
            <div class="chart-container" style="height:350px"><canvas id="networkSigma"></canvas></div>
        </div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> PoEI参数调节面板</div>
        <div class="hkc-grid hkc-grid-3">
            <div>
                <label style="color:#8899AA;font-size:13px">α (知识×质押指数): <span id="val-alpha">{alpha}</span></label><br>
                <input type="range" id="slider-alpha" min="0.1" max="1.5" step="0.05" value="{alpha}"
                    style="width:100%;margin-top:8px;accent-color:#FFD700">
            </div>
            <div>
                <label style="color:#8899AA;font-size:13px">β (协同因子指数): <span id="val-beta">{beta}</span></label><br>
                <input type="range" id="slider-beta" min="0.5" max="2.0" step="0.05" value="{beta}"
                    style="width:100%;margin-top:8px;accent-color:#FFD700">
            </div>
            <div>
                <label style="color:#8899AA;font-size:13px">γ (质押衰减系数): <span id="val-gamma">{gamma}</span></label><br>
                <input type="range" id="slider-gamma" min="0.1" max="1.0" step="0.05" value="{gamma}"
                    style="width:100%;margin-top:8px;accent-color:#FFD700">
            </div>
        </div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> Epoch 时间线</div>
        <div style="overflow-x:auto">
        <table class="hkc-table" id="epochTable">
            <thead><tr><th>Epoch</th><th>出块者</th><th>参与节点</th><th>Slashing</th><th>α</th><th>β</th><th>γ</th></tr></thead>
            <tbody>{epoch_rows}</tbody>
        </table>
        </div>
    </div>
    """

    # 预计算JS变量
    js_sigma_nodes = escape_js(sigma_nodes)
    js_sigma_edges = escape_js(sigma_edges)
    js_k_matrix = escape_js(k_matrix)
    js_k_labels = escape_js(k_labels)

    extra_js = f"""
    drawBarChart('barEmergence', {bar_data}, {{
        title: '涌现分数 E_i (按等级着色)',
        barColors: {bar_colors},
        padding: {{top:30, right:20, bottom:60, left:60}},
        showValues: false
    }});

    drawPieChart('pieBlock', {pie_data}, {{
        title: '出块权分布 (%)',
        donut: true
    }});

    drawHeatmap('heatKnowledge', {js_k_matrix}, {{
        title: '知识贡献度关联矩阵',
        rowLabels: {js_k_labels}, colLabels: {js_k_labels}
    }});

    (function(){{
        var c = initCanvas('networkSigma');
        if (!c) return;
        var ctx = c.ctx, w = c.w, h = c.h;
        var nodes = {js_sigma_nodes};
        var edges = {js_sigma_edges};
        var cx = w/2, cy = h/2, r = Math.min(w,h)/2 - 60;
        nodes.forEach(function(n, i) {{
            n.x = cx + r * Math.cos(2*Math.PI*i/nodes.length - Math.PI/2);
            n.y = cy + r * Math.sin(2*Math.PI*i/nodes.length - Math.PI/2);
        }});
        edges.forEach(function(e) {{
            var s = nodes[e.source], t = nodes[e.target];
            ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(t.x, t.y);
            ctx.strokeStyle = 'rgba(255,215,0,' + Math.min(e.weight, 1) * 0.6 + ')';
            ctx.lineWidth = Math.max(1, e.weight * 3);
            ctx.stroke();
        }});
        nodes.forEach(function(n) {{
            var nr = 8 + n.sigma * 15;
            ctx.beginPath(); ctx.arc(n.x, n.y, nr, 0, Math.PI*2);
            var g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, nr);
            g.addColorStop(0, '#FFD700'); g.addColorStop(1, '#0A1628');
            ctx.fillStyle = g; ctx.fill();
            ctx.strokeStyle = '#FFD700'; ctx.lineWidth = 1.5; ctx.stroke();
            ctx.fillStyle = '#E0E6ED'; ctx.font = '9px sans-serif';
            ctx.textAlign = 'center'; ctx.fillText(n.name, n.x, n.y + nr + 12);
        }});
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center'; ctx.fillText('协同因子网络 σ_i', cx, 20);
    }})();

    ['alpha','beta','gamma'].forEach(function(p) {{
        var slider = document.getElementById('slider-' + p);
        var label = document.getElementById('val-' + p);
        slider.addEventListener('input', function() {{ label.textContent = slider.value; }});
    }});

    setupTableSort('epochTable');
    """

    html_content = wrap_html(
        title="HKC PoEI共识仪表盘",
        nav_active="consensus",
        body_content=body,
        extra_js=extra_js
    )
    return save_html(html_content, output_path)
