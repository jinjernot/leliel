from flask import render_template
import requests
import json

from app.api.api_error import process_api_error
from config import client_cert_path, client_key_path, api_companions

def get_companions(sku, country_code, language_code):
    try:
        
        api_language_code = language_code
        if country_code == 'mx' and language_code == 'mx':
            api_language_code = 'mx'
        
        
        client_cert = (client_cert_path, client_key_path)
        json_data = {
            "sku": [sku],
            "reqLinkType": ["services", "accessories", "supplies"],
            "countryCode": country_code,
            "languageCode": api_language_code,
            "requestor": "TEST",
            "biDirectional": True,
            "layoutName": "IMAGE",
            "charLayoutName": "COMPANION-SPECS"
        }

        api_response = requests.post(
            api_companions,
            cert=client_cert,
            verify=False,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(json_data)
        )

        if api_response.status_code == 200:
            response_json = api_response.json()
            
            # Save the response to a JSON file
            #filename = f"api_response_companions_{sku}.json"
            #with open(filename, 'w') as json_file:
            #    json.dump(response_json, json_file, indent=4)
                
            return response_json
        else:
            return process_api_error(api_response)
            
    except Exception as e:
        error_message = f'An error occurred while fetching companions: {e}'
        return {'error': error_message}