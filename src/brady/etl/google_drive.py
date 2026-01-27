"""
Google Drive File Downloader for Brady ETL Pipeline
====================================================

This script downloads the source files from Google Drive for local processing.

Usage:
    1. Install requirements: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
    2. Enable Google Drive API in Google Cloud Console
    3. Create OAuth credentials and download the JSON file
    4. Run: python google_drive_downloader.py --credentials path/to/credentials.json

Alternatively, you can manually download files from Google Drive:
    - Crime Gun Dealer DB: https://docs.google.com/spreadsheets/d/1SOUl4Xrv6FLUY_t5bNAzO6xB8pftIYcfY3NUBwutC58
    - Demand Letters: https://docs.google.com/spreadsheets/d/1l7iUG1t4sti3LM2HRVc2Yb3CZVBsh-GS0MiG5gITZLk
    - PA Trace Data: https://drive.google.com/drive/folders/1ZN7XEq2ols6XEKFsQH6e7rAkKaMv5LNT
"""

import os
import io
from pathlib import Path
from typing import Optional

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")


# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# File IDs from your Google Drive
FILES_TO_DOWNLOAD = {
    'crime_gun_dealer_db': {
        'id': '1SOUl4Xrv6FLUY_t5bNAzO6xB8pftIYcfY3NUBwutC58',
        'name': 'crime_gun_dealer_database.xlsx',
        'type': 'spreadsheet',
        'description': 'Crime Gun Dealer Database with court doc FFLs, Philadelphia Trace, Rochester Trace'
    },
    'demand_letters': {
        'id': '1l7iUG1t4sti3LM2HRVc2Yb3CZVBsh-GS0MiG5gITZLk',
        'name': 'demand_letters_database.xlsx',
        'type': 'spreadsheet',
        'description': 'Demand Letter 2 FFLs tracking DL2 program participation 2021-2024'
    },
    'pa_trace_xlsx': {
        'id': '1RS-BUBBgkGhsa9iBw0F7JZQ0Xv15mKT7',
        'name': 'PA-gunTracingData.xlsx',
        'type': 'file',
        'description': 'Pennsylvania gun tracing data (XLSX format, 65.9 MB)'
    },
}

# Folder ID containing raw files
GUNDATA_FOLDER_ID = '1ZN7XEq2ols6XEKFsQH6e7rAkKaMv5LNT'


def get_credentials(credentials_path: str, token_path: str = 'token.json') -> Optional[Credentials]:
    """Get or refresh Google API credentials"""
    creds = None

    # Check for existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                print(f"ERROR: Credentials file not found: {credentials_path}")
                print("\nTo get credentials:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a project and enable Google Drive API")
                print("3. Create OAuth 2.0 credentials (Desktop app)")
                print("4. Download the credentials JSON file")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for next time
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds


def download_spreadsheet_as_xlsx(service, file_id: str, output_path: str) -> bool:
    """Download a Google Spreadsheet as XLSX"""
    try:
        request = service.files().export_media(
            fileId=file_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"  Download progress: {int(status.progress() * 100)}%")

        fh.seek(0)
        with open(output_path, 'wb') as f:
            f.write(fh.read())

        print(f"  Saved to: {output_path}")
        return True

    except Exception as e:
        print(f"  ERROR downloading spreadsheet: {e}")
        return False


def download_file(service, file_id: str, output_path: str) -> bool:
    """Download a regular file from Google Drive"""
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"  Download progress: {int(status.progress() * 100)}%")

        fh.seek(0)
        with open(output_path, 'wb') as f:
            f.write(fh.read())

        print(f"  Saved to: {output_path}")
        return True

    except Exception as e:
        print(f"  ERROR downloading file: {e}")
        return False


def list_folder_contents(service, folder_id: str):
    """List contents of a Google Drive folder"""
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name, mimeType, size)"
        ).execute()

        files = results.get('files', [])

        print(f"\nFolder contents ({len(files)} files):")
        for f in files:
            size = f.get('size', 'N/A')
            if size != 'N/A':
                size = f"{int(size) / (1024*1024):.1f} MB"
            print(f"  - {f['name']} ({size})")
            print(f"    ID: {f['id']}")
            print(f"    Type: {f['mimeType']}")

        return files

    except Exception as e:
        print(f"ERROR listing folder: {e}")
        return []


