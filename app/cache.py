import os
from flask import current_app, send_from_directory
from werkzeug.utils import secure_filename

def get_cached_product(sku, country_code, language_code):
    """
    Retrieves a cached product page if it exists.
    """
    cache_dir = current_app.config['CACHE_DIR']
    cached_filename = get_cached_filename(sku, country_code, language_code)
    if os.path.exists(os.path.join(cache_dir, cached_filename)):
        return send_from_directory(cache_dir, cached_filename)
    return None

def save_to_cache(rendered_page, sku, country_code, language_code):
    """
    Saves a rendered product page to the cache.
    """
    cache_dir = current_app.config['CACHE_DIR']
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    cached_filename = get_cached_filename(sku, country_code, language_code)
    with open(os.path.join(cache_dir, cached_filename), 'w', encoding='utf-8') as f:
        f.write(rendered_page)

def get_cached_filename(sku, country_code, language_code):
    """
    Generates a secure filename for caching.
    """
    safe_sku = secure_filename(sku)
    safe_country = secure_filename(country_code)
    safe_lang = secure_filename(language_code)
    return f"{safe_sku}_{safe_country}_{safe_lang}.html"