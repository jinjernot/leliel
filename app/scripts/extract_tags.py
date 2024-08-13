import json

def extract_tag_values_from_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            tag_values = []
            
            products = data.get("products", {})

            for product_key, product_data in products.items():
                chunks = product_data.get("chunks", [])
                for chunk in chunks:
                    for detail in chunk.get("details", []):
                        if "tag" in detail:
                            tag_values.append(detail["tag"])

            return tag_values
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError:
        print(f"Invalid JSON format in file: {file_path}")

# Example usage:
file_path = "response.json"
tag_values = extract_tag_values_from_json(file_path)
print("Tag values extracted from JSON file:", tag_values)
