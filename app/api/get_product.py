from flask import render_template, request, send_from_directory, current_app
import requests
import os
import re
import json
import logging

from config import CACHE_DIR
from app.api.process_product import process_api_response
from app.api.api_error import process_api_error
from config import API_URL

def sanitize_filename(filename):

    return re.sub(r'[^a-zA-Z0-9_.-]', '', filename)

def clean_json_response(response_text):
    
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


def get_product():
    
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        sku = sanitize_filename(request.form.get('sku', '').strip())
        country_code = sanitize_filename(request.form.get('country', '').strip())
        language_code = sanitize_filename(request.form.get('language', '').strip())
        
        logging.info(f"Requesting product with SKU: {sku}, Country: {country_code}, Language: {language_code}")

        cached_filename = f"{sku}_{country_code}_{language_code}.html"
        if os.path.exists(os.path.join(CACHE_DIR, cached_filename)):
            logging.info(f"Returning cached file: {cached_filename}")
            return send_from_directory(CACHE_DIR, cached_filename)

        api_url = f"{API_URL}/{country_code}/{language_code}/{sku}/all"
        logging.info(f"Calling API: {api_url}")

        api_response = requests.get(
            api_url,
            verify=False,
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
                class MockResponse:
                    def __init__(self, text, json_data):
                        self.text = text
                        self._json_data = json_data
                    def json(self):
                        return self._json_data

                mock_response = MockResponse(api_response.text, response_json)
                return process_api_error(mock_response)
            
            # Check for product-level error before processing
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

        with open(os.path.join(CACHE_DIR, cached_filename), 'w', encoding='utf-8') as f:
            f.write(rendered_page)
        logging.info(f"Saved rendered page to cache: {cached_filename}")
        return rendered_page

    except Exception as e:
        logging.error(f"An unexpected error occurred in get_product: {e}", exc_info=True)
        return render_template('error.html', error_message=f'An error occurred: {e}'), 400


def get_product_by_params(sku, country_code, language_code):
    
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        sku = sanitize_filename(sku)
        country_code = sanitize_filename(country_code)
        language_code = sanitize_filename(language_code)

        logging.info(f"Requesting product by params - SKU: {sku}, Country: {country_code}, Language: {language_code}")

        cached_filename = f"{sku}_{country_code}_{language_code}.html"
        if os.path.exists(os.path.join(CACHE_DIR, cached_filename)):
            logging.info(f"Returning cached file: {cached_filename}")
            return send_from_directory(CACHE_DIR, cached_filename)

        api_url = f"{API_URL}/{country_code}/{language_code}/{sku}/all"
        logging.info(f"Calling API: {api_url}")

        api_response = requests.get(
            api_url,
            verify=False,
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
                class MockResponse:
                    def __init__(self, text, json_data):
                        self.text = text
                        self._json_data = json_data
                    def json(self):
                        return self._json_data

                mock_response = MockResponse(api_response.text, response_json)
                return process_api_error(mock_response)
            
            # Check for product-level error before processing
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
        
        with open(os.path.join(CACHE_DIR, cached_filename), 'w', encoding='utf-8') as f:
            f.write(rendered_page)
        logging.info(f"Saved rendered page to cache: {cached_filename}")
        return rendered_page
            
    except Exception as e:
        logging.error(f"An unexpected error occurred in get_product_by_params: {e}", exc_info=True)
        return render_template('error.html', error_message=str(e)), 400