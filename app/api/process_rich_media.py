from app.core.rich_media_template import build_template_rich_media
from flask import render_template

def process_api_response(response_json, sku):
    try:
        result = build_template_rich_media(response_json, sku)
        if "error" in result:
            raise ValueError(result["error"])
        # Render the HTML template with the image details, image_count, and counts
        return render_template('rich_media.html', image_details=result["image_details"], image_count=result["image_count"], counts=result["counts"], sku=result["sku"])
    except Exception as e:
        # Handle the error and render the error template
        return render_template('error.html', error_message=str(e))
