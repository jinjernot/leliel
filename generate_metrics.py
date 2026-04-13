"""
Standalone metrics report generator.

Reads all JSON files from the metrics/ directory and renders a self-contained
HTML report — no Flask server required.

Usage:
    python generate_metrics.py
    python generate_metrics.py --days 14
    python generate_metrics.py --days 30 --out report.html
    python generate_metrics.py --metrics-dir /path/to/metrics

Output:
    metrics_report.html  (or whatever --out specifies)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from jinja2 import Environment

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ── Data loading ──────────────────────────────────────────────────────────────

def _empty_day():
    return {
        "server_id": "",
        "page_views": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "errors": 0,
        "top_skus": {},
        "top_locales": {},
        "top_product_types": {},
        "top_families": {},
        "error_details": [],
    }


def _merge_day(base, extra):
    for key in ("page_views", "cache_hits", "cache_misses", "errors"):
        base[key] = base.get(key, 0) + extra.get(key, 0)
    for key in ("top_skus", "top_locales", "top_product_types", "top_families"):
        for k, v in extra.get(key, {}).items():
            base.setdefault(key, {})[k] = base.get(key, {}).get(k, 0) + v
    base["error_details"] = (
        base.get("error_details", []) + extra.get("error_details", [])
    )[-100:]
    servers     = base.get("server_id", "")
    extra_svr   = extra.get("server_id", "")
    if extra_svr and extra_svr not in servers:
        base["server_id"] = f"{servers}, {extra_svr}" if servers else extra_svr


def get_summary(metrics_dir: str, days: int = 7) -> list:
    """Return list of day dicts merged across servers, newest-first."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    by_date: dict = {}

    if not os.path.exists(metrics_dir):
        logging.warning(f"Metrics directory not found: {metrics_dir}")
        return []

    for fname in os.listdir(metrics_dir):
        if not fname.endswith(".json"):
            continue
        date = fname[:10]
        if date < cutoff:
            continue
        try:
            with open(os.path.join(metrics_dir, fname), "r", encoding="utf-8") as f:
                day_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"Skipping {fname}: {e}")
            continue
        if date not in by_date:
            by_date[date] = {**_empty_day(), "date": date}
        _merge_day(by_date[date], day_data)

    sorted_days = sorted(by_date.values(), key=lambda d: d["date"], reverse=True)
    return sorted_days[:days]


