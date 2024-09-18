import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
import os

# Define image dimensions
img_height, img_width = 430, 573  # Adjust according to your images
image_dir = 'downloaded_images'  # Directory with images

# Create an ImageDataGenerator for preprocessing
datagen = ImageDataGenerator(
    rescale=1./255,  # Normalize pixel values to [0, 1]
    validation_split=0.2  # Split data into training and validation sets
)

# Load training data
train_generator = datagen.flow_from_directory(
    directory=image_dir,
    target_size=(img_height, img_width),
    batch_size=32,
    class_mode='binary',  # Adjust according to your problem
    subset='training'
)

# Load validation data
validation_generator = datagen.flow_from_directory(
    directory=image_dir,
    target_size=(img_height, img_width),
    batch_size=32,
    class_mode='binary',  # Adjust according to your problem
    subset='validation'
)

# Build a simple CNN model
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(img_height, img_width, 3)),
    MaxPooling2D((2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Flatten(),
    Dense(512, activation='relu'),
    Dense(1, activation='sigmoid')  # Adjust for binary classification
])

# Compile the model
model.compile(optimizer='adam',
              loss='binary_crossentropy',  # Adjust based on your task
              metrics=['accuracy'])

# Print model summary
model.summary()

# Train the model
history = model.fit(
    train_generator,
    epochs=10,  # Adjust the number of epochs
    validation_data=validation_generator
)

# Save the trained model
model.save('trained_model.h5')

# Evaluate the model
val_loss, val_accuracy = model.evaluate(validation_generator)
print(f'Validation accuracy: {val_accuracy * 100:.2f}%')
