from flask import render_template
import json

def process_api_error(api_response):
    try:
        # Parse the API response JSON
        response_json = api_response.json()
        # Check if the API has an error
        if response_json.get('status') == 'Error':
            error_message = response_json.get('statusMessage', 'An error occurred')
            # Check locale or cc
            if error_message in ['Invalid Country or Language Code', 'Non publishable Product']:
                return render_template('error.html', error_message=error_message), 400
        # Check if product is non-publishable
        if response_json.get('status') == 'Success' and response_json.get('statusMessage') == 'Non publishable Product':
            error_message = 'Non publishable Product'
            return render_template('error.html', error_message=error_message), 400
    except json.JSONDecodeError:
        # Generic error message
        return render_template('error.html', error_message='An unknown error occurred'), 400
