from app.core.product_template import build_product_template
from app.core.companion_template import build_template_companions
from app.api.get_companions import get_companions
from flask import render_template
import pandas as pd

def process_api_response(response_json, sku):
    # Extract data from the response using the SKU
    product = response_json.get('products', {}).get(sku, {})

    # Fetch companions
    country_code = response_json.get('request', {}).get('countryCode')
    language_code = response_json.get('request', {}).get('languageCode')
    companions_response = get_companions(sku, country_code, language_code)
    companions = build_template_companions(companions_response, sku)

    # Build the product template DataFrames
    df, df_images, df_footnotes = build_product_template(response_json)

    mm_blocks = []
    # Create a copy of the images DataFrame to track used images
    available_images = df_images.copy()

    # Iterate through potential KSPs (e.g., from 1 to 10)
    for i in range(1, 11):
        headline_tag = f'ksp_{i:02}_headline_medium'
        support_tag = f'ksp_{i:02}_suppt_01_long'

        # Check if the KSP headline or support text exists in the dataframe
        headline_series = df[df['tag'] == headline_tag]['value']
        support_series = df[df['tag'] == support_tag]['value']

        if not headline_series.empty or not support_series.empty:
            # If a KSP exists, find an available image
            if not available_images.empty:
                # Get the highest priority available image
                image_row = available_images.iloc[0]
                
                mm_blocks.append({
                    'headline': headline_series.iloc[0] if not headline_series.empty else '',
                    'support': support_series.iloc[0] if not support_series.empty else '',
                    'image_url': image_row['imageUrlHttps']
                })
                
                # Remove the used image from the available pool
                available_images = available_images.drop(available_images.index[0])

    # Render the template, passing the dynamically created mm_blocks
    return render_template('product_template.html', df=df, df_images=df_images, companions=companions, df_footnotes=df_footnotes, mm_blocks=mm_blocks)