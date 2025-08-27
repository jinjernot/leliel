from flask import render_template, request, send_from_directory, current_app
import requests
import os
import re
import json

from config import CACHE_DIR
from app.api.process_product import process_api_response
from app.api.api_error import process_api_error
from config import API_URL

def sanitize_filename(filename):
    """Sanitizes a filename by removing directory traversal characters."""
    return re.sub(r'[^a-zA-Z0-9_.-]', '', filename)

def clean_json_response(response_text):
    """
    Removes leading and trailing non-JSON text from the response.
    Returns a clean JSON string or raises a ValueError if no JSON object is found.
    """
    # Find the start of the JSON object
    json_start_index = response_text.find('{')
    if json_start_index == -1:
        raise ValueError("No JSON object found in the response.")

    # Find the end of the JSON object
    json_end_index = response_text.rfind('}')
    if json_end_index == -1:
        raise ValueError("JSON object is not properly terminated.")

    # Extract the potential JSON string
    json_string = response_text[json_start_index:json_end_index + 1]

    # Validate that this is a valid JSON
    try:
        json.loads(json_string)
        return json_string
    except json.JSONDecodeError as e:
        raise ValueError(f"Extracted string is not valid JSON: {e}")


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
        api_url = f"{API_URL}/{country_code}/{language_code}/{sku}/all"

        api_response = requests.get(
            api_url,
            verify=False,
            headers={'Content-Type': 'application/json'}
        )

        if api_response.status_code == 200:
            try:
                cleaned_response_text = clean_json_response(api_response.text)
                response_json = json.loads(cleaned_response_text)
            except ValueError as e:
                # Log the error and the problematic response
                current_app.logger.error(f"Failed to clean or parse JSON response: {e}")
                current_app.logger.debug(f"Problematic API response text: {api_response.text}")
                return render_template('error.html', error_message="Could not parse the data from the API."), 500


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
        api_url = f"{API_URL}/{country_code}/{language_code}/{sku}/all"


        api_response = requests.get(
            api_url,
            verify=False,
            headers={'Content-Type': 'application/json'}
        )

        if api_response.status_code == 200:
            try:
                cleaned_response_text = clean_json_response(api_response.text)
                response_json = json.loads(cleaned_response_text)
            except ValueError as e:
                # Log the error and the problematic response
                current_app.logger.error(f"Failed to clean or parse JSON response: {e}")
                current_app.logger.debug(f"Problematic API response text: {api_response.text}")
                return render_template('error.html', error_message="Could not parse the data from the API."), 500

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