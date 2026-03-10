from flask import render_template, current_app
import json
import logging


def _normalize_locale(locale):
    """Normalize locale values to `cc-ll` lowercase format."""
    if not locale:
        return None
    normalized = str(locale).strip().replace('_', '-').lower()
    parts = normalized.split('-')
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return f"{parts[0]}-{parts[1]}"


def render_friendly_error(
    message,
    status_code=400,
    title='We could not load this product page',
    details=None,
    sku=None,
    current_locale=None,
    locale_options=None
):
    """Render a user-friendly error page with optional locale alternatives."""
    normalized_current_locale = _normalize_locale(current_locale)
    normalized_options = []

    for locale in locale_options or []:
        normalized = _normalize_locale(locale)
        if normalized and normalized not in normalized_options:
            normalized_options.append(normalized)

    return (
        render_template(
            'error.html',
            error_title=title,
            error_message=message,
            error_details=details,
            sku=sku,
            current_locale=normalized_current_locale,
            locale_options=normalized_options,
            locale_names=current_app.config.get('LOCALE_NAMES', {})
        ),
        status_code
    )


def render_locale_unavailable_error(sku, country_code, language_code, locale_options=None):
    """Render a specific error when SKU is not available for the requested locale."""
    current_locale = f"{(country_code or '').lower()}-{(language_code or '').lower()}"
    return render_friendly_error(
        title='This product page is not available in your selected country',
        message='The requested product is not currently published for this country/language combination.',
        details='Please choose another country/language option below to continue.',
        status_code=404,
        sku=sku,
        current_locale=current_locale,
        locale_options=locale_options or []
    )


def process_api_error(api_response):
    """
    Processes API error responses and returns appropriate error pages.
    """
    try:
        if api_response is None:
            logging.error("API request failed before receiving an HTTP response.")
            return render_friendly_error(
                message='The request timed out or could not connect to the product service.',
                status_code=504,
                title='Service temporarily unavailable',
                details='Please try again in a moment.'
            )

        error_text = getattr(api_response, 'text', '')
        logging.error(f"API Error Response: {error_text}")

        response_json = api_response.json()

        # Check for "Non publishable Product" first
        if response_json.get('Status') == 'Success' and response_json.get('StatusMessage') == 'Non publishable Product':
            return render_friendly_error(
                message='This product page is not published for public viewing.',
                status_code=400,
                title='Product page unavailable'
            )

        # Then, check for other API errors
        if response_json.get('Status') == 'ERROR':
            error_message = response_json.get(
                'StatusMessage', 'An unknown API error occurred.')
            return render_friendly_error(
                message=error_message,
                status_code=400,
                title='Could not load product information'
            )

    except json.JSONDecodeError:
        return render_friendly_error(
            message='The product service returned an unexpected response.',
            status_code=400,
            title='Unexpected service response'
        )
    except Exception as e:
        return render_friendly_error(
            message='An unexpected error occurred while loading this page.',
            status_code=500,
            title='Something went wrong',
            details=str(e)
        )

    return render_friendly_error(
        message='An unknown error occurred while loading this product page.',
        status_code=500,
        title='Something went wrong'
    )
