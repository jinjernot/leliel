def build_template_qa_rich_media(response_json, skus):
    try:
        all_sku_details = []
        # Define the list of image types to access
        image_types = ['Image - Annotated', 'Image - At a glance', 'Image - Banners']

        # Iterate over each SKU in the input
        for sku in skus:
            product = response_json.get('products', {}).get(sku, {})
            
            # Create a list to hold all image details for this SKU
            sku_image_details = []
            print("antes del for")

            # Access specified image types directly from richmedia
            if 'richmedia' in product:
                for image_type in image_types:
                    images = product['richmedia'].get(image_type, [])
                    for detail in images:  # Iterate directly over the list of details
                        print("despuescito del for")
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
                            "background": detail.get('background'),  # Add if you want to count this
                            "dateInserted": detail.get('dateInserted'),
                            "imageUrlHttps": detail.get('imageUrlHttps'),
                            "orientation": detail.get('orientation'),
                            "pixelHeight": detail.get('pixelHeight'),
                            "pixelWidth": detail.get('pixelWidth'),
                            "renditionId": detail.get('renditionId')
                        }
                        # Append image details for this SKU
                        sku_image_details.append(image_data)

            # Function to filter out non-hashable types (lists) and None values
            def filter_values(attribute):
                print("entro al filter")
                values = [image[attribute] for image in sku_image_details if image[attribute] is not None]
                filtered_values = []
                for v in values:
                    if isinstance(v, list):
                        # Convert list to tuple to make it hashable
                        filtered_values.append(tuple(v))
                    else:
                        filtered_values.append(v)
                return filtered_values, len(set(filtered_values))  # Return both filtered values and unique count

            # Count each unique value for assetCategory
            print("cuentame")
            document_type_detail_counts = {}
            for image in sku_image_details:
                document_type_detail = image.get('assetCategory')
                if document_type_detail:
                    if document_type_detail not in document_type_detail_counts:
                        document_type_detail_counts[document_type_detail] = 1
                    else:
                        document_type_detail_counts[document_type_detail] += 1

            # Calculate counts for each attribute for this SKU
            counts = {
                "assetCategory_count": filter_values('assetCategory')[1],
                "assetCategory_breakdown": document_type_detail_counts,
                "assetDescription_count": filter_values('assetDescription')[1],
                "assetId_count": filter_values('assetId')[1],
                "assetModifiedDate_count": filter_values('assetModifiedDate')[1],
                "assetName_count": filter_values('assetName')[1],
                "assetTitle_count": filter_values('assetTitle')[1],
                "background_count": filter_values('background')[1],  # Added background count
                "dateInserted_count": filter_values('dateInserted')[1],
                "imageDetail_count": filter_values('imageDetail')[1],
                "imageUrlHttps_count": filter_values('imageUrlHttps')[1],
                "keyword_count": filter_values('keyword')[1],
                "languageCodes_count": filter_values('languageCodes')[1],
                "orientation_count": filter_values('orientation')[1],
                "pixelHeight_count": filter_values('pixelHeight')[1],
                "pixelWidth_count": filter_values('pixelWidth')[1],                
                "renditionId_count": filter_values('renditionId')[1],                                          
                "total_image_count": len(sku_image_details)  # Use the length of sku_image_details for total count
            }

            # Add "notes" with specific details if duplicates or missing colours are found
            notes = ""  # Customize notes logic as needed

            # Store SKU details and counts
            sku_data = {
                "sku": sku,
                "image_details": sku_image_details,
                "counts": counts,
                "image_count": len(sku_image_details),  # Count of images
                "notes": notes
            }
            all_sku_details.append(sku_data)

        # Return the processed details and counts for all SKUs
        print("paso todo?")
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
