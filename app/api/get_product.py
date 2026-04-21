from flask import request, current_app
import logging
import threading
import time
from app.api.process_product import process_api_response
from app.api.client import get_product_data, get_product_locales
from app.cache import get_cached_product, save_to_cache
from app.api.api_error import render_friendly_error
from app import metrics as app_metrics

# Per-key locks prevent duplicate concurrent API calls for the same product/locale
_inflight_registry_lock = threading.Lock()
_inflight_locks: dict = {}


def _get_inflight_lock(key):
    with _inflight_registry_lock:
        if key not in _inflight_locks:
            _inflight_locks[key] = threading.Lock()
        return _inflight_locks[key]


def _fetch_and_process_product(sku, country_code, language_code):
    """
    A helper function to fetch, process, and cache the product page.
    """
    cached_page = get_cached_product(sku, country_code, language_code)
    if cached_page:
        app_metrics.record_cache_hit(current_app.config.get('METRICS_DIR', 'metrics'))
        return cached_page

    key = f"{sku}_{country_code}_{language_code}"
    with _get_inflight_lock(key):
        # Re-check cache — a concurrent request may have populated it while we waited
        cached_page = get_cached_product(sku, country_code, language_code)
        if cached_page:
            app_metrics.record_cache_hit(current_app.config.get('METRICS_DIR', 'metrics'))
            return cached_page

        app_metrics.record_cache_miss(current_app.config.get('METRICS_DIR', 'metrics'))

        api_start = time.monotonic()
        result = get_product_data(sku, country_code, language_code)
        api_elapsed = round(time.monotonic() - api_start, 3)
        response_json, error_response, error_reason = result[0], result[1], result[2]
        error_detail = result[3] if len(result) > 3 else None
        if error_response:
            app_metrics.record_error(current_app.config.get('METRICS_DIR', 'metrics'), sku, f"{country_code}-{language_code}", error_reason or 'api_error', detail=error_detail)
            return error_response

        locales = get_product_locales(sku)
        rendered_page = process_api_response(response_json, sku, locales, country_code, language_code, response_time=api_elapsed)

        if isinstance(rendered_page, tuple):
            app_metrics.record_error(current_app.config.get('METRICS_DIR', 'metrics'), sku, f"{country_code}-{language_code}", 'render_error')
            return rendered_page

        save_to_cache(rendered_page, sku, country_code, language_code)
        logging.info(f"Saved rendered page to cache for SKU: {sku}")
        return rendered_page


def get_product():
    """
    Fetches product data from the API based on form input.
    """
    try:
        sku = request.form.get('sku', '').strip()
        country_code = request.form.get('country', '').strip()
        language_code = request.form.get('language', '').strip()
        allowed_countries = current_app.config['ALLOWED_COUNTRIES']
        allowed_languages = current_app.config['ALLOWED_LANGUAGES']

        if country_code.lower() not in allowed_countries or language_code.lower() not in allowed_languages:
            locale_options = get_product_locales(sku) if sku else []
            return render_friendly_error(
                message='The selected country/language combination is not supported.',
                status_code=400,
                title='Invalid location selection',
                sku=sku,
                current_locale=f"{country_code.lower()}-{language_code.lower()}",
                locale_options=locale_options
            )

        return _fetch_and_process_product(sku, country_code, language_code)

    except Exception as e:
        logging.error(
            f"Unexpected error in get_product: {e}", exc_info=True)
        return render_friendly_error(
            message='An unexpected error occurred. Please try again later.',
            status_code=500,
            title='Could not load product page'
        )


def get_product_by_params(sku, country_code, language_code):
    """
    Fetches product data from the API based on URL parameters.
    """
    try:
        allowed_countries = current_app.config['ALLOWED_COUNTRIES']
        allowed_languages = current_app.config['ALLOWED_LANGUAGES']

        if country_code.lower() not in allowed_countries or language_code.lower() not in allowed_languages:
            locale_options = get_product_locales(sku) if sku else []
            return render_friendly_error(
                message='The selected country/language combination is not supported.',
                status_code=400,
                title='Invalid location selection',
                sku=sku,
                current_locale=f"{country_code.lower()}-{language_code.lower()}",
                locale_options=locale_options
            )

        return _fetch_and_process_product(sku, country_code, language_code)

    except Exception as e:
        logging.error(
            f"Unexpected error in get_product_by_params: {e}", exc_info=True)
        return render_friendly_error(
            message='An unexpected error occurred. Please try again later.',
            status_code=500,
            title='Could not load product page'
        )