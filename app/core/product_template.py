import pandas as pd
import json
from flask import current_app

def build_product_template(api_response):
    """
    Builds the product template data structures from the API response.
    """

    if not isinstance(api_response, dict):
        try:
            api_response = api_response.json()
        except AttributeError:
            print("Error: Unable to convert the response to a dictionary.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}, None

    # Load config from the application context
    config = current_app.config.get('PRODUCT_TEMPLATES_CONFIG', {})
    excluded_tags = config.get('EXCLUDED_TECHSPEC_TAGS', [])
    excluded_groups = config.get('EXCLUDED_TECHSPEC_GROUPS', [])
    priority_orientations = config.get('IMAGE_PRIORITY_ORIENTATIONS', [])
    image_pixel_width = config.get('IMAGE_PIXEL_WIDTH', '573')
    image_type = config.get('IMAGE_TYPE', 'png')
    video_asset_category = config.get('VIDEO_ASSET_CATEGORY', "Video - 360 Spin")

    all_details_with_order = []
    tech_specs_by_group = {}
    df_images_data = []
    footnotes_data = []
    df_disclaimers_data = []
    processed_orientations = set()
    primary_product_color = None
    video_data = None

    products = api_response.get('products', {})
    for sku, product_data in products.items():
        content = product_data.get('content', {})
        images = product_data.get('images', [])
        footnotes = product_data.get('footnotes', [])
        videos = product_data.get('videos', [])

        for tag, details in content.items():
            if 'tag' not in details:
                details['tag'] = tag
            
            all_details_with_order.append(details)
            
            if (details.get('type') == 'techspecs' and
                details.get('tag') not in excluded_tags and
                details.get('group') not in excluded_groups):

                group = details.get('group', 'Other')
                if group not in tech_specs_by_group:
                    tech_specs_by_group[group] = []
                tech_specs_by_group[group].append(details)

        temp_images = []
        for detail in images:
            if detail.get('pixelWidth') == image_pixel_width and detail.get('type') == image_type and 'imageUrlHttps' in detail:
                orientation = detail.get('orientation', '')
                try:
                    priority = priority_orientations.index(orientation)
                except ValueError:
                    priority = len(priority_orientations)
                temp_images.append({**detail, 'priority': priority})

        if temp_images:
            temp_images.sort(key=lambda x: x.get('priority'))
            primary_product_color = temp_images[0].get('productColor')

        for detail in images:
            orientation = detail.get('orientation', '')
            product_color = detail.get('productColor')

            if (detail.get('pixelWidth') == image_pixel_width and
                detail.get('type') == image_type and
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

        for footnote in footnotes:
            if footnote.get('type') == 'footnote':
                footnotes_data.append(footnote)
            elif footnote.get('type') == 'legal_disclaimer':
                 df_disclaimers_data.append(footnote)

        for video in videos:
            if video.get("assetCategory") == video_asset_category:
                video_data = {
                    "assetUrl": video.get("assetUrl"),
                    "previewURL": video.get("previewURL")
                }
                break

    df_images_data.sort(key=lambda x: x.get('priority'))
    for group in tech_specs_by_group:
        tech_specs_by_group[group].sort(key=lambda x: x.get('displayOrder', 0))
    df = pd.DataFrame(all_details_with_order)
    df_images = pd.DataFrame(df_images_data)
    df_footnotes = pd.DataFrame(footnotes_data)
    df_disclaimers = pd.DataFrame(df_disclaimers_data)

    return df, df_images, df_footnotes, df_disclaimers, tech_specs_by_group, video_data