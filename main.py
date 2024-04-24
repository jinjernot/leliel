from config import client_cert_path, client_key_path, url
from flask import Flask, render_template, request
from app.laptop_template import build_template
import requests
import config
import json

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
        sku = request.form.get('sku')
        country_code = request.form.get('country')
        language_code = request.form.get('language')

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

            # Validate JSON response
            response_json = api_response.json()
            product = response_json.get('products', {}).get(sku, {})
            product_hierarchy = product.get('productHierarchy', {})
            product_type = product_hierarchy.get('productType', {})
            pmoid = product_type.get('pmoid', '')

            # Check if the product type is a laptop
            if pmoid != "321957":
                return render_template('error.html', error_message="The product is not a laptop."), 400

            # Build template using response data
            df = build_template(api_response)

            # Render product template with obtained data
            rendered_template = render_template('product.html', df=df)

            # Save the rendered HTML content to a file with explicit encoding
            #with open("output.html", "w", encoding="utf-8") as html_file:
            #    html_file.write(rendered_template)

            return rendered_template
        else:
            # Handle failed requests
            print(f"Request failed with status code {api_response.status_code}")
            print(f"response content: {api_response.text}")
            response_json = api_response.json()

            if response_json.get('status') == 'Error' and response_json.get('statusMessage') == 'Invalid Country or Language Code':
                error_message = "Invalid Country or Language Code"
                return render_template('error.html', error_message=error_message), 400

            if response_json.get('Status') == 'ERROR' and response_json.get('StatusMessage') == 'Country Code provided is Invalid':
                error_message = "Non publishable Product"
                return render_template('error.html', error_message=error_message), 400
            
            if response_json.get('status') == 'Success' and response_json.get('statusMessage') == 'Non publishable Product':
                error_message = "Non publishable Product"
                return render_template('error.html', error_message=error_message), 400

    except Exception as e:
        # Handle exceptions
        error_message = f"An error occurred: {e}"
        print(error_message)
        return render_template('error.html', error_message=error_message), 400