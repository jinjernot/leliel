from config import ca_cert_path, client_cert_path, client_key_path, url

from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)
app.use_static_for = 'static'

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/get_product', methods=['POST'])
def get_product():
    try:
        ca_cert = ca_cert_path
        client_cert = (client_cert_path, client_key_path)

        sku = request.form.get('sku')
        country_code = request.form.get('country')

        json_data = {
            "sku": [sku],
            "countryCode": country_code,
            "languageCode": "EN",
            "layoutName": "PDPCOMBO",
            "requestor": "HERMESQA-PRO",
            "reqContent": ["chunks", "images", "hierarchy", "plc"]
        }

        response = requests.post(
            url,
            cert=client_cert,
            verify=ca_cert,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
        )

        if response.status_code == 200:
            print("Request successful!")
            print(response.json())
            #with open("api_response.json", "w") as json_file:
            #    json.dump(response.json(), json_file)
            product_data = response.json()

            return render_template("product.html", product_data=product_data)
        else:
            print(f"Request failed with status code {response.status_code}")
            print(f"Response content: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return render_template("error.html")

if __name__ == '__main__':
    app.run(debug=True)
