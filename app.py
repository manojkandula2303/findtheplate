from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename
import os
import base64
import requests

# -----------------------------
# Config
# -----------------------------
app = Flask(__name__)

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# OCR.Space API key (set in Render → Environment)
OCR_API_KEY = os.getenv("OCR_API_KEY", "K89643438588957").strip()

# Google Apps Script Web App URL (set in Render → Environment)
# This must be the deployed web app URL (Execute as: Me, Access: Anyone with the link)
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL", "https://script.google.com/macros/s/AKfycby3Fm-stNZ3wAFMcLeIoNl89FPPCMJgAlg4AoQwaTJW_6Mwl9IUvUVbVXMBCjAsOruz/exec").strip()

# -----------------------------
# Helpers
# -----------------------------
def ocr_space_parse_image(file_path: str, api_key: str, language: str = "eng") -> str:
    """
    Calls OCR.Space to parse text from an image file.
    Returns the parsed text or raises an Exception on failure.
    """
    if not api_key:
        raise RuntimeError("OCR API key not set. Please set OCR_API_KEY env var in Render.")

    with open(file_path, "rb") as f:
        resp = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": f},
            data={
                "apikey": api_key,
                "language": language,
                "isOverlayRequired": "false",
                "OCREngine": "2",  # newer engine
            },
            timeout=90,
        )

    resp.raise_for_status()
    data = resp.json()

    # If API indicates an error
    if data.get("IsErroredOnProcessing"):
        # The API can return either a string or an array here
        err = data.get("ErrorMessage") or data.get("ErrorDetails") or "Unknown OCR error"
        # Normalize list to string if needed
        if isinstance(err, list):
            err = "; ".join([str(x) for x in err])
        raise RuntimeError(f"OCR.Space error: {err}")

    parsed = (data.get("ParsedResults", [{}])[0].get("ParsedText") or "").strip()
    return parsed


def send_to_google_drive_and_sheet(plate_number: str, image_path: str) -> dict:
    """
    Sends base64 image + plate number to your Google Apps Script web app.
    Your Apps Script expects JSON with keys: 'image' (base64) and 'plate_number'.
    Returns parsed JSON from the script (should include success flag and image_url).
    """
    if not GOOGLE_SCRIPT_URL:
        raise RuntimeError("Google Script URL not set. Please set GOOGLE_SCRIPT_URL env var in Render.")

    with open(image_path, "rb") as img_file:
        img_b64 = base64.b64encode(img_file.read()).decode("utf-8")

    payload = {
        "image": img_b64,          # your script reads data.image
        "plate_number": plate_number,  # your script reads data.plate_number
    }

    resp = requests.post(GOOGLE_SCRIPT_URL, json=payload, timeout=90)
    # Some Apps Script deployments return text/plain — try JSON decode safely
    try:
        data = resp.json()
    except Exception:
        # Fallback if Apps Script returned plain text
        data = {"success": resp.ok, "raw": resp.text}

    if not resp.ok:
        return {"success": False, "error": f"HTTP {resp.status_code}", "raw": data}

    return data


# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    error_message = ""
    plate_number = ""
    image_url = ""          # URL for <img> in the page
    google_drive_url = ""   # File URL returned by Apps Script

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

        # Save upload
        filename = secure_filename(f.filename)
        saved_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(saved_path)

        # Build a public URL for the static file (for display only)
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
            if result.get("success"):
                # Your script returns 'image_url' when successful
                google_drive_url = result.get("image_url") or result.get("fileUrl") or ""
            else:
                # Combine script-side error with any earlier error
                script_err = result.get("error") or result.get("raw") or "Unknown error from Apps Script"
                error_message = f"{error_message} | Drive upload failed: {script_err}".strip(" |")
        except Exception as drive_err:
            error_message = f"{error_message} | Drive upload failed: {drive_err}".strip(" |")

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
    # Local testing only. In Render, use: gunicorn app:app
    app.run(host="0.0.0.0", port=5000, debug=True)
