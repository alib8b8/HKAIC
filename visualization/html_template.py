"""
Hongkun AI Chain — HTML模板引擎 (html_template.py)
====================================================
生成自包含HTML文件：内嵌CSS+JS，无外部依赖。
通用样式：深色主题，HKAIC品牌色（金色#FFD700 + 深蓝#0A1628）。
纯Python标准库，零外部依赖。
"""

import html as _html
import json as _json
import time as _time
from typing import Dict, List, Optional, Any


# ====== 品牌色 ======
BRAND_GOLD = "#FFD700"
BRAND_DEEP_BLUE = "#0A1628"
BRAND_DARK = "#0D1B2A"
BRAND_CARD = "#1B2838"
BRAND_BORDER = "#2A3F5F"
BRAND_TEXT = "#E0E6ED"
BRAND_TEXT_DIM = "#8899AA"
BRAND_GREEN = "#00E676"
BRAND_RED = "#FF5252"
BRAND_ORANGE = "#FF9800"
BRAND_YELLOW = "#FFEB3B"
BRAND_CYAN = "#00BCD4"


def escape_js(obj: Any) -> str:
    """将Python对象安全转为JS字面量"""
    return _json.dumps(obj, ensure_ascii=False, default=str)


def generate_head(title: str = "HKC 可视化", extra_css: str = "") -> str:
    """生成HTML <head> 部分，包含完整CSS"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_html.escape(title)}</title>
<style>
/* ====== HKC全局样式 ====== */
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: {BRAND_DEEP_BLUE};
    color: {BRAND_TEXT};
    line-height: 1.6;
    min-height: 100vh;
}}
a {{ color: {BRAND_GOLD}; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* 导航栏 */
.hkc-nav {{
    background: {BRAND_DARK};
    border-bottom: 2px solid {BRAND_GOLD};
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}}
.hkc-nav .logo {{
    font-size: 22px; font-weight: 700;
    color: {BRAND_GOLD};
    letter-spacing: 2px;
}}
.hkc-nav .logo span {{ color: {BRAND_TEXT}; font-weight: 300; font-size: 14px; margin-left: 8px; }}
.hkc-nav .nav-links {{ display:flex; gap:16px; flex-wrap:wrap; }}
.hkc-nav .nav-links a {{
    color: {BRAND_TEXT_DIM}; font-size:13px; padding:4px 8px;
    border-radius:4px; transition:all .2s;
}}
.hkc-nav .nav-links a:hover, .hkc-nav .nav-links a.active {{
    color: {BRAND_GOLD}; background: rgba(255,215,0,.1);
}}

/* 主容器 */
.hkc-container {{ max-width: 1440px; margin: 0 auto; padding: 24px; }}

/* 页面标题 */
.hkc-page-title {{
    font-size: 28px; font-weight: 700; color: {BRAND_GOLD};
    margin: 20px 0 8px;
    display: flex; align-items: center; gap: 12px;
}}
.hkc-page-title .icon {{ font-size: 32px; }}
.hkc-subtitle {{ color: {BRAND_TEXT_DIM}; font-size: 14px; margin-bottom: 24px; }}

/* 卡片 */
.hkc-card {{
    background: {BRAND_CARD};
    border: 1px solid {BRAND_BORDER};
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    transition: border-color .2s;
}}
.hkc-card:hover {{ border-color: {BRAND_GOLD}; }}
.hkc-card-title {{
    font-size: 16px; font-weight: 600;
    color: {BRAND_GOLD}; margin-bottom: 12px;
    display: flex; align-items: center; gap: 8px;
}}
.hkc-card-title .dot {{
    width:8px; height:8px; border-radius:50%;
    background: {BRAND_GOLD}; display:inline-block;
}}

/* 网格布局 */
.hkc-grid {{ display:grid; gap:20px; }}
.hkc-grid-2 {{ grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); }}
.hkc-grid-3 {{ grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }}
.hkc-grid-4 {{ grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}

/* 图表容器 */
.chart-container {{
    position: relative;
    width: 100%;
    min-height: 320px;
}}
.chart-container canvas {{
    width: 100%; height: 100%;
    display: block;
}}

/* 统计数字 */
.stat-box {{
    text-align: center; padding: 16px;
}}
.stat-value {{
    font-size: 32px; font-weight: 700; color: {BRAND_GOLD};
}}
.stat-label {{
    font-size: 12px; color: {BRAND_TEXT_DIM}; margin-top: 4px;
}}

/* 表格 */
.hkc-table {{
    width: 100%; border-collapse: collapse; font-size: 13px;
}}
.hkc-table th {{
    background: {BRAND_DARK}; color: {BRAND_GOLD};
    padding: 10px 12px; text-align: left; cursor: pointer;
    user-select: none; white-space: nowrap;
    border-bottom: 2px solid {BRAND_BORDER};
}}
.hkc-table th:hover {{ background: rgba(255,215,0,.1); }}
.hkc-table td {{
    padding: 8px 12px; border-bottom: 1px solid {BRAND_BORDER};
}}
.hkc-table tr:hover td {{ background: rgba(255,215,0,.03); }}

/* 徽章 */
.badge {{
    display:inline-block; padding:2px 8px; border-radius:10px;
    font-size:11px; font-weight:600;
}}
.badge-gold   {{ background:rgba(255,215,0,.2); color:{BRAND_GOLD}; }}
.badge-green  {{ background:rgba(0,230,118,.15); color:{BRAND_GREEN}; }}
.badge-red    {{ background:rgba(255,82,82,.15); color:{BRAND_RED}; }}
.badge-orange {{ background:rgba(255,152,0,.15); color:{BRAND_ORANGE}; }}
.badge-cyan   {{ background:rgba(0,188,212,.15); color:{BRAND_CYAN}; }}

/* Tooltip */
.hkc-tooltip {{
    position:absolute; pointer-events:none;
    background:rgba(13,27,42,.95); border:1px solid {BRAND_GOLD};
    border-radius:8px; padding:8px 12px;
    font-size:12px; color:{BRAND_TEXT};
    z-index:1000; white-space:nowrap;
    display:none;
}}

/* 时间筛选 */
.time-filter {{
    display:flex; gap:6px; margin-bottom:16px; flex-wrap:wrap;
}}
.time-filter button {{
    background:{BRAND_DARK}; color:{BRAND_TEXT_DIM};
    border:1px solid {BRAND_BORDER}; padding:6px 14px;
    border-radius:6px; cursor:pointer; font-size:12px;
    transition:all .2s;
}}
.time-filter button:hover, .time-filter button.active {{
    background:rgba(255,215,0,.15); color:{BRAND_GOLD};
    border-color:{BRAND_GOLD};
}}

/* 主题切换 */
.theme-toggle {{
    background:none; border:1px solid {BRAND_BORDER};
    color:{BRAND_TEXT_DIM}; padding:6px 10px;
    border-radius:6px; cursor:pointer; font-size:12px;
}}

/* 亮色主题覆盖 */
body.light {{
    background:#F0F2F5; color:#1A1A2E;
}}
body.light .hkc-card {{ background:#FFFFFF; border-color:#D0D5DD; }}
body.light .hkc-nav {{ background:#FFFFFF; border-bottom-color:{BRAND_GOLD}; }}
body.light .hkc-table th {{ background:#F8F9FA; color:#333; }}
body.light .hkc-table td {{ border-bottom-color:#E5E7EB; }}
body.light .hkc-page-title {{ color:#0A1628; }}
body.light .hkc-card-title {{ color:#0A1628; }}
body.light .stat-value {{ color:#0A1628; }}

/* 页脚 */
.hkc-footer {{
    text-align:center; padding:24px;
    color:{BRAND_TEXT_DIM}; font-size:12px;
    border-top:1px solid {BRAND_BORDER};
    margin-top:40px;
}}

/* 动画 */
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.5}} }}
@keyframes slideIn {{ from{{opacity:0;transform:translateY(20px)}} to{{opacity:1;transform:translateY(0)}} }}
.animate-pulse {{ animation: pulse 2s infinite; }}
.animate-slide {{ animation: slideIn .5s ease-out; }}

/* 响应式 */
@media(max-width:768px){{
    .hkc-container {{ padding:12px; }}
    .hkc-page-title {{ font-size:20px; }}
    .hkc-grid-2,.hkc-grid-3,.hkc-grid-4 {{ grid-template-columns:1fr; }}
    .stat-value {{ font-size:24px; }}
}}

/* 滚动条 */
::-webkit-scrollbar {{ width:8px; }}
::-webkit-scrollbar-track {{ background:{BRAND_DARK}; }}
::-webkit-scrollbar-thumb {{ background:{BRAND_BORDER}; border-radius:4px; }}
::-webkit-scrollbar-thumb:hover {{ background:{BRAND_GOLD}; }}

{extra_css}
</style>
</head>"""


