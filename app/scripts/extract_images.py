import json
import requests
from PIL import Image
from io import BytesIO
import os

# Function to download and save images
def download_image(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img.save(save_path)
            print(f"Downloaded: {save_path}")
        else:
            print(f"Failed to download image: {url} (Status code: {response.status_code})")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Load JSON data from a file
def load_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data

# Main function to download only "Left facing" images with pixelWidth 573 from JSON
def download_images_from_json(json_file, image_dir):
    os.makedirs(image_dir, exist_ok=True)  # Create directory if it doesn't exist
    
    data = load_json(json_file)
    
    # Print loaded data for debugging
    print("Loaded JSON data:", data)
    
    # Navigate through the products
    products = data.get('products', {})
    print("Number of products found:", len(products))
    
    for sku, product in products.items():
        images = product.get('images', [])
        print(f"Processing product {sku} with {len(images)} image groups")
        
        for img_group_idx, image_group in enumerate(images):
            details = image_group.get('details', [])
            print(f"Processing image group {img_group_idx} with {len(details)} details")
            
            for detail_idx, detail in enumerate(details):
                # Apply filters
                if (detail.get('orientation') == 'Left facing' and 
                    detail.get('pixelWidth') == '573'):
                    image_url = detail.get('imageUrlHttps')
                    if image_url:
                        file_name = f"product_{sku}_group_{img_group_idx}_detail_{detail_idx}.png"  # Naming files incrementally
                        file_path = os.path.join(image_dir, file_name)
                        print(f"Downloading image {image_url}")
                        download_image(image_url, file_path)
                    else:
                        print(f"No imageUrlHttps for entry {sku}_{img_group_idx}_{detail_idx}")
                else:
                    print(f"Skipping image {sku}_{img_group_idx}_{detail_idx} with orientation {detail.get('orientation')} and pixelWidth {detail.get('pixelWidth')}")

# Example usage
json_file = 'api_response_qa.json'  # Path to your JSON file
image_dir = 'downloaded_images'  # Directory to save the images

download_images_from_json(json_file, image_dir)
