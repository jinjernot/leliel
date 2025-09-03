from flask import render_template, request, send_from_directory, current_app
import requests
import os
import re
import json
import logging
from werkzeug.utils import secure_filename

from app.api.process_product import process_api_response
from app.api.api_error import process_api_error

def clean_json_response(response_text):
    """
    Cleans the API response text to extract a valid JSON object.
    """
    json_start_index = response_text.find('{')
    if json_start_index == -1:
        raise ValueError("No JSON object found in the response.")

    json_end_index = response_text.rfind('}')
    if json_end_index == -1:
        raise ValueError("JSON object is not properly terminated.")

    json_string = response_text[json_start_index:json_end_index + 1]

    try:
        json.loads(json_string)
        return json_string
    except json.JSONDecodeError as e:
        raise ValueError(f"Extracted string is not valid JSON: {e}")

def _fetch_and_process_product(sku, country_code, language_code):
    """
    A helper function to fetch, process, and cache the product page.
    """
    # Use config from the application context
    cache_dir = current_app.config['CACHE_DIR']
    api_url_base = current_app.config['API_URL']

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Sanitize user input before using it for file paths
    safe_sku = secure_filename(sku)
    safe_country = secure_filename(country_code)
    safe_lang = secure_filename(language_code)
    
    logging.info(f"Requesting product with SKU: {safe_sku}, Country: {safe_country}, Language: {safe_lang}")

    cached_filename = f"{safe_sku}_{safe_country}_{safe_lang}.html"
    if os.path.exists(os.path.join(cache_dir, cached_filename)):
        logging.info(f"Returning cached file: {cached_filename}")
        return send_from_directory(cache_dir, cached_filename)

    api_url = f"{api_url_base}/{safe_country}/{safe_lang}/{safe_sku}/all"
    logging.info(f"Calling API: {api_url}")

    api_response = requests.get(
        api_url,
        headers={'Content-Type': 'application/json'}
    )

    if api_response.status_code != 200:
        logging.error(f"API call failed with status code: {api_response.status_code}")
        return process_api_error(api_response)

    logging.info("API call successful (Status 200)")
    try:
        cleaned_response_text = clean_json_response(api_response.text)
        response_json = json.loads(cleaned_response_text)
        logging.info("Successfully cleaned and parsed JSON response.")

        if response_json.get('Status') == 'ERROR':
            logging.error(f"API returned a 200 status but with an error message: {response_json.get('StatusMessage')}")
            return process_api_error(api_response)
        
        product_data = response_json.get('products', {}).get(sku.upper())
        if not product_data or product_data.get('status') is False:
            error_message = product_data.get('statusMessage', 'Invalid SKU or Culture is not available.')
            logging.error(f"Product-level error for SKU {sku}: {error_message}")
            return render_template('error.html', error_message=error_message), 400

    except ValueError as e:
        current_app.logger.error(f"Failed to clean or parse JSON response: {e}")
        current_app.logger.debug(f"Problematic API response text: {api_response.text}")
        return render_template('error.html', error_message="Could not parse the data from the API."), 500

    rendered_page = process_api_response(response_json, sku)
    
    if isinstance(rendered_page, tuple):
        return rendered_page

    with open(os.path.join(cache_dir, cached_filename), 'w', encoding='utf-8') as f:
        f.write(rendered_page)
    logging.info(f"Saved rendered page to cache: {cached_filename}")
    return rendered_page

def get_product():
    """
    Fetches product data from the API based on form input.
    """
    try:
        sku = request.form.get('sku', '').strip()
        country_code = request.form.get('country', '').strip()
        language_code = request.form.get('language', '').strip()
        
        # Get allowed values from the app config
        allowed_countries = current_app.config['ALLOWED_COUNTRIES']
        allowed_languages = current_app.config['ALLOWED_LANGUAGES']

        if country_code.lower() not in allowed_countries or language_code.lower() not in allowed_languages:
            return render_template('error.html', error_message='Invalid country or language code provided.'), 400

        return _fetch_and_process_product(sku, country_code, language_code)

    except Exception as e:
        logging.error(f"An unexpected error occurred in get_product: {e}", exc_info=True)
        return render_template('error.html', error_message='An unexpected error occurred. Please try again later.'), 500


def get_product_by_params(sku, country_code, language_code):
    """
    Fetches product data from the API based on URL parameters.
    """
    try:
        # Get allowed values from the app config
        allowed_countries = current_app.config['ALLOWED_COUNTRIES']
        allowed_languages = current_app.config['ALLOWED_LANGUAGES']

        if country_code.lower() not in allowed_countries or language_code.lower() not in allowed_languages:
            return render_template('error.html', error_message='Invalid country or language code provided.'), 400
        
        return _fetch_and_process_product(sku, country_code, language_code)
            
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_product_by_params: {e}", exc_info=True)
        return render_template('error.html', error_message='An unexpected error occurred. Please try again later.'), 500