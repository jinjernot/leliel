import json

def extract_tag_values_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            tag_values = []

            # Access the "products" dictionary
            products = data.get('products', {})

            # Iterate over the products
            for product_key, product_data in products.items():
                # Access the "chunks" list for each product
                chunks = product_data.get('chunks', [])
                # Iterate over the chunks
                for chunk in chunks:
                    # Iterate over details in each chunk
                    for detail in chunk.get('details', []):
                        # Check if the detail has a 'tag' key and append its value to tag_values list
                        if 'tag' in detail:
                            tag_values.append(detail['tag'])

            return tag_values
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Invalid JSON format in file: {file_path}")

# Example usage:
file_path = 'response.json'  # Replace 'data.json' with the path to your JSON file
tag_values = extract_tag_values_from_json(file_path)
print("Tag values extracted from JSON file:", tag_values)
