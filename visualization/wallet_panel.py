"""
Hongkun AI Chain — 涌信钱包面板 (wallet_panel.py)
==================================================
可视化涌信钱包数据：资产分布、信用分、交易历史、收益走势。
纯Python零依赖，生成自包含HTML。
"""

import math as _math
import random as _random
from typing import Dict, List, Optional, Any

from .html_template import (
    wrap_html, escape_js, save_html,
    BRAND_GOLD, BRAND_GREEN, BRAND_RED, BRAND_ORANGE, BRAND_CYAN
)


def _模拟钱包数据() -> Dict:
    """生成模拟钱包数据"""
    assets = [
        {"type": "HKAIC持仓", "amount": 52800, "color": BRAND_GOLD},
        {"type": "质押中", "amount": 35000, "color": BRAND_GREEN},
        {"type": "跨链资产", "amount": 12000, "color": BRAND_CYAN},
        {"type": "待领取收益", "amount": 3200, "color": BRAND_ORANGE}
    ]
    total = sum(a["amount"] for a in assets)
    credit_score = _random.randint(650, 920)

    tx_types = ["转账", "质押", "解除质押", "跨链转出", "跨链转入", "合约交互"]
    transactions = []
    for i in range(20):
        tx_type = _random.choice(tx_types)
        risk = _random.choice(["安全", "安全", "安全", "注意", "警告"])
        transactions.append({
            "hash": f"0x{_random.randint(0,0xFFFFFF):06x}...{_random.randint(0,0xFF):02x}",
            "type": tx_type, "amount": round(_random.uniform(10, 5000), 2),
            "time": f"2小时前" if i < 3 else f"{i+1}天前",
            "risk": risk,
            "counterparty": f"0x{_random.randint(0,0xFFFF):04x}...{_random.randint(0,0xFFFF):04x}"
        })

    staking_earnings = []
    bridge_earnings = []
    cumulative_stake = 0
    cumulative_bridge = 0
    for d in range(30):
        cumulative_stake += _random.uniform(5, 50)
        cumulative_bridge += _random.uniform(0, 20)
        staking_earnings.append(round(cumulative_stake, 2))
        bridge_earnings.append(round(cumulative_bridge, 2))

    gas_weekly = [
        {"week": f"W{i+1}", "gas": round(_random.uniform(5, 35), 1)}
        for i in range(12)
    ]

    return {
        "assets": assets, "total": total,
        "credit_score": credit_score,
        "transactions": transactions,
        "staking_earnings": staking_earnings,
        "bridge_earnings": bridge_earnings,
        "gas_weekly": gas_weekly
    }


def generate_wallet_panel(
    wallet_data: Optional[Dict] = None,
    output_path: str = "wallet_panel.html"
) -> str:
    """生成涌信钱包面板HTML"""
    if wallet_data is None:
        wallet_data = _模拟钱包数据()

    assets = wallet_data["assets"]
    total = wallet_data["total"]
    credit = wallet_data["credit_score"]
    txs = wallet_data["transactions"]

    # 预计算JS数据
    js_asset_pie = escape_js([{"label": a["type"], "value": a["amount"], "color": a["color"]} for a in assets])
    js_staking = escape_js(wallet_data["staking_earnings"])
    js_bridge_earn = escape_js(wallet_data["bridge_earnings"])
    js_earn_days = escape_js([str(d+1) for d in range(30)])
    js_gas_bar = escape_js([{"label": g["week"], "value": g["gas"]} for g in wallet_data["gas_weekly"]])

    # 交易表格
    tx_rows = ""
    for t in txs:
        risk_cls = "badge-green" if t["risk"]=="安全" else ("badge-orange" if t["risk"]=="注意" else "badge-red")
        tx_rows += f'<tr><td style="font-family:monospace;font-size:11px">{t["hash"]}</td>'
        tx_rows += f'<td><span class="badge badge-cyan">{t["type"]}</span></td>'
        tx_rows += f'<td>{t["amount"]}</td>'
        tx_rows += f'<td style="font-family:monospace;font-size:11px">{t["counterparty"]}</td>'
        tx_rows += f'<td><span class="badge {risk_cls}">{t["risk"]}</span></td>'
        tx_rows += f'<td>{t["time"]}</td></tr>\n'

    body = f"""
    <div class="hkc-page-title"><span class="icon">💰</span> 涌信钱包面板</div>
    <div class="hkc-subtitle">Emergent Wallet — 资产/信用/交易/收益/Gas</div>

    <div class="hkc-grid hkc-grid-4 animate-slide">
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{total:,.0f}</div><div class="stat-label">总资产 HKAIC</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value" style="color:{BRAND_GREEN}">{credit}</div><div class="stat-label">涌智信用分</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{assets[0]["amount"]:,.0f}</div><div class="stat-label">可用余额</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{assets[1]["amount"]:,.0f}</div><div class="stat-label">质押中</div>
        </div></div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 资产分布</div>
            <div class="chart-container" style="height:320px"><canvas id="assetPie"></canvas></div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 涌智信用分</div>
            <div class="chart-container" style="height:320px"><canvas id="creditGauge"></canvas></div>
        </div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 收益累积走势</div>
        <div class="chart-container" style="height:300px"><canvas id="earningChart"></canvas></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 周度Gas消耗</div>
        <div class="chart-container" style="height:260px"><canvas id="gasBar"></canvas></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 交易历史</div>
        <div style="overflow-x:auto;max-height:300px;overflow-y:auto">
        <table class="hkc-table" id="txTable">
            <thead><tr><th>交易哈希</th><th>类型</th><th>金额</th><th>对方</th><th>AI风险</th><th>时间</th></tr></thead>
            <tbody>{tx_rows}</tbody>
        </table>
        </div>
    </div>
    """

    extra_js = f"""
    drawPieChart('assetPie', {js_asset_pie}, {{
        title: '资产分布', donut: true
    }});

    drawGauge('creditGauge', {credit}, 1000, {{
        title: '涌智信用分 (0-1000)', unit: '',
        startAngle: Math.PI * 0.8, endAngle: Math.PI * 0.2,
        colors: ['#FF5252', '#FF9800', '#FFEB3B', '#00E676', '#FFD700']
    }});

    drawLineChart('earningChart', [
        {{name: '质押收益', values: {js_staking}, labels: {js_earn_days}}},
        {{name: '跨链收益', values: {js_bridge_earn}, labels: {js_earn_days}}}
    ], {{ title: '30天累积收益(HKAIC)', fillArea: true }});

    drawBarChart('gasBar', {js_gas_bar}, {{
        title: '周度Gas消耗(Gwei)', barColor: '#FF5252', showValues: true
    }});

    setupTableSort('txTable');
    """

    html_content = wrap_html(
        title="HKC 涌信钱包",
        nav_active="wallet",
        body_content=body,
        extra_js=extra_js
    )
    return save_html(html_content, output_path)
