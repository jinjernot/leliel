def build_template_qa(response_json, skus):
    try:
        all_sku_details = []  # To hold all details per SKU
        for sku in skus:  # Iterate over each SKU in the input
            product = response_json.get('products', {}).get(sku, {})
            images = product.get('images', [])
            sku_image_count = len(images)  # Count the number of images for this SKU

            # Create a list to hold all image details for this SKU
            sku_image_details = []
            for image in images:
                for detail in image.get('details', []):
                    image_data = {
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
                    sku_image_details.append(image_data)

            # Function to filter out non-hashable types (lists) and None values
            def filter_values(attribute):
                values = [image[attribute] for image in sku_image_details if image[attribute] is not None]
                filtered_values = []
                for v in values:
                    if isinstance(v, list):
                        # Convert list to tuple to make it hashable
                        filtered_values.append(tuple(v))
                    else:
                        filtered_values.append(v)
                return len(set(filtered_values))

            # Calculate counts for each attribute for this SKU
            counts = {
                "pixelWidth_count": filter_values('pixelWidth'),
                "pixelHeight_count": filter_values('pixelHeight'),
                "orientation_count": filter_values('orientation'),
                "productColor_count": filter_values('productColor'),
                "documentTypeDetail_count": filter_values('documentTypeDetail'),
                "imageUrlHttp_count": filter_values('imageUrlHttp'),
                "imageUrlHttps_count": filter_values('imageUrlHttps'),
                "background_count": filter_values('background'),
                "masterObjectName_count": filter_values('masterObjectName'),
                "type_count": filter_values('type'),
                "total_image_count": sku_image_count  # Total number of images for this SKU
            }

            # Store SKU details and counts
            sku_data = {
                "sku": sku,
                "image_details": sku_image_details,  # The list of images for this SKU
                "counts": counts,
                "image_count": sku_image_count  # Total images for this SKU
            }
            all_sku_details.append(sku_data)

        # Return the processed details and counts for all SKUs
        return {"sku_details": all_sku_details}
    
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
