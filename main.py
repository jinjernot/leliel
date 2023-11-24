from config import ca_cert_path, client_cert_path, client_key_path, client_pfx_path, passphrase

import pandas as pd
import requests
import json

url = "https://hermesws.ext.hp.com/HermesWS/secure/v2/productcontent"
 
try:
    ca_cert = ca_cert_path
    client_cert = (client_cert_path, client_key_path)

    json_data = {
    "sku": [
      "8EP60AAE"
    ],
    "countryCode": "GB",
    "languageCode": "EN",
    "layoutName": "PDPCOMBO",
    "requestor": "HERMESQA-PRO",
    "reqContent": [
      "chunks",
      "images",
      "hierarchy",
      "plc"
    ]
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

       # Convert the API response to a DataFrame
        response_data = response.json()
        df = pd.json_normalize(response_data)

        # Save the DataFrame to an Excel file
        excel_file_path = "api_results.xlsx"
        df.to_excel(excel_file_path, index=False)

    else:
        print(f"Request failed with status code {response.status_code}")
        print(f"Response content: {response.text}")
except Exception as e:
    print(f"An error occurred: {e}")