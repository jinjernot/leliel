import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import requests
from io import BytesIO
from PIL import Image

# Load the trained model
model = tf.keras.models.load_model('model.h5')

# Define image dimensions
img_height, img_width = 430, 573

# Function to preprocess the image from URL
def preprocess_image_from_url(img_url):
    try:
        response = requests.get(img_url)
        img = Image.open(BytesIO(response.content))

        # Convert the image to RGB if it has an alpha channel (RGBA)
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        img = img.resize((img_width, img_height))  # Resize to match model input size
        img_array = image.img_to_array(img)  # Convert to numpy array
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        img_array /= 255.0  # Normalize the image to [0, 1] range
        return img_array
    except Exception as e:
        print(f"Error processing image from URL: {img_url}, error: {str(e)}")
        return None

# Function to make predictions from URL
def predict_image_from_url(model, img_url):
    img_array = preprocess_image_from_url(img_url)
    if img_array is not None:
        prediction = model.predict(img_array)[0][0]
        if prediction > 0.5:
            return "Pen Detected"
        else:
            return "No Pen Detected"
    else:
        return "Image Processing Failed"

# Updated build_template_images function with ML check
def build_template_images(response_json, sku):
    try:
        product = response_json.get('products', {}).get(sku, {})
        sku = product.get('sku', [])
        images = product.get('images', [])
        
        # Create a list to hold all image details
        all_image_details = []
        image_count = 0

        # Iterate over each image and extract details
        for image in images:
            for detail in image['details']:
                image_data = {
                    "pixelWidth": detail.get('pixelWidth'),
                    "pixelHeight": detail.get('pixelHeight'),
                    "orientation": detail.get('orientation'),
                    "productColor": detail.get('productColor'),
                    "documentTypeDetail": detail.get('documentTypeDetail'),
                    "imageUrlHttp": detail.get('imageUrlHttp'),
                    "imageUrlHttps": detail.get('imageUrlHttps'),
                    "background": detail.get('background'),
                    "masterObjectName": detail.get('masterObjectName'),
                    "type": detail.get('type'),
                    "ml_prediction": ""
                }

                # Check for pen detection using the ML model
                img_url = detail.get('imageUrlHttp') or detail.get('imageUrlHttps')
                if img_url:
                    prediction = predict_image_from_url(model, img_url)
                    image_data["ml_prediction"] = prediction  # Add the ML result to the image data
                
                all_image_details.append(image_data)
                image_count += 1

        # Calculate counts for each attribute
        counts = {
            "pixelWidth_count": len(set([image['pixelWidth'] for image in all_image_details])),
            "pixelHeight_count": len(set([image['pixelHeight'] for image in all_image_details])),
            "orientation_count": len(set([image['orientation'] for image in all_image_details])),
            "productColor_count": len(set([image['productColor'] for image in all_image_details])),
            "documentTypeDetail_count": len(set([image['documentTypeDetail'] for image in all_image_details])),
            "imageUrlHttp_count": len(set([image['imageUrlHttp'] for image in all_image_details])),
            "imageUrlHttps_count": len(set([image['imageUrlHttps'] for image in all_image_details])),
            "background_count": len(set([image['background'] for image in all_image_details])),
            "masterObjectName_count": len(set([image['masterObjectName'] for image in all_image_details])),
            "type_count": len(set([image['type'] for image in all_image_details])),
        }

        return {"image_details": all_image_details, "image_count": image_count, "counts": counts, "sku": sku}
    
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
