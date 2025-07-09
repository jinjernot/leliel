from flask import render_template, request, send_from_directory
import requests
import json
import os

from app.api.process_product import process_api_response
from app.api.api_error import process_api_error
from config import client_cert_path, client_key_path, api_productcontent

CACHE_DIR = 'cached_pages'

def get_product():
    try:
        # Create cache directory if it doesn't exist
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        # Extract data from the request
        sku = request.form.get('sku', '').strip()
        country_code = request.form.get('country', '').strip()
        language_code = request.form.get('language', '').strip()

        # Check for cached file
        cached_filename = f"{sku}_{country_code}_{language_code}.html"
        if os.path.exists(os.path.join(CACHE_DIR, cached_filename)):
            return send_from_directory(CACHE_DIR, cached_filename)

        # If not cached, proceed with API call
        client_cert = (client_cert_path, client_key_path)
        json_data = {
            "sku": [sku],
            "countryCode": country_code,
            "languageCode": language_code,
            "layoutName": "ALL-Specs",
            "requestor": "APIQA-PRO",
            "reqContent": ["chunks", "images", "hierarchy", "plc"]
        }

        api_response = requests.post(
            api_productcontent,
            cert=client_cert,
            verify=False,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
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

        # Check for cached file
        cached_filename = f"{sku}_{country_code}_{language_code}.html"
        if os.path.exists(os.path.join(CACHE_DIR, cached_filename)):
            return send_from_directory(CACHE_DIR, cached_filename)

        api_language_code = language_code
        if country_code == 'mx' and language_code == 'mx':
            api_language_code = 'mx'

        client_cert = (client_cert_path, client_key_path)
        json_data = {
            "sku": [sku],
            "countryCode": country_code,
            "languageCode": api_language_code,
            "layoutName": "ALL-Specs",
            "requestor": "APIQA-PRO",
            "reqContent": ["chunks", "images", "hierarchy", "plc"]
        }

        api_response = requests.post(
            api_productcontent,
            cert=client_cert,
            verify=False,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
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