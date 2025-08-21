from flask import Flask, render_template, request, session, abort
import logging
import secrets

# Import the configuration from config.py
from config import SECRET_KEY, PRODUCT_HIERARCHY, TOP_COMPONENTS, TECH_SPEC_GROUP_ORDER

from app.api.get_product import get_product, get_product_by_params

# Initialize Flask app
app = Flask(__name__)
# Set the secret key from the config file
app.config['SECRET_KEY'] = SECRET_KEY
app.use_static_for = 'static'

# Add the imported dictionaries to the app config
app.config['PRODUCT_HIERARCHY'] = PRODUCT_HIERARCHY
app.config['TOP_COMPONENTS'] = TOP_COMPONENTS
app.config['TECH_SPEC_GROUP_ORDER'] = TECH_SPEC_GROUP_ORDER

# Setup logging
logging.basicConfig(level=logging.INFO)

@app.route('/main')
def index():
    # Generate a CSRF token and store it in the session
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return render_template('index.html', csrf_token=session['_csrf_token'])

@app.route('/get_product', methods=['POST'])
def call_get_product():
    # Validate the CSRF token
    submitted_token = request.form.get('csrf_token')
    expected_token = session.pop('_csrf_token', None)

    if not expected_token or submitted_token != expected_token:
        abort(400, 'Invalid CSRF token. Please try submitting the form again.')

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