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

# Main function to download images with pixelWidth 573 and organize them in color/orientation folders
def download_images_from_json(json_file, image_dir):
    os.makedirs(image_dir, exist_ok=True)
    
    data = load_json(json_file)
    
    # Initialize a set to keep track of downloaded image URLs
    downloaded_urls = set()
    
    # Navigate through the products
    products = data.get('products', {})
    
    for sku, product in products.items():
        images = product.get('images', [])
        
        for img_group_idx, image_group in enumerate(images):
            details = image_group.get('details', [])
            
            for detail_idx, detail in enumerate(details):
                orientation = detail.get('orientation')
                pixel_width = detail.get('pixelWidth')
                color = detail.get('productColor', 'Unknown')  # Default to 'Unknown' if color is not available
                
                # Only process images with pixelWidth 573
                if orientation and pixel_width == '573':
                    image_url = detail.get('imageUrlHttps')
                    
                    if image_url:
                        # Check if the image has already been downloaded
                        if image_url not in downloaded_urls:
                            # Add URL to the set to mark it as downloaded
                            downloaded_urls.add(image_url)
                            
                            # Create a folder structure based on color and orientation
                            color_folder = os.path.join(image_dir, color)
                            orientation_folder = os.path.join(color_folder, orientation)
                            os.makedirs(orientation_folder, exist_ok=True)
                            
                            # Save image in the color/orientation folder
                            file_name = f"product_{sku}_group_{img_group_idx}_detail_{detail_idx}.png"
                            file_path = os.path.join(orientation_folder, file_name)
                            print(f"Downloading image {image_url} to folder '{color}/{orientation}'")
                            download_image(image_url, file_path)
                        else:
                            print(f"Skipping duplicate image {image_url}")
                    else:
                        print(f"No imageUrlHttps for entry {sku}_{img_group_idx}_{detail_idx}")
                else:
                    print(f"Skipping image {sku}_{img_group_idx}_{detail_idx} with orientation {orientation}, color {color}, and pixelWidth {pixel_width}")

# Example usage
json_file = 'api_response_qa.json'
image_dir = 'downloaded_images'

download_images_from_json(json_file, image_dir)
