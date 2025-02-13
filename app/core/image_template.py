def build_template_images(response_json, sku):
    try:
        product = response_json.get('products', {}).get(sku, {})
        sku = product.get('sku', [])
        images = product.get('images', [])
        # Create a list to hold all image details
        all_image_details = []
        image_count = 0

        # Iterate over each image and extract details
        for image in images:
            for detail in image['details']:
                image_data = {
                    "pixelWidth": detail.get('pºixelWidth'),
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

        return {"image_details": all_image_details, "image_count": image_count, "counts": counts, "sku":sku}
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