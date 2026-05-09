"""
Hongkun AI Chain — P2P网络拓扑图 (network_topology.py)
======================================================
可视化涌知路由P2P网络：节点关系、信息传播、网络健康指标。
纯Python零依赖，生成自包含HTML。
"""

import math as _math
import random as _random
from typing import Dict, List, Optional, Any

from .html_template import (
    wrap_html, escape_js, save_html,
    BRAND_GOLD, BRAND_GREEN, BRAND_RED, BRAND_ORANGE, BRAND_CYAN
)


def _模拟网络数据(节点数: int = 30) -> Dict:
    """生成模拟P2P网络数据"""
    nodes = []
    for i in range(节点数):
        K_i = _random.uniform(5, 100)
        sigma_i = _random.uniform(0.05, 0.9)
        status = _random.choices(["在线", "同步中", "离线"], weights=[80, 15, 5])[0]
        bandwidth = _random.uniform(1, 100)
        latency = _random.uniform(10, 200)
        nodes.append({
            "id": f"Node-{i:02d}",
            "K_i": round(K_i, 2), "sigma_i": round(sigma_i, 3),
            "status": status, "bandwidth": round(bandwidth, 1),
            "latency": round(latency, 1),
            "version": _random.choice(["4.0.0", "3.2.1", "4.0.0"]),
            "connections": _random.randint(3, 15)
        })

    edges = []
    for i in range(节点数):
        for j in range(i+1, 节点数):
            if _random.random() < 0.15:
                edges.append({
                    "source": i, "target": j,
                    "weight": round(_random.uniform(0.1, 1.0), 2)
                })

    connected = sum(1 for n in nodes if n["status"] != "离线")
    connectivity = round(connected / 节点数 * 100, 1) if 节点数 > 0 else 0
    avg_path = round(_random.uniform(2.0, 4.5), 1)
    clustering = round(_random.uniform(0.3, 0.7), 2)

    return {
        "nodes": nodes, "edges": edges,
        "metrics": {
            "connectivity": connectivity, "avg_path_length": avg_path,
            "clustering_coefficient": clustering, "total_nodes": 节点数,
            "online": connected, "syncing": sum(1 for n in nodes if n["status"]=="同步中"),
            "offline": sum(1 for n in nodes if n["status"]=="离线")
        }
    }


