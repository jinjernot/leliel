from app.core.ink_printer_template import build_template_ink
from app.core.monitor_template import build_template_monitor
from app.core.laptop_template import build_template_laptop
from app.core.companion_template import build_template_companions
from app.api.get_companions import get_companions
from flask import render_template

def process_api_response(response_json, sku):
    # Extract data from the response using the SKU
    product = response_json.get('products', {}).get(sku, {})
    product_hierarchy = product.get('productHierarchy', {})
    pmoid = product_hierarchy.get('productType', {}).get('pmoid', '')

    # Fetch companions
    country_code = response_json.get('request', {}).get('countryCode')
    language_code = response_json.get('request', {}).get('languageCode')
    companions_response = get_companions(sku, country_code, language_code)
    companions = build_template_companions(companions_response, sku)


    # Laptop
    if pmoid == '321957':
        df, df_images = build_template_laptop(response_json)
        return render_template('laptop.html', df=df, df_images=df_images, companions=companions)
    # Desktops
    elif pmoid == '12454':
        df, df_images = build_template_laptop(response_json)
        return render_template('laptop.html', df=df, df_images=df_images, companions=companions)
    # Ink_Printer
    elif product_hierarchy.get('marketingCategory', {}).get('pmoid') == '238444':  
        df = build_template_ink(response_json)
        return render_template('ink_printer.html', df=df, companions=companions)
    # Monitor
    elif product_hierarchy.get('productType', {}).get('pmoid') == '382087':
        df = build_template_monitor(response_json)
        return render_template('monitor.html', df=df, companions=companions)
    # Not yet
    else:
        return render_template('error.html', error_message='The product is not supported (yet)'), 400