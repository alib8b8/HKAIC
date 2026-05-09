"""
Hongkun AI Chain — 经济仿真图表 (economy_charts.py)
====================================================
可视化HKAIC代币经济数据：供应曲线、通胀通缩、质押收益、分布直方图。
纯Python零依赖，生成自包含HTML。
"""

import math as _math
import random as _random
from typing import Dict, List, Optional, Any

from .html_template import (
    wrap_html, escape_js, save_html,
    BRAND_GOLD, BRAND_GREEN, BRAND_RED, BRAND_ORANGE, BRAND_CYAN
)

HKAIC_TOTAL = 21_000_000


def _模拟经济数据(天数: int = 365) -> Dict:
    """生成模拟经济仿真数据"""
    流通量 = 5_000_000
    质押量 = 3_000_000
    销毁量 = 0
    data = {"days": [], "circulating": [], "staking": [], "burned": [],
            "price": [], "apy": [], "gas": [], "inflation": [], "users": []}
    for d in range(天数):
        流通量 += _random.uniform(1000, 50000)
        质押量 += _random.uniform(-20000, 30000)
        质押量 = max(1000000, min(流通量*0.7, 质押量))
        销毁量 += _random.uniform(500, 8000)
        流通量 = min(流通量, HKAIC_TOTAL)
        price = 0.5 + _random.gauss(0, 0.05) + d * 0.001
        price = max(0.1, price)
        staking_ratio = 质押量 / 流通量 if 流通量 > 0 else 0
        apy = 0.15 / (1 + staking_ratio * 5)
        gas = 1.0 + _random.uniform(0, 2.0)
        data["days"].append(d+1)
        data["circulating"].append(round(流通量, 0))
        data["staking"].append(round(质押量, 0))
        data["burned"].append(round(销毁量, 0))
        data["price"].append(round(price, 4))
        data["apy"].append(round(apy*100, 2))
        data["gas"].append(round(gas, 2))
        data["inflation"].append(round(_random.uniform(-0.5, 1.5), 2))
        data["users"].append(1000 + d * 10 + _random.randint(-50, 50))
    return data


def _模拟持币分布() -> List[Dict]:
    """模拟持币地址分布"""
    return [
        {"range": "0-100", "count": 8500, "type": "散户"},
        {"range": "100-1K", "count": 2800, "type": "散户"},
        {"range": "1K-10K", "count": 900, "type": "中等"},
        {"range": "10K-100K", "count": 200, "type": "大户"},
        {"range": "100K-1M", "count": 45, "type": "鲸鱼"},
        {"range": "1M+", "count": 8, "type": "巨鲸"},
    ]


