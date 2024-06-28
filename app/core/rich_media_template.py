import pandas as pd
import json

def build_template_rich_media(response_json, sku):
    try:
        product = response_json.get('products', {}).get(sku, {})
        images = product.get('richmedia', {}).get('Image - Annotated', [])
        sku = product.get('sku', [])
        
        # Create a list to hold all image details
        all_image_details = []
        image_count = 0

        # Iterate over each image and extract details
        for image in images:
            image_data = {
                "assetCategory": image.get('assetCategory'),
                "assetDescription": image.get('assetDescription'),
                "assetId": image.get('assetId'),
                "assetModifiedDate": image.get('assetModifiedDate'),
                "assetName": image.get('assetName'),
                "assetTitle": image.get('assetTitle'),
                "background": image.get('background'),
                "imageDetail": image.get('imageDetail'),
                "imageUrlHttps": image.get('imageUrlHttps'),
                "keyword": image.get('keyword'),
                "languageCodes": image.get('languageCodes'),
                "orientation": image.get('orientation'),
                "pixelHeight": image.get('pixelHeight'),
                "pixelWidth": image.get('pixelWidth'),
                "renditionId": image.get('renditionId')
            }
            all_image_details.append(image_data)
            image_count += 1

        # Calculate counts for each attribute
        counts = {
            "pixelWidth_count": len(set([image['pixelWidth'] for image in all_image_details])),
            "pixelHeight_count": len(set([image['pixelHeight'] for image in all_image_details])),
            "orientation_count": len(set([image['orientation'] for image in all_image_details])),
            "background_count": len(set([image['background'] for image in all_image_details])),
            "assetCategory_count": len(set([image['assetCategory'] for image in all_image_details])),
            "languageCodes_count": len(set([image['languageCodes'] for image in all_image_details])),
            "assetId_count": len(set([image['assetId'] for image in all_image_details])),
            "assetModifiedDate_count": len(set([image['assetModifiedDate'] for image in all_image_details])),
            "assetName_count": len(set([image['assetName'] for image in all_image_details])),
            "assetTitle_count": len(set([image['assetTitle'] for image in all_image_details])),
            "keyword_count": len(set([item for image in all_image_details for item in image['keyword']])),
            "renditionId_count": len(set([image['renditionId'] for image in all_image_details])),
        }

        return {"image_details": all_image_details, "image_count": image_count, "counts": counts, "sku": sku}
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
