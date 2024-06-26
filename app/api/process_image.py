from app.core.image_template import build_template_images
from flask import render_template

def process_api_response(response_json, sku):

    image_details = build_template_images(response_json, sku)
        
    # Render the HTML template with the image details
    return render_template('product_images.html', image_details=image_details)