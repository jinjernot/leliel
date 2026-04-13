import os
import time
import logging
from flask import current_app, send_from_directory
from werkzeug.utils import secure_filename

def get_cached_product(sku, country_code, language_code):
    """
    Retrieves a cached product page if it exists and has not expired.
    """
    cache_dir = current_app.config['CACHE_DIR']
    ttl_seconds = current_app.config.get('CACHE_TTL_DAYS', 7) * 86400
    cached_filename = get_cached_filename(sku, country_code, language_code)
    cached_path = os.path.join(cache_dir, cached_filename)

    if os.path.exists(cached_path):
        age = time.time() - os.path.getmtime(cached_path)
        if age <= ttl_seconds:
            return send_from_directory(cache_dir, cached_filename)
        # Expired — remove so a fresh copy is fetched
        os.remove(cached_path)
        logging.info(f"Cache expired for {cached_filename}, removed.")

    return None

def save_to_cache(rendered_page, sku, country_code, language_code):
    """
    Saves a rendered product page to the cache, then prunes if over the file limit.
    """
    cache_dir = current_app.config['CACHE_DIR']
    max_files = current_app.config.get('CACHE_MAX_FILES', 1000)
    prune_count = current_app.config.get('CACHE_PRUNE_COUNT', 200)

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    cached_filename = get_cached_filename(sku, country_code, language_code)
    with open(os.path.join(cache_dir, cached_filename), 'w', encoding='utf-8') as f:
        f.write(rendered_page)

    _prune_cache(cache_dir, max_files, prune_count)

def _prune_cache(cache_dir, max_files, prune_count):
    """
    Removes the oldest `prune_count` files when the cache exceeds `max_files`.
    """
    try:
        files = [
            os.path.join(cache_dir, f)
            for f in os.listdir(cache_dir)
            if f.endswith('.html')
        ]
        if len(files) <= max_files:
            return
        files.sort(key=os.path.getmtime)
        for path in files[:prune_count]:
            os.remove(path)
        logging.info(f"Cache pruned: removed {prune_count} oldest files ({len(files)} total).")
    except OSError as e:
        logging.warning(f"Cache pruning failed: {e}")

def get_cached_filename(sku, country_code, language_code):
    """
    Generates a secure filename for caching.
    """
    safe_sku = secure_filename(sku)
    safe_country = secure_filename(country_code)
    safe_lang = secure_filename(language_code)
    return f"{safe_sku}_{safe_country}_{safe_lang}.html"
