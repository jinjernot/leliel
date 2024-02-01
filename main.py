from config import ca_cert_path, client_cert_path, client_key_path, url
from flask import Flask, render_template, request
from app.template import build_template
import requests
import json
import config


app = Flask(__name__)
app.use_static_for = 'static'

# Configuration
app.config.from_object(config)

@app.route('/app4')
def index():
    return render_template('index.html')

@app.route('/get_product', methods=['POST'])
def get_product():
    
    try:
        print("Entering try block")
        print(f"CA Cert Path: {ca_cert_path}")
        print(f"Client Cert Path: {client_cert_path}")
        print(f"Client Key Path: {client_key_path}")
        ca_cert = ca_cert_path
        client_cert = (client_cert_path, client_key_path)
        sku = request.form.get('sku')
        country_code = request.form.get('country')
        language_code = request.form.get('language')

        json_data = {
            "sku": [sku],
            "countryCode": country_code,
            "languageCode": language_code,
            "layoutName": "PDPCOMBO",
            "requestor": "HERMESQA-PRO",
            "reqContent": ["chunks", "images", "hierarchy", "plc"]
        }

        api_response = requests.post(
            url,
            cert=client_cert,
            verify=ca_cert,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
        )

        if api_response.status_code == 200:
            print("Request successful!")

            #with open("api_response.json", "w") as json_file:
            #    json.dump(api_response.json(), json_file)
            product_data = api_response.json()

            df = build_template(api_response)
            
            #rendered_template = render_template("product.html", product_data=product_data)

                # Save the rendered template to a new HTML file
            #with open("output_product.html", "w", encoding="utf-8") as output_file:
            #    output_file.write(rendered_template)

            return render_template('product.html', df=df)
        else:
            print(f"Request failed with status code {api_response.status_code}")
            print(f"response content: {api_response.text}")
    except Exception as e:
        print(f"An error occurred: {e}"), 500
    return render_template('error.html'), 400

if __name__ == '__main__':
    app.run(debug=True)
