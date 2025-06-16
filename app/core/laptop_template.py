import pandas as pd
import json

def build_template_laptop(api_response):
    # Check if api_response is a dictionary
    if not isinstance(api_response, dict):
        try:
            api_response = api_response.json()
        except AttributeError:
            print("Error: Unable to convert the response to a dictionary.")
            return pd.DataFrame(), pd.DataFrame()

    # Load tag data from JSON file
    # Use the appropriate path for your server or local environment
    try:
        with open("app/data/tags_laptop.json", "r") as f: # Server
            tags_data = json.load(f)
    except FileNotFoundError:
        with open("app/data/tags_laptop.json", "r") as f: # Local
            tags_data = json.load(f)


    # Extract tags
    all_tags = tags_data.get("atf_tags", []) + tags_data.get("btf_tags", [])
    image_tags = tags_data.get("image_tags", [])

    # Initialize lists to hold data
    df_data = []
    df_images_data = []

    # Extract product data
    products = api_response.get('products', {})
    for sku in api_response.get('request', {}).get('sku', []):
        product_data = products.get(sku, {})
        chunks = product_data.get('chunks', [])
        images = product_data.get('images', [])

        # Process chunks
        for chunk in chunks:
            if 'details' in chunk:
                for detail in chunk['details']:
                    if detail.get('tag') in all_tags and 'value' in detail:
                        df_data.append({'tag': detail['tag'], 'name': detail.get('name', ''), 'value': detail['value']})

        # Process images
        for image in images:
            if 'details' in image:
                for detail in image['details']:
                    if detail.get('orientation') in image_tags and 'imageUrlHttps' in detail:
                        df_images_data.append({
                            'orientation': detail.get('orientation'),
                            'pixelWidth': detail.get('pixelWidth'),
                            'type': detail.get('type'),
                            'imageUrlHttps': detail.get('imageUrlHttps')
                        })

    # Create DataFrames from lists
    df = pd.DataFrame(df_data)
    df_images = pd.DataFrame(df_images_data)

    return df, df_images