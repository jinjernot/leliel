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


def _normalize_locale(locale):
    """Normalize locale strings to `cc-ll` lowercase format."""
    if not locale:
        return None
    normalized = str(locale).strip().replace('_', '-').lower()
    parts = normalized.split('-')
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return f"{parts[0]}-{parts[1]}"


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
            error_message = (product_data or {}).get('statusMessage', '')
            logging.error(
                f"Product-level error for SKU {sku}: {error_message}")

            if re.search(r'culture\s+is\s+not\s+available|locale\s+is\s+not\s+available', error_message, re.IGNORECASE):
                locale_options = get_product_locales(sku)
                if locale_options:
                    return None, render_locale_unavailable_error(sku, country_code, language_code, locale_options)
                return None, render_friendly_error(
                    message=f"We couldn\u2019t find a product matching \u2018{sku}\u2019. Please verify the product number and try again.",
                    status_code=404,
                    title='Product not found'
                )

            return None, render_friendly_error(
                message=f"We couldn\'t find a product matching \u2018{sku}\u2019. Please verify the product number and try again.",
                status_code=404,
                title='Product not found'
            )

        # Validation for live products
        plc_status = product_data.get('plcStatus')
        if plc_status != 'Live':
            error_message = f"SKU {sku} is not live. Status is '{plc_status}'."
            logging.error(error_message)
            return None, render_friendly_error(
                message='This product page is not published for public viewing.',
                status_code=404,
                title='Product page unavailable'
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
                    status_code=404,
                    title='Product not yet available'
                )

        return response_json, None

    except requests.exceptions.HTTPError as e:
        response = e.response
        if response is not None:
            error_json = {}
            try:
                cleaned_response_text = clean_json_response(getattr(response, 'text', ''))
                error_json = json.loads(cleaned_response_text)
            except (ValueError, json.JSONDecodeError):
                error_json = {}

            product_data = (
                error_json.get('products', {}).get(sku.upper())
                or error_json.get('products', {}).get(sku)
                or {}
            )
            product_status_message = str(
                product_data.get('statusMessage')
                or error_json.get('StatusMessage')
                or ''
            )

            if re.search(r'culture\s+is\s+not\s+available|locale\s+is\s+not\s+available', product_status_message, re.IGNORECASE):
                locale_options = get_product_locales(sku)
                if locale_options:
                    return None, render_locale_unavailable_error(sku, country_code, language_code, locale_options)
                return None, render_friendly_error(
                    message=f"We couldn\u2019t find a product matching \u2018{sku}\u2019. Please verify the product number and try again.",
                    status_code=404,
                    title='Product not found'
                )

            if re.search(r'non\s+publishable\s+product', product_status_message, re.IGNORECASE):
                requested_locale = _normalize_locale(f"{country_code}-{language_code}")
                locale_options = get_product_locales(sku)
                normalized_locale_options = [
                    locale for locale in (_normalize_locale(opt) for opt in locale_options) if locale
                ]

                if requested_locale and normalized_locale_options and requested_locale not in normalized_locale_options:
                    return None, render_locale_unavailable_error(
                        sku,
                        country_code,
                        language_code,
                        normalized_locale_options
                    )

                return None, render_friendly_error(
                    message='This product page is not published for public viewing.',
                    status_code=404,
                    title='Product page unavailable'
                )

            if response.status_code == 404:
                requested_locale = _normalize_locale(f"{country_code}-{language_code}")
                locale_options = get_product_locales(sku)
                normalized_locale_options = [
                    locale for locale in (_normalize_locale(opt) for opt in locale_options) if locale
                ]

                if requested_locale and normalized_locale_options and requested_locale not in normalized_locale_options:
                    logging.info(
                        "SKU %s exists but locale %s is unavailable. Redirecting to locale selector.",
                        sku,
                        requested_locale
                    )
                    return None, render_locale_unavailable_error(sku, country_code, language_code, normalized_locale_options)

        logging.error(f"API call failed: {e}. timeout={timeout}")
        return None, process_api_error(response, sku=sku)
    except requests.exceptions.ConnectTimeout as e:
        if isinstance(api_url_base, str) and 'localhost' in api_url_base.lower():
            logging.error(
                f"API connect timeout to localhost endpoint: {api_url}. "
                "Possible causes: Apache/Nginx vhost routing loop, Hermes service not bound to loopback, "
                "or local firewall/SELinux policy."
            )
        logging.error(f"API call failed: {e}. timeout={timeout}")
        return None, process_api_error(e.response, sku=sku)
    except requests.exceptions.RequestException as e:
        logging.error(f"API call failed: {e}. timeout={timeout}")
        return None, process_api_error(e.response, sku=sku)
    except ValueError as e:
        current_app.logger.error(
            f"Failed to clean or parse JSON response: {e}")
        return None, render_friendly_error(
            message='The product service returned an unexpected response.',
            status_code=502,
            title='Unexpected service response'
        )