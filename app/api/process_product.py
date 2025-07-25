from app.core.product_template import build_product_template
from app.core.companion_template import build_template_companions
from flask import render_template
import pandas as pd

def process_api_response(response_json, sku):
    # Extract data from the response using the SKU
    product = response_json.get('products', {}).get(sku, {})

    # Build the companions template
    companions = build_template_companions(response_json, sku)

    # Build the product template DataFrames
    df, df_images, df_footnotes, df_disclaimers, tech_specs_by_group = build_product_template(response_json)

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
    # Limit to the first 4 feature blocks
    feature_count = 0
    for i in range(1, 11):
        if feature_count >= 4:
            break
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
                feature_count += 1
                if feature_count >= 4:
                    break

    return render_template('product_template.html', df=df, tech_specs_by_group=tech_specs_by_group, df_images=df_images, companions=companions, df_footnotes=df_footnotes, df_disclaimers=df_disclaimers, mm_blocks=mm_blocks, feature_blocks=feature_blocks)