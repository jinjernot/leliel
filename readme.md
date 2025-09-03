Flask-based web application designed to build dynamic product pages by fetching data from the HERMES API. It retrieves product information, including technical specifications, images, and marketing content, and renders it into a user-friendly HTML template.

The application will be accessible at

http://127.0.0.1:5000/main
http://127.0.0.1:5000/qr?pn=<SKU>&cc=<COUNTRY_CODE>&ll=<LANGUAGE_CODE>

qr_page/
├── app/
│   ├── api/
│   │   ├── get_product.py
│   │   ├── process_product.py
│   │   └── api_error.py
│   └── core/
│       ├── product_template.py
│       └── companion_template.py
├── static/
│   ├── css/
│   ├── images/
│   └── js/
├── templates/
│   ├── index.html
│   ├── product_template.html
│   └── error.html
├── .gitignore
├── config.py
├── main.py
├── requirements.txt
└── wsgi.py