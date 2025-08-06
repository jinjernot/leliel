from flask import render_template, request, send_from_directory
import requests
import json
import os
import re

from app.api.process_product import process_api_response
from app.api.api_error import process_api_error
from config import api_productcontent

CACHE_DIR = 'cached_pages'

def sanitize_filename(filename):
    """Sanitizes a filename by removing directory traversal characters."""
    return re.sub(r'[^a-zA-Z0-9_.-]', '', filename)

def get_product():
    try:
        # Create cache directory if it doesn't exist
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        # Extract and sanitize data from the request
        sku = sanitize_filename(request.form.get('sku', '').strip())
        country_code = sanitize_filename(request.form.get('country', '').strip())
        language_code = sanitize_filename(request.form.get('language', '').strip())

        # Check for cached file
        cached_filename = f"{sku}_{country_code}_{language_code}.html"
        if os.path.exists(os.path.join(CACHE_DIR, cached_filename)):
            return send_from_directory(CACHE_DIR, cached_filename)

        # If not cached, proceed with API call
        # Construct the new API URL
        api_url = f"{api_productcontent}/{country_code}/{language_code}/{sku}/all"

        api_response = requests.get(
            api_url,
            verify=False,
            headers={'Content-Type': 'application/json'}
        )

        if api_response.status_code == 200:
            response_json = api_response.json()

            # Process and render the page
            rendered_page = process_api_response(response_json, sku)

            # Save the rendered page to cache
            with open(os.path.join(CACHE_DIR, cached_filename), 'w', encoding='utf-8') as f:
                f.write(rendered_page)

            return rendered_page
        else:
            return process_api_error(api_response)

    except Exception as e:
        error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message), 400

def get_product_by_params(sku, country_code, language_code):
    try:
        # Create cache directory if it doesn't exist
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        # Sanitize parameters
        sku = sanitize_filename(sku)
        country_code = sanitize_filename(country_code)
        language_code = sanitize_filename(language_code)

        # Check for cached file
        cached_filename = f"{sku}_{country_code}_{language_code}.html"
        if os.path.exists(os.path.join(CACHE_DIR, cached_filename)):
            return send_from_directory(CACHE_DIR, cached_filename)

        # Construct the new API URL
        api_url = f"{api_productcontent}/{country_code}/{language_code}/{sku}/all"


        api_response = requests.get(
            api_url,
            verify=False,
            headers={'Content-Type': 'application/json'}
        )

        if api_response.status_code == 200:
            response_json = api_response.json()

            # Process and render the page
            rendered_page = process_api_response(response_json, sku)

            # Save the rendered page to cache
            with open(os.path.join(CACHE_DIR, cached_filename), 'w', encoding='utf-8') as f:
                f.write(rendered_page)

            return rendered_page
        else:
            return process_api_error(api_response)
    except Exception as e:
        error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message), 400