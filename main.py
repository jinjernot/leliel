from config import client_cert_path, client_key_path, url
from flask import Flask, render_template, request
from app.template import build_template
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
    """
    Renders the index.html page.

    Returns:
        str: Rendered HTML for the index page.
    """
    return render_template('index.html')

# Route for getting product data via POST request
@app.route('/get_product', methods=['POST'])
def get_product():
    """
    Retrieves product data based on form input and renders the product.html page.

    Returns:
        str: Rendered HTML for the product page.
    """
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

            # Build template using response data
            df = build_template(api_response)

            # Render product template with obtained data
            rendered_template = render_template('product.html', df=df)
            
            # Save the rendered HTML content to a file with explicit encoding
            with open("output.html", "w", encoding="utf-8") as html_file:
                html_file.write(rendered_template)
            
            return rendered_template
        else:
            # Handle failed requests
            print(f"Request failed with status code {api_response.status_code}")
            print(f"response content: {api_response.text}")
            
    except Exception as e:
        # Handle exceptions
        print(f"An error occurred: {e}")
        return render_template('error.html'), 400

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
