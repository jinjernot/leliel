import requests
import json




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
    else:
        print(f"Request failed with status code {response.status_code}")
        print(f"Response content: {response.text}")
except Exception as e:
    print(f"An error occurred: {e}")