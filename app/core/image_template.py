import pandas as pd
import json

def build_template_images(response_json, sku):
    try:
        product = response_json.get('products', {}).get(sku, {})
        images = product.get('images', [])
        # Create a list to hold all image details
        all_image_details = []
        image_count = 0

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
                image_count += 1

        # Calculate counts for each attribute
        counts = {
            "oid_count": len(set([image['oid'] for image in all_image_details])),
            "sku_count": len(set([image['sku'] for image in all_image_details])),
            "status_count": len(set([image['status'] for image in all_image_details])),
            "statusMessage_count": len(set([image['statusMessage'] for image in all_image_details])),
            "fallbackApplied_count": len(set([image['fallbackApplied'] for image in all_image_details])),
            "group_count": len(set([image['group'] for image in all_image_details])),
            "pixelWidth_count": len(set([image['pixelWidth'] for image in all_image_details])),
            "pixelHeight_count": len(set([image['pixelHeight'] for image in all_image_details])),
            "orientation_count": len(set([image['orientation'] for image in all_image_details])),
            "productColor_count": len(set([image['productColor'] for image in all_image_details])),
            "documentTypeDetail_count": len(set([image['documentTypeDetail'] for image in all_image_details])),
            "imageUrlHttp_count": len(set([image['imageUrlHttp'] for image in all_image_details])),
            "imageUrlHttps_count": len(set([image['imageUrlHttps'] for image in all_image_details])),
            "background_count": len(set([image['background'] for image in all_image_details])),
            "masterObjectName_count": len(set([image['masterObjectName'] for image in all_image_details])),
            "type_count": len(set([image['type'] for image in all_image_details])),
        }

        return {"image_details": all_image_details, "image_count": image_count, "counts": counts}
    except KeyError as e:
        # Handle missing keys in the JSON response
        error_message = f"Key error: {str(e)}"
        return {"error": error_message}
    except TypeError as e:
        # Handle type errors, such as NoneType being accessed
        error_message = f"Type error: {str(e)}"
        return {"error": error_message}
    except Exception as e:
        # Handle any other exceptions
        error_message = f"An unexpected error occurred: {str(e)}"
        return {"error": error_message}
