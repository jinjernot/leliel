from flask import Flask, render_template, request
import requests
import json
import logging
from app.core.ink_printer_template import build_template_ink
from app.core.monitor_template import build_template_monitor
from app.core.laptop_template import build_template_laptop
from config import client_cert_path, client_key_path, url
import config

# Initialize Flask application
app = Flask(__name__)
app.use_static_for = 'static'

# Configuration
app.config.from_object(config)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Route for the index page
@app.route('/app4')
def index():
    return render_template('index.html')

# Route for getting product data via POST request
@app.route('/get_product', methods=['POST'])
def get_product():
    try:
        # Extract necessary data from the request
        client_cert = (client_cert_path, client_key_path)
        sku = request.form.get('sku', '').strip()
        country_code = request.form.get('country', '').strip()
        language_code = request.form.get('language', '').strip()

        if not sku or not country_code or not language_code:
            return render_template('error.html', error_message='Missing required parameters'), 400

        # Prepare JSON data to be sent to the API
        json_data = {
            "sku": [sku],
            "countryCode": country_code,
            "languageCode": language_code,
            "layoutName": "ALL-Specs",
            "requestor": "APIQA-PRO",
            "reqContent": ["chunks", "images", "hierarchy", "plc"]
        }

        # Send POST request to the API
        api_response = requests.post(
            url,
            cert=client_cert,
            verify=False,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
        )

        # Check if request was successful
        if api_response.status_code == 200:
            logging.info("Request successful!")
            response_json = api_response.json()
            return process_response(response_json, sku)
        else:
            logging.error(f"Request failed with status code {api_response.status_code}")
            logging.error(f"Response content: {api_response.text}")
            return handle_api_error(api_response)
    except Exception as e:
        logging.exception("An error occurred while processing the request")
        error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message), 400

def process_response(response_json, sku):
    product = response_json.get('products', {}).get(sku, {})
    product_hierarchy = product.get('productHierarchy', {})
    pmoid = product_hierarchy.get('productType', {}).get('pmoid', '')

    if pmoid == '321957':  # Laptop
        df, df_images = build_template_laptop(response_json)
        return render_template('laptop.html', df=df, df_images=df_images)
    elif product_hierarchy.get('marketingCategory', {}).get('pmoid') == '238444':  # Ink_Printer
        df = build_template_ink(response_json)
        return render_template('ink_printer.html', df=df)
    elif product_hierarchy.get('productType', {}).get('pmoid') == '382087':  # Monitor
        df = build_template_monitor(response_json)
        return render_template('monitor.html', df=df)
    else:
        return render_template('error.html', error_message='The product is not supported (yet)'), 400

def handle_api_error(api_response):
    try:
        response_json = api_response.json()
        if response_json.get('status') == 'Error':
            error_message = response_json.get('statusMessage', 'An error occurred')
            if error_message in ['Invalid Country or Language Code', 'Non publishable Product']:
                return render_template('error.html', error_message=error_message), 400
        if response_json.get('status') == 'Success' and response_json.get('statusMessage') == 'Non publishable Product':
            error_message = 'Non publishable Product'
            return render_template('error.html', error_message=error_message), 400
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON response")

    return render_template('error.html', error_message='An unknown error occurred'), 400

if __name__ == '__main__':
    app.run(debug=True)
