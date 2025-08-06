from flask import Flask, render_template, request
import logging

from app.api.get_product import get_product, get_product_by_params

# Initialize Flask app
app = Flask(__name__)
app.use_static_for = 'static'
CACHE_DIR = 'cached_pages'

# Setup logging
logging.basicConfig(level=logging.INFO)

@app.route('/main')
def index():
    return render_template('index.html')

@app.route('/get_product', methods=['POST'])
def call_get_product():
    try:
        response = get_product()
        if response is None:
            raise ValueError("No response from get_product")
        return response
    except Exception as e:
        app.logger.error(f"Error in call_get_product: {e}")
        return render_template('error.html', error_message=str(e))

@app.route('/qr')
def call_get_product_from_qr():
    try:
        sku = request.args.get('pn')
        country = request.args.get('cc')
        language = request.args.get('ll')

        if not sku:
            return render_template('error.html', error_message='Missing required URL parameter: pn'), 400

        if not country or not language:
            return render_template('product_template.html', pn=sku)
        
        response = get_product_by_params(sku, country, language)
        if response is None:
            raise ValueError("No response from get_product_by_params")
        return response
            
    except Exception as e:
        app.logger.error(f"Error in call_get_product_from_qr: {e}")
        return render_template('error.html', error_message=str(e))

if __name__ == '__main__':
    app.run(debug=True)