def generate_nav(active: str = "", links: Optional[List[Dict]] = None) -> str:
    """生成导航栏"""
    if links is None:
        links = [
            {"name": "共识仪表盘", "href": "#consensus", "id": "consensus"},
            {"name": "经济图表", "href": "#economy", "id": "economy"},
            {"name": "跨链桥", "href": "#bridge", "id": "bridge"},
            {"name": "网络拓扑", "href": "#network", "id": "network"},
            {"name": "钱包面板", "href": "#wallet", "id": "wallet"},
            {"name": "守护大屏", "href": "#guardian", "id": "guardian"},
            {"name": "区块浏览器", "href": "#explorer", "id": "explorer"},
        ]
    link_html = ""
    for lk in links:
        cls = ' class="active"' if lk.get("id") == active else ""
        link_html += f'<a href="{_html.escape(lk["href"])}"{cls}>{_html.escape(lk["name"])}</a>\n'
    return f"""<nav class="hkc-nav">
    <div class="logo">HKC<span>v4.0.0 可视化</span></div>
    <div class="nav-links">{link_html}</div>
    <button class="theme-toggle" onclick="toggleTheme()">🌓 切换主题</button>
</nav>"""


def generate_footer() -> str:
    """生成页脚"""
    ts = _time.strftime("%Y-%m-%d %H:%M:%S")
    return f"""<footer class="hkc-footer">
    Hongkun AI Chain v4.0.0 — PoEI涌智证明 · ETB涌信桥 · ATH自主信任<br>
    报告生成时间: {ts} · 纯Python零依赖可视化
</footer>"""


