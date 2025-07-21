import pandas as pd
import json

def build_product_template(api_response):
    # Check if api_response is a dictionary
    if not isinstance(api_response, dict):
        try:
            api_response = api_response.json()
        except AttributeError:
            print("Error: Unable to convert the response to a dictionary.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}

    all_details_with_order = []
    tech_specs_by_group = {}  # Changed to a dictionary
    df_images_data = []
    footnotes_data = []
    df_disclaimers_data = []
    processed_orientations = set()
    primary_product_color = None

    # Extract product data
    products = api_response.get('products', {})
    for sku, product_data in products.items():
        content = product_data.get('content', {})
        images = product_data.get('images', [])
        footnotes = product_data.get('footnotes', [])

        # Process content
        for tag, details in content.items():
            all_details_with_order.append(details)
            if details.get('type') == 'techspecs' and details.get('tag') not in ['promolink', 'codename', 'tangibleflag', 'energyeffcompal', 'carepackregistrationflag', 'custfacingdes']:
                group = details.get('group', 'Other')
                if group not in tech_specs_by_group:
                    tech_specs_by_group[group] = []
                tech_specs_by_group[group].append(details)

        # First pass to determine the primary product color
        temp_images = []
        priority_orientations = ["Center facing", "Left facing", "Right facing"]
        for detail in images:
            if detail.get('pixelWidth') == '573' and detail.get('type') == 'png' and 'imageUrlHttps' in detail:
                orientation = detail.get('orientation', '')
                try:
                    priority = priority_orientations.index(orientation)
                except ValueError:
                    priority = len(priority_orientations)
                temp_images.append({**detail, 'priority': priority})
        
        if temp_images:
            temp_images.sort(key=lambda x: x.get('priority'))
            primary_product_color = temp_images[0].get('productColor')

        # Second pass to build the final image list
        for detail in images:
            orientation = detail.get('orientation', '')
            product_color = detail.get('productColor')
            
            if (detail.get('pixelWidth') == '573' and
                detail.get('type') == 'png' and
                'imageUrlHttps' in detail and
                orientation not in processed_orientations and
                product_color == primary_product_color):

                processed_orientations.add(orientation)
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

        # Process footnotes
        for footnote in footnotes:
            if footnote.get('type') == 'footnote':
                footnotes_data.append(footnote)
            elif footnote.get('type') == 'legal_disclaimer':
                 df_disclaimers_data.append(footnote)

    # Sort images and tech specs within each group
    df_images_data.sort(key=lambda x: x.get('priority'))
    for group in tech_specs_by_group:
        tech_specs_by_group[group].sort(key=lambda x: x.get('displayOrder', 0))

    # Create DataFrames
    df = pd.DataFrame(all_details_with_order)
    df_images = pd.DataFrame(df_images_data)
    df_footnotes = pd.DataFrame(footnotes_data)
    df_disclaimers = pd.DataFrame(df_disclaimers_data)

    return df, df_images, df_footnotes, df_disclaimers, tech_specs_by_group