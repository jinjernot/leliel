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
    for sku, product_data in products.items():
        content = product_data.get('content', {})
        images = product_data.get('images', [])
        footnotes = product_data.get('footnotes', [])


        # Process content to get all tech specs and their display order
        for tag, details in content.items():
            # Only include content of type 'techspecs'
            if details.get('type') == 'techspecs':
                detail_with_order = details.copy()
                all_details_with_order.append(detail_with_order)

        # Define the priority for image orientations
        priority_orientations = ["Center facing", "Left facing", "Right facing"]

        # Process images, filtering for 573px width and png type
        for detail in images:
            if detail.get('pixelWidth') == '573' and detail.get('type') == 'png' and 'imageUrlHttps' in detail:
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
        
        # Process footnotes
        for footnote in footnotes:
            if footnote.get('type') == 'footnote':
                footnotes_data.append(footnote)
            elif footnote.get('type') == 'legal_disclaimer':
                 df_disclaimers_data.append(footnote)


    # Sort images by the assigned priority
    df_images_data.sort(key=lambda x: x.get('priority', len(priority_orientations)))

    # Sort all details based on their displayOrder
    all_details_with_order.sort(key=lambda x: x.get('displayOrder', 0))

    # Create DataFrames from the sorted lists
    df = pd.DataFrame(all_details_with_order)
    df_images = pd.DataFrame(df_images_data)
    df_footnotes = pd.DataFrame(footnotes_data)
    df_disclaimers = pd.DataFrame(df_disclaimers_data)


    return df, df_images, df_footnotes, df_disclaimers