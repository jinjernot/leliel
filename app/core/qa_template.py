def build_template_qa(response_json, skus):
    try:
        all_sku_details = []  # To hold all details per SKU
        for sku in skus:  # Iterate over each SKU in the input
            product = response_json.get('products', {}).get(sku, {})
            images = product.get('images', [])
            sku_image_count = len(images)  # Count the number of images for this SKU

            # Get the name from the SKU hierarchy
            product_hierarchy = product.get('productHierarchy', {})
            sku_hierarchy_name = product_hierarchy.get('sku', {}).get('name', 'N/A')

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
                    # Append image details for this SKU
                    sku_image_details.append(image_data)

            # Collect tuples of (orientation, pixelWidth, pixelHeight, documentTypeDetail)
            orientation_combinations = [
                (image.get('orientation'), image.get('pixelWidth'), image.get('pixelHeight'), image.get('documentTypeDetail')) 
                for image in sku_image_details
            ]

            # Count duplicates of (orientation, pixelWidth, pixelHeight, documentTypeDetail)
            unique_combinations = set(orientation_combinations)
            duplicate_orientations = [
                combo for combo in orientation_combinations 
                if orientation_combinations.count(combo) > 1
            ]

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
                return filtered_values, len(set(filtered_values))  # Return both filtered values and unique count

            # Calculate counts for each attribute for this SKU
            counts = {
                "pixelWidth_count": filter_values('pixelWidth')[1],
                "pixelHeight_count": filter_values('pixelHeight')[1],
                "orientation_count": filter_values('orientation')[1],
                "productColor_count": filter_values('productColor')[1],
                "documentTypeDetail_count": filter_values('documentTypeDetail')[1],
                "imageUrlHttp_count": filter_values('imageUrlHttp')[1],
                "imageUrlHttps_count": filter_values('imageUrlHttps')[1],
                "background_count": filter_values('background')[1],
                "masterObjectName_count": filter_values('masterObjectName')[1],
                "type_count": filter_values('type')[1],
                "total_image_count": sku_image_count  # Total number of images for this SKU
            }

            # Add "notes" with specific details if duplicates are found
            notes = ""
            if duplicate_orientations:
                notes = f"Duplicate combinations found for orientation(s): {', '.join(set([combo[0] for combo in duplicate_orientations]))}"

            # Store SKU details and counts
            sku_data = {
                "sku": sku,
                "sku_name": sku_hierarchy_name,  # Include the SKU name from product hierarchy
                "image_details": sku_image_details,  # The list of images for this SKU
                "counts": counts,
                "image_count": sku_image_count,  # Total images for this SKU
                "notes": notes  # Add notes if any
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