# ── HTML template ─────────────────────────────────────────────────────────────

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FRAME — Metrics Report ({{ generated_at }})</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons/font/bootstrap-icons.css">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #f4f4f9;
      color: #333;
      line-height: 1.6;
    }
    a { text-decoration: none; color: inherit; }
    .wrapper { max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem 3rem; }

    /* ── Header ── */
    .page-header {
      display: flex;
      align-items: baseline;
      gap: 1rem;
      flex-wrap: wrap;
      margin-bottom: 1.5rem;
    }
    .page-title {
      font-size: 1.8rem;
      font-weight: 700;
      color: #024ad8;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .page-meta { font-size: 0.82rem; color: #999; }

    /* ── Day filter ── */
    .day-filter { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 1.75rem; }
    .day-filter a {
      padding: 4px 14px;
      border-radius: 20px;
      border: 1px solid #ddd;
      font-size: 0.82rem;
      font-weight: 500;
      color: #555;
    }
    .day-filter a.active { background: #024ad8; border-color: #024ad8; color: #fff; }

    /* ── Stat cards ── */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }
    .stat-card {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 1.25rem 1.5rem;
      box-shadow: 0 2px 5px rgba(0,0,0,.05);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .stat-label {
      font-size: 0.78rem;
      color: #888;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: .04em;
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .stat-value { font-size: 2rem; font-weight: 700; color: #024ad8; line-height: 1.1; }
    .stat-sub   { font-size: 0.78rem; color: #aaa; }

    /* ── Charts ── */
    .charts-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.25rem;
      margin-bottom: 1.25rem;
    }
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.25rem;
      margin-bottom: 2rem;
    }
    .chart-card {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      padding: 1.25rem 1.5rem;
      box-shadow: 0 2px 5px rgba(0,0,0,.05);
    }
    .chart-card-title {
      font-size: 0.78rem;
      font-weight: 600;
      color: #555;
      text-transform: uppercase;
      letter-spacing: .04em;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .chart-wrap { position: relative; }

    /* ── Tables ── */
    .card {
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      box-shadow: 0 2px 5px rgba(0,0,0,.05);
      overflow: hidden;
    }
    .metrics-table { width: 100%; border-collapse: collapse; font-size: .9rem; }
    .metrics-table th {
      text-align: left;
      padding: 8px 12px;
      background: #f5f7ff;
      border-bottom: 2px solid #024ad8;
      font-weight: 600;
      color: #333;
      white-space: nowrap;
    }
    .metrics-table td {
      padding: 8px 12px;
      border-bottom: 1px solid #eee;
      vertical-align: middle;
    }
    .metrics-table tr:last-child td { border-bottom: none; }
    .metrics-table tr:hover td { background: #fafbff; }
    .badge-hit  { color: #1a7f37; font-weight: 600; }
    .badge-miss { color: #024ad8; font-weight: 600; }
    .badge-err  { color: #d1242f; font-weight: 600; }

    /* ── Inline spark bars ── */
    .spark-bar {
      height: 6px;
      background: #eef0f8;
      border-radius: 3px;
      overflow: hidden;
      min-width: 60px;
    }
    .spark-bar-fill { height: 100%; border-radius: 3px; background: #024ad8; }

    .section-title {
      font-size: 1.05rem;
      font-weight: 600;
      margin: 2rem 0 .75rem;
      color: #333;
      border-bottom: 2px solid #024ad8;
      padding-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 7px;
    }
    .empty-state { color: #aaa; font-style: italic; padding: 1rem 0; }
    footer { margin-top: 3rem; font-size: .8rem; color: #bbb; text-align: center; }

    @media (max-width: 768px) {
      .charts-grid, .charts-row { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
<div class="wrapper">

  <div class="page-header">
    <h1 class="page-title"><i class="bi bi-bar-chart-line"></i> Usage Metrics</h1>
    <span class="page-meta">Generated {{ generated_at }} &mdash; last {{ days }} days</span>
  </div>

  {% if not summary %}
  <p class="empty-state">No metrics data found in the specified directory.</p>
  {% else %}

  {# ── Pre-compute aggregates ── #}
  {% set ns = namespace(views=0, hits=0, misses=0, errors=0) %}
  {% for day in summary %}
    {% set ns.views   = ns.views   + day.page_views %}
    {% set ns.hits    = ns.hits    + day.cache_hits %}
    {% set ns.misses  = ns.misses  + day.cache_misses %}
    {% set ns.errors  = ns.errors  + day.errors %}
  {% endfor %}

  {% set all_skus = {} %}
  {% for day in summary %}{% for sku, cnt in day.top_skus.items() %}
    {% if sku in all_skus %}{% set _ = all_skus.update({sku: all_skus[sku] + cnt}) %}
    {% else %}{% set _ = all_skus.update({sku: cnt}) %}{% endif %}
  {% endfor %}{% endfor %}

  {% set all_locales = {} %}
  {% for day in summary %}{% for loc, cnt in day.top_locales.items() %}
    {% if loc in all_locales %}{% set _ = all_locales.update({loc: all_locales[loc] + cnt}) %}
    {% else %}{% set _ = all_locales.update({loc: cnt}) %}{% endif %}
  {% endfor %}{% endfor %}

  {% set all_types = {} %}
  {% for day in summary %}{% for pt, cnt in (day.top_product_types | default({})).items() %}
    {% if pt in all_types %}{% set _ = all_types.update({pt: all_types[pt] + cnt}) %}
    {% else %}{% set _ = all_types.update({pt: cnt}) %}{% endif %}
  {% endfor %}{% endfor %}

  {% set all_families = {} %}
  {% for day in summary %}{% for fam, cnt in (day.top_families | default({})).items() %}
    {% if fam in all_families %}{% set _ = all_families.update({fam: all_families[fam] + cnt}) %}
    {% else %}{% set _ = all_families.update({fam: cnt}) %}{% endif %}
  {% endfor %}{% endfor %}

  {% set recent_errors = [] %}
  {% for day in summary %}{% for e in day.error_details %}{% set _ = recent_errors.append(e) %}{% endfor %}{% endfor %}

  {% set sorted_days = summary | sort(attribute='date') %}

  {# ── Stat cards ── #}
  <div class="metrics-grid">
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-eye"></i> Page Views</span>
      <span class="stat-value">{{ ns.views }}</span>
      <span class="stat-sub">last {{ days }} days</span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-lightning-charge-fill" style="color:#1a7f37;"></i> Cache Hits</span>
      <span class="stat-value" style="color:#1a7f37;">{{ ns.hits }}</span>
      <span class="stat-sub">
        {% if ns.hits + ns.misses > 0 %}{{ ((ns.hits / (ns.hits + ns.misses)) * 100) | round(1) }}% hit rate{% else %}—{% endif %}
      </span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-cloud-download"></i> Cache Misses</span>
      <span class="stat-value" style="color:#024ad8;">{{ ns.misses }}</span>
      <span class="stat-sub">fresh API fetches</span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-exclamation-triangle-fill" style="color:#d1242f;"></i> Errors</span>
      <span class="stat-value" style="color:#d1242f;">{{ ns.errors }}</span>
      <span class="stat-sub">
        {% if ns.views > 0 %}{{ ((ns.errors / ns.views) * 100) | round(1) }}% error rate{% else %}—{% endif %}
      </span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-server"></i> Total Requests</span>
      <span class="stat-value">{{ ns.hits + ns.misses }}</span>
      <span class="stat-sub">cache checks</span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-calendar3"></i> Days with Data</span>
      <span class="stat-value">{{ summary | length }}</span>
      <span class="stat-sub">in range</span>
    </div>
  </div>

  {# ── Charts row 1: Daily trend + Cache donut ── #}
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-graph-up"></i> Daily Activity</div>
      <div class="chart-wrap" style="height:260px;"><canvas id="trendChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-pie-chart-fill"></i> Cache Performance</div>
      <div class="chart-wrap" style="height:260px;display:flex;align-items:center;justify-content:center;">
        <canvas id="cacheChart" style="max-width:220px;max-height:220px;"></canvas>
      </div>
    </div>
  </div>

  {# ── Charts row 2: Top Locales + Top SKUs ── #}
  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-globe2"></i> Top Locales</div>
      <div class="chart-wrap" style="height:280px;"><canvas id="localesChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-upc-scan"></i> Top SKUs</div>
      <div class="chart-wrap" style="height:280px;"><canvas id="skusChart"></canvas></div>
    </div>
  </div>

  <script>
  (function () {
    Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    Chart.defaults.font.size = 12;
    const BLUE   = 'rgba(2,74,216,0.80)';
    const GREEN  = 'rgba(26,127,55,0.80)';
    const RED    = 'rgba(209,36,47,0.90)';
    const ORANGE = 'rgba(227,98,9,0.80)';
    const GRID   = '#f0f0f6';

    // Daily trend
    const trendLabels = {{ sorted_days | map(attribute='date')        | list | tojson }};
    const trendViews  = {{ sorted_days | map(attribute='page_views')   | list | tojson }};
    const trendHits   = {{ sorted_days | map(attribute='cache_hits')   | list | tojson }};
    const trendMisses = {{ sorted_days | map(attribute='cache_misses') | list | tojson }};
    const trendErrors = {{ sorted_days | map(attribute='errors')       | list | tojson }};

    new Chart(document.getElementById('trendChart'), {
      data: {
        labels: trendLabels,
        datasets: [
          { type:'bar',  label:'Page Views',    data:trendViews,  backgroundColor:BLUE,   borderRadius:4, order:3 },
          { type:'bar',  label:'Cache Hits',    data:trendHits,   backgroundColor:GREEN,  borderRadius:4, order:4 },
          { type:'bar',  label:'Cache Misses',  data:trendMisses, backgroundColor:ORANGE, borderRadius:4, order:5 },
          { type:'line', label:'Errors', data:trendErrors,
            borderColor:RED, backgroundColor:'rgba(209,36,47,0.08)',
            borderWidth:2, pointRadius:4, fill:false, tension:0.3, order:1, yAxisID:'yErr' },
        ],
      },
      options: {
        responsive:true, maintainAspectRatio:false,
        interaction:{ mode:'index', intersect:false },
        plugins:{ legend:{ position:'bottom', labels:{ boxWidth:12, padding:14 } } },
        scales: {
          x:    { grid:{ display:false } },
          y:    { beginAtZero:true, grid:{ color:GRID }, ticks:{ precision:0 } },
          yErr: { beginAtZero:true, position:'right', grid:{ drawOnChartArea:false },
                  ticks:{ precision:0, color:'#d1242f' },
                  title:{ display:true, text:'Errors', color:'#d1242f', font:{ size:11 } } },
        },
      },
    });

    // Cache donut
    new Chart(document.getElementById('cacheChart'), {
      type:'doughnut',
      data:{
        labels:['Cache Hits','Cache Misses'],
        datasets:[{ data:[{{ ns.hits }},{{ ns.misses }}],
          backgroundColor:['rgba(26,127,55,0.85)','rgba(2,74,216,0.85)'],
          borderWidth:0, hoverOffset:8 }],
      },
      options:{
        responsive:true, maintainAspectRatio:false, cutout:'68%',
        plugins:{
          legend:{ position:'bottom', labels:{ boxWidth:12, padding:14 } },
          tooltip:{ callbacks:{ label(ctx) {
            const total = ctx.dataset.data.reduce((a,b)=>a+b,0);
            const pct = total>0 ? ((ctx.parsed/total)*100).toFixed(1) : 0;
            return ` ${ctx.label}: ${ctx.parsed.toLocaleString()} (${pct}%)`;
          }}},
        },
      },
    });

    // Top locales
    const localeData = {{ (all_locales | dictsort(by='value', reverse=true))[:12] | tojson }};
    new Chart(document.getElementById('localesChart'), {
      type:'bar',
      data:{ labels:localeData.map(d=>d[0]), datasets:[{ label:'Requests', data:localeData.map(d=>d[1]), backgroundColor:BLUE, borderRadius:4 }] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ beginAtZero:true, grid:{ color:GRID }, ticks:{ precision:0 } }, y:{ grid:{ display:false } } } },
    });

    // Top SKUs
    const skuData = {{ (all_skus | dictsort(by='value', reverse=true))[:12] | tojson }};
    new Chart(document.getElementById('skusChart'), {
      type:'bar',
      data:{ labels:skuData.map(d=>d[0]), datasets:[{ label:'Requests', data:skuData.map(d=>d[1]), backgroundColor:GREEN, borderRadius:4 }] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ beginAtZero:true, grid:{ color:GRID }, ticks:{ precision:0 } }, y:{ grid:{ display:false } } } },
    });
  })();
  </script>

  {# ── Daily breakdown table ── #}
  <h2 class="section-title"><i class="bi bi-calendar-range"></i> Daily Breakdown</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead>
        <tr>
          <th>Date</th><th>Server</th><th>Page Views</th>
          <th>Cache Hits</th><th>Cache Misses</th><th>Errors</th>
        </tr>
      </thead>
      <tbody>
        {% for day in summary %}
        <tr>
          <td><strong>{{ day.date }}</strong></td>
          <td><code style="font-size:.8rem;">{{ day.server_id | default('—') }}</code></td>
          <td>{{ day.page_views }}</td>
          <td class="badge-hit">{{ day.cache_hits }}</td>
          <td class="badge-miss">{{ day.cache_misses }}</td>
          <td class="badge-err">{{ day.errors }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  {# ── Top SKUs ── #}
  {% if all_skus %}
  {% set top_skus_list = all_skus | dictsort(by='value', reverse=true) %}
  {% set max_sku = top_skus_list[0][1] if top_skus_list else 1 %}
  <h2 class="section-title"><i class="bi bi-upc-scan"></i> Top SKUs</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>SKU</th><th>Requests</th><th style="width:40%;"></th></tr></thead>
      <tbody>
        {% for sku, cnt in top_skus_list[:20] %}
        <tr>
          <td><strong>{{ sku }}</strong></td>
          <td>{{ cnt }}</td>
          <td><div class="spark-bar"><div class="spark-bar-fill" style="width:{{ ((cnt/max_sku)*100)|round }}%;"></div></div></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Top Locales ── #}
  {% if all_locales %}
  {% set top_locales_list = all_locales | dictsort(by='value', reverse=true) %}
  {% set max_loc = top_locales_list[0][1] if top_locales_list else 1 %}
  <h2 class="section-title"><i class="bi bi-globe2"></i> Top Locales</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Locale</th><th>Requests</th><th style="width:40%;"></th></tr></thead>
      <tbody>
        {% for loc, cnt in top_locales_list[:20] %}
        <tr>
          <td>{{ loc }}</td>
          <td>{{ cnt }}</td>
          <td><div class="spark-bar"><div class="spark-bar-fill" style="width:{{ ((cnt/max_loc)*100)|round }}%;"></div></div></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Top Product Types ── #}
  {% if all_types %}
  <h2 class="section-title"><i class="bi bi-box-seam"></i> Top Product Types</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Product Type</th><th>Requests</th></tr></thead>
      <tbody>
        {% for pt, cnt in (all_types | dictsort(by='value', reverse=true)) %}
        <tr><td>{{ pt }}</td><td>{{ cnt }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Top Product Families ── #}
  {% if all_families %}
  <h2 class="section-title"><i class="bi bi-collection"></i> Top Product Families</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Family</th><th>Requests</th></tr></thead>
      <tbody>
        {% for fam, cnt in (all_families | dictsort(by='value', reverse=true))[:20] %}
        <tr><td>{{ fam }}</td><td>{{ cnt }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Recent Errors ── #}
  {% if recent_errors %}
  <h2 class="section-title"><i class="bi bi-x-octagon"></i> Recent Errors</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Timestamp</th><th>Server</th><th>SKU</th><th>Locale</th><th>Reason</th></tr></thead>
      <tbody>
        {% for e in recent_errors[-50:] | reverse %}
        <tr>
          <td style="white-space:nowrap;font-size:.82rem;">{{ e.ts }}</td>
          <td><code style="font-size:.8rem;">{{ e.server_id | default('—') }}</code></td>
          <td><strong>{{ e.sku }}</strong></td>
          <td>{{ e.locale }}</td>
          <td class="badge-err">{{ e.reason }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {% endif %}

  <footer>HP Inc. Restricted &mdash; Copyright 2025 HP Inc. Company.</footer>
</div>
</body>
</html>
"""


# ── Renderer ──────────────────────────────────────────────────────────────────

def render_html(summary: list, days: int) -> str:
    env = Environment(autoescape=False)

    def dictsort_filter(d, by="key", reverse=False):
        idx = 1 if by == "value" else 0
        return sorted(d.items(), key=lambda x: x[idx], reverse=reverse)

    def tojson_filter(v):
        return json.dumps(v, ensure_ascii=False)

    env.filters["dictsort"] = dictsort_filter
    env.filters["tojson"]   = tojson_filter

    tmpl = env.from_string(_TEMPLATE)
    return tmpl.render(
        summary=summary,
        days=days,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a standalone HTML metrics report from the metrics/ directory."
    )
    parser.add_argument(
        "--days", type=int, default=7,
        help="Number of days to include (default: 7, max: 30)",
    )
    parser.add_argument(
        "--metrics-dir", default=None,
        help="Path to metrics directory (default: metrics/ next to this script)",
    )
    parser.add_argument(
        "--out", default="metrics_report.html",
        help="Output file path (default: metrics_report.html)",
    )
    args = parser.parse_args()

    days        = min(max(args.days, 1), 30)
    script_dir  = Path(__file__).parent
    metrics_dir = args.metrics_dir or str(script_dir / "metrics")

    logging.info(f"Reading metrics from: {metrics_dir}")
    logging.info(f"Days: {days}")

    summary = get_summary(metrics_dir, days=days)

    if not summary:
        logging.warning("No metrics data found — the report will show an empty state.")

    html = render_html(summary, days)

    out_path = Path(args.out)
    out_path.write_text(html, encoding="utf-8")
    logging.info(f"Report written to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
