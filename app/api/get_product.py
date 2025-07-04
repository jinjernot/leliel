from flask import render_template, request
import requests
import json

from app.api.process_product import process_api_response
from app.api.api_error import process_api_error
from config import client_cert_path, client_key_path, api_productcontent

def get_product():
    try:
        # Extract data from the request
        client_cert = (client_cert_path, client_key_path)
        sku = request.form.get('sku', '').strip()
        country_code = request.form.get('country', '').strip()
        language_code = request.form.get('language', '').strip()

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
            api_productcontent,
            cert=client_cert,
            verify=False,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
        )

        # Check if request was successful
        if api_response.status_code == 200:
            response_json = api_response.json()
            filename = f"api_response_product_{sku}.json"  # Set the filename for the JSON file
            with open(filename, 'w') as json_file:
                json.dump(response_json, json_file, indent=4)

            return process_api_response(response_json, sku)
        else:
            return process_api_error(api_response)
    except Exception as e:
        error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message), 400

def get_product_by_params(sku, country_code, language_code):
    try:
       
        api_language_code = language_code
        if country_code == 'mx' and language_code == 'mx':
            api_language_code = 'mx'
       

        client_cert = (client_cert_path, client_key_path)
        # Prepare JSON data to be sent to the API
        json_data = {
            "sku": [sku],
            "countryCode": country_code,
            "languageCode": api_language_code, # Use the mapped language code
            "layoutName": "ALL-Specs",
            "requestor": "APIQA-PRO",
            "reqContent": ["chunks", "images", "hierarchy", "plc"]
        }

        # Send POST request to the API
        api_response = requests.post(
            api_productcontent,
            cert=client_cert,
            verify=False,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
        )

        # Check if request was successful
        if api_response.status_code == 200:
            response_json = api_response.json()
            #filename = f"api_response_product_{sku}.json"
            #with open(filename, 'w') as json_file:
            #    json.dump(response_json, json_file, indent=4)
            return process_api_response(response_json, sku)
        else:
            return process_api_error(api_response)
    except Exception as e:
        error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message), 400