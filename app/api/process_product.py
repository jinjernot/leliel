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
    df, df_images, df_footnotes, df_disclaimers = build_product_template(response_json)

    # --- Dynamically build MM blocks ---
    mm_blocks = []
    available_images = df_images.copy()
    for i in range(1, 11):
        headline_tag = f'ksp_{i:02}_headline_medium'
        support_tag = f'ksp_{i:02}_suppt_01_long'
        headline_series = df[df['tag'] == headline_tag]['value']
        support_series = df[df['tag'] == support_tag]['value']

        if not headline_series.empty or not support_series.empty:
            if not available_images.empty:
                image_row = available_images.iloc[0]
                mm_blocks.append({
                    'headline': headline_series.iloc[0] if not headline_series.empty else '',
                    'support': support_series.iloc[0] if not support_series.empty else '',
                    'image_url': image_row['imageUrlHttps']
                })
                available_images = available_images.drop(available_images.index[0])

    feature_blocks = []
    for i in range(1, 11):
        for j in range(1, 11):
            headline_tag = f'feature_{i:02}_headline_{j:02}_statement'
            support_tag = f'feature_{i:02}_suppt_{j:02}_medium'
            image_url_tag = f'feature_{i:02}_image_{j:02}_url'

            headline_series = df[df['tag'] == headline_tag]['value']
            support_series = df[df['tag'] == support_tag]['value']
            image_url_series = df[df['tag'] == image_url_tag]['value']

            if not headline_series.empty and not image_url_series.empty:
                feature_blocks.append({
                    'headline': headline_series.iloc[0],
                    'support': support_series.iloc[0] if not support_series.empty else '',
                    'image_url': image_url_series.iloc[0]
                })

    return render_template('product_template.html', df=df, df_images=df_images, companions=companions, df_footnotes=df_footnotes, df_disclaimers=df_disclaimers, mm_blocks=mm_blocks, feature_blocks=feature_blocks)