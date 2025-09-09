from flask import render_template, request, current_app
import logging
from app.api.process_product import process_api_response
from app.api.client import get_product_data
from app.cache import get_cached_product, save_to_cache


def _fetch_and_process_product(sku, country_code, language_code):
    """
    A helper function to fetch, process, and cache the product page.
    """
    cached_page = get_cached_product(sku, country_code, language_code)
    if cached_page:
        logging.info(f"Returning cached file for SKU: {sku}")
        return cached_page

    response_json, error_response = get_product_data(
        sku, country_code, language_code)
    if error_response:
        return error_response

    rendered_page = process_api_response(response_json, sku)

    if isinstance(rendered_page, tuple):
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
            return render_template('error.html', error_message='Invalid country or language code provided.'), 400

        return _fetch_and_process_product(sku, country_code, language_code)

    except Exception as e:
        logging.error(
            f"An unexpected error occurred in get_product: {e}", exc_info=True)
        return render_template('error.html', error_message='An unexpected error occurred. Please try again later.'), 500


def get_product_by_params(sku, country_code, language_code):
    """
    Fetches product data from the API based on URL parameters.
    """
    try:
        allowed_countries = current_app.config['ALLOWED_COUNTRIES']
        allowed_languages = current_app.config['ALLOWED_LANGUAGES']

        if country_code.lower() not in allowed_countries or language_code.lower() not in allowed_languages:
            return render_template('error.html', error_message='Invalid country or language code provided.'), 400

        return _fetch_and_process_product(sku, country_code, language_code)

    except Exception as e:
        logging.error(
            f"An unexpected error occurred in get_product_by_params: {e}", exc_info=True)
        return render_template('error.html', error_message='An unexpected error occurred. Please try again later.'), 500
