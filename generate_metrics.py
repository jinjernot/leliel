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
import base64
import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from jinja2 import Environment

# Import the pmoid → English name map from config
sys.path.insert(0, str(Path(__file__).parent))
from config import PRODUCT_HIERARCHY

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
        "top_plc_statuses": {},
        "top_categories": {},
        "top_series": {},
        "fallback_count": 0,
        "response_time_sum": 0.0,
        "response_time_count": 0,
        "response_time_min": None,
        "response_time_max": 0.0,
        "video_views": 0,
        "no_video_views": 0,
        "companion_views": 0,
        "no_companion_views": 0,
        "image_count_sum": 0,
        "image_count_count": 0,
        "spec_group_count_sum": 0,
        "spec_group_count_count": 0,
        "eol_soon_skus": {},
    }


def _merge_day(base, extra):
    for key in ("page_views", "cache_hits", "cache_misses", "errors",
                "fallback_count", "video_views", "no_video_views",
                "companion_views", "no_companion_views",
                "image_count_sum", "image_count_count",
                "spec_group_count_sum", "spec_group_count_count"):
        base[key] = base.get(key, 0) + extra.get(key, 0)
    for key in ("top_skus", "top_locales", "top_product_types", "top_families",
                "top_plc_statuses", "top_categories", "top_series", "eol_soon_skus"):
        for k, v in extra.get(key, {}).items():
            if isinstance(v, (int, float)):
                base.setdefault(key, {})[k] = base.get(key, {}).get(k, 0) + v
            else:
                base.setdefault(key, {})[k] = v
    base["error_details"] = (
        base.get("error_details", []) + extra.get("error_details", [])
    )[-100:]
    # Response time aggregation
    base["response_time_sum"] = base.get("response_time_sum", 0.0) + extra.get("response_time_sum", 0.0)
    base["response_time_count"] = base.get("response_time_count", 0) + extra.get("response_time_count", 0)
    extra_min = extra.get("response_time_min")
    if extra_min is not None:
        base_min = base.get("response_time_min")
        if base_min is None or extra_min < base_min:
            base["response_time_min"] = extra_min
    extra_max = extra.get("response_time_max", 0.0)
    if extra_max > base.get("response_time_max", 0.0):
        base["response_time_max"] = extra_max
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
  <title>QR Code Page — Metrics Report ({{ generated_at }})</title>
  <link rel="icon" type="image/png" href="{{ hp_logo_b64 }}">
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
    <img src="{{ hp_logo_b64 }}" alt="HP Logo" style="height:36px;width:auto;">
    <h1 class="page-title">Usage Metrics</h1>
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
  {% set recent_errors = recent_errors | sort(attribute='ts', reverse=true) %}

  {% set sorted_days = summary | sort(attribute='date') %}

  {# ── Extended aggregates ── #}
  {% set ns2 = namespace(rt_sum=0.0, rt_count=0, rt_min=None, rt_max=0.0,
                         fallbacks=0, vid=0, no_vid=0, comp=0, no_comp=0,
                         img_sum=0, img_count=0, sg_sum=0, sg_count=0) %}
  {% for day in summary %}
    {% set ns2.rt_sum = ns2.rt_sum + (day.response_time_sum | default(0)) %}
    {% set ns2.rt_count = ns2.rt_count + (day.response_time_count | default(0)) %}
    {% set day_min = day.response_time_min | default(None) %}
    {% if day_min is not none and (ns2.rt_min is none or day_min < ns2.rt_min) %}
      {% set ns2.rt_min = day_min %}
    {% endif %}
    {% set day_max = day.response_time_max | default(0) %}
    {% if day_max > ns2.rt_max %}{% set ns2.rt_max = day_max %}{% endif %}
    {% set ns2.fallbacks = ns2.fallbacks + (day.fallback_count | default(0)) %}
    {% set ns2.vid = ns2.vid + (day.video_views | default(0)) %}
    {% set ns2.no_vid = ns2.no_vid + (day.no_video_views | default(0)) %}
    {% set ns2.comp = ns2.comp + (day.companion_views | default(0)) %}
    {% set ns2.no_comp = ns2.no_comp + (day.no_companion_views | default(0)) %}
    {% set ns2.img_sum = ns2.img_sum + (day.image_count_sum | default(0)) %}
    {% set ns2.img_count = ns2.img_count + (day.image_count_count | default(0)) %}
    {% set ns2.sg_sum = ns2.sg_sum + (day.spec_group_count_sum | default(0)) %}
    {% set ns2.sg_count = ns2.sg_count + (day.spec_group_count_count | default(0)) %}
  {% endfor %}

  {% set all_plc = {} %}
  {% for day in summary %}{% for s, cnt in (day.top_plc_statuses | default({})).items() %}
    {% if s in all_plc %}{% set _ = all_plc.update({s: all_plc[s] + cnt}) %}
    {% else %}{% set _ = all_plc.update({s: cnt}) %}{% endif %}
  {% endfor %}{% endfor %}

  {% set all_categories = {} %}
  {% for day in summary %}{% for c, cnt in (day.top_categories | default({})).items() %}
    {% if c in all_categories %}{% set _ = all_categories.update({c: all_categories[c] + cnt}) %}
    {% else %}{% set _ = all_categories.update({c: cnt}) %}{% endif %}
  {% endfor %}{% endfor %}

  {% set all_series = {} %}
  {% for day in summary %}{% for s, cnt in (day.top_series | default({})).items() %}
    {% if s in all_series %}{% set _ = all_series.update({s: all_series[s] + cnt}) %}
    {% else %}{% set _ = all_series.update({s: cnt}) %}{% endif %}
  {% endfor %}{% endfor %}

  {% set all_eol = {} %}
  {% for day in summary %}{% for sku, dt in (day.eol_soon_skus | default({})).items() %}
    {% set _ = all_eol.update({sku: dt}) %}
  {% endfor %}{% endfor %}

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
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-stopwatch"></i> Avg Response Time</span>
      <span class="stat-value" style="font-size:1.6rem;">
        {% if ns2.rt_count > 0 %}{{ (ns2.rt_sum / ns2.rt_count) | round(2) }}s{% else %}—{% endif %}
      </span>
      <span class="stat-sub">
        {% if ns2.rt_count > 0 %}min {{ ns2.rt_min | round(2) }}s · max {{ ns2.rt_max | round(2) }}s{% else %}no data yet{% endif %}
      </span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-camera-video" style="color:#6f42c1;"></i> Video Available</span>
      <span class="stat-value" style="color:#6f42c1;">
        {% if ns2.vid + ns2.no_vid > 0 %}{{ ((ns2.vid / (ns2.vid + ns2.no_vid)) * 100) | round(1) }}%{% else %}—{% endif %}
      </span>
      <span class="stat-sub">{{ ns2.vid }} of {{ ns2.vid + ns2.no_vid }} pages</span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-people-fill" style="color:#0969da;"></i> With Companions</span>
      <span class="stat-value" style="color:#0969da;">
        {% if ns2.comp + ns2.no_comp > 0 %}{{ ((ns2.comp / (ns2.comp + ns2.no_comp)) * 100) | round(1) }}%{% else %}—{% endif %}
      </span>
      <span class="stat-sub">{{ ns2.comp }} of {{ ns2.comp + ns2.no_comp }} pages</span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-arrow-repeat" style="color:#9a6700;"></i> Fallbacks</span>
      <span class="stat-value" style="color:#9a6700;">{{ ns2.fallbacks }}</span>
      <span class="stat-sub">
        {% if ns.views > 0 %}{{ ((ns2.fallbacks / ns.views) * 100) | round(1) }}% of views{% else %}—{% endif %}
      </span>
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

  {# ══════════════════════════════════════════════════════════════════════════ #}
  {# ── API Performance ── #}
  {# ══════════════════════════════════════════════════════════════════════════ #}
  {% if ns2.rt_count > 0 %}
  <h2 class="section-title"><i class="bi bi-speedometer2"></i> API Response Time</h2>
  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-clock-history"></i> Daily Avg Response Time (s)</div>
      <div class="chart-wrap" style="height:260px;"><canvas id="rtChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-speedometer"></i> Daily Min / Max (s)</div>
      <div class="chart-wrap" style="height:260px;"><canvas id="rtRangeChart"></canvas></div>
    </div>
  </div>
  <script>
  (function () {
    const GRID = '#f0f0f6';
    const rtLabels = {{ sorted_days | map(attribute='date') | list | tojson }};
    const rtAvg = [{% for d in sorted_days %}{{ ((d.response_time_sum|default(0)) / (d.response_time_count|default(1))) | round(3) if d.response_time_count|default(0) > 0 else 0 }}{{ ',' if not loop.last }}{% endfor %}];
    const rtMin = [{% for d in sorted_days %}{{ d.response_time_min|default(0)|round(3) }}{{ ',' if not loop.last }}{% endfor %}];
    const rtMax = [{% for d in sorted_days %}{{ d.response_time_max|default(0)|round(3) }}{{ ',' if not loop.last }}{% endfor %}];

    new Chart(document.getElementById('rtChart'), {
      type:'line',
      data:{ labels:rtLabels, datasets:[{
        label:'Avg Response (s)', data:rtAvg,
        borderColor:'rgba(2,74,216,0.85)', backgroundColor:'rgba(2,74,216,0.08)',
        borderWidth:2, pointRadius:4, fill:true, tension:0.3
      }]},
      options:{ responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ grid:{ display:false } }, y:{ beginAtZero:true, grid:{ color:GRID }, title:{ display:true, text:'seconds' } } } },
    });

    new Chart(document.getElementById('rtRangeChart'), {
      type:'bar',
      data:{ labels:rtLabels, datasets:[
        { label:'Min', data:rtMin, backgroundColor:'rgba(26,127,55,0.75)', borderRadius:4 },
        { label:'Max', data:rtMax, backgroundColor:'rgba(209,36,47,0.75)', borderRadius:4 },
      ]},
      options:{ responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ position:'bottom', labels:{ boxWidth:12 } } },
        scales:{ x:{ grid:{ display:false } }, y:{ beginAtZero:true, grid:{ color:GRID }, title:{ display:true, text:'seconds' } } } },
    });
  })();
  </script>
  {% endif %}

  {# ══════════════════════════════════════════════════════════════════════════ #}
  {# ── PLC Status & Product Hierarchy ── #}
  {# ══════════════════════════════════════════════════════════════════════════ #}
  {% if all_plc %}
  <h2 class="section-title"><i class="bi bi-diagram-3"></i> Product Lifecycle & Hierarchy</h2>
  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-pie-chart-fill"></i> PLC Status Breakdown</div>
      <div class="chart-wrap" style="height:260px;display:flex;align-items:center;justify-content:center;">
        <canvas id="plcChart" style="max-width:260px;max-height:260px;"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-grid-3x3-gap"></i> Top Categories</div>
      <div class="chart-wrap" style="height:260px;"><canvas id="catChart"></canvas></div>
    </div>
  </div>
  <script>
  (function () {
    const GRID = '#f0f0f6';
    const plcData = {{ all_plc | dictsort(by='value', reverse=true) | tojson }};
    const plcColors = {'Live':'rgba(26,127,55,0.85)','Obsolete':'rgba(209,36,47,0.85)'};
    new Chart(document.getElementById('plcChart'), {
      type:'doughnut',
      data:{ labels:plcData.map(d=>d[0]),
        datasets:[{ data:plcData.map(d=>d[1]),
          backgroundColor:plcData.map(d=>plcColors[d[0]]||'rgba(130,80,223,0.85)'),
          borderWidth:0, hoverOffset:8 }] },
      options:{ responsive:true, maintainAspectRatio:false, cutout:'65%',
        plugins:{ legend:{ position:'bottom', labels:{ boxWidth:12, padding:14 } },
          tooltip:{ callbacks:{ label(ctx){ const t=ctx.dataset.data.reduce((a,b)=>a+b,0); return ` ${ctx.label}: ${ctx.parsed.toLocaleString()} (${(ctx.parsed/t*100).toFixed(1)}%)`; }}} } },
    });

    {% if all_categories %}
    const catData = {{ (all_categories | dictsort(by='value', reverse=true))[:10] | tojson }};
    new Chart(document.getElementById('catChart'), {
      type:'bar',
      data:{ labels:catData.map(d=>d[0]), datasets:[{ label:'Views', data:catData.map(d=>d[1]),
        backgroundColor:'rgba(2,74,216,0.8)', borderRadius:4 }] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ beginAtZero:true, grid:{ color:GRID }, ticks:{ precision:0 } }, y:{ grid:{ display:false } } } },
    });
    {% endif %}
  })();
  </script>
  {% endif %}

  {# ── Top Series table ── #}
  {% if all_series %}
  {% set top_series_list = all_series | dictsort(by='value', reverse=true) %}
  {% set max_ser = top_series_list[0][1] if top_series_list else 1 %}
  <h2 class="section-title"><i class="bi bi-stack"></i> Top Product Series</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Series</th><th>Views</th><th style="width:40%;"></th></tr></thead>
      <tbody>
        {% for ser, cnt in top_series_list[:20] %}
        <tr>
          <td>{{ ser }}</td>
          <td>{{ cnt }}</td>
          <td><div class="spark-bar"><div class="spark-bar-fill" style="width:{{ ((cnt/max_ser)*100)|round }}%;"></div></div></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Top Categories table ── #}
  {% if all_categories %}
  {% set top_cat_list = all_categories | dictsort(by='value', reverse=true) %}
  {% set max_cat = top_cat_list[0][1] if top_cat_list else 1 %}
  <h2 class="section-title"><i class="bi bi-grid-3x3-gap"></i> Top Marketing Categories</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Category</th><th>Views</th><th style="width:40%;"></th></tr></thead>
      <tbody>
        {% for cat, cnt in top_cat_list %}
        <tr>
          <td>{{ cat }}</td>
          <td>{{ cnt }}</td>
          <td><div class="spark-bar"><div class="spark-bar-fill" style="width:{{ ((cnt/max_cat)*100)|round }}%;"></div></div></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ══════════════════════════════════════════════════════════════════════════ #}
  {# ── Content Completeness ── #}
  {# ══════════════════════════════════════════════════════════════════════════ #}
  {% if ns2.vid + ns2.no_vid > 0 or ns2.img_count > 0 %}
  <h2 class="section-title"><i class="bi bi-check2-square"></i> Content Completeness</h2>
  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-camera-video"></i> Video &amp; Companion Availability</div>
      <div class="chart-wrap" style="height:260px;"><canvas id="contentChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-images"></i> Avg Images &amp; Spec Groups per Page</div>
      <div class="chart-wrap" style="height:260px;display:flex;align-items:center;justify-content:center;">
        <canvas id="avgContentChart" style="max-width:320px;max-height:260px;"></canvas>
      </div>
    </div>
  </div>
  <script>
  (function () {
    new Chart(document.getElementById('contentChart'), {
      type:'bar',
      data:{
        labels:['360° Video','Companion Products'],
        datasets:[
          { label:'Available', data:[{{ ns2.vid }},{{ ns2.comp }}], backgroundColor:'rgba(26,127,55,0.8)', borderRadius:4 },
          { label:'Missing', data:[{{ ns2.no_vid }},{{ ns2.no_comp }}], backgroundColor:'rgba(209,36,47,0.6)', borderRadius:4 },
        ]
      },
      options:{ responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ position:'bottom', labels:{ boxWidth:12 } } },
        scales:{ x:{ grid:{ display:false }, stacked:true }, y:{ beginAtZero:true, grid:{ color:'#f0f0f6' }, stacked:true, ticks:{ precision:0 } } } },
    });

    const avgImg = {{ ((ns2.img_sum / ns2.img_count) | round(1)) if ns2.img_count > 0 else 0 }};
    const avgSpec = {{ ((ns2.sg_sum / ns2.sg_count) | round(1)) if ns2.sg_count > 0 else 0 }};
    new Chart(document.getElementById('avgContentChart'), {
      type:'bar',
      data:{
        labels:['Avg Images / Page','Avg Spec Groups / Page'],
        datasets:[{ data:[avgImg, avgSpec],
          backgroundColor:['rgba(2,74,216,0.8)','rgba(130,80,223,0.8)'], borderRadius:6 }]
      },
      options:{ responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false },
          tooltip:{ callbacks:{ label(ctx){ return ` ${ctx.parsed.y}`; }}} },
        scales:{ x:{ grid:{ display:false } }, y:{ beginAtZero:true, grid:{ color:'#f0f0f6' } } } },
    });
  })();
  </script>
  {% endif %}

  {# ══════════════════════════════════════════════════════════════════════════ #}
  {# ── EOL Watchlist ── #}
  {# ══════════════════════════════════════════════════════════════════════════ #}
  {% if all_eol %}
  {% set sorted_eol = all_eol | dictsort(by='value') %}
  <h2 class="section-title"><i class="bi bi-clock-history" style="color:#d1242f;"></i> End-of-Sales Watchlist (≤90 days)</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>SKU</th><th>End of Sales Date</th></tr></thead>
      <tbody>
        {% for sku, dt in sorted_eol %}
        <tr>
          <td><strong>{{ sku }}</strong></td>
          <td class="badge-err">{{ dt }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Error Analysis ── #}
  {% if recent_errors %}

  {# ── Aggregate errors by reason, SKU, locale, server, date ── #}
  {% set errors_by_reason = {} %}
  {% for e in recent_errors %}
    {% set r = e.reason | default('unknown') %}
    {% if r in errors_by_reason %}{% set _ = errors_by_reason.update({r: errors_by_reason[r] + 1}) %}
    {% else %}{% set _ = errors_by_reason.update({r: 1}) %}{% endif %}
  {% endfor %}

  {% set errors_by_sku = {} %}
  {% for e in recent_errors %}
    {% set s = e.sku | default('unknown') %}
    {% if s in errors_by_sku %}{% set _ = errors_by_sku.update({s: errors_by_sku[s] + 1}) %}
    {% else %}{% set _ = errors_by_sku.update({s: 1}) %}{% endif %}
  {% endfor %}

  {% set errors_by_locale = {} %}
  {% for e in recent_errors %}
    {% set l = e.locale | default('unknown') %}
    {% if l in errors_by_locale %}{% set _ = errors_by_locale.update({l: errors_by_locale[l] + 1}) %}
    {% else %}{% set _ = errors_by_locale.update({l: 1}) %}{% endif %}
  {% endfor %}

  {% set errors_by_server = {} %}
  {% for e in recent_errors %}
    {% set sv = e.server_id | default('unknown') %}
    {% if sv in errors_by_server %}{% set _ = errors_by_server.update({sv: errors_by_server[sv] + 1}) %}
    {% else %}{% set _ = errors_by_server.update({sv: 1}) %}{% endif %}
  {% endfor %}

  {% set errors_by_date = {} %}
  {% for e in recent_errors %}
    {% set d = e.ts[:10] if e.ts else 'unknown' %}
    {% if d in errors_by_date %}{% set _ = errors_by_date.update({d: errors_by_date[d] + 1}) %}
    {% else %}{% set _ = errors_by_date.update({d: 1}) %}{% endif %}
  {% endfor %}

  {% set sorted_reasons = errors_by_reason | dictsort(by='value', reverse=true) %}
  {% set sorted_err_skus = errors_by_sku | dictsort(by='value', reverse=true) %}
  {% set sorted_err_locales = errors_by_locale | dictsort(by='value', reverse=true) %}
  {% set sorted_err_servers = errors_by_server | dictsort(by='value', reverse=true) %}
  {% set sorted_err_dates = errors_by_date | dictsort(by='key') %}

  {% set unique_reasons = sorted_reasons | length %}
  {% set unique_err_skus = sorted_err_skus | length %}
  {% set unique_err_locales = sorted_err_locales | length %}
  {% set total_err = recent_errors | length %}

  <h2 class="section-title"><i class="bi bi-exclamation-diamond-fill"></i> Error Analysis</h2>

  {# ── Error summary cards ── #}
  <div class="metrics-grid" style="margin-bottom:1.5rem;">
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-bug-fill" style="color:#d1242f;"></i> Total Errors Logged</span>
      <span class="stat-value" style="color:#d1242f;">{{ total_err }}</span>
      <span class="stat-sub">across all servers</span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-tags-fill" style="color:#9a6700;"></i> Unique Reasons</span>
      <span class="stat-value" style="color:#9a6700;">{{ unique_reasons }}</span>
      <span class="stat-sub">distinct error types</span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-upc-scan" style="color:#8250df;"></i> SKUs Affected</span>
      <span class="stat-value" style="color:#8250df;">{{ unique_err_skus }}</span>
      <span class="stat-sub">distinct products</span>
    </div>
    <div class="stat-card">
      <span class="stat-label"><i class="bi bi-globe2" style="color:#0969da;"></i> Locales Affected</span>
      <span class="stat-value" style="color:#0969da;">{{ unique_err_locales }}</span>
      <span class="stat-sub">distinct locales</span>
    </div>
  </div>

  {# ── Error charts ── #}
  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-bar-chart-horizontal"></i> Errors by Reason</div>
      <div class="chart-wrap" style="height:{{ [180, sorted_reasons | length * 36] | max }}px;"><canvas id="errReasonChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-calendar-event"></i> Errors by Day</div>
      <div class="chart-wrap" style="height:280px;"><canvas id="errDailyChart"></canvas></div>
    </div>
  </div>

  <div class="charts-row">
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-upc-scan"></i> Top Failing SKUs</div>
      <div class="chart-wrap" style="height:280px;"><canvas id="errSkuChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title"><i class="bi bi-globe2"></i> Top Failing Locales</div>
      <div class="chart-wrap" style="height:280px;"><canvas id="errLocaleChart"></canvas></div>
    </div>
  </div>

  <script>
  (function () {
    const RED    = 'rgba(209,36,47,0.80)';
    const ORANGE = 'rgba(227,98,9,0.80)';
    const PURPLE = 'rgba(130,80,223,0.80)';
    const CYAN   = 'rgba(9,105,218,0.80)';
    const GRID   = '#f0f0f6';
    const BAR_COLORS = [RED, ORANGE, '#e36209','#9a6700','#8250df','#0969da','#1a7f37','#6e7781','#d1242f','#57606a'];

    // Errors by Reason
    const reasonData = {{ sorted_reasons | tojson }};
    new Chart(document.getElementById('errReasonChart'), {
      type:'bar',
      data:{ labels:reasonData.map(d=>d[0]), datasets:[{ label:'Errors', data:reasonData.map(d=>d[1]),
        backgroundColor: reasonData.map((_,i) => BAR_COLORS[i % BAR_COLORS.length]), borderRadius:4 }] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ beginAtZero:true, grid:{ color:GRID }, ticks:{ precision:0 } }, y:{ grid:{ display:false } } } },
    });

    // Errors by Day
    const errDayData = {{ sorted_err_dates | tojson }};
    new Chart(document.getElementById('errDailyChart'), {
      type:'bar',
      data:{ labels:errDayData.map(d=>d[0]), datasets:[{ label:'Errors', data:errDayData.map(d=>d[1]),
        backgroundColor:RED, borderRadius:4 }] },
      options:{ responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ grid:{ display:false } }, y:{ beginAtZero:true, grid:{ color:GRID }, ticks:{ precision:0 } } } },
    });

    // Top Failing SKUs
    const errSkuData = {{ sorted_err_skus[:15] | tojson }};
    new Chart(document.getElementById('errSkuChart'), {
      type:'bar',
      data:{ labels:errSkuData.map(d=>d[0]), datasets:[{ label:'Errors', data:errSkuData.map(d=>d[1]),
        backgroundColor:PURPLE, borderRadius:4 }] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ beginAtZero:true, grid:{ color:GRID }, ticks:{ precision:0 } }, y:{ grid:{ display:false } } } },
    });

    // Top Failing Locales
    const errLocData = {{ sorted_err_locales[:15] | tojson }};
    new Chart(document.getElementById('errLocaleChart'), {
      type:'bar',
      data:{ labels:errLocData.map(d=>d[0]), datasets:[{ label:'Errors', data:errLocData.map(d=>d[1]),
        backgroundColor:CYAN, borderRadius:4 }] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ display:false } },
        scales:{ x:{ beginAtZero:true, grid:{ color:GRID }, ticks:{ precision:0 } }, y:{ grid:{ display:false } } } },
    });
  })();
  </script>

  {# ── Error Breakdown by Reason table ── #}
  <h2 class="section-title"><i class="bi bi-tags-fill"></i> Error Breakdown by Reason</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Reason</th><th>Count</th><th>% of Errors</th><th style="width:35%;"></th></tr></thead>
      <tbody>
        {% set max_reason = sorted_reasons[0][1] if sorted_reasons else 1 %}
        {% for reason, cnt in sorted_reasons %}
        <tr>
          <td><span class="badge-err">{{ reason }}</span></td>
          <td><strong>{{ cnt }}</strong></td>
          <td>{{ ((cnt / total_err) * 100) | round(1) }}%</td>
          <td><div class="spark-bar"><div class="spark-bar-fill" style="width:{{ ((cnt/max_reason)*100)|round }}%;background:#d1242f;"></div></div></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  {# ── Top Failing SKUs table ── #}
  {% if sorted_err_skus %}
  {% set max_err_sku = sorted_err_skus[0][1] if sorted_err_skus else 1 %}
  <h2 class="section-title"><i class="bi bi-upc-scan"></i> Top Failing SKUs</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>SKU</th><th>Errors</th><th>% of Errors</th><th style="width:35%;"></th></tr></thead>
      <tbody>
        {% for sku, cnt in sorted_err_skus[:25] %}
        <tr>
          <td><strong>{{ sku }}</strong></td>
          <td>{{ cnt }}</td>
          <td>{{ ((cnt / total_err) * 100) | round(1) }}%</td>
          <td><div class="spark-bar"><div class="spark-bar-fill" style="width:{{ ((cnt/max_err_sku)*100)|round }}%;background:#8250df;"></div></div></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Top Failing Locales table ── #}
  {% if sorted_err_locales %}
  {% set max_err_loc = sorted_err_locales[0][1] if sorted_err_locales else 1 %}
  <h2 class="section-title"><i class="bi bi-globe2"></i> Top Failing Locales</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Locale</th><th>Errors</th><th>% of Errors</th><th style="width:35%;"></th></tr></thead>
      <tbody>
        {% for loc, cnt in sorted_err_locales[:20] %}
        <tr>
          <td>{{ loc }}</td>
          <td>{{ cnt }}</td>
          <td>{{ ((cnt / total_err) * 100) | round(1) }}%</td>
          <td><div class="spark-bar"><div class="spark-bar-fill" style="width:{{ ((cnt/max_err_loc)*100)|round }}%;background:#0969da;"></div></div></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Errors by Server table ── #}
  {% if sorted_err_servers | length > 1 %}
  <h2 class="section-title"><i class="bi bi-hdd-rack"></i> Errors by Server</h2>
  <div class="card" style="overflow:auto;">
    <table class="metrics-table">
      <thead><tr><th>Server</th><th>Errors</th><th>% of Errors</th></tr></thead>
      <tbody>
        {% for srv, cnt in sorted_err_servers %}
        <tr>
          <td><code style="font-size:.82rem;">{{ srv }}</code></td>
          <td>{{ cnt }}</td>
          <td>{{ ((cnt / total_err) * 100) | round(1) }}%</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  {# ── Recent Error Log (detailed) ── #}
  <h2 class="section-title"><i class="bi bi-list-columns-reverse"></i> Recent Error Log</h2>
  <div style="margin-bottom:.5rem;font-size:.82rem;color:#888;">
    Showing latest {{ [recent_errors|length, 100] | min }} of {{ total_err }} errors
  </div>
  <div class="card" style="overflow:auto;max-height:600px;">
    <table class="metrics-table" style="font-size:.85rem;">
      <thead style="position:sticky;top:0;z-index:1;">
        <tr><th>Timestamp</th><th>Server</th><th>SKU</th><th>Locale</th><th>Reason</th><th>Detail</th></tr>
      </thead>
      <tbody>
        {% for e in recent_errors[:100] %}
        <tr>
          <td style="white-space:nowrap;font-size:.8rem;">{{ e.ts }}</td>
          <td><code style="font-size:.78rem;">{{ e.server_id | default('—') }}</code></td>
          <td><strong>{{ e.sku }}</strong></td>
          <td>{{ e.locale }}</td>
          <td class="badge-err">{{ e.reason }}</td>
          <td style="font-size:.8rem;color:#666;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{{ e.detail | default('') }}">{{ e.detail | default('—') }}</td>
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
    # Normalise top_product_types: resolve pmoids → English names, drop translated
    english_names = set(PRODUCT_HIERARCHY.values())
    for day in summary:
        normalised: dict = {}
        for key, cnt in day.get('top_product_types', {}).items():
            if key in PRODUCT_HIERARCHY:          # pmoid key (new data)
                english = PRODUCT_HIERARCHY[key]
            elif key in english_names:            # already English
                english = key
            else:                                 # historical translated name — skip
                continue
            normalised[english] = normalised.get(english, 0) + cnt
        day['top_product_types'] = normalised

    env = Environment(autoescape=False)

    def dictsort_filter(d, by="key", reverse=False):
        idx = 1 if by == "value" else 0
        return sorted(d.items(), key=lambda x: x[idx], reverse=reverse)

    def tojson_filter(v):
        return json.dumps(v, ensure_ascii=False)

    env.filters["dictsort"] = dictsort_filter
    env.filters["tojson"]   = tojson_filter

    # Embed HP logo as base64 data URI
    logo_path = Path(__file__).parent / "static" / "images" / "hp-logo.png"
    hp_logo_b64 = ""
    if logo_path.exists():
        logo_data = logo_path.read_bytes()
        hp_logo_b64 = f"data:image/png;base64,{base64.b64encode(logo_data).decode()}"

    tmpl = env.from_string(_TEMPLATE)
    return tmpl.render(
        summary=summary,
        days=days,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        hp_logo_b64=hp_logo_b64,
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
