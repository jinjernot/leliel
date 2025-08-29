from flask import render_template
import json
import logging

def process_api_error(api_response):
    try:
        error_text = api_response.text
        logging.error(f"API Error Response: {error_text}")

        response_json = api_response.json()
        
        if response_json.get('Status') == 'ERROR':
            error_message = response_json.get('StatusMessage', 'An unknown API error occurred.')
            return render_template('error.html', error_message=error_message), 400
        
        if response_json.get('Status') == 'Success' and response_json.get('StatusMessage') == 'Non publishable Product':
            return render_template('error.html', error_message='Non publishable Product'), 400
            
    except json.JSONDecodeError:
        return render_template('error.html', error_message=f"An unknown error occurred. API Response: {api_response.text}"), 400
    except Exception as e:
        return render_template('error.html', error_message=f"An unexpected error occurred: {str(e)}"), 500

    return render_template('error.html', error_message='An unknown error occurred'), 500