# ====== 通用JS工具 ======
COMMON_JS = """
<script>
// ====== HKC通用JS工具 ======

// 主题切换
function toggleTheme() {
    document.body.classList.toggle('light');
    localStorage.setItem('hkc-theme', document.body.classList.contains('light') ? 'light' : 'dark');
}
(function() {
    if (localStorage.getItem('hkc-theme') === 'light') document.body.classList.add('light');
})();

// 时间筛选
function setupTimeFilter(containerId, callback) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', function() {
            el.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            if (callback) callback(this.dataset.range);
        });
    });
}

// Canvas高清适配
function initCanvas(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = Math.max(300, rect.height) * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = Math.max(300, rect.height) + 'px';
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return { ctx, w: rect.width, h: Math.max(300, rect.height), canvas };
}

// 绘制柱状图
function drawBarChart(canvasId, data, options) {
    const c = initCanvas(canvasId);
    if (!c) return;
    const { ctx, w, h } = c;
    const opts = Object.assign({
        title: '', padding: { top:40, right:20, bottom:60, left:60 },
        barColor: '#FFD700', barColors: null,
        labelColor: '#8899AA', valueColor: '#E0E6ED',
        gridColor: 'rgba(42,63,95,0.5)', showValues: true,
        animate: true
    }, options || {});
    ctx.clearRect(0, 0, w, h);
    const p = opts.padding;
    const cw = w - p.left - p.right;
    const ch = h - p.top - p.bottom;
    const maxVal = Math.max(...data.map(d => d.value), 1);
    // 标题
    if (opts.title) {
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center'; ctx.fillText(opts.title, w/2, 24);
    }
    // 网格线
    ctx.strokeStyle = opts.gridColor; ctx.lineWidth = 0.5;
    for (let i = 0; i <= 5; i++) {
        const y = p.top + ch - (ch * i / 5);
        ctx.beginPath(); ctx.moveTo(p.left, y); ctx.lineTo(p.left + cw, y); ctx.stroke();
        ctx.fillStyle = opts.labelColor; ctx.font = '11px sans-serif'; ctx.textAlign = 'right';
        ctx.fillText((maxVal * i / 5).toFixed(1), p.left - 8, y + 4);
    }
    // 柱子
    const barW = Math.max(8, cw / data.length * 0.6);
    const gap = cw / data.length;
    data.forEach((d, i) => {
        const x = p.left + gap * i + (gap - barW) / 2;
        const barH = (d.value / maxVal) * ch;
        const y = p.top + ch - barH;
        const color = opts.barColors ? (opts.barColors[i] || opts.barColor) : (d.color || opts.barColor);
        // 渐变
        const grad = ctx.createLinearGradient(x, y, x, p.top + ch);
        grad.addColorStop(0, color); grad.addColorStop(1, color + '44');
        ctx.fillStyle = grad;
        ctx.beginPath();
        const r = Math.min(4, barW / 4);
        ctx.moveTo(x + r, y); ctx.lineTo(x + barW - r, y);
        ctx.quadraticCurveTo(x + barW, y, x + barW, y + r);
        ctx.lineTo(x + barW, p.top + ch); ctx.lineTo(x, p.top + ch);
        ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.fill();
        // 值
        if (opts.showValues) {
            ctx.fillStyle = opts.valueColor; ctx.font = '11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(d.value.toFixed(1), x + barW/2, y - 6);
        }
        // 标签
        ctx.fillStyle = opts.labelColor; ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.save(); ctx.translate(x + barW/2, p.top + ch + 10);
        const lbl = d.label || '';
        if (lbl.length > 8) ctx.rotate(-0.4);
        ctx.fillText(lbl, 0, 0); ctx.restore();
    });
}

// 绘制折线图
function drawLineChart(canvasId, datasets, options) {
    const c = initCanvas(canvasId);
    if (!c) return;
    const { ctx, w, h } = c;
    const opts = Object.assign({
        title: '', padding: { top:40, right:20, bottom:40, left:60 },
        lineColors: ['#FFD700','#00E676','#00BCD4','#FF9800','#FF5252'],
        gridColor: 'rgba(42,63,95,0.5)', labelColor: '#8899AA',
        fillArea: true, smooth: true, showDots: true
    }, options || {});
    ctx.clearRect(0, 0, w, h);
    const p = opts.padding;
    const cw = w - p.left - p.right;
    const ch = h - p.top - p.bottom;
    // 收集全局范围
    let allVals = [];
    datasets.forEach(ds => allVals = allVals.concat(ds.values));
    const maxVal = Math.max(...allVals, 1);
    const minVal = Math.min(...allVals, 0);
    const range = maxVal - minVal || 1;
    // 标题
    if (opts.title) {
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center'; ctx.fillText(opts.title, w/2, 24);
    }
    // 网格
    ctx.strokeStyle = opts.gridColor; ctx.lineWidth = 0.5;
    for (let i = 0; i <= 5; i++) {
        const y = p.top + ch - (ch * i / 5);
        ctx.beginPath(); ctx.moveTo(p.left, y); ctx.lineTo(p.left + cw, y); ctx.stroke();
        ctx.fillStyle = opts.labelColor; ctx.font = '11px sans-serif'; ctx.textAlign = 'right';
        ctx.fillText((minVal + range * i / 5).toFixed(1), p.left - 8, y + 4);
    }
    // X轴标签
    const labels = datasets[0]?.labels || [];
    const n = labels.length;
    if (n > 0) {
        ctx.fillStyle = opts.labelColor; ctx.font = '10px sans-serif'; ctx.textAlign = 'center';
        const step = Math.max(1, Math.floor(n / 10));
        for (let i = 0; i < n; i += step) {
            const x = p.left + (i / (n - 1 || 1)) * cw;
            ctx.fillText(labels[i], x, p.top + ch + 20);
        }
    }
    // 折线
    datasets.forEach((ds, di) => {
        const color = opts.lineColors[di % opts.lineColors.length];
        const vals = ds.values;
        const points = vals.map((v, i) => ({
            x: p.left + (i / (vals.length - 1 || 1)) * cw,
            y: p.top + ch - ((v - minVal) / range) * ch
        }));
        // 面积填充
        if (opts.fillArea && points.length > 1) {
            ctx.beginPath(); ctx.moveTo(points[0].x, p.top + ch);
            points.forEach(pt => ctx.lineTo(pt.x, pt.y));
            ctx.lineTo(points[points.length-1].x, p.top + ch); ctx.closePath();
            const grd = ctx.createLinearGradient(0, p.top, 0, p.top + ch);
            grd.addColorStop(0, color + '33'); grd.addColorStop(1, color + '05');
            ctx.fillStyle = grd; ctx.fill();
        }
        // 线条
        if (points.length > 1) {
            ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = 2;
            if (opts.smooth && points.length > 2) {
                ctx.moveTo(points[0].x, points[0].y);
                for (let i = 1; i < points.length - 1; i++) {
                    const xc = (points[i].x + points[i+1].x) / 2;
                    const yc = (points[i].y + points[i+1].y) / 2;
                    ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
                }
                ctx.lineTo(points[points.length-1].x, points[points.length-1].y);
            } else {
                points.forEach((pt, i) => i === 0 ? ctx.moveTo(pt.x, pt.y) : ctx.lineTo(pt.x, pt.y));
            }
            ctx.stroke();
        }
        // 点
        if (opts.showDots) {
            points.forEach(pt => {
                ctx.beginPath(); ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
                ctx.fillStyle = color; ctx.fill();
            });
        }
    });
    // 图例
    datasets.forEach((ds, i) => {
        const x = p.left + i * 120;
        const y = p.top - 12;
        ctx.fillStyle = opts.lineColors[i % opts.lineColors.length];
        ctx.fillRect(x, y - 6, 12, 3);
        ctx.fillStyle = '#8899AA'; ctx.font = '11px sans-serif'; ctx.textAlign = 'left';
        ctx.fillText(ds.name || '', x + 16, y);
    });
}

// 绘制饼图/环形图
function drawPieChart(canvasId, data, options) {
    const c = initCanvas(canvasId);
    if (!c) return;
    const { ctx, w, h } = c;
    const opts = Object.assign({
        title: '', donut: true, innerRatio: 0.55,
        colors: ['#FFD700','#00E676','#00BCD4','#FF9800','#FF5252','#9C27B0','#3F51B5','#E91E63'],
        labelColor: '#E0E6ED', showLabels: true, showPercent: true
    }, options || {});
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2;
    const cy = h / 2;
    const r = Math.min(w, h) / 2 - 40;
    const ir = opts.donut ? r * opts.innerRatio : 0;
    const total = data.reduce((s, d) => s + d.value, 0) || 1;
    // 标题
    if (opts.title) {
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center'; ctx.fillText(opts.title, cx, 24);
    }
    let angle = -Math.PI / 2;
    data.forEach((d, i) => {
        const sweep = (d.value / total) * Math.PI * 2;
        const color = d.color || opts.colors[i % opts.colors.length];
        ctx.beginPath();
        ctx.arc(cx, cy, r, angle, angle + sweep);
        ctx.arc(cx, cy, ir, angle + sweep, angle, true);
        ctx.closePath();
        ctx.fillStyle = color; ctx.fill();
        ctx.strokeStyle = '#0A1628'; ctx.lineWidth = 2; ctx.stroke();
        // 标签引导线
        if (opts.showLabels && sweep > 0.15) {
            const mid = angle + sweep / 2;
            const lx = cx + (r + 20) * Math.cos(mid);
            const ly = cy + (r + 20) * Math.sin(mid);
            const lx2 = cx + (r + 40) * Math.cos(mid);
            ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = 1;
            ctx.moveTo(cx + r * Math.cos(mid), cy + r * Math.sin(mid));
            ctx.lineTo(lx, ly); ctx.lineTo(lx2, ly); ctx.stroke();
            ctx.fillStyle = opts.labelColor; ctx.font = '11px sans-serif';
            ctx.textAlign = mid > Math.PI/2 && mid < Math.PI*1.5 ? 'right' : 'left';
            const pct = ((d.value / total) * 100).toFixed(1) + '%';
            ctx.fillText((d.label || '') + (opts.showPercent ? ' ' + pct : ''), lx2 + (ctx.textAlign==='left'?4:-4), ly + 4);
        }
        angle += sweep;
    });
    // 中心文字
    if (opts.donut) {
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 20px sans-serif';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(total.toFixed(0), cx, cy - 6);
        ctx.fillStyle = '#8899AA'; ctx.font = '11px sans-serif';
        ctx.fillText('总计', cx, cy + 14);
    }
}

// 绘制仪表盘
function drawGauge(canvasId, value, maxValue, options) {
    const c = initCanvas(canvasId);
    if (!c) return;
    const { ctx, w, h } = c;
    const opts = Object.assign({
        title: '', startAngle: Math.PI * 0.8, endAngle: Math.PI * 0.2,
        colors: ['#FF5252','#FF9800','#FFEB3B','#00E676','#FFD700'],
        labelColor: '#E0E6ED', unit: '', size: 0.7
    }, options || {});
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2;
    const cy = h * 0.55;
    const r = Math.min(w, h) * opts.size / 2;
    const ratio = Math.min(value / (maxValue || 1), 1);
    const totalAngle = Math.PI * 1.4;
    // 背景弧
    ctx.beginPath(); ctx.arc(cx, cy, r, opts.startAngle, Math.PI * 2 + opts.endAngle);
    ctx.strokeStyle = '#2A3F5F'; ctx.lineWidth = 20; ctx.lineCap = 'round'; ctx.stroke();
    // 渐变弧
    const valAngle = opts.startAngle + totalAngle * ratio;
    const grad = ctx.createLinearGradient(cx - r, cy, cx + r, cy);
    opts.colors.forEach((c, i) => grad.addColorStop(i / (opts.colors.length - 1), c));
    ctx.beginPath(); ctx.arc(cx, cy, r, opts.startAngle, valAngle);
    ctx.strokeStyle = grad; ctx.lineWidth = 20; ctx.lineCap = 'round'; ctx.stroke();
    // 数值
    ctx.fillStyle = '#FFD700'; ctx.font = 'bold 28px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(value.toFixed(0) + opts.unit, cx, cy);
    // 标签
    if (opts.title) {
        ctx.fillStyle = '#8899AA'; ctx.font = '12px sans-serif';
        ctx.fillText(opts.title, cx, cy + 30);
    }
    // 刻度
    for (let i = 0; i <= 10; i++) {
        const a = opts.startAngle + totalAngle * i / 10;
        const x1 = cx + (r - 15) * Math.cos(a);
        const y1 = cy + (r - 15) * Math.sin(a);
        const x2 = cx + (r + 2) * Math.cos(a);
        const y2 = cy + (r + 2) * Math.sin(a);
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
        ctx.strokeStyle = '#8899AA'; ctx.lineWidth = 1; ctx.stroke();
    }
}

// 绘制雷达图
function drawRadarChart(canvasId, datasets, options) {
    const c = initCanvas(canvasId);
    if (!c) return;
    const { ctx, w, h } = c;
    const opts = Object.assign({
        title: '', sides: 5, levels: 5,
        colors: ['#FFD700','#00E676','#00BCD4'],
        labels: [], maxVal: 100, gridColor: 'rgba(42,63,95,0.5)'
    }, options || {});
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2; const cy = h / 2;
    const r = Math.min(w, h) / 2 - 50;
    const n = opts.sides;
    const step = Math.PI * 2 / n;
    // 网格
    for (let lv = 1; lv <= opts.levels; lv++) {
        const lr = r * lv / opts.levels;
        ctx.beginPath();
        for (let i = 0; i < n; i++) {
            const a = -Math.PI/2 + step * i;
            const x = cx + lr * Math.cos(a);
            const y = cy + lr * Math.sin(a);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle = opts.gridColor; ctx.lineWidth = 0.5; ctx.stroke();
    }
    // 轴线 + 标签
    for (let i = 0; i < n; i++) {
        const a = -Math.PI/2 + step * i;
        ctx.beginPath(); ctx.moveTo(cx, cy);
        ctx.lineTo(cx + r * Math.cos(a), cy + r * Math.sin(a));
        ctx.strokeStyle = opts.gridColor; ctx.lineWidth = 0.5; ctx.stroke();
        if (opts.labels[i]) {
            ctx.fillStyle = '#8899AA'; ctx.font = '11px sans-serif';
            ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(opts.labels[i], cx + (r + 20) * Math.cos(a), cy + (r + 20) * Math.sin(a));
        }
    }
    // 数据
    datasets.forEach((ds, di) => {
        const color = opts.colors[di % opts.colors.length];
        ctx.beginPath();
        ds.values.forEach((v, i) => {
            const a = -Math.PI/2 + step * i;
            const vr = r * Math.min(v / opts.maxVal, 1);
            const x = cx + vr * Math.cos(a);
            const y = cy + vr * Math.sin(a);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
        ctx.closePath();
        ctx.fillStyle = color + '33'; ctx.fill();
        ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
        // 顶点
        ds.values.forEach((v, i) => {
            const a = -Math.PI/2 + step * i;
            const vr = r * Math.min(v / opts.maxVal, 1);
            ctx.beginPath(); ctx.arc(cx + vr * Math.cos(a), cy + vr * Math.sin(a), 3, 0, Math.PI*2);
            ctx.fillStyle = color; ctx.fill();
        });
    });
    // 标题
    if (opts.title) {
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center'; ctx.fillText(opts.title, cx, 20);
    }
}

// 绘制热力图
function drawHeatmap(canvasId, matrix, options) {
    const c = initCanvas(canvasId);
    if (!c) return;
    const { ctx, w, h } = c;
    const opts = Object.assign({
        title: '', rowLabels: [], colLabels: [],
        colorLow: '#0A1628', colorHigh: '#FFD700',
        labelColor: '#8899AA'
    }, options || {});
    ctx.clearRect(0, 0, w, h);
    const rows = matrix.length;
    const cols = matrix[0]?.length || 1;
    const pL = 80, pT = 40, pR = 20, pB = 40;
    const cw = (w - pL - pR) / cols;
    const ch = (h - pT - pB) / rows;
    let maxV = -Infinity, minV = Infinity;
    matrix.forEach(row => row.forEach(v => { if(v>maxV)maxV=v; if(v<minV)minV=v; }));
    const range = maxV - minV || 1;
    // 绘制格子
    matrix.forEach((row, ri) => {
        row.forEach((v, ci) => {
            const t = (v - minV) / range;
            const r0 = parseInt(opts.colorLow.slice(1,3),16);
            const g0 = parseInt(opts.colorLow.slice(3,5),16);
            const b0 = parseInt(opts.colorLow.slice(5,7),16);
            const r1 = parseInt(opts.colorHigh.slice(1,3),16);
            const g1 = parseInt(opts.colorHigh.slice(3,5),16);
            const b1 = parseInt(opts.colorHigh.slice(5,7),16);
            const cr = Math.round(r0 + (r1-r0)*t);
            const cg = Math.round(g0 + (g1-g0)*t);
            const cb = Math.round(b0 + (b1-b0)*t);
            ctx.fillStyle = 'rgb('+cr+','+cg+','+cb+')';
            ctx.fillRect(pL + ci*cw, pT + ri*ch, cw-1, ch-1);
        });
    });
    // 标签
    ctx.fillStyle = opts.labelColor; ctx.font = '10px sans-serif';
    (opts.rowLabels||[]).forEach((l,i) => {
        ctx.textAlign = 'right'; ctx.fillText(l, pL-4, pT + i*ch + ch/2 + 4);
    });
    (opts.colLabels||[]).forEach((l,i) => {
        ctx.textAlign = 'center'; ctx.fillText(l, pL + i*cw + cw/2, pT - 6);
    });
    if (opts.title) {
        ctx.fillStyle = '#FFD700'; ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'center'; ctx.fillText(opts.title, w/2, 20);
    }
}

// 导出PNG
function exportPNG(canvasId, filename) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = filename || 'hkc-chart.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
}

// 表格排序
function setupTableSort(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const headers = table.querySelectorAll('th');
    headers.forEach((th, colIdx) => {
        th.addEventListener('click', () => {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const asc = th.dataset.sort !== 'asc';
            table.querySelectorAll('th').forEach(h => delete h.dataset.sort);
            th.dataset.sort = asc ? 'asc' : 'desc';
            rows.sort((a, b) => {
                const aVal = a.children[colIdx]?.textContent || '';
                const bVal = b.children[colIdx]?.textContent || '';
                const aNum = parseFloat(aVal); const bNum = parseFloat(bVal);
                if (!isNaN(aNum) && !isNaN(bNum)) return asc ? aNum - bNum : bNum - aNum;
                return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            });
            rows.forEach(r => tbody.appendChild(r));
        });
    });
}

// 窗口resize重绘
let _resizeTimers = {};
function onResizeRedraw(canvasId, drawFn, delay) {
    window.addEventListener('resize', () => {
        clearTimeout(_resizeTimers[canvasId]);
        _resizeTimers[canvasId] = setTimeout(drawFn, delay || 200);
    });
}
</script>
"""


def wrap_html(title: str, nav_active: str = "",
              body_content: str = "",
              extra_css: str = "",
              extra_js: str = "") -> str:
    """组装完整HTML页面"""
    return (generate_head(title, extra_css) +
            "<body>\n" +
            generate_nav(nav_active) +
            f'<div class="hkc-container">\n{body_content}\n</div>\n' +
            generate_footer() +
            COMMON_JS +
            (f"<script>\n{extra_js}\n</script>" if extra_js else "") +
            "\n</body></html>")


def save_html(content: str, filepath: str) -> str:
    """保存HTML到文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath
