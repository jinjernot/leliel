from flask import render_template, request
import requests
import json

from app.api.process_qa import process_api_response, process_api_response_rich_media
from app.api.api_error import process_api_error
from config import client_cert_path, client_key_path, api_productcontent,api_richmedia

def get_qa():
    try:
        # Extract multiple SKUs from the request, split by commas
        client_cert = (client_cert_path, client_key_path)
        skus = request.form.get('sku', '').strip().split(',')  # Split by commas
        skus = [sku.strip() for sku in skus if sku.strip()]  # Remove surrounding spaces and empty SKUs
        country_code = request.form.get('country', '').strip()
        language_code = request.form.get('language', '').strip()

        # Prepare JSON data to be sent to the API
        json_data = {
            "sku": skus,
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
            filename = "api_response_qa.json"  # Set the filename for the JSON file
            with open(filename, 'w') as json_file:   
                json.dump(response_json, json_file)
            return process_api_response(response_json, skus)
        else:
            return process_api_error(api_response)
    except Exception as e:
        error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message), 400
    
    
def get_qa_rich_media():
    try:
        # Extract multiple SKUs from the request, split by commas
        client_cert = (client_cert_path, client_key_path)
        skus = request.form.get('sku', '').strip().split(',')  # Split by commas
        skus = [sku.strip() for sku in skus if sku.strip()]  # Remove surrounding spaces and empty SKUs
        country_code = request.form.get('country', '').strip()
        language_code = request.form.get('language', '').strip()

        # Prepare JSON data to be sent to the API
        json_data = {
            "skus": skus,
            "countryCode": country_code,
            "languageCode": language_code,
            "layoutName": "RICHMEDIA",
            "requestor": "APIQA-PRO",
        }

        # Send POST request to the API
        api_response = requests.post(
            api_richmedia,
            cert=client_cert,
            verify=False,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
        )

        # Check if request was successful
        if api_response.status_code == 200:
            print("entro a response 200")
            response_json = api_response.json()
            filename = "api_response_qa_rich_media.json"  # Set the filename for the JSON file
            with open(filename, 'w') as json_file:   
                json.dump(response_json, json_file)
            return process_api_response_rich_media(response_json, skus)
        else:
            return process_api_error(api_response)
    except Exception as e:
        error_message = f'An error occurred: {e}'
        return render_template('error.html', error_message=error_message), 400