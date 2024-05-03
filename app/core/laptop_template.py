import pandas as pd
import json

def build_template_laptop(api_response):
    # Ensure api_response is a dictionary
    if not isinstance(api_response, dict):
        try:
            api_response = api_response.json()
        except AttributeError:
            print("Error: Unable to convert the response to a dictionary.")
            return {}

    # Load tag data from JSON file
    with open("app/data/tags_laptop.json", "r") as f:
        tags_data = json.load(f)

    # Extract tags
    atf_tags = tags_data["atf_tags"]
    btf_tags = tags_data["btf_tags"]
    all_tags = atf_tags + btf_tags
    image_tags = tags_data["image_tags"]

    # Initialize DataFrames
    df = pd.DataFrame(columns=['tag', 'name', 'value'])
    df_images = pd.DataFrame(columns=['orientation', 'pixelWidth', 'imageUrlHttps'])

    # Extract product data
    products = api_response.get('products', {})
    for sku in api_response['request']['sku']:
        chunks = products.get(sku, {}).get('chunks', [])
        images = products.get(sku, {}).get('images', [])

        # Process chunks
        for chunk in chunks:
            if 'details' in chunk:
                for detail in chunk['details']:
                    if 'tag' in detail and detail['tag'] in all_tags and 'value' in detail:
                        df = df.append({'tag': detail['tag'], 'name': detail['name'], 'value': detail['value']}, ignore_index=True)

        # Process images
        for image in images:
            if 'details' in image:
                for detail in image['details']:
                    if 'orientation' in detail and detail['orientation'] in image_tags and 'imageUrlHttps' in detail:
                        df_images = df_images.append({'orientation': detail['orientation'], 'pixelWidth': detail['pixelWidth'], 'imageUrlHttps': detail['imageUrlHttps']}, ignore_index=True)

    # Save to Excel file with separate sheets
    with pd.ExcelWriter("excel.xlsx", engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='chunks')
        df_images.to_excel(writer, index=False, sheet_name='images')

    return df, df_images
