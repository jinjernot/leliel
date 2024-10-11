# Load the trained model
model = tf.keras.models.load_model('/app/core/pigo.h5')

# Load class indices
with open('class_indices.json', 'r') as f:
    class_indices = json.load(f)

# Define image dimensions
img_height, img_width = 430, 573

# Function to make predictions for color and orientation
def predict_color_orientation(model, img_url, productColor, orientation):
    img_array = preprocess_image_from_url(img_url)
    if img_array is not None:
        predictions = model.predict(img_array)
        
        # Assuming your model outputs probabilities for color and orientation separately
        predicted_color_idx = np.argmax(predictions[0])  # Index of predicted color
        predicted_orientation_idx = np.argmax(predictions[1])  # Index of predicted orientation
        
        # Map indices to the actual color and orientation classes
        color_labels = list(class_indices.keys())  # Use loaded class indices
        orientation_labels = list(class_indices.keys())  # Use loaded class indices
        
        predicted_color = color_labels[predicted_color_idx]
        predicted_orientation = orientation_labels[predicted_orientation_idx]

        # Check if predicted values match the actual values
        color_match = predicted_color.lower() == productColor.lower()
        orientation_match = predicted_orientation.lower() == orientation.lower()

        return {
            "predicted_color": predicted_color,
            "color_match": color_match,
            "predicted_orientation": predicted_orientation,
            "orientation_match": orientation_match
        }
    else:
        return {
            "error": "Image processing failed"
        }
