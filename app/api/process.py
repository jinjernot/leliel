from app.core.ink_printer_template import build_template_ink
from app.core.monitor_template import build_template_monitor
from app.core.laptop_template import build_template_laptop
from flask import render_template
import json

def process_api_response(response_json, sku):
    # Extract data from the response using the SKU
    product = response_json.get('products', {}).get(sku, {})
    product_hierarchy = product.get('productHierarchy', {})
    pmoid = product_hierarchy.get('productType', {}).get('pmoid', '')
    # Laptop
    if pmoid == '321957':
        df, df_images = build_template_laptop(response_json)
        return render_template('laptop.html', df=df, df_images=df_images)
    # Ink_Printer
    elif product_hierarchy.get('marketingCategory', {}).get('pmoid') == '238444':  
        df = build_template_ink(response_json)
        return render_template('ink_printer.html', df=df)
    # Monitor
    elif product_hierarchy.get('productType', {}).get('pmoid') == '382087':
        df = build_template_monitor(response_json)
        return render_template('monitor.html', df=df)
    # Not yet
    else:
        return render_template('error.html', error_message='The product is not supported (yet)'), 400

def process_api_error(api_response):
    try:
        # Parse the API response JSON
        response_json = api_response.json()
        # Check if the API has an error
        if response_json.get('status') == 'Error':
            error_message = response_json.get('statusMessage', 'An error occurred')
            # Check locale or cc
            if error_message in ['Invalid Country or Language Code', 'Non publishable Product']:
                return render_template('error.html', error_message=error_message), 400
        # Check if product is non-publishable
        if response_json.get('status') == 'Success' and response_json.get('statusMessage') == 'Non publishable Product':
            error_message = 'Non publishable Product'
            return render_template('error.html', error_message=error_message), 400
    except json.JSONDecodeError:
        # Generic error message
        return render_template('error.html', error_message='An unknown error occurred'), 400
