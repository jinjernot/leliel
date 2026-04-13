import os
import json
import socket
import threading
import logging
from datetime import datetime, timezone

_lock = threading.Lock()

_SERVER_ID = os.environ.get('SERVER_ID', socket.gethostname())


def _metrics_path(metrics_dir):
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    # One file per server per day so load-balanced servers don't overwrite each other
    return os.path.join(metrics_dir, f"{today}_{_SERVER_ID}.json")


def _empty_day():
    return {
        'server_id': _SERVER_ID,
        'page_views': 0,
        'cache_hits': 0,
        'cache_misses': 0,
        'errors': 0,
        'top_skus': {},
        'top_locales': {},
        'top_product_types': {},
        'top_families': {},
        'error_details': []
    }


def _load(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return _empty_day()


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def record_page_view(metrics_dir, sku, locale, product_type=None, family=None):
    try:
        with _lock:
            path = _metrics_path(metrics_dir)
            data = _load(path)
            data['page_views'] += 1
            data['top_skus'][sku] = data['top_skus'].get(sku, 0) + 1
            data['top_locales'][locale] = data['top_locales'].get(locale, 0) + 1
            if product_type:
                data.setdefault('top_product_types', {})
                data['top_product_types'][product_type] = data['top_product_types'].get(product_type, 0) + 1
            if family:
                data.setdefault('top_families', {})
                data['top_families'][family] = data['top_families'].get(family, 0) + 1
            _save(path, data)
    except OSError as e:
        logging.warning(f"Metrics write failed: {e}")


def record_cache_hit(metrics_dir):
    try:
        with _lock:
            path = _metrics_path(metrics_dir)
            data = _load(path)
            data['cache_hits'] += 1
            _save(path, data)
    except OSError as e:
        logging.warning(f"Metrics write failed: {e}")


def record_cache_miss(metrics_dir):
    try:
        with _lock:
            path = _metrics_path(metrics_dir)
            data = _load(path)
            data['cache_misses'] += 1
            _save(path, data)
    except OSError as e:
        logging.warning(f"Metrics write failed: {e}")


def record_error(metrics_dir, sku, locale, reason):
    try:
        with _lock:
            path = _metrics_path(metrics_dir)
            data = _load(path)
            data['errors'] += 1
            entry = {
                'ts': datetime.now(timezone.utc).isoformat(),
                'server_id': _SERVER_ID,
                'sku': sku,
                'locale': locale,
                'reason': reason
            }
            # Keep last 100 error details per day per server
            data['error_details'] = (data['error_details'] + [entry])[-100:]
            _save(path, data)
    except OSError as e:
        logging.warning(f"Metrics write failed: {e}")



def _load(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return _empty_day()


def _merge_day(base, extra):
    """Merge `extra` day dict into `base` in-place."""
    for key in ('page_views', 'cache_hits', 'cache_misses', 'errors'):
        base[key] = base.get(key, 0) + extra.get(key, 0)
    for key in ('top_skus', 'top_locales', 'top_product_types', 'top_families'):
        for k, v in extra.get(key, {}).items():
            base.setdefault(key, {})[k] = base.get(key, {}).get(k, 0) + v
    base['error_details'] = (base.get('error_details', []) + extra.get('error_details', []))[-100:]
    servers = base.get('server_id', '')
    extra_server = extra.get('server_id', '')
    if extra_server and extra_server not in servers:
        base['server_id'] = f"{servers}, {extra_server}" if servers else extra_server


def get_summary(metrics_dir, days=7):
    """Return aggregated metrics for the last `days` days, merging all servers per day."""
    by_date = {}
    try:
        if not os.path.exists(metrics_dir):
            return []
        for fname in os.listdir(metrics_dir):
            if not fname.endswith('.json'):
                continue
            # filename format: YYYY-MM-DD_serverid.json  or  YYYY-MM-DD.json
            date = fname[:10]
            try:
                with open(os.path.join(metrics_dir, fname), 'r', encoding='utf-8') as f:
                    day_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            if date not in by_date:
                by_date[date] = {**_empty_day(), 'date': date, 'server_id': ''}
            _merge_day(by_date[date], day_data)
    except OSError as e:
        logging.warning(f"Metrics read failed: {e}")

    sorted_days = sorted(by_date.values(), key=lambda d: d['date'], reverse=True)
    return sorted_days[:days]