def generate_network_topology(
    network_data: Optional[Dict] = None,
    output_path: str = "network_topology.html"
) -> str:
    """生成P2P网络拓扑图HTML"""
    if network_data is None:
        network_data = _模拟网络数据()

    m = network_data["metrics"]
    nodes = network_data["nodes"]
    edges = network_data["edges"]

    # 预计算JS数据
    topo_nodes = [{"id": n["id"], "K_i": n["K_i"], "status": n["status"], "bandwidth": n["bandwidth"]} for n in nodes]
    js_topo_nodes = escape_js(topo_nodes)
    js_edges = escape_js(edges)

    # 带宽热力图
    bw_nodes = nodes[:12]
    bw_labels = [n["id"][-5:] for n in bw_nodes]
    bw_matrix = [[round(_random.uniform(0, n["bandwidth"]/100), 2) for _ in bw_nodes] for n in bw_nodes]
    js_bw_matrix = escape_js(bw_matrix)
    js_bw_labels = escape_js(bw_labels)

    clustering_pct = round(m["clustering_coefficient"] * 100, 1)

    # 节点表格
    node_rows = ""
    for n in nodes:
        status_cls = "badge-green" if n["status"]=="在线" else ("badge-orange" if n["status"]=="同步中" else "badge-red")
        node_rows += f'<tr><td>{n["id"]}</td>'
        node_rows += f'<td><span class="badge {status_cls}">{n["status"]}</span></td>'
        node_rows += f'<td>{n["K_i"]}</td><td>{n["sigma_i"]}</td><td>{n["bandwidth"]}</td>'
        node_rows += f'<td>{n["latency"]}</td><td>{n["connections"]}</td></tr>\n'

    body = f"""
    <div class="hkc-page-title"><span class="icon">🌐</span> P2P 网络拓扑</div>
    <div class="hkc-subtitle">涌知路由 — 知识引力路由/智能Gossip/协同净化</div>

    <div class="hkc-grid hkc-grid-4 animate-slide">
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{m["total_nodes"]}</div><div class="stat-label">总节点数</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:{BRAND_GREEN}">{m["online"]}</div><div class="stat-label">在线</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{m["connectivity"]}%</div><div class="stat-label">连通度</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{m["avg_path_length"]}</div><div class="stat-label">平均路径长度</div>
        </div></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 节点关系图（大小=知识贡献度，颜色=状态）</div>
        <div class="chart-container" style="height:500px"><canvas id="topoCanvas"></canvas></div>
        <div style="display:flex;gap:16px;margin-top:8px;font-size:12px;color:#8899AA">
            <span>● 在线</span><span style="color:{BRAND_ORANGE}">● 同步中</span><span style="color:{BRAND_RED}">● 离线</span>
            <span style="margin-left:auto">节点大小 = K_i 知识贡献度</span>
        </div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 节点带宽热力图</div>
            <div class="chart-container" style="height:320px"><canvas id="bwHeatmap"></canvas></div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 网络健康指标</div>
            <div class="chart-container" style="height:160px"><canvas id="connGauge"></canvas></div>
            <div class="chart-container" style="height:160px"><canvas id="clusterGauge"></canvas></div>
        </div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 节点状态详情</div>
        <div style="overflow-x:auto;max-height:300px;overflow-y:auto">
        <table class="hkc-table" id="nodeTable">
            <thead><tr><th>节点ID</th><th>状态</th><th>K_i</th><th>σ_i</th><th>带宽</th><th>延迟(ms)</th><th>连接数</th></tr></thead>
            <tbody>{node_rows}</tbody>
        </table>
        </div>
    </div>
    """

    extra_js = f"""
    (function(){{
        var c = initCanvas('topoCanvas');
        if (!c) return;
        var ctx = c.ctx, w = c.w, h = c.h;
        var nodes = {js_topo_nodes};
        var edges = {js_edges};

        var cx = w/2, cy = h/2;
        nodes.forEach(function(n, i) {{
            var a = 2*Math.PI*i/nodes.length;
            n.x = cx + (w*0.3)*Math.cos(a) + (Math.random()-0.5)*40;
            n.y = cy + (h*0.3)*Math.sin(a) + (Math.random()-0.5)*40;
        }});
        for (var iter = 0; iter < 50; iter++) {{
            for (var i = 0; i < nodes.length; i++) {{
                for (var j = i+1; j < nodes.length; j++) {{
                    var dx = nodes[j].x - nodes[i].x;
                    var dy = nodes[j].y - nodes[i].y;
                    var dist = Math.sqrt(dx*dx+dy*dy) || 1;
                    var force = 2000 / (dist*dist);
                    nodes[i].x -= dx/dist*force;
                    nodes[i].y -= dy/dist*force;
                    nodes[j].x += dx/dist*force;
                    nodes[j].y += dy/dist*force;
                }}
            }}
            edges.forEach(function(e) {{
                var s = nodes[e.source], t = nodes[e.target];
                var dx = t.x - s.x, dy = t.y - s.y;
                var dist = Math.sqrt(dx*dx+dy*dy) || 1;
                var force = (dist - 100) * 0.01;
                s.x += dx/dist*force; s.y += dy/dist*force;
                t.x -= dx/dist*force; t.y -= dy/dist*force;
            }});
            nodes.forEach(function(n) {{
                n.x += (cx - n.x) * 0.01;
                n.y += (cy - n.y) * 0.01;
                n.x = Math.max(30, Math.min(w-30, n.x));
                n.y = Math.max(30, Math.min(h-30, n.y));
            }});
        }}
        edges.forEach(function(e) {{
            var s = nodes[e.source], t = nodes[e.target];
            ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(t.x, t.y);
            ctx.strokeStyle = 'rgba(255,215,0,' + e.weight*0.3 + ')';
            ctx.lineWidth = e.weight * 2; ctx.stroke();
        }});
        var statusColors = {{"在线": '#00E676', "同步中": '#FF9800', "离线": '#FF5252'}};
        nodes.forEach(function(n) {{
            var nr = 5 + n.K_i / 10;
            ctx.beginPath(); ctx.arc(n.x, n.y, nr, 0, Math.PI*2);
            var g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, nr);
            g.addColorStop(0, statusColors[n.status] || '#FFD700');
            g.addColorStop(1, '#0A1628');
            ctx.fillStyle = g; ctx.fill();
            ctx.strokeStyle = statusColors[n.status] || '#FFD700';
            ctx.lineWidth = 1.5; ctx.stroke();
            if (n.K_i > 50) {{
                ctx.fillStyle = '#8899AA'; ctx.font = '8px sans-serif';
                ctx.textAlign = 'center'; ctx.fillText(n.id.slice(-2), n.x, n.y + nr + 10);
            }}
        }});
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center'; ctx.fillText('涌知路由 P2P 网络', cx, 20);
    }})();

    drawHeatmap('bwHeatmap', {js_bw_matrix}, {{
        title: '节点间带宽矩阵',
        rowLabels: {js_bw_labels}, colLabels: {js_bw_labels}
    }});

    drawGauge('connGauge', {m['connectivity']}, 100, {{
        title: '网络连通度', unit: '%', size: 0.5
    }});

    drawGauge('clusterGauge', {clustering_pct}, 100, {{
        title: '聚类系数', unit: '%', size: 0.5
    }});

    setupTableSort('nodeTable');
    """

    html_content = wrap_html(
        title="HKC P2P网络拓扑",
        nav_active="network",
        body_content=body,
        extra_js=extra_js
    )
    return save_html(html_content, output_path)
