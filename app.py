import os
import base64
import requests
from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename

# -----------------------------
# Config
# -----------------------------
app = Flask(__name__)

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Set these in your environment
OCR_API_KEY = os.getenv("OCR_API_KEY", "K89643438588957").strip()
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "https://script.google.com/macros/s/AKfycbxI91eW3bGkW3YaoWv1-H3hbM1-wGBOCIiFxLNhQ6RLX3r5vZWpG26d4kVgDqCEgzfV/exec").strip()

# -----------------------------
# Helpers
# -----------------------------
def ocr_space_parse_image(file_path: str, api_key: str, language: str = "eng") -> str:
    """
    Calls OCR.Space to parse text from an image file.
    Returns the parsed text, or raises an Exception with details.
    """
    if not api_key:
        raise RuntimeError("OCR_API_KEY is not set.")

    with open(file_path, "rb") as f:
        # IMPORTANT: OCR.Space expects multipart/form-data with fields in 'data', not JSON
        resp = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": f},
            data={
                "apikey": api_key,
                "language": language,
                "isOverlayRequired": "false",
                "OCREngine": "2",
            },
            timeout=90,
        )

    # Will raise for 4xx/5xx (e.g., 403 if key invalid/quota exceeded)
    resp.raise_for_status()
    data = resp.json()

    if data.get("IsErroredOnProcessing"):
        err = data.get("ErrorMessage") or data.get("ErrorDetails") or "Unknown OCR error"
        if isinstance(err, list):
            err = "; ".join(map(str, err))
        raise RuntimeError(f"OCR.Space error: {err}")

    parsed = (data.get("ParsedResults", [{}])[0].get("ParsedText") or "").strip()
    return parsed


def send_to_google_drive_and_sheet(plate_number: str, image_path: str) -> dict:
    """
    Sends base64 image + plate number to your Google Apps Script web app.
    Expects the script to return JSON with { status: 'success', imageUrl, plateNumber }.
    """
    if not GOOGLE_SCRIPT_URL:
        raise RuntimeError("GOOGLE_SCRIPT_URL is not set.")

    with open(image_path, "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode("utf-8")

    payload = {
        "imageBase64": img_b64,     # matches Apps Script
        "plateNumber": plate_number # matches Apps Script
    }

    headers = {"Content-Type": "application/json"}
    resp = requests.post(
        GOOGLE_SCRIPT_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=90
    )


    # Parse response as JSON if possible
    try:
        data = resp.json()
    except Exception:
        data = {"status": "error", "raw": resp.text}

    # If HTTP not OK, surface error
    if not resp.ok:
        return {"status": "error", "error": f"HTTP {resp.status_code}", "raw": data}

    return data


# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    error_message = ""
    plate_number = ""
    image_url = ""
    google_drive_url = ""

    if request.method == "POST":
        f = request.files.get("image")
        if not f or not f.filename:
            error_message = "No image selected."
            return render_template(
                "index.html",
                error_message=error_message,
                plate_number=plate_number,
                image_url=image_url,
                google_drive_url=google_drive_url,
            )

        # Save uploaded file
        filename = secure_filename(f.filename)
        saved_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(saved_path)

        # Public URL (served by Flask static)
        image_url = url_for("static", filename=f"uploads/{filename}")

        # --- OCR ---
        try:
            plate_number = ocr_space_parse_image(saved_path, OCR_API_KEY)
            if not plate_number:
                plate_number = "Not Detected"
        except Exception as ocr_err:
            plate_number = "Not Detected"
            error_message = f"OCR failed: {ocr_err}"

        # --- Google Drive + Sheet ---
        try:
            result = send_to_google_drive_and_sheet(plate_number, saved_path)
            # Expecting { status: 'success', imageUrl, ... }
            if result.get("status") == "success":
                google_drive_url = result.get("imageUrl") or ""
            else:
                script_err = result.get("error") or result.get("message") or result.get("raw") or "Unknown error from Apps Script"
                error_message = (error_message + (" | " if error_message else "") + f"Drive upload failed: {script_err}")
        except Exception as drive_err:
            error_message = (error_message + (" | " if error_message else "") + f"Drive upload failed: {drive_err}")

    return render_template(
        "index.html",
        error_message=error_message,
        plate_number=plate_number,
        image_url=image_url,
        google_drive_url=google_drive_url,
    )


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    # Local testing only; in production use gunicorn/uwsgi
    app.run(host="0.0.0.0", port=5000, debug=True)
