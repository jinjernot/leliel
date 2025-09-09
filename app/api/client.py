import requests
from flask import current_app, render_template
import json
import logging
import re
from app.api.api_error import process_api_error


def clean_json_response(response_text):
    """
    Cleans the API response text to extract a valid JSON object.
    """
    try:
        # Find the first opening curly brace and the last closing curly brace
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in the response.")
        
        json_string = response_text[start:end+1]
        json.loads(json_string)
        return json_string
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Extracted string is not valid JSON: {e}")


def get_product_data(sku, country_code, language_code):
    """
    Fetches product data from the HERMES API.
    """
    api_url_base = current_app.config['API_URL']
    api_url = f"{api_url_base}/{country_code}/{language_code}/{sku}/all"
    logging.info(f"Calling API: {api_url}")

    try:
        api_response = requests.get(
            api_url,
            headers={'Content-Type': 'application/json'}
        )
        api_response.raise_for_status()  # Raise an exception for bad status codes

        logging.info("API call successful (Status 200)")
        cleaned_response_text = clean_json_response(api_response.text)
        response_json = json.loads(cleaned_response_text)
        logging.info("Successfully cleaned and parsed JSON response.")

        if response_json.get('Status') == 'ERROR':
            logging.error(
                f"API returned a 200 status but with an error message: {response_json.get('StatusMessage')}")
            return None, process_api_error(api_response)

        product_data = response_json.get('products', {}).get(sku.upper())
        if not product_data or product_data.get('status') is False:
            error_message = product_data.get(
                'statusMessage', 'Invalid SKU or Culture is not available.')
            logging.error(
                f"Product-level error for SKU {sku}: {error_message}")
            return None, (render_template('error.html', error_message=error_message), 400)

        return response_json, None

    except requests.exceptions.RequestException as e:
        logging.error(f"API call failed: {e}")
        return None, process_api_error(e.response)
    except ValueError as e:
        current_app.logger.error(
            f"Failed to clean or parse JSON response: {e}")
        return None, (render_template('error.html', error_message="Could not parse the data from the API."), 500)