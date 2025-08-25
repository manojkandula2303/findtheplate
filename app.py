import os
import base64
import requests
from flask import Flask, render_template, request, jsonify
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
GOOGLE_SCRIPT_URL = os.getenv(
    "GOOGLE_SCRIPT_URL",
    "https://script.google.com/macros/s/AKfycbz-dcG1KESQRZoPAMdcbDFmkrTrLbHny9_jZGK5kNnnyqj9QBYbIAv-BKKRiBdTWyq6/exec"
).strip()

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
        "plateNumber": plate_number,
        "fileName": os.path.basename(image_path),  # ✅ added filename
        "base64Image": img_b64
    }

    resp = requests.post(
        GOOGLE_SCRIPT_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=90
    )

    try:
        data = resp.json()
    except Exception:
        data = {"status": "error", "raw": resp.text}

    if not resp.ok:
        return {"status": "error", "error": f"HTTP {resp.status_code}", "raw": data}

    return data


# -----------------------------
# Routes
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save file locally
    filename = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(filename)

    # ✅ Run OCR
    try:
        plate_number = ocr_space_parse_image(filename, OCR_API_KEY)
    except Exception as e:
        return jsonify({"error": f"OCR failed: {e}"}), 500

    # ✅ Send to Google Apps Script
    try:
        resp = send_to_google_drive_and_sheet(plate_number, filename)
    except Exception as e:
        return jsonify({"error": f"Drive/Sheet upload failed: {e}"}), 500

    return jsonify({
        "plate_number": plate_number,
        "google_response": resp
    })


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
