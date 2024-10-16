from app.core.qa_template import build_template_qa
from app.core.qa_template_rich_media import build_template_qa_rich_media
from flask import render_template

def process_api_response(response_json, skus):
    try:
        result = build_template_qa(response_json, skus)
        if "error" in result:
            raise ValueError(result["error"])
        # Extract data from result dictionary
        sku_details = result.get("sku_details", [])
        counts = sku_details[0].get("counts", {}) if sku_details else {}
        image_count = sku_details[0].get("image_count", 0) if sku_details else 0
        # Render the HTML template with the image details, image_count, and counts
        return render_template('qa.html', sku_details=sku_details, counts=counts, image_count=image_count)
    except Exception as e:
        # Handle the error and render the error template
        return render_template('error.html', error_message=str(e))

def process_api_response_rich_media(response_json, skus):
    try:
        result = build_template_qa_rich_media(response_json, skus)
        if "error" in result:
            raise ValueError(result["error"])
        # Extract data from result dictionary
        sku_details = result.get("sku_details", [])
        image_count = sku_details[0].get("image_count", 0) if sku_details else 0
        # Render the HTML template with the image details and image_count
        return render_template('qa_rich_media.html', sku_details=sku_details, image_count=image_count)
    except Exception as e:
        # Handle the error and render the error template
        return render_template('error.html', error_message=str(e))

