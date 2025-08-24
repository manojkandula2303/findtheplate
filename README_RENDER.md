
# Deploy to Render (OCR.Space version)

## 1) Repo contents
- `app.py` (uses OCR.Space API; no Tesseract required)
- `templates/index.html`
- `static/`

## 2) Environment variables (Render → Settings → Environment)
- `OCR_API_KEY` = your OCR.Space API key
- (optional) `GOOGLE_APPS_SCRIPT_URL` = your Apps Script Web App URL

## 3) Render service settings
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Instance type: Free or above

## 4) Notes
- Make sure the service has `static/uploads` write access (it does by default).
- If you use a custom domain, enable HTTPS in Render dashboard.
