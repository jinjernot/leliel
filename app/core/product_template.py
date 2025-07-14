import pandas as pd
import json

def build_product_template(api_response):
    # Check if api_response is a dictionary
    if not isinstance(api_response, dict):
        try:
            api_response = api_response.json()
        except AttributeError:
            print("Error: Unable to convert the response to a dictionary.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    all_details_with_order = []
    df_images_data = []
    footnotes_data = []
    df_disclaimers_data = []

    # Extract product data
    products = api_response.get('products', {})
    for sku in api_response.get('request', {}).get('sku', []):
        product_data = products.get(sku, {})
        chunks = product_data.get('chunks', [])
        images = product_data.get('images', [])

        # Process chunks to get all tech specs and their display order
        for chunk in chunks:
            if 'details' in chunk:
                group_name = chunk.get('group')
                if group_name == 'PRISM_Footnotes':
                    footnotes_data.extend(chunk['details'])
                # Exclude specified groups, but still process "PRISM_Legal Information" for disclaimers
                elif group_name in ['PRISM_Product Names', 'PRISM_Product Description', 'PRISM_Legal Information', 'PRISM_Key Selling Points', 'PRISM_Playbook Icons', 'PRISM_Metadata', 'PRISM_System Internal','PRISM_Core Features', 'PRISM_Features', 'PRISM_Category', 'PRISM_PSG_Accessories_Headsets[TS]','PRISM_Product Lines']:
                    if group_name == 'PRISM_Legal Information':
                        df_disclaimers_data.extend(chunk['details'])
                    continue  # Skip these chunks from the main tech specs
                else:
                    group_order = chunk.get('contentDisplayOrder', 0)
                    for detail in chunk['details']:
                        if 'tag' in detail and 'value' in detail:
                            detail_with_order = detail.copy()
                            detail_with_order['groupOrder'] = group_order
                            all_details_with_order.append(detail_with_order)
        
        # Define the priority for image orientations
        priority_orientations = ["Center facing", "Left facing", "Right facing"]
        
        # Process images, filtering for 400px width and png type
        for image in images:
            if 'details' in image:
                for detail in image['details']:
                    if detail.get('pixelWidth') == '400' and detail.get('type') == 'png' and 'imageUrlHttps' in detail:
                        orientation = detail.get('orientation', '')
                        # Assign a priority number to each image based on its orientation
                        try:
                            priority = priority_orientations.index(orientation)
                        except ValueError:
                            priority = len(priority_orientations)

                        df_images_data.append({
                            'orientation': orientation,
                            'pixelWidth': detail.get('pixelWidth'),
                            'type': detail.get('type'),
                            'imageUrlHttps': detail.get('imageUrlHttps'),
                            'priority': priority
                        })

    # Sort images by the assigned priority
    df_images_data.sort(key=lambda x: x.get('priority', len(priority_orientations)))

    # Sort all details based on the group order first, then by their own order
    all_details_with_order.sort(key=lambda x: (x.get('groupOrder', 0), x.get('displayOrder', 0)))

    # Create DataFrames from the sorted lists
    df = pd.DataFrame(all_details_with_order)
    df_images = pd.DataFrame(df_images_data)
    df_footnotes = pd.DataFrame(footnotes_data)
    df_disclaimers = pd.DataFrame(df_disclaimers_data)

    return df, df_images, df_footnotes, df_disclaimers