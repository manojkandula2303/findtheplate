import os
import re
import json
import time
import string
import requests
from datetime import datetime


from flask import Flask, render_template, request, jsonify


# --- Image / Video & OCR ---
import cv2
import numpy as np
import pytesseract


# --- Google Drive ---
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


###############################################
# CONFIGURATION — EDIT THESE VALUES
###############################################
# 1) Path to your Tesseract binary (Windows usually like below). If not needed, leave as None
TESSERACT_CMD = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe" # or None on Linux/mac when tesseract is in PATH


# 2) Google Service Account JSON key file (downloaded from Google Cloud)
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service_account.json')


# 3) Google Drive folder ID where files should be uploaded
DRIVE_FOLDER_ID = '1HTPMqzuLBXQHU79lDlQCVmkm_6ad-n6l' # ← your folder ID


# 4) Deployed Google Apps Script Web App URL (to log rows into Sheets)
APPS_SCRIPT_WEBAPP_URL = 'https://script.google.com/macros/s/PASTE_YOUR_DEPLOYMENT_ID/exec' # ← replace!


# 5) (Optional) Sheet URL to show users (purely for UI convenience)
SHEET_HUMAN_URL = 'https://docs.google.com/spreadsheets/d/1CwHs7pCZeQkwgu3O3PaybCI5sEEPibcovoDmL8u-zP0/edit#gid=0'


###############################################
# App & Clients
###############################################
app = Flask(__name__)
UPLOAD_DIR = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


if TESSERACT_CMD:
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


SCOPES = [
'https://www.googleapis.com/auth/drive.file', # create/edit files your app creates
'https://www.googleapis.com/auth/drive.readonly'
]


def _drive_client():
creds = service_account.Credentials.from_service_account_file(
SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
return build('drive', 'v3', credentials=creds, cache_discovery=False)


###############################################
# Helpers — OCR
###############################################
PLATE_CHAR_WHITELIST = string.ascii_uppercase + string.digits
app.run(host='0.0.0.0', port=port, debug=True)
