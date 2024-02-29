
import pandas as pd

def build_template(api_response):

    # Ensure api_response is a dictionary
    if not isinstance(api_response, dict):
        try:
            api_response = api_response.json()  # Assuming 'api_response' is a JSON-like object
        except AttributeError:
            print("Error: Unable to convert the response to a dictionary.")
            return {}

    atf_tags = {}

    # Define the tags to search for
    target_tags = ['prodname','proddes_overview_extended','ksp_01_suppt_01_long','ksp_02_suppt_01_long','ksp_03_suppt_01_long','osinstalled','processorname','memstdes_01','hd_01des','displaymet','graphicseg_01card_01','whatsinbox','ksp_01_headline_medium','ksp_02_headline_medium','ksp_03_headline_medium']
    image_tags = ['Center facing','Left facing','Right facing','Left rear facing','Rear facing','Left rear facing','Top view closed','Detail view','Left profile closed','Right profile closed','Right rear facing']

    # Access the 'products' dictionary in the API api_response
    products = api_response.get('products', {})

    # Iterate through the 'sku' values in the 'request' dictionary
    for sku in api_response['request']['sku']:
        # Access the 'chunks' list for each 'sku'
        chunks = products.get(sku, {}).get('chunks', [])
        images = products.get(sku, {}).get('images', [])
        # Iterate through the chunks in the API api_response
        for chunk in chunks:
            # Check if 'details' key is present in the chunk
            if 'details' in chunk:
                # Iterate through the details in the chunk
                for detail in chunk['details']:
                    if 'tag' in detail and detail['tag'] in target_tags:
                        atf_tags[detail['tag']] = detail['value']

        for image in images:
            # Check if 'details' key is present in the chunk
            if 'details' in image:
                # Iterate through the details in the chunk
                for detail in image['details']:
                    if 'orientation' in detail and detail['orientation'] in image_tags:
                        atf_tags[detail['orientation']] = detail['imageUrlHttps']

    df = pd.DataFrame([atf_tags])
    df.to_excel("excel.xlsx", index=False, engine='xlsxwriter')

    return df
