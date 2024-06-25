from flask import Flask, render_template
from app.api.get_product import get_product
from app.api.get_images import get_images

# Initialize Flask app
app = Flask(__name__)
app.use_static_for = 'static'

# Route for the index page
@app.route('/app4')
def index():
    return render_template('index.html')

# Route to get product data for template
@app.route('/get_product', methods=['POST'])
def call_get_product():
    return get_product()

# Route to get product data for images template
@app.route('/get_images', methods=['POST'])
def call_get_images():
    return get_images()

if __name__ == '__main__':
    app.run(debug=True)
