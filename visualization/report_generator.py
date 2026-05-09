"""
Hongkun AI Chain — 综合报告生成器 (report_generator.py)
=======================================================
一键生成完整链状态报告，整合所有可视化模块。
输出为单个HTML文件，浏览器打开即看。
纯Python零依赖，生成自包含HTML。
"""

import time as _time
import os as _os
from typing import Dict, List, Optional, Any

from .html_template import (
    generate_head, generate_nav, generate_footer, COMMON_JS,
    wrap_html, escape_js, save_html,
    BRAND_GOLD, BRAND_GREEN, BRAND_RED, BRAND_ORANGE, BRAND_CYAN,
    BRAND_DEEP_BLUE, BRAND_DARK, BRAND_CARD, BRAND_BORDER, BRAND_TEXT, BRAND_TEXT_DIM
)
from .consensus_dashboard import _模拟节点数据, _模拟epoch历史
from .economy_charts import _模拟经济数据, _模拟持币分布
from .bridge_monitor import _模拟跨链数据
from .network_topology import _模拟网络数据
from .wallet_panel import _模拟钱包数据
from .guardian_dashboard import _模拟守护者数据
from .block_explorer_ui import _模拟链数据


def generate_report(
    include_panels: Optional[List[str]] = None,
    output_path: str = "hkc_full_report.html",
    title: str = "HKC v4.0.0 综合状态报告"
) -> str:
    """生成综合报告HTML"""
    all_panels = ["consensus", "economy", "bridge", "network", "wallet", "guardian", "explorer"]
    if include_panels is None:
        include_panels = all_panels

    nodes = _模拟节点数据()
    epochs = _模拟epoch历史()
    economy = _模拟经济数据()
    dist = _模拟持币分布()
    bridge = _模拟跨链数据()
    network = _模拟网络数据()
    wallet = _模拟钱包数据()
    guardian = _模拟守护者数据()
    chain = _模拟链数据()

    ts = _time.strftime("%Y-%m-%d %H:%M:%S")
    online_nodes = network["metrics"]["online"]
    total_nodes = network["metrics"]["total_nodes"]
    current_circ = economy["circulating"][-1]
    current_apy = economy["apy"][-1]
    health = 78.5

    panel_names = {
        "consensus": {"icon": "⚡", "name": "PoEI共识仪表盘"},
        "economy": {"icon": "📊", "name": "经济仿真图表"},
        "bridge": {"icon": "🌉", "name": "跨链桥监控"},
        "network": {"icon": "🌐", "name": "P2P网络拓扑"},
        "wallet": {"icon": "💰", "name": "涌信钱包面板"},
        "guardian": {"icon": "🛡️", "name": "AI守护者大屏"},
        "explorer": {"icon": "🔍", "name": "区块浏览器"}
    }

    toc_items = []
    for pid in include_panels:
        if pid in panel_names:
            p = panel_names[pid]
            toc_items.append(
                '<a href="#section-' + pid + '" class="hkc-card" '
                'style="display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit">'
                '<span style="font-size:28px">' + p["icon"] + '</span>'
                '<span style="font-size:16px;font-weight:600;color:' + BRAND_GOLD + '">' + p["name"] + '</span></a>'
            )
    toc_html = "\n".join(toc_items)

    body = (
        '<div style="text-align:center;padding:40px 0 20px">'
        '<div style="font-size:42px;font-weight:700;color:' + BRAND_GOLD + ';letter-spacing:4px">Hongkun AI Chain</div>'
        '<div style="font-size:18px;color:' + BRAND_TEXT_DIM + ';margin:8px 0">v4.0.0 综合状态报告</div>'
        '<div style="font-size:13px;color:' + BRAND_TEXT_DIM + '">生成时间: ' + ts + '</div>'
        '</div>'
        '<div class="hkc-grid hkc-grid-4 animate-slide">'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(total_nodes) + '</div><div class="stat-label">网络节点</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{current_circ/1e6:.1f}" + 'M</div><div class="stat-label">HKAIC流通量</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{current_apy:.1f}" + '%</div><div class="stat-label">质押APY</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value" style="color:' + BRAND_GREEN + '">' + str(health) + '</div><div class="stat-label">健康指数</div></div></div>'
        '</div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 报告目录 — 点击跳转</div>'
        '<div class="hkc-grid hkc-grid-3" style="margin-top:8px">' + toc_html + '</div></div>'
    )

    if "consensus" in include_panels:
        body += _gen_consensus_section(nodes)
    if "economy" in include_panels:
        body += _gen_economy_section(economy)
    if "bridge" in include_panels:
        body += _gen_bridge_section(bridge)
    if "network" in include_panels:
        body += _gen_network_section(network)
    if "wallet" in include_panels:
        body += _gen_wallet_section(wallet)
    if "guardian" in include_panels:
        body += _gen_guardian_section(guardian)
    if "explorer" in include_panels:
        body += _gen_explorer_section(chain)

    extra_js = _gen_all_js(nodes, epochs, economy, dist, bridge, network, wallet, guardian, chain, include_panels)

    html_content = wrap_html(title=title, body_content=body, extra_js=extra_js)
    return save_html(html_content, output_path)


