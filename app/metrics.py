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
        'error_details': [],
        # Extended metrics
        'top_plc_statuses': {},
        'top_categories': {},
        'top_series': {},
        'fallback_count': 0,
        'response_time_sum': 0.0,
        'response_time_count': 0,
        'response_time_min': None,
        'response_time_max': 0.0,
        'video_views': 0,
        'no_video_views': 0,
        'companion_views': 0,
        'no_companion_views': 0,
        'image_count_sum': 0,
        'image_count_count': 0,
        'spec_group_count_sum': 0,
        'spec_group_count_count': 0,
        'eol_soon_skus': {},
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


def record_page_view(metrics_dir, sku, locale, product_type=None, family=None,
                     plc_status=None, category=None, series=None,
                     fallback=False, response_time=None,
                     has_video=False, has_companions=False,
                     image_count=0, spec_group_count=0, eol_date=None):
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
            # Extended metrics
            if plc_status:
                data.setdefault('top_plc_statuses', {})
                data['top_plc_statuses'][plc_status] = data['top_plc_statuses'].get(plc_status, 0) + 1
            if category:
                data.setdefault('top_categories', {})
                data['top_categories'][category] = data['top_categories'].get(category, 0) + 1
            if series:
                data.setdefault('top_series', {})
                data['top_series'][series] = data['top_series'].get(series, 0) + 1
            if fallback:
                data['fallback_count'] = data.get('fallback_count', 0) + 1
            if response_time is not None:
                data['response_time_sum'] = data.get('response_time_sum', 0.0) + response_time
                data['response_time_count'] = data.get('response_time_count', 0) + 1
                current_min = data.get('response_time_min')
                if current_min is None or response_time < current_min:
                    data['response_time_min'] = response_time
                if response_time > data.get('response_time_max', 0.0):
                    data['response_time_max'] = response_time
            if has_video:
                data['video_views'] = data.get('video_views', 0) + 1
            else:
                data['no_video_views'] = data.get('no_video_views', 0) + 1
            if has_companions:
                data['companion_views'] = data.get('companion_views', 0) + 1
            else:
                data['no_companion_views'] = data.get('no_companion_views', 0) + 1
            if image_count > 0:
                data['image_count_sum'] = data.get('image_count_sum', 0) + image_count
                data['image_count_count'] = data.get('image_count_count', 0) + 1
            if spec_group_count > 0:
                data['spec_group_count_sum'] = data.get('spec_group_count_sum', 0) + spec_group_count
                data['spec_group_count_count'] = data.get('spec_group_count_count', 0) + 1
            if eol_date:
                data.setdefault('eol_soon_skus', {})
                data['eol_soon_skus'][sku] = eol_date
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


def record_error(metrics_dir, sku, locale, reason, detail=None):
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
            if detail:
                entry['detail'] = str(detail)[:300]
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
    for key in ('page_views', 'cache_hits', 'cache_misses', 'errors',
                'fallback_count', 'video_views', 'no_video_views',
                'companion_views', 'no_companion_views',
                'image_count_sum', 'image_count_count',
                'spec_group_count_sum', 'spec_group_count_count'):
        base[key] = base.get(key, 0) + extra.get(key, 0)
    for key in ('top_skus', 'top_locales', 'top_product_types', 'top_families',
                'top_plc_statuses', 'top_categories', 'top_series', 'eol_soon_skus'):
        for k, v in extra.get(key, {}).items():
            if isinstance(v, (int, float)):
                base.setdefault(key, {})[k] = base.get(key, {}).get(k, 0) + v
            else:
                base.setdefault(key, {})[k] = v
    base['error_details'] = (base.get('error_details', []) + extra.get('error_details', []))[-100:]
    # Response time aggregation
    base['response_time_sum'] = base.get('response_time_sum', 0.0) + extra.get('response_time_sum', 0.0)
    base['response_time_count'] = base.get('response_time_count', 0) + extra.get('response_time_count', 0)
    extra_min = extra.get('response_time_min')
    if extra_min is not None:
        base_min = base.get('response_time_min')
        if base_min is None or extra_min < base_min:
            base['response_time_min'] = extra_min
    extra_max = extra.get('response_time_max', 0.0)
    if extra_max > base.get('response_time_max', 0.0):
        base['response_time_max'] = extra_max
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
