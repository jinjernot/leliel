from flask import render_template
import json

def process_api_error(api_response):
    try:
        # Log the full response text for debugging
        error_text = api_response.text
        print(f"API Error Response: {error_text}")

        # Try to parse the API response JSON
        response_json = api_response.json()
        
        # Check if the API has an error
        if response_json.get('status') == 'Error':
            error_message = response_json.get('statusMessage', 'An error occurred')
            # Check for specific error messages
            if error_message in ['Invalid Country or Language Code', 'Non publishable Product']:
                return render_template('error.html', error_message=error_message), 400
        
        # Check if product is non-publishable
        if response_json.get('status') == 'Success' and response_json.get('statusMessage') == 'Non publishable Product':
            error_message = 'Non publishable Product'
            return render_template('error.html', error_message=error_message), 400
            
    except json.JSONDecodeError:
        # If JSON decoding fails, use the raw text as the error message
        return render_template('error.html', error_message=f"An unknown error occurred. API Response: {api_response.text}"), 400
    except Exception as e:
        # Catch any other exceptions and display a generic error
        return render_template('error.html', error_message=f"An unexpected error occurred: {str(e)}"), 500

    # Fallback for other unhandled errors
    return render_template('error.html', error_message='An unknown error occurred'), 500