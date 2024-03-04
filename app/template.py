import pandas as pd
import json


def build_template(api_response):
    """
    Builds a template DataFrame from the API response containing product details.

    Args:
        api_response (dict): The API response containing product information.

    Returns:
        pandas.DataFrame: DataFrame containing product details.
    """
    # Ensure api_response is a dictionary
    if not isinstance(api_response, dict):
        try:
            api_response = api_response.json() 
        except AttributeError:
            print("Error: Unable to convert the response to a dictionary.")
            return {}
    atf_tags = {}

    # Load the tags from a JSON file
    with open("app/data/tags.json", "r") as f:
        tags_data = json.load(f)

    # Chunks
    target_tags = tags_data["target_tags"]
    # Images
    image_tags = tags_data["image_tags"]

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
        # Get the images
        for image in images:
            # Check if 'details' key is present in the chunk
            if 'details' in image:
                # Iterate through the details in the chunk
                for detail in image['details']:
                    if 'orientation' in detail and detail['orientation'] in image_tags:
                        atf_tags[detail['orientation']] = detail['imageUrlHttps']
    # Save to an excel file
    df = pd.DataFrame([atf_tags])
    df.to_excel("excel.xlsx", index=False, engine='xlsxwriter')

    return df
