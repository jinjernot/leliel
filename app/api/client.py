import requests
from flask import current_app
import json
import logging
import re
from app.api.api_error import process_api_error, render_friendly_error, render_locale_unavailable_error
from datetime import datetime


def clean_json_response(response_text):
    """
    Cleans the API response text to extract a valid JSON object.
    """
    try:
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in the response.")

        json_string = response_text[start:end+1]
        json.loads(json_string)
        return json_string
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"Extracted string is not valid JSON: {e}")


def _get_timeout_tuple():
    """
    Returns the configured (connect_timeout, read_timeout) for outbound API calls.
    """
    connect_timeout = current_app.config.get('API_CONNECT_TIMEOUT', 3)
    read_timeout = current_app.config.get('API_READ_TIMEOUT', 20)
    return (connect_timeout, read_timeout)


def get_product_locales(sku):
    """
    Fetches available locales for a product from the PCB API.
    """
    api_url = f"{current_app.config['API_PCB_URL']}{sku}"
    logging.info(f"Calling PCB API: {api_url}")
    timeout = _get_timeout_tuple()
    try:
        api_response = requests.get(
            api_url,
            headers={'Content-Type': 'application/json'},
            verify=False,
            timeout=timeout
        )
        api_response.raise_for_status()

        cleaned_response_text = clean_json_response(api_response.text)
        response_json = json.loads(cleaned_response_text)

        locales = response_json.get('plc', {}).get('liveLocales')

        if locales is None:
            logging.warning(
                f"'liveLocales' not found for SKU {sku} in PCB API response.")
            return []

        logging.info(
            f"Successfully fetched locales for SKU {sku}: {locales}")
        return locales

    except requests.exceptions.RequestException as e:
        logging.error(f"PCB API call failed: {e}. timeout={timeout}")
        return []
    except (ValueError, json.JSONDecodeError) as e:
        current_app.logger.error(
            f"Failed to parse JSON response from PCB API: {e}")
        return []


def get_product_data(sku, country_code, language_code):
    """
    Fetches product data from the HERMES API.
    """
    api_url_base = current_app.config['API_URL']
    api_url = f"{api_url_base}/{country_code}/{language_code}/{sku}/all"
    logging.info(f"Calling API: {api_url}")
    timeout = _get_timeout_tuple()

    try:
        api_response = requests.get(
            api_url,
            headers={'Content-Type': 'application/json'},
            timeout=timeout
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
            error_message = (product_data or {}).get(
                'statusMessage', 'Invalid SKU or Culture is not available.')
            logging.error(
                f"Product-level error for SKU {sku}: {error_message}")

            if re.search(r'culture\s+is\s+not\s+available|locale\s+is\s+not\s+available', error_message, re.IGNORECASE):
                locale_options = get_product_locales(sku)
                return None, render_locale_unavailable_error(sku, country_code, language_code, locale_options)

            return None, render_friendly_error(
                message=error_message,
                status_code=400,
                title='Could not load this product page'
            )

        # Validation for live products
        plc_status = product_data.get('plcStatus')
        if plc_status != 'Live':
            error_message = f"SKU {sku} is not live. Status is '{plc_status}'."
            logging.error(error_message)
            return None, render_friendly_error(
                message='This product page is not currently published.',
                status_code=400,
                title='Product page unavailable',
                details=error_message
            )

        general_availability_date_str = product_data.get(
            'plcDates', {}).get('generalAvailabilityDate')
        if general_availability_date_str:
            general_availability_date = datetime.strptime(
                general_availability_date_str, '%Y-%m-%d').date()
            if general_availability_date > datetime.now().date():
                error_message = f"Product SKU {sku} is not yet available. General availability date is {general_availability_date_str}."
                logging.error(error_message)
                return None, render_friendly_error(
                    message='This product is not yet available in the selected market.',
                    status_code=400,
                    title='Product not yet available',
                    details=error_message
                )

        return response_json, None

    except requests.exceptions.ConnectTimeout as e:
        if isinstance(api_url_base, str) and 'localhost' in api_url_base.lower():
            logging.error(
                f"API connect timeout to localhost endpoint: {api_url}. "
                "Possible causes: Apache/Nginx vhost routing loop, Hermes service not bound to loopback, "
                "or local firewall/SELinux policy."
            )
        logging.error(f"API call failed: {e}. timeout={timeout}")
        return None, process_api_error(e.response)
    except requests.exceptions.RequestException as e:
        logging.error(f"API call failed: {e}. timeout={timeout}")
        return None, process_api_error(e.response)
    except ValueError as e:
        current_app.logger.error(
            f"Failed to clean or parse JSON response: {e}")
        return None, render_friendly_error(
            message='Could not parse the response from the product service.',
            status_code=500,
            title='Unexpected service response'
        )