def _gen_consensus_section(nodes):
    gold_count = sum(1 for n in nodes if n["tier"] == "涌金")
    silver_count = sum(1 for n in nodes if n["tier"] == "涌银")
    total_E = sum(n["E_i"] for n in nodes) or 1
    bar_data = escape_js([{"label": n["name"][-5:], "value": n["E_i"], "color": n["color"]} for n in nodes])
    bar_colors = escape_js([n["color"] for n in nodes])
    pie_items = [{"label": n["name"][-5:], "value": round(n["E_i"]/total_E*100, 2)} for n in nodes[:8]]
    pie_items.append({"label": "其他", "value": round(sum(n["E_i"] for n in nodes[8:])/total_E*100, 2)})
    pie_data = escape_js(pie_items)

    return (
        '<div id="section-consensus" class="hkc-page-title" style="margin-top:40px">'
        '<span class="icon">⚡</span> PoEI 共识仪表盘</div>'
        '<div class="hkc-grid hkc-grid-3">'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(len(nodes)) + '</div><div class="stat-label">活跃节点</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value" style="color:#FFD700">' + str(gold_count) + '</div><div class="stat-label">涌金节点</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value" style="color:#C0C0C0">' + str(silver_count) + '</div><div class="stat-label">涌银节点</div></div></div>'
        '</div>'
        '<div class="hkc-grid hkc-grid-2">'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 涌现分数柱状图</div>'
        '<div class="chart-container" style="height:320px"><canvas id="r_barEmergence"></canvas></div></div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 出块权分布</div>'
        '<div class="chart-container" style="height:320px"><canvas id="r_pieBlock"></canvas></div></div>'
        '</div>'
    )


