import pandas as pd
import json

def build_template_images(response_json, sku):
    product = response_json.get('products', {}).get(sku, {})
    images = product.get('images', [])
    # Create a list to hold all image details
    all_image_details = []

    # Iterate over each image and extract details
    for image in images:
        for detail in image['details']:
            image_data = {
                "oid": product.get('oid'),
                "sku": product.get('sku'),
                "status": product.get('status'),
                "statusMessage": product.get('statusMessage'),
                "fallbackApplied": product.get('fallbackApplied'),
                "group": image.get('group'),
                "pixelWidth": detail.get('pixelWidth'),
                "pixelHeight": detail.get('pixelHeight'),
                "orientation": detail.get('orientation'),
                "productColor": detail.get('productColor'),
                "documentTypeDetail": detail.get('documentTypeDetail'),
                "imageUrlHttp": detail.get('imageUrlHttp'),
                "imageUrlHttps": detail.get('imageUrlHttps'),
                "background": detail.get('background'),
                "masterObjectName": detail.get('masterObjectName'),
                "type": detail.get('type')
            }
            all_image_details.append(image_data)

    return all_image_details