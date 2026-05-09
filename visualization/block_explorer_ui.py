"""
Hongkun AI Chain — 区块浏览器UI (block_explorer_ui.py)
======================================================
可视化区块链数据：最新区块、区块详情、交易详情、地址详情、搜索。
纯Python零依赖，生成自包含HTML。
"""

import math as _math
import random as _random
import hashlib as _hashlib
from typing import Dict, List, Optional, Any

from .html_template import (
    wrap_html, escape_js, save_html,
    BRAND_GOLD, BRAND_GREEN, BRAND_RED, BRAND_ORANGE, BRAND_CYAN
)


def _模拟链数据(区块数: int = 20, 每块交易数: int = 5) -> Dict:
    """生成模拟区块链数据"""
    blocks = []
    base_time = 1700000000
    for i in range(区块数):
        height = 区块数 - i
        proposer = f"HKC-Node-{_random.randint(1,21):02d}"
        tx_count = _random.randint(1, 每块交易数*2)
        E_i = round(_random.uniform(200, 1200), 1)
        gas_used = _random.randint(100000, 8000000)
        gas_limit = 8000000
        txs = []
        for j in range(tx_count):
            sender = f"0x{_hashlib.sha256(f's{j}'.encode()).hexdigest()[:8]}..."
            receiver = f"0x{_hashlib.sha256(f'r{j}'.encode()).hexdigest()[:8]}..."
            txs.append({
                "hash": f"0x{_hashlib.sha256(f'tx{height}{j}'.encode()).hexdigest()[:16]}...",
                "from": sender, "to": receiver,
                "amount": round(_random.uniform(1, 10000), 4),
                "gas": _random.randint(21000, 500000),
                "status": _random.choice(["成功", "成功", "成功", "失败"])
            })
        blocks.append({
            "height": height,
            "hash": f"0x{_hashlib.sha256(f'blk{height}'.encode()).hexdigest()[:16]}...",
            "proposer": proposer, "E_i": E_i,
            "tx_count": tx_count, "transactions": txs,
            "gas_used": gas_used, "gas_limit": gas_limit,
            "time": base_time + i * 12
        })

    addresses = []
    for k in range(10):
        addr = f"0x{_hashlib.sha256(f'addr{k}'.encode()).hexdigest()[:8]}...{_random.randint(0,0xFFFF):04x}"
        addresses.append({
            "address": addr,
            "balance": round(_random.uniform(100, 100000), 2),
            "tx_count": _random.randint(5, 200),
            "credit_score": _random.randint(300, 950),
            "E_i": round(_random.uniform(0, 800), 1)
        })

    return {"blocks": blocks, "addresses": addresses}


