def build_template_companions(api_response, sku):
    if not isinstance(api_response, dict):
        return []

    products = api_response.get('products', {})
    product_data = products.get(sku, {})
    
    companions_list = []

    # Process accessories, services and supplies, so they appear in that order.
    for companion_type in ['supplies', 'accessories', 'services']:
        if companion_type in product_data:
            # Sort all companions by date.
            sorted_companions = sorted(product_data[companion_type], key=lambda x: x.get('fullDate', '0'), reverse=True)
            
            for companion in sorted_companions[2:10]:
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

def build_top_companions_by_type(api_response, sku):
    if not isinstance(api_response, dict):
        return {}

    products = api_response.get('products', {})
    product_data = products.get(sku, {})
    
    top_companions = {}

    # Process accessories, services and supplies to get the top two of each.
    for companion_type in ['supplies', 'accessories', 'services']:
        if companion_type in product_data:
            # Sort all companions by date.
            sorted_companions = sorted(product_data[companion_type], key=lambda x: x.get('fullDate', '0'), reverse=True)
            
            # Take the top 2 companions with an image.
            found_companions = []
            for companion in sorted_companions:
                if len(found_companions) >= 2:
                    break
                
                image_url = ''
                if companion.get('image'):
                    image_url = companion.get('image', {}).get('url', '')

                if image_url:
                    found_companions.append({
                        'type': companion_type,
                        'name': companion.get('name'),
                        'sku': companion.get('number'),
                        'image_url': image_url
                    })
            
            if found_companions:
                top_companions[companion_type] = found_companions
    
    return top_companions