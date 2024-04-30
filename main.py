from app.core.ink_printer_template import build_template_ink
from app.core.monitor_template import build_template_monitor
from app.core.laptop_template import build_template_laptop
from config import client_cert_path, client_key_path, url

from flask import Flask, render_template, request
import requests
import config
import json
import os

# Initialize Flask application
app = Flask(__name__)
app.use_static_for = 'static'

# Configuration
app.config.from_object(config)

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
        sku = request.form.get('sku').strip() if request.form.get('sku') else None
        country_code = request.form.get('country').strip() if request.form.get('country') else None
        language_code = request.form.get('language').strip() if request.form.get('language') else None

        # Prepare JSON data to be sent to the API
        json_data = {
            "sku": [sku],
            "countryCode": country_code,
            "languageCode": language_code,
            "layoutName": "PDPCOMBO",
            "requestor": "HERMESQA-PRO",
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
            print("Request successful!")

            # Save the API response JSON to a file
            response_json_file_path = os.path.join(app.static_folder, 'api_response.json')
            with open(response_json_file_path, 'w') as json_file:
                json.dump(api_response.json(), json_file)
            print(f"API response JSON saved to {response_json_file_path}")

            # Validate JSON response
            response_json = api_response.json()
            product = response_json.get('products', {}).get(sku, {})
            product_hierarchy = product.get('productHierarchy', {})
            product_type = product_hierarchy.get('productType', {})
            pmoid = product_type.get('pmoid', '')

            # Product Selection
            if pmoid == '321957': # Laptop
                df = build_template_laptop(api_response)
                rendered_template = render_template('laptop.html', df=df)

            elif product_hierarchy.get('marketingCategory', {}).get('pmoid') == '238444': # Ink_Printer
                df = build_template_ink(api_response)
                rendered_template = render_template('ink_printer.html', df=df)

            elif product_hierarchy.get('productType', {}).get('pmoid') == '382087': # Monitor
                df = build_template_monitor(api_response)
                rendered_template = render_template('monitor.html', df=df)
                
            else:
                return render_template('error.html', error_message='The product is not supported.'), 400

            return rendered_template
        else:
            print(f"Request failed with status code {api_response.status_code}")
            print(f"response content: {api_response.text}")
            response_json = api_response.json()

            if response_json.get('status') == 'Error' and response_json.get('statusMessage') == 'Invalid Country or Language Code':
                error_message = 'Invalid Country or Language Code'
                return render_template('error.html', error_message=error_message), 400
            
            if response_json.get('Status') == 'ERROR' and response_json.get('StatusMessage') == 'Country Code provided is Invalid':
                error_message = 'Non publishable Product'
                return render_template('error.html', error_message=error_message), 400
            
            if response_json.get('status') == 'Success' and response_json.get('statusMessage') == 'Non publishable Product':
                error_message = 'Non publishable Product'
                return render_template('error.html', error_message=error_message), 400
            
        return render_template('error.html', error_message='The product is not supported.'), 400

    except Exception as e:
        error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message), 400

if __name__ == '__main__':
    app.run(debug=True)