def _gen_economy_section(economy):
    current_circ = economy["circulating"][-1]
    current_stake = economy["staking"][-1]
    current_burn = economy["burned"][-1]
    current_apy = economy["apy"][-1]
    current_price = economy["price"][-1]
    health = 78.5

    step = max(1, len(economy["days"]) // 60)
    days_s = economy["days"][::step]
    circ_s = economy["circulating"][:len(days_s)]
    stake_s = economy["staking"][:len(days_s)]
    burn_s = economy["burned"][:len(days_s)]
    js_days = escape_js([str(d) for d in days_s])
    js_circ = escape_js(circ_s)
    js_stake = escape_js(stake_s)
    js_burn = escape_js(burn_s)

    circ_free = round(current_circ - current_stake, 0)
    unreleased = round(21_000_000 - current_circ, 0)
    asset_pie = escape_js([
        {"label": "流通中", "value": circ_free},
        {"label": "质押中", "value": round(current_stake, 0)},
        {"label": "已销毁", "value": round(current_burn, 0)},
        {"label": "未释放", "value": unreleased}
    ])

    return (
        '<div id="section-economy" class="hkc-page-title" style="margin-top:40px">'
        '<span class="icon">📊</span> 经济仿真图表</div>'
        '<div class="hkc-grid hkc-grid-4">'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{current_circ/1e6:.1f}" + 'M</div><div class="stat-label">流通量</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{current_stake/1e6:.1f}" + 'M</div><div class="stat-label">质押量</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{current_apy:.1f}" + '%</div><div class="stat-label">APY</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">$' + f"{current_price:.2f}" + '</div><div class="stat-label">价格</div></div></div>'
        '</div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 供应曲线</div>'
        '<div class="chart-container" style="height:300px"><canvas id="r_supplyChart"></canvas></div></div>'
        '<div class="hkc-grid hkc-grid-2">'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 经济健康指数</div>'
        '<div class="chart-container" style="height:250px"><canvas id="r_healthGauge"></canvas></div></div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 资产分布</div>'
        '<div class="chart-container" style="height:250px"><canvas id="r_assetPie"></canvas></div></div>'
        '</div>'
    )


def _gen_bridge_section(bridge):
    total_vol = sum(f["volume"] for f in bridge["flows"])
    pool_bal = bridge["pool_history"][-1]["balance"]
    radar_labels = ["信誉评分", "履约率", "响应速度", "ATH验证", "资金规模", "完成量"]
    top3 = bridge["solvers"][:3]
    radar_ds = escape_js([{
        "name": s["id"],
        "values": [s["reputation"], s["fulfill_rate"]*100, s["speed"]*50,
                   100 if s["ath_verified"] else 40, min(s["capital"]/50000, 100),
                   min(s["completed"]/20, 100)]
    } for s in top3])
    js_radar_labels = escape_js(radar_labels)

    return (
        '<div id="section-bridge" class="hkc-page-title" style="margin-top:40px">'
        '<span class="icon">🌉</span> 跨链桥监控</div>'
        '<div class="hkc-grid hkc-grid-3">'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{total_vol/1e6:.1f}" + 'M</div><div class="stat-label">跨链总量</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{pool_bal/1e6:.2f}" + 'M</div><div class="stat-label">保险池余额</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(len(bridge["solvers"])) + '</div><div class="stat-label">活跃Solver</div></div></div>'
        '</div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> Solver排行</div>'
        '<div class="chart-container" style="height:300px"><canvas id="r_solverRadar"></canvas></div></div>'
    )


def _gen_network_section(network):
    m = network["metrics"]
    nd = network["nodes"]
    edges = network["edges"]
    js_topo_nodes = escape_js([{"id": n["id"], "K_i": n["K_i"], "status": n["status"]} for n in nd])
    js_edges = escape_js(edges)

    return (
        '<div id="section-network" class="hkc-page-title" style="margin-top:40px">'
        '<span class="icon">🌐</span> P2P网络拓扑</div>'
        '<div class="hkc-grid hkc-grid-4">'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(m["total_nodes"]) + '</div><div class="stat-label">总节点</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value" style="color:#00E676">' + str(m["online"]) + '</div><div class="stat-label">在线</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(m["connectivity"]) + '%</div><div class="stat-label">连通度</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(m["avg_path_length"]) + '</div><div class="stat-label">平均路径</div></div></div>'
        '</div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 网络拓扑图</div>'
        '<div class="chart-container" style="height:400px"><canvas id="r_topoCanvas"></canvas></div></div>'
    )


def _gen_wallet_section(wallet):
    total = wallet["total"]
    credit = wallet["credit_score"]
    assets = wallet["assets"]
    js_asset = escape_js([{"label": a["type"], "value": a["amount"], "color": a["color"]} for a in assets])

    return (
        '<div id="section-wallet" class="hkc-page-title" style="margin-top:40px">'
        '<span class="icon">💰</span> 涌信钱包面板</div>'
        '<div class="hkc-grid hkc-grid-3">'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{total:,.0f}" + '</div><div class="stat-label">总资产</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value" style="color:#00E676">' + str(credit) + '</div><div class="stat-label">信用分</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + f"{wallet['staking_earnings'][-1]:.1f}" + '</div><div class="stat-label">累计收益</div></div></div>'
        '</div>'
        '<div class="hkc-grid hkc-grid-2">'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 资产分布</div>'
        '<div class="chart-container" style="height:260px"><canvas id="r_walletAsset"></canvas></div></div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 信用分</div>'
        '<div class="chart-container" style="height:260px"><canvas id="r_walletCredit"></canvas></div></div>'
        '</div>'
    )


def _gen_guardian_section(guardian):
    threats = guardian["threats"]
    js_threats = escape_js([{"label": t["type"], "value": t["count"]} for t in threats])

    return (
        '<div id="section-guardian" class="hkc-page-title" style="margin-top:40px">'
        '<span class="icon">🛡️</span> AI守护者大屏</div>'
        '<div class="hkc-grid hkc-grid-3">'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + guardian["guardian_level"] + '</div><div class="stat-label">守护等级</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value" style="color:#FF5252">' + str(guardian["intercepts_today"]) + '</div><div class="stat-label">今日拦截</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(len(guardian["events"])) + '</div><div class="stat-label">检测事件</div></div></div>'
        '</div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 威胁类型分布</div>'
        '<div class="chart-container" style="height:280px"><canvas id="r_threatPie"></canvas></div></div>'
    )


def _gen_explorer_section(chain):
    blocks = chain["blocks"]
    latest = blocks[0] if blocks else None
    total_tx = sum(b["tx_count"] for b in blocks)
    js_proposer = escape_js([{"label": b["proposer"][-5:], "value": b["E_i"]} for b in blocks[:15]])
    latest_height = latest["height"] if latest else 0

    return (
        '<div id="section-explorer" class="hkc-page-title" style="margin-top:40px">'
        '<span class="icon">🔍</span> 区块浏览器</div>'
        '<div class="hkc-grid hkc-grid-3">'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(latest_height) + '</div><div class="stat-label">最新区块</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">' + str(total_tx) + '</div><div class="stat-label">总交易数</div></div></div>'
        '<div class="hkc-card"><div class="stat-box"><div class="stat-value">12s</div><div class="stat-label">出块间隔</div></div></div>'
        '</div>'
        '<div class="hkc-card"><div class="hkc-card-title"><span class="dot"></span> 出块者涌现分数</div>'
        '<div class="chart-container" style="height:260px"><canvas id="r_proposerChart"></canvas></div></div>'
    )


def _gen_all_js(nodes, epochs, economy, dist, bridge, network, wallet, guardian, chain, panels):
    parts = []

    if "consensus" in panels:
        total_E = sum(n["E_i"] for n in nodes) or 1
        bar_data = escape_js([{"label": n["name"][-5:], "value": n["E_i"], "color": n["color"]} for n in nodes])
        bar_colors = escape_js([n["color"] for n in nodes])
        pie_items = [{"label": n["name"][-5:], "value": round(n["E_i"]/total_E*100, 2)} for n in nodes[:8]]
        pie_items.append({"label": "其他", "value": round(sum(n["E_i"] for n in nodes[8:])/total_E*100, 2)})
        pie_data = escape_js(pie_items)
        parts.append(
            "drawBarChart('r_barEmergence', " + bar_data + ", {title:'涌现分数E_i', barColors:" + bar_colors + ", showValues:false});\n"
            "drawPieChart('r_pieBlock', " + pie_data + ", {title:'出块权分布', donut:true});"
        )

    if "economy" in panels:
        step = max(1, len(economy["days"]) // 60)
        days_s = economy["days"][::step]
        circ_s = economy["circulating"][:len(days_s)]
        stake_s = economy["staking"][:len(days_s)]
        burn_s = economy["burned"][:len(days_s)]
        js_days = escape_js([str(d) for d in days_s])
        js_circ = escape_js(circ_s)
        js_stake = escape_js(stake_s)
        js_burn = escape_js(burn_s)
        current_circ = economy["circulating"][-1]
        current_stake = economy["staking"][-1]
        current_burn = economy["burned"][-1]
        circ_free = round(current_circ - current_stake, 0)
        unreleased = round(21_000_000 - current_circ, 0)
        asset_pie = escape_js([
            {"label": "流通中", "value": circ_free},
            {"label": "质押中", "value": round(current_stake, 0)},
            {"label": "已销毁", "value": round(current_burn, 0)},
            {"label": "未释放", "value": unreleased}
        ])
        parts.append(
            "drawLineChart('r_supplyChart', [\n"
            "  {name:'流通量', values:" + js_circ + ", labels:" + js_days + "},\n"
            "  {name:'质押量', values:" + js_stake + ", labels:" + js_days + "},\n"
            "  {name:'销毁量', values:" + js_burn + ", labels:" + js_days + "}\n"
            "], {title:'HKAIC供应量', fillArea:true});\n"
            "drawGauge('r_healthGauge', 78.5, 100, {title:'经济健康指数', unit:'分'});\n"
            "drawPieChart('r_assetPie', " + asset_pie + ", {title:'HKAIC分配'});"
        )

    if "bridge" in panels:
        radar_labels = ["信誉评分", "履约率", "响应速度", "ATH验证", "资金规模", "完成量"]
        top3 = bridge["solvers"][:3]
        radar_ds = escape_js([{
            "name": s["id"],
            "values": [s["reputation"], s["fulfill_rate"]*100, s["speed"]*50,
                       100 if s["ath_verified"] else 40, min(s["capital"]/50000, 100),
                       min(s["completed"]/20, 100)]
        } for s in top3])
        js_radar_labels = escape_js(radar_labels)
        parts.append(
            "drawRadarChart('r_solverRadar', " + radar_ds + ", {title:'Solver Top-3', sides:6, labels:" + js_radar_labels + ", maxVal:100});"
        )

    if "network" in panels:
        nd = network["nodes"]
        edges = network["edges"]
        js_topo_nodes = escape_js([{"id": n["id"], "K_i": n["K_i"], "status": n["status"]} for n in nd])
        js_edges = escape_js(edges)
        parts.append(
            "(function(){\n"
            "var c = initCanvas('r_topoCanvas'); if(!c) return;\n"
            "var ctx=c.ctx, w=c.w, h=c.h;\n"
            "var nodes=" + js_topo_nodes + ";\n"
            "var edges=" + js_edges + ";\n"
            "var cx=w/2, cy=h/2, r=Math.min(w,h)/2-60;\n"
            "var statusColors={'在线':'#00E676','同步中':'#FF9800','离线':'#FF5252'};\n"
            "nodes.forEach(function(n,i){var a=2*Math.PI*i/nodes.length;n.x=cx+r*0.8*Math.cos(a);n.y=cy+r*0.8*Math.sin(a);});\n"
            "edges.forEach(function(e){var s=nodes[e.source],t=nodes[e.target];ctx.beginPath();ctx.moveTo(s.x,s.y);ctx.lineTo(t.x,t.y);ctx.strokeStyle='rgba(255,215,0,'+e.weight*0.3+')';ctx.lineWidth=e.weight*2;ctx.stroke();});\n"
            "nodes.forEach(function(n){var nr=5+n.K_i/10;ctx.beginPath();ctx.arc(n.x,n.y,nr,0,Math.PI*2);ctx.fillStyle=statusColors[n.status]||'#FFD700';ctx.fill();});\n"
            "ctx.fillStyle='#FFD700';ctx.font='bold 14px sans-serif';ctx.textAlign='center';ctx.fillText('P2P网络拓扑',cx,20);\n"
            "})();"
        )

    if "wallet" in panels:
        assets = wallet["assets"]
        credit = wallet["credit_score"]
        js_asset = escape_js([{"label": a["type"], "value": a["amount"], "color": a["color"]} for a in assets])
        parts.append(
            "drawPieChart('r_walletAsset', " + js_asset + ", {title:'资产分布',donut:true});\n"
            "drawGauge('r_walletCredit', " + str(credit) + ", 1000, {title:'涌智信用分',unit:'',colors:['#FF5252','#FF9800','#FFEB3B','#00E676','#FFD700']});"
        )

    if "guardian" in panels:
        threats = guardian["threats"]
        js_threats = escape_js([{"label": t["type"], "value": t["count"]} for t in threats])
        parts.append(
            "drawPieChart('r_threatPie', " + js_threats + ", {title:'威胁类型分布',donut:true});"
        )

    if "explorer" in panels:
        blocks = chain["blocks"]
        js_proposer = escape_js([{"label": b["proposer"][-5:], "value": b["E_i"]} for b in blocks[:15]])
        parts.append(
            "drawBarChart('r_proposerChart', " + js_proposer + ", {title:'出块者涌现分数',barColor:'#FFD700',showValues:false});"
        )

    return "\n".join(parts)