def download_all_files(credentials_path: str, output_dir: str = './brady_source_data'):
    """Download all source files from Google Drive"""
    if not GOOGLE_API_AVAILABLE:
        print("ERROR: Google API libraries not available")
        return False

    print("=" * 60)
    print("BRADY ETL - GOOGLE DRIVE DOWNLOADER")
    print("=" * 60)

    # Setup
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get credentials
    print("\nAuthenticating with Google Drive...")
    creds = get_credentials(credentials_path)
    if not creds:
        return False

    # Build service
    service = build('drive', 'v3', credentials=creds)
    print("Authentication successful!")

    # List folder contents
    print(f"\nListing GunData folder contents...")
    list_folder_contents(service, GUNDATA_FOLDER_ID)

    # Download each file
    print("\n" + "=" * 60)
    print("DOWNLOADING FILES...")
    print("=" * 60)

    for key, file_info in FILES_TO_DOWNLOAD.items():
        print(f"\n[{key}] {file_info['description']}")
        output_file = output_path / file_info['name']

        if file_info['type'] == 'spreadsheet':
            success = download_spreadsheet_as_xlsx(service, file_info['id'], str(output_file))
        else:
            success = download_file(service, file_info['id'], str(output_file))

        if success:
            print(f"  SUCCESS!")
        else:
            print(f"  FAILED - you may need to download manually")

    print("\n" + "=" * 60)
    print(f"Files downloaded to: {output_path}")
    print("=" * 60)

    return True


def manual_download_instructions():
    """Print instructions for manual download"""
    print("""
================================================================================
MANUAL DOWNLOAD INSTRUCTIONS
================================================================================

If you cannot use the automated downloader, download files manually:

1. CRIME GUN DEALER DATABASE
   URL: https://docs.google.com/spreadsheets/d/1SOUl4Xrv6FLUY_t5bNAzO6xB8pftIYcfY3NUBwutC58
   Download as: File > Download > Microsoft Excel (.xlsx)
   Save as: crime_gun_dealer_database.xlsx

2. DEMAND LETTERS DATABASE
   URL: https://docs.google.com/spreadsheets/d/1l7iUG1t4sti3LM2HRVc2Yb3CZVBsh-GS0MiG5gITZLk
   Download as: File > Download > Microsoft Excel (.xlsx)
   Save as: demand_letters_database.xlsx

3. PA GUN TRACING DATA (CSV)
   Folder: https://drive.google.com/drive/folders/1ZN7XEq2ols6XEKFsQH6e7rAkKaMv5LNT
   Download: PA-gunTracingData.csv
   Size: ~275 MB

4. PA GUN TRACING DATA (XLSX)
   Folder: https://drive.google.com/drive/folders/1ZN7XEq2ols6XEKFsQH6e7rAkKaMv5LNT
   Download: PA-gunTracingData.xlsx
   Size: ~66 MB

After downloading, run the ETL script:
    python brady_unified_etl.py \\
        --crime-gun crime_gun_dealer_database.xlsx \\
        --demand-letters demand_letters_database.xlsx \\
        --pa-trace-csv PA-gunTracingData.csv \\
        --pa-trace-xlsx PA-gunTracingData.xlsx

================================================================================
""")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Download Brady ETL source files from Google Drive')
    parser.add_argument('--credentials', type=str, help='Path to Google OAuth credentials JSON')
    parser.add_argument('--output-dir', type=str, default='./brady_source_data', help='Output directory')
    parser.add_argument('--manual', action='store_true', help='Show manual download instructions')

    args = parser.parse_args()

    if args.manual:
        manual_download_instructions()
    elif args.credentials:
        download_all_files(args.credentials, args.output_dir)
    else:
        print("No credentials provided. Showing manual download instructions...\n")
        manual_download_instructions()
