from app.core.product_template import build_product_template
from app.core.companion_template import build_template_companions
from app.api.get_companions import get_companions
from flask import render_template

def process_api_response(response_json, sku):
    # Extract data from the response using the SKU
    product = response_json.get('products', {}).get(sku, {})

    # Fetch companions
    country_code = response_json.get('request', {}).get('countryCode')
    language_code = response_json.get('request', {}).get('languageCode')
    companions_response = get_companions(sku, country_code, language_code)
    companions = build_template_companions(companions_response, sku)

    # Always use the product template
    df, df_images = build_product_template(response_json)
    return render_template('product_template.html', df=df, df_images=df_images, companions=companions)