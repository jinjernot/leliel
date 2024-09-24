import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from PIL import Image

# Load the trained model
model = tf.keras.models.load_model('trained_model.h5')

# Define image dimensions
img_height, img_width = 430, 573

# Function to preprocess the image
def preprocess_image(img_path):
    img = image.load_img(img_path, target_size=(img_height, img_width))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array /= 255.0 
    return img_array

# Function to make predictions
def predict_image(model, img_path):
    img_array = preprocess_image(img_path)
    prediction = model.predict(img_array)[0][0]
    if prediction > 0.5:
        return "Pen Detected"
    else:
        return "No Pen Detected"

image_folder = 'downloaded_images'

# Iterate over the images in the folder
for img_file in os.listdir(image_folder):
    if img_file.endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(image_folder, img_file)
        result = predict_image(model, img_path)
        print(f"Image: {img_file} -> {result}")
