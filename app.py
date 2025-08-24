
from flask import Flask, render_template, request
import os
import base64
import requests

app = Flask(__name__)

# Upload folder
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Google Apps Script URL (keep your existing value or set via env var)
GOOGLE_APPS_SCRIPT_URL = os.getenv('GOOGLE_APPS_SCRIPT_URL', 'https://script.google.com/macros/s/AKfycby7BWctJ1HuX5vhwvnfD32N1KjKvuGlYSyoiQlVRK47tyh206Y0pYs7PIxv5EXq0NBC/exec')

# OCR.Space API Key (set in Render as env var OCR_API_KEY)
OCR_API_KEY = os.getenv('OCR_API_KEY', 'K89643438588957')

def ocr_space_parse_image(file_path, api_key, language='eng'):
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': f},
            data={'apikey': api_key, 'language': language}
        )
    resp.raise_for_status()
    data = resp.json()
    # Handle common error structures
    if data.get('IsErroredOnProcessing'):
        err = data.get('ErrorMessage') or data.get('ErrorDetails')
        raise RuntimeError(f"OCR.Space error: {err}")
    parsed = data.get('ParsedResults', [{}])[0].get('ParsedText', '')
    return (parsed or '').strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    plate_number = ""
    image_path = ""
    google_drive_url = ""
    error_message = ""

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename:
            try:
                # Save image
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(image_path)

                # OCR via OCR.Space
                try:
                    plate_number = ocr_space_parse_image(image_path, OCR_API_KEY)
                    if not plate_number:
                        plate_number = "Not Detected"
                except Exception as ocr_err:
                    error_message = f"OCR failed: {ocr_err}"
                    plate_number = "Not Detected"

                # Convert image to base64 for Google Apps Script
                try:
                    with open(image_path, 'rb') as img_file:
                        image_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                    payload = {
                        "image": image_base64,
                        "filename": os.path.basename(image_path),
                        "plate_number": plate_number
                    }
                    response_drive = requests.post(GOOGLE_APPS_SCRIPT_URL, data=payload, timeout=60)
                    if response_drive.status_code == 200:
                        google_drive_url = response_drive.text
                    else:
                        error_message += " | Failed to upload to Google Drive."
                except Exception as drive_err:
                    if error_message:
                        error_message += " | "
                    error_message += f"Drive upload failed: {drive_err}"

            except Exception as e:
                error_message = f"Error processing image: {str(e)}"

    return render_template(
        'index.html',
        plate_number=plate_number,
        image_path=image_path,
        google_drive_url=google_drive_url,
        error_message=error_message
    )

if __name__ == '__main__':
    # For local testing only
    app.run(host='0.0.0.0', port=5000, debug=True)
