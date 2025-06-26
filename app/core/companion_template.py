def build_template_companions(api_response, sku):
    if not isinstance(api_response, dict):
        return []

    products = api_response.get('products', {})
    product_data = products.get(sku, {})
    companions_data = product_data.get('companions', {})

    companions_list = []

    for companion_type in ['services', 'accessories']:
        if companion_type in companions_data:
            for companion in companions_data[companion_type]:
                image_url = ''
                if companion.get('images'):
                    for image_group in companion.get('images', []):
                        if image_group.get('details'):
                            # Use the first available image
                            image_url = image_group['details'][0].get('imageUrlHttps', '')
                            break
                
                # Only add the companion if it has an image
                if image_url:
                    companions_list.append({
                        'type': companion_type,
                        'name': companion.get('name'),
                        'sku': companion.get('number'),
                        'image_url': image_url
                    })

    return companions_list