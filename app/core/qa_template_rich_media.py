def build_template_qa_rich_media(response_json, skus):
    try:
        all_sku_details = []
        # Iterate over each SKU in the input
        for sku in skus:
            product = response_json.get('products', {}).get(sku, {})
            
            if not isinstance(product, dict):
                print(f"Warning: Product for SKU {sku} is not a valid dictionary: {product}")
                continue
            
            richmedia = product.get('richmedia', {})
            if not isinstance(richmedia, dict):
                print(f"Warning: Richmedia for SKU {sku} is not a valid dictionary: {richmedia}")
                continue
            
            # Define the image types you want to include
            image_types = ['Image - Annotated', 'Image - At a glance', 'Image - Banners']

            # Create a list to hold all image details for this SKU
            sku_image_details = []
            sku_image_count = 0
            
            # Initialize breakdowns
            asset_category_breakdown = {}

            for image_type in image_types:
                images = richmedia.get(image_type, [])
                
                if not isinstance(images, list):
                    print(f"Warning: Expected a list for {image_type}, but got: {type(images).__name__}")
                    continue
                
                sku_image_count += len(images)

                for detail in images:
                    if not isinstance(detail, dict):
                        print(f"Warning: Expected detail to be a dictionary, but got: {type(detail).__name__}")
                        continue
                    
                    image_data = {
                        "assetCategory": detail.get('assetCategory'),
                        "assetDescription": detail.get('assetDescription'),
                        "assetId": detail.get('assetId'),
                        "assetModifiedDate": detail.get('assetModifiedDate'),
                        "assetName": detail.get('assetName'),
                        "assetTitle": detail.get('assetTitle'),
                        "imageDetail": detail.get('imageDetail'),
                        "keyword": detail.get('keyword'),
                        "languageCodes": detail.get('languageCodes'),
                    }

                    # Append image details for this SKU
                    sku_image_details.append(image_data)

                    # Update breakdown count for assetCategory
                    asset_category = image_data.get('assetCategory')
                    if asset_category:
                        asset_category_breakdown[asset_category] = asset_category_breakdown.get(asset_category, 0) + 1

            # Prepare counts
            counts = {
                "total_image_count": sku_image_count,
                "image_details_count": len(sku_image_details),
                "assetCategory_breakdown": asset_category_breakdown,
                # Add other counts similarly as needed
            }

            # Store SKU details
            sku_data = {
                "sku": sku,
                "image_details": sku_image_details,
                "image_count": sku_image_count,
                "counts": counts,
                "notes": ""  # Placeholder for notes
            }
            all_sku_details.append(sku_data)

        return {"sku_details": all_sku_details}
    
    except KeyError as e:
        return {"error": f"Key error: {str(e)}"}
    except TypeError as e:
        return {"error": f"Type error: {str(e)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