def generate_economy_charts(
    economy_data: Optional[Dict] = None,
    output_path: str = "economy_charts.html"
) -> str:
    """生成经济仿真图表HTML"""
    if economy_data is None:
        economy_data = _模拟经济数据()

    dist_data = _模拟持币分布()

    current_circ = economy_data["circulating"][-1]
    current_stake = economy_data["staking"][-1]
    current_burn = economy_data["burned"][-1]
    current_price = economy_data["price"][-1]
    current_apy = economy_data["apy"][-1]
    stake_ratio = current_stake / current_circ * 100 if current_circ > 0 else 0
    burn_ratio = current_burn / HKAIC_TOTAL * 100
    health = round(stake_ratio * 0.3 + (1 - burn_ratio/100) * 0.3 + min(current_apy/15, 1) * 0.2 + min(current_price, 1) * 0.2 * 100, 1)
    health = min(100, max(0, health))

    step = max(1, len(economy_data["days"]) // 90)
    days_s = economy_data["days"][::step]
    circ_s = economy_data["circulating"][::step]
    stake_s = economy_data["staking"][::step]
    burn_s = economy_data["burned"][::step]
    price_s = economy_data["price"][::step]
    apy_s = economy_data["apy"][::step]
    gas_s = economy_data["gas"][::step]
    infl_s = economy_data["inflation"][::step]

    # 预计算JS数据
    js_days = escape_js([str(d) for d in days_s])
    js_circ = escape_js(circ_s)
    js_stake = escape_js(stake_s)
    js_burn = escape_js(burn_s)
    js_apy = escape_js(apy_s)
    js_infl = escape_js(infl_s)
    js_gas = escape_js(gas_s)
    dist_bar_data = escape_js([{"label": d["range"], "value": d["count"],
        "color": "#FFD700" if d["type"] in ("鲸鱼","巨鲸") else "#00BCD4"} for d in dist_data])

    circ_free = round(current_circ - current_stake, 0)
    unreleased = round(HKAIC_TOTAL - current_circ, 0)
    asset_pie = escape_js([
        {"label": "流通中", "value": circ_free},
        {"label": "质押中", "value": round(current_stake, 0)},
        {"label": "已销毁", "value": round(current_burn, 0)},
        {"label": "未释放", "value": unreleased}
    ])

    body = f"""
    <div class="hkc-page-title"><span class="icon">📊</span> HKAIC 经济仿真图表</div>
    <div class="hkc-subtitle">代币经济可视化 — 供应/通胀/质押/分布/Gas</div>

    <div class="hkc-grid hkc-grid-4 animate-slide">
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{current_circ/1e6:.1f}M</div><div class="stat-label">流通量 HKAIC</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{current_stake/1e6:.1f}M</div><div class="stat-label">质押量</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{current_apy:.1f}%</div><div class="stat-label">当前APY</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">${current_price:.2f}</div><div class="stat-label">HKAIC价格</div>
        </div></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 代币供应曲线</div>
        <div class="chart-container" style="height:360px"><canvas id="supplyChart"></canvas></div>
        <div class="time-filter" id="tf-supply">
            <button data-range="30" class="active">30天</button>
            <button data-range="90">90天</button>
            <button data-range="365">1年</button>
        </div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 通胀/通缩指标</div>
            <div class="chart-container" style="height:300px"><canvas id="inflationChart"></canvas></div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 质押APY趋势</div>
            <div class="chart-container" style="height:300px"><canvas id="apyChart"></canvas></div>
        </div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> HKAIC持币分布</div>
            <div class="chart-container" style="height:300px"><canvas id="distChart"></canvas></div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> Gas费趋势</div>
            <div class="chart-container" style="height:300px"><canvas id="gasChart"></canvas></div>
        </div>
    </div>

    <div class="hkc-grid hkc-grid-2">
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 经济健康指数</div>
            <div class="chart-container" style="height:280px"><canvas id="healthGauge"></canvas></div>
        </div>
        <div class="hkc-card">
            <div class="hkc-card-title"><span class="dot"></span> 资产分布</div>
            <div class="chart-container" style="height:280px"><canvas id="assetPie"></canvas></div>
        </div>
    </div>
    """

    extra_js = f"""
    drawLineChart('supplyChart', [
        {{name:'流通量', values: {js_circ}, labels: {js_days}}},
        {{name:'质押量', values: {js_stake}, labels: {js_days}}},
        {{name:'销毁量', values: {js_burn}, labels: {js_days}}}
    ], {{ title: 'HKAIC供应量变化', fillArea: true }});

    drawLineChart('inflationChart', [
        {{name:'净发行率(%)', values: {js_infl}, labels: {js_days}}}
    ], {{ title: '月度通胀/通缩指标', lineColors: ['#FF9800'] }});

    drawLineChart('apyChart', [
        {{name:'APY(%)', values: {js_apy}, labels: {js_days}}}
    ], {{ title: '质押年化收益', lineColors: ['#00E676'], fillArea: true }});

    drawBarChart('distChart', {dist_bar_data}, {{
        title: '持币地址数', showValues: true
    }});

    drawLineChart('gasChart', [
        {{name:'Gas价格(Gwei)', values: {js_gas}, labels: {js_days}}}
    ], {{ title: '平均Gas价格', lineColors: ['#FF5252'] }});

    drawGauge('healthGauge', {health}, 100, {{
        title: '经济健康指数', unit: '分'
    }});

    drawPieChart('assetPie', {asset_pie}, {{
        title: 'HKAIC 2100万分配'
    }});
    """

    html_content = wrap_html(
        title="HKC 经济仿真图表",
        nav_active="economy",
        body_content=body,
        extra_js=extra_js
    )
    return save_html(html_content, output_path)
