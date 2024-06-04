from flask import Flask, render_template
from app.api.get_product import get_product

# Initialize Flask app
app = Flask(__name__)
app.use_static_for = 'static'

# Route for the index page
@app.route('/app4')
def index():
    return render_template('index.html')

# Route to get product data 
@app.route('/get_product', methods=['POST'])
def call_get_product():
    return get_product()

if __name__ == '__main__':
    app.run(debug=True)
