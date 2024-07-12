from flask import Flask, render_template

from app.api.get_rich_media import get_rich_media
from app.api.get_product import get_product
from app.api.get_images import get_images

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
            raise ValueError("No response from get_images")
        return response
    except Exception as e:
        # Handle the error and render the error template
        return render_template('error.html', error_message=str(e))

if __name__ == '__main__':
    app.run(debug=True)
