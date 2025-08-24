# Google Drive + Sheets + Apps Script Integration Setup Guide

## Overview
This guide will help you set up the Google Drive + Sheets + Apps Script integration for your License Plate Recognition app. The system will:
1. Upload images to Google Drive
2. Store image links and OCR results in Google Sheets
3. Create a simple, clean database without traditional server-side databases

## Step 1: Create Google Drive Folder

1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder called "License Plate Images"
3. Right-click the folder and select "Share"
4. Set permissions to "Anyone with the link can view"
5. Copy the folder ID from the URL (it's the long string after `/folders/`)

## Step 2: Create Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet called "License Plate Database"
3. Copy the spreadsheet ID from the URL (it's the long string between `/d/` and `/edit`)

## Step 3: Set Up Google Apps Script

1. Go to [Google Apps Script](https://script.google.com)
2. Click "New Project"
3. Replace the default code with the contents of `google_apps_script.js`
4. Update the configuration variables:
   ```javascript
   const DRIVE_FOLDER_ID = 'YOUR_ACTUAL_FOLDER_ID';
   const SPREADSHEET_ID = 'YOUR_ACTUAL_SPREADSHEET_ID';
   ```

## Step 4: Deploy Apps Script as Web App

1. Click "Deploy" → "New deployment"
2. Choose "Web app" as the type
3. Set "Execute as" to "Me"
4. Set "Who has access" to "Anyone"
5. Click "Deploy"
6. Copy the Web App URL

## Step 5: Update Flask Configuration

1. Open `app.py`
2. Replace `YOUR_APPS_SCRIPT_WEB_APP_URL` with your actual Web App URL:
   ```python
   GOOGLE_APPS_SCRIPT_URL = 'https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec'
   ```

## Step 6: Test the Integration

1. Run your Flask app: `python app.py`
2. Upload an image through the web interface
3. Check that:
   - Image appears in your Google Drive folder
   - Data appears in your Google Sheets
   - The web interface shows success status

## Troubleshooting

### Common Issues:

1. **"Google Drive upload failed"**
   - Check that your Apps Script URL is correct
   - Verify folder and spreadsheet IDs
   - Ensure Apps Script has necessary permissions

2. **"Apps Script URL not configured"**
   - Update the `GOOGLE_APPS_SCRIPT_URL` in `app.py`

3. **Permission errors**
   - Make sure your Google account has access to Drive and Sheets
   - Check that the Apps Script is deployed as a web app with proper permissions

### Testing Apps Script:

1. In Apps Script editor, run the `testSetup()` function
2. Check the execution log for any errors
3. Run `setupInitialStructure()` to create the sheet if needed

## Security Considerations

- The current setup makes images publicly accessible via links
- Consider restricting access if you need privacy
- Apps Script runs with your Google account permissions

## Data Structure

Your Google Sheet will have these columns:
- **Timestamp**: When the image was processed
- **Image URL**: Direct link to the image in Google Drive
- **Plate Number**: OCR-extracted text
- **Processed Date**: Human-readable date

## Maintenance

- Monitor your Google Drive storage usage
- Regularly backup your spreadsheet data
- Consider archiving old images if storage becomes an issue

## Benefits of This Approach

✅ **No database setup required**
✅ **Familiar Google interface**
✅ **Automatic backups**
✅ **Easy data export**
✅ **Scalable storage**
✅ **Cost-effective**
✅ **Real-time collaboration possible**

## Next Steps

Once working, you can enhance the system with:
- Email notifications for new entries
- Data analytics and charts
- Automated reporting
- Integration with other Google services
