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

    all_details_with_order = []
    df_images_data = []

    # Extract product data
    products = api_response.get('products', {})
    for sku in api_response.get('request', {}).get('sku', []):
        product_data = products.get(sku, {})
        chunks = product_data.get('chunks', [])
        images = product_data.get('images', [])

        # Process chunks to get all tech specs and their display order
        for chunk in chunks:
            if 'details' in chunk:
                # Get the display order for the whole group
                group_order = chunk.get('contentDisplayOrder', 0)
                for detail in chunk['details']:
                    if 'tag' in detail and 'value' in detail:
                        # Add the group's order to each individual detail
                        detail_with_order = detail.copy()
                        detail_with_order['groupOrder'] = group_order
                        all_details_with_order.append(detail_with_order)
        
        # Process images
        image_tags = ["Center facing", "Left facing", "Right facing", "Rear facing", "Left rear facing", "Top view closed", "Detail view", "Left profile closed", "Right profile closed", "Right rear facing", "Left and Right facing"]
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

    # Sort all details based on the group order first, then by their own order
    all_details_with_order.sort(key=lambda x: (x.get('groupOrder', 0), x.get('displayOrder', 0)))

    # Create DataFrames from the sorted list
    df = pd.DataFrame(all_details_with_order)
    df_images = pd.DataFrame(df_images_data)

    return df, df_images