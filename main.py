from flask import Flask, render_template, request, send_file
import pandas as pd
import json

from app.api.get_rich_media import get_rich_media
from app.api.get_product import get_product
from app.api.get_images import get_images
from app.api.get_qa import get_qa
from app.core.build_excel import build_excel

# Initialize Flask app
app = Flask(__name__)
app.use_static_for = 'static'

# Route for the index page
@app.route('/main')
def index():
    return render_template('index.html')

# Route to get product data for template
@app.route('/get_product', methods=['POST'])
def call_get_product():
    try:
        response = get_product()
        if response is None:
            raise ValueError("No response from get_product")
        return response
    except Exception as e:
        # Handle the error and render the error template
        return render_template('error.html', error_message=str(e))

# Route to get product data for images template
@app.route('/get_images', methods=['POST'])
def call_get_images():
    try:
        response = get_images()
        if response is None:
            raise ValueError("No response from get_images")
        return response
    except Exception as e:
        # Handle the error and render the error template
        return render_template('error.html', error_message=str(e))
    
# Route to get product data for rich_media template
@app.route('/get_rich_media', methods=['POST'])
def call_get_rich_media():
    try:
        response = get_rich_media()
        if response is None:
            raise ValueError("No response from get_rich_media")
        return response
    except Exception as e:
        # Handle the error and render the error template
        return render_template('error.html', error_message=str(e))
    
# Route to get product data for rich_media template
@app.route('/get_qa', methods=['POST'])
def call_get_qa():
    try:
        response = get_qa()
        if response is None:
            raise ValueError("No response from get_qa")
        return response
    except Exception as e:
        # Handle the error and render the error template
        return render_template('error.html', error_message=str(e))
    
    
@app.route('/export-excel', methods=['POST'])
def export_excel():
    try:
        # Extract sku_details from the form
        sku_details_json = request.form['sku_details']
        sku_details = json.loads(sku_details_json)

        # Call the function to build the Excel file in memory
        excel_file_buffer = build_excel(sku_details)

        # Send the Excel file as a response
        return send_file(
            excel_file_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            attachment_filename='product_images_qa.xlsx'
        )
    except Exception as e:
        return render_template('error.html', error_message=str(e))


if __name__ == '__main__':
    app.run(debug=True)