import logging
import secrets
import os
import re
from flask import Flask, render_template, request, session, abort, current_app
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

from config import (CACHE_DIR, ALLOWED_COUNTRIES, ALLOWED_LANGUAGES,
                    PRODUCT_HIERARCHY, TOP_COMPONENTS,
                    TECH_SPEC_GROUP_ORDER, PRODUCT_TEMPLATES_CONFIG,
                    PRINTER_PRODUCT_TYPES, MM_BLOCKS_CONFIG, FEATURE_BLOCKS_CONFIG, COUNTRY_NAMES, LOCALE_NAMES, TRANSLATIONS)
from app.api.get_product import get_product, get_product_by_params
from app.api.client import get_product_locales
from app.api.api_error import render_friendly_error

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['API_URL'] = os.environ.get('API_URL')
app.config['API_PCB_URL'] = os.environ.get('API_PCB_URL')
app.config['API_CONNECT_TIMEOUT'] = float(os.environ.get('API_CONNECT_TIMEOUT', '3'))
app.config['API_READ_TIMEOUT'] = float(os.environ.get('API_READ_TIMEOUT', '20'))
app.config['CACHE_DIR'] = CACHE_DIR
app.config['ALLOWED_COUNTRIES'] = ALLOWED_COUNTRIES
app.config['ALLOWED_LANGUAGES'] = ALLOWED_LANGUAGES
app.config['PRODUCT_HIERARCHY'] = PRODUCT_HIERARCHY
app.config['TOP_COMPONENTS'] = TOP_COMPONENTS
app.config['TECH_SPEC_GROUP_ORDER'] = TECH_SPEC_GROUP_ORDER
app.config['PRODUCT_TEMPLATES_CONFIG'] = PRODUCT_TEMPLATES_CONFIG
app.config['PRINTER_PRODUCT_TYPES'] = PRINTER_PRODUCT_TYPES
app.config['MM_BLOCKS_CONFIG'] = MM_BLOCKS_CONFIG
app.config['FEATURE_BLOCKS_CONFIG'] = FEATURE_BLOCKS_CONFIG
app.config['COUNTRY_NAMES'] = COUNTRY_NAMES
app.config['LOCALE_NAMES'] = LOCALE_NAMES
app.config['TRANSLATIONS'] = TRANSLATIONS

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
app.use_static_for = 'static'

logging.basicConfig(level=logging.INFO)

@app.after_request
def apply_security_headers(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response

# Route for testing products without qr code
@app.route('/main')
def index():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return render_template('index.html', csrf_token=session['_csrf_token'])

@app.route('/get_product', methods=['POST'])
def call_get_product():
    submitted_token = request.form.get('csrf_token')
    expected_token = session.pop('_csrf_token', None)

    if not expected_token or submitted_token != expected_token:
        abort(400, 'Invalid CSRF token. Please try submitting the form again.')

    return get_product()

# QR code route
@app.route('/')
def call_get_product_from_qr():
    sku = request.args.get('pn')
    country = request.args.get('cc')
    language = request.args.get('ll')

    if not sku:
        return render_friendly_error(
            message='The product number is missing from the link.',
            status_code=400,
            title='Missing product information',
            details='Please scan the QR code again or verify the URL contains the pn parameter.'
        )

    if not re.match(r'^[a-zA-Z0-9\-\/]+$', sku):
        return render_friendly_error(
            message='The product number format is invalid.',
            status_code=400,
            title='Invalid product number'
        )

    if not country or not language:
        locales = get_product_locales(sku)
        return render_template(
            'product_template.html',
            pn=sku,
            config=current_app.config.get('PRODUCT_TEMPLATES_CONFIG'),
            locales=locales,
            locale_names=current_app.config['LOCALE_NAMES']
        )
    
    if country.lower() not in current_app.config['ALLOWED_COUNTRIES'] or \
       language.lower() not in current_app.config['ALLOWED_LANGUAGES']:
        locale_options = get_product_locales(sku)
        return render_friendly_error(
            message='The selected country/language is not supported for this request.',
            status_code=400,
            title='Invalid location selection',
            details='Please choose one of the available country/language options below.',
            sku=sku,
            current_locale=f"{country.lower()}-{language.lower()}",
            locale_options=locale_options
        )
    
    return get_product_by_params(sku, country, language)

if __name__ == '__main__':
    app.run(debug=False)