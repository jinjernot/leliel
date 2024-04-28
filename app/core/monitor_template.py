import pandas as pd
import json

def build_template_monitor(api_response):

    # Ensure api_response is a dictionary
    if not isinstance(api_response, dict):
        try:
            api_response = api_response.json() 
        except AttributeError:
            print("Error: Unable to convert the response to a dictionary.")
            return {}

    # Load the tags from a JSON file
    #with open("/opt/ais/app/python/api/app/data/tags_monitor.json", "r") as f:
    with open("app/data/tags_monitor.json", "r") as f:
        tags_data = json.load(f)

    # ATF Content
    atf_tags = tags_data["atf_tags"]

    # BTF Content
    btf_tags = tags_data["btf_tags"]

    # Combine ATF and BTF tags
    all_tags = atf_tags + btf_tags

    # Images
    image_tags = tags_data["image_tags"]

    # Create an empty DataFrame to store the details
    df = pd.DataFrame(columns=['tag', 'name', 'value'])

    # Access the 'products' dictionary in the API api_response
    products = api_response.get('products', {})

    # Iterate through the 'sku' values in the 'request' dictionary
    for sku in api_response['request']['sku']:
        # Access the 'chunks' list for each 'sku'
        chunks = products.get(sku, {}).get('chunks', [])
        images = products.get(sku, {}).get('images', [])
        # Iterate through the chunks in the API api_response
        for chunk in chunks:
            # Check if 'details' key is present in the chunk
            if 'details' in chunk:
                # Iterate through the details in the chunk
                for detail in chunk['details']:
                    if 'tag' in detail and detail['tag'] in all_tags and 'value' in detail:
                        df = df.append({'tag': detail['tag'], 'name': detail['name'], 'value': detail['value']}, ignore_index=True)

        # Get the images
        for image in images:
            # Check if 'details' key is present in the chunk
            if 'details' in image:
                # Iterate through the details in the chunk
                for detail in image['details']:
                    if 'orientation' in detail and detail['orientation'] in image_tags and 'imageUrlHttps' in detail:
                        df = df.append({'tag': detail['orientation'], 'name': 'image_url', 'value': detail['imageUrlHttps']}, ignore_index=True)

    # Save to an excel file
    #df.to_excel("/opt/ais/app/python/api/excel.xlsx", index=False, engine='xlsxwriter')

    return df