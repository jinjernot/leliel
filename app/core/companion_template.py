def build_template_companions(api_response, sku):
    if not isinstance(api_response, dict):
        return []

    products = api_response.get('products', {})
    product_data = products.get(sku, {})
    
    companions_list = []

    # Process accessories, services and supplies, so they appear in that order.
    for companion_type in ['supplies', 'accessories', 'services']:
        if companion_type in product_data:
            # Sort the companions by the 'sortOrder' field as an integer.
            sorted_companions = sorted(product_data[companion_type], key=lambda x: int(x.get('sortOrder', 0)))
            
            # Take the top 5 companions from the sorted list.
            for companion in sorted_companions[:5]:
                image_url = ''
                if companion.get('image'):
                    image_url = companion.get('image', {}).get('url', '')

                # Only add the companion to the list if it has an image.
                if image_url:
                    companions_list.append({
                        'type': companion_type,
                        'name': companion.get('name'),
                        'sku': companion.get('number'),
                        'image_url': image_url
                    })

    return companions_list