def generate_block_explorer_ui(
    chain_data: Optional[Dict] = None,
    output_path: str = "block_explorer_ui.html"
) -> str:
    """生成区块浏览器UI HTML"""
    if chain_data is None:
        chain_data = _模拟链数据()

    blocks = chain_data["blocks"]
    addrs = chain_data["addresses"]
    latest = blocks[0] if blocks else None
    total_tx = sum(b["tx_count"] for b in blocks)
    tps = round(total_tx / (len(blocks) * 12), 1) if blocks else 0

    # 预计算JS数据
    js_blocks = escape_js(blocks)
    js_proposer_bar = escape_js([{"label": b["proposer"][-5:], "value": b["E_i"]} for b in blocks[:15]])

    # 区块表格行
    block_rows = ""
    for b in blocks[:15]:
        gas_pct = b["gas_used"]*100//b["gas_limit"]
        block_rows += f'<tr style="cursor:pointer" onclick="showBlock({b["height"]})">'
        block_rows += f'<td style="color:{BRAND_GOLD};font-weight:600">{b["height"]}</td>'
        block_rows += f'<td style="font-family:monospace;font-size:11px">{b["hash"]}</td>'
        block_rows += f'<td>{b["proposer"]}</td>'
        block_rows += f'<td>{b["E_i"]}</td>'
        block_rows += f'<td>{b["tx_count"]}</td>'
        block_rows += f'<td>{gas_pct}%</td>'
        block_rows += f'<td>{b["time"]}</td></tr>\n'

    # 地址表格行
    addr_rows = ""
    for a in addrs:
        score_cls = "badge-gold" if a["credit_score"]>800 else ("badge-green" if a["credit_score"]>600 else "badge-orange")
        addr_rows += f'<tr><td style="font-family:monospace;font-size:11px">{a["address"]}</td>'
        addr_rows += f'<td>{a["balance"]} HKAIC</td>'
        addr_rows += f'<td>{a["tx_count"]}</td>'
        addr_rows += f'<td><span class="badge {score_cls}">{a["credit_score"]}</span></td>'
        addr_rows += f'<td>{a["E_i"]}</td></tr>\n'

    latest_height = latest['height'] if latest else 0

    body = f"""
    <div class="hkc-page-title"><span class="icon">🔍</span> 区块浏览器</div>
    <div class="hkc-subtitle">Block Explorer — 区块/交易/地址 搜索与浏览</div>

    <div class="hkc-card" style="margin-bottom:20px">
        <div style="display:flex;gap:12px;align-items:center">
            <input type="text" id="searchInput" placeholder="输入区块高度 / 交易哈希 / 地址..."
                style="flex:1;padding:12px 16px;background:#0D1B2A;border:1px solid #2A3F5F;
                border-radius:8px;color:#E0E6ED;font-size:14px;outline:none">
            <button onclick="doSearch()" style="padding:12px 24px;background:#FFD700;color:#0A1628;
                border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:14px">搜索</button>
        </div>
    </div>

    <div class="hkc-grid hkc-grid-4 animate-slide">
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{latest_height}</div><div class="stat-label">最新区块</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{total_tx}</div><div class="stat-label">总交易数</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">{tps}</div><div class="stat-label">TPS</div>
        </div></div>
        <div class="hkc-card"><div class="stat-box">
            <div class="stat-value">12s</div><div class="stat-label">出块间隔</div>
        </div></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 最新区块</div>
        <div style="overflow-x:auto">
        <table class="hkc-table" id="blockTable">
            <thead><tr><th>高度</th><th>区块哈希</th><th>出块者</th><th>E_i</th><th>交易数</th><th>Gas使用率</th><th>时间</th></tr></thead>
            <tbody>{block_rows}</tbody>
        </table>
        </div>
    </div>

    <div class="hkc-card" id="blockDetail" style="display:none">
        <div class="hkc-card-title"><span class="dot"></span> 区块详情</div>
        <div id="blockDetailContent"></div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 活跃地址</div>
        <div style="overflow-x:auto">
        <table class="hkc-table" id="addrTable">
            <thead><tr><th>地址</th><th>余额</th><th>交易数</th><th>信用分</th><th>E_i</th></tr></thead>
            <tbody>{addr_rows}</tbody>
        </table>
        </div>
    </div>

    <div class="hkc-card">
        <div class="hkc-card-title"><span class="dot"></span> 出块者涌现分数分布</div>
        <div class="chart-container" style="height:280px"><canvas id="proposerChart"></canvas></div>
    </div>
    """

    extra_js = f"""
    drawBarChart('proposerChart', {js_proposer_bar}, {{
        title: '出块者涌现分数',
        barColor: '#FFD700', showValues: false
    }});

    var allBlocks = {js_blocks};

    function doSearch() {{
        var q = document.getElementById('searchInput').value.trim();
        if (!q) return;
        var found = allBlocks.find(function(b) {{ return b.height == q || b.hash.startsWith(q); }});
        if (found) showBlock(found.height);
        else alert('未找到匹配的区块或交易: ' + q);
    }}

    function showBlock(height) {{
        var b = allBlocks.find(function(bl) {{ return bl.height === height; }});
        if (!b) return;
        var el = document.getElementById('blockDetail');
        var content = document.getElementById('blockDetailContent');
        var html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px">';
        html += '<div><span style="color:#8899AA">区块高度:</span> <b>' + b.height + '</b></div>';
        html += '<div><span style="color:#8899AA">哈希:</span> <code>' + b.hash + '</code></div>';
        html += '<div><span style="color:#8899AA">出块者:</span> ' + b.proposer + '</div>';
        html += '<div><span style="color:#8899AA">涌现分数:</span> <span style="color:#FFD700">' + b.E_i + '</span></div>';
        html += '<div><span style="color:#8899AA">交易数:</span> ' + b.tx_count + '</div>';
        html += '<div><span style="color:#8899AA">Gas:</span> ' + (b.gas_used*100/b.gas_limit).toFixed(1) + '%</div>';
        html += '</div>';
        html += '<table class="hkc-table"><thead><tr><th>交易哈希</th><th>发送</th><th>接收</th><th>金额</th><th>Gas</th><th>状态</th></tr></thead><tbody>';
        b.transactions.forEach(function(tx) {{
            html += '<tr><td style="font-family:monospace;font-size:11px">' + tx.hash + '</td>';
            html += '<td style="font-family:monospace;font-size:11px">' + tx.from + '</td>';
            html += '<td style="font-family:monospace;font-size:11px">' + tx.to + '</td>';
            html += '<td>' + tx.amount + '</td><td>' + tx.gas + '</td>';
            html += '<td><span class="badge ' + (tx.status==='成功'?'badge-green':'badge-red') + '">' + tx.status + '</span></td></tr>';
        }});
        html += '</tbody></table>';
        content.innerHTML = html;
        el.style.display = 'block';
        el.scrollIntoView({{behavior:'smooth'}});
    }}

    setupTableSort('blockTable');
    setupTableSort('addrTable');
    """

    html_content = wrap_html(
        title="HKC 区块浏览器",
        nav_active="explorer",
        body_content=body,
        extra_js=extra_js
    )
    return save_html(html_content, output_path)
