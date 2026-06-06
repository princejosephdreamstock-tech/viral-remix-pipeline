#!/usr/bin/env python3
"""
Backup posted videos to Google Drive.
Usage: python backup_to_drive.py
"""

import os, json, pickle, sys
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

DL_BASE = os.path.expanduser("~/storage/downloads/gameplay_machine")
BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
TOKEN_PATH = os.path.join(BASE_DIR, "drive_token.pickle")
SECRET_PATH = os.path.join(BASE_DIR, "drive_client_secret.json")
BACKUP_LOG = os.path.join(BASE_DIR, "drive_backup_log.json")

SCOPES = ['https://www.googleapis.com/auth/drive.file']

CHANNELS = {
    "main": {
        "name": "Iam Jay",
        "folder": os.path.join(DL_BASE, "channel_main", "gameplay"),
        "posted_log": os.path.join(BASE_DIR, "posted_main.json"),
        "drive_folder": None  # Will be created automatically
    },
    "channel_2": {
        "name": "Channel 2",
        "folder": os.path.join(DL_BASE, "channel_2", "gameplay"),
        "posted_log": os.path.join(BASE_DIR, "channels", "channel_2", "posted_videos.json"),
        "drive_folder": None
    }
}

def get_drive_service():
    """Authenticate and return Drive service."""
    if not os.path.exists(SECRET_PATH):
        print("ERROR: drive_client_secret.json not found")
        print("Download from Google Cloud Console (Desktop app)")
        print(f"Place it at: {SECRET_PATH}")
        return None
    
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as f:
            creds = pickle.load(f)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                SECRET_PATH, SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            print("\n1. Open this URL in your browser:")
            print(auth_url)
            print("\n2. Enter the code:")
            code = input("> ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)
    
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(drive, folder_name):
    """Get or create a folder in Google Drive."""
    # Search for existing folder
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive.files().list(q=query, fields="files(id,name)").execute()
    folders = results.get('files', [])
    
    if folders:
        return folders[0]['id']
    
    # Create new folder
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = drive.files().create(body=folder_metadata, fields='id').execute()
    print(f"  Created folder: {folder_name}")
    return folder['id']

def load_backup_log():
    if os.path.exists(BACKUP_LOG):
        with open(BACKUP_LOG, 'r') as f:
            return json.load(f)
    return {}

def save_backup_log(log):
    with open(BACKUP_LOG, 'w') as f:
        json.dump(log, f, indent=2)

def backup_channel(drive, channel_key, ch, backup_log):
    """Backup all posted but not-yet-backed-up videos for one channel."""
    print(f"\n{'='*50}")
    print(f"  {ch['name']} ({channel_key})")
    print(f"{'='*50}")
    
    # Get posted videos
    if not os.path.exists(ch["posted_log"]):
        print("  No posted log yet. Nothing to backup.")
        return 0
    
    with open(ch["posted_log"], 'r') as f:
        posted = json.load(f)
    
    if not posted:
        print("  No posted videos yet.")
        return 0
    
    # Get already backed up list
    channel_backups = backup_log.get(channel_key, [])
    
    # Find videos to backup
    to_backup = [v for v in posted if v not in channel_backups]
    
    if not to_backup:
        print(f"  All {len(posted)} posted videos already backed up.")
        return 0
    
    print(f"  Posted: {len(posted)}")
    print(f"  Already backed up: {len(channel_backups)}")
    print(f"  To backup: {len(to_backup)}")
    
    # Create channel folder in Drive
    folder_id = get_or_create_folder(drive, f"GameplayMachine_{ch['name']}")
    
    # Upload each video
    backed_up = 0
    for vf in to_backup:
        vpath = os.path.join(ch["folder"], vf)
        
        if not os.path.exists(vpath):
            print(f"  ⚠️  File missing: {vf}")
            continue
        
        print(f"  Uploading: {vf[:50]}...")
        
        try:
            file_metadata = {
                'name': vf,
                'parents': [folder_id]
            }
            media = MediaFileUpload(vpath, mimetype='video/mp4', resumable=True)
            drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
            
            channel_backups.append(vf)
            backed_up += 1
            print(f"    ✅ Done")
        except Exception as e:
            print(f"    ❌ Failed: {str(e)[:80]}")
    
    # Update backup log
    backup_log[channel_key] = channel_backups
    save_backup_log(backup_log)
    
    print(f"\n  Backed up: {backed_up}/{len(to_backup)}")
    return backed_up

def backup_all():
    """Run backup for all channels."""
    print(f"\n{'='*55}")
    print(f"  GOOGLE DRIVE BACKUP")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")
    
    drive = get_drive_service()
    if not drive:
        return
    
    backup_log = load_backup_log()
    
    total = 0
    for key, ch in CHANNELS.items():
        total += backup_channel(drive, key, ch, backup_log)
    
    print(f"\n{'='*55}")
    print(f"  Total backed up: {total} videos")
    print(f"  Run daily: python backup_to_drive.py")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    backup_all()
