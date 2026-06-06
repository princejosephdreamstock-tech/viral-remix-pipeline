#!/usr/bin/env python3
"""
Channel 2 Uploader — Uploads to YouTube + saves to Google Drive
"""
import os, sys, json, pickle, subprocess, re
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
TOKEN_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/channels/channel_2/token.pickle")
GAMEPLAY_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_machine/gameplay")

def get_youtube_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("❌ Channel 2 not authenticated")
            return None
    return build('youtube', 'v3', credentials=creds)

def upload_to_drive(file_path):
    """Upload video to Google Drive using Drive API"""
    try:
        import pickle
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload as DriveMedia
        
        TOKEN_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/channels/channel_2/drive_token.pickle")
        
        creds = None
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        if creds and creds.valid:
            drive = build('drive', 'v3', credentials=creds)
            media = DriveMedia(file_path, mimetype='video/mp4', resumable=True)
            file_metadata = {'name': os.path.basename(file_path)}
            
            print("   📤 Uploading to Google Drive...")
            uploaded_file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = uploaded_file.get('id')
            print(f"   ✅ Drive: https://drive.google.com/file/d/{file_id}/view")
        else:
            print("   ⚠️  Drive not authenticated")
    except Exception as e:
        print(f"   ⚠️  Drive upload failed: {e}")

def parse_metadata(txt_file):
    if not os.path.exists(txt_file):
        return None
    with open(txt_file) as f:
        content = f.read()
    data = {}
    title_match = re.search(r'TITLE:\s*(.+)', content, re.IGNORECASE)
    if title_match: data['title'] = title_match.group(1).strip()
    desc_match = re.search(r'DESCRIPTION:\s*\n?(.+?)(?=\n[A-Z]+:|\Z)', content, re.DOTALL | re.IGNORECASE)
    if desc_match: data['description'] = desc_match.group(1).strip().replace('\n', ' ')
    tags_match = re.search(r'TAGS:\s*(.+)', content, re.IGNORECASE)
    if tags_match: data['tags'] = [t.strip() for t in tags_match.group(1).split(',') if t.strip()]
    return data

def upload_video(video_path, metadata):
    youtube = get_youtube_service()
    if not youtube:
        return None
    
    title = metadata.get('title', os.path.basename(video_path).replace('.mp4', ''))
    description = metadata.get('description', '')
    tags = metadata.get('tags', [])
    
    body = {
        'snippet': {
            'title': title[:100],
            'description': description[:5000],
            'tags': tags[:20],
            'categoryId': '28'
        },
        'status': {
            'privacyStatus': 'public',
            'madeForKids': False
        }
    }
    
    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
    
    print(f"📤 Uploading: {os.path.basename(video_path)}")
    print(f"   Title: {title[:60]}")
    
    try:
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   {int(status.progress() * 100)}%")
        
        video_id = response['id']
        print(f"   ✅ https://youtube.com/watch?v={video_id}")
        
        # Upload to Google Drive after YouTube
        upload_to_drive(video_path)
        
        return video_id
    except Exception as e:
        print(f"   ❌ {e}")
        return None

def upload_all():
    videos = sorted(
        [f for f in os.listdir(GAMEPLAY_FOLDER) if f.endswith('.mp4')],
        key=lambda x: os.path.getmtime(os.path.join(GAMEPLAY_FOLDER, x))
    )
    
    if not videos:
        print("❌ No videos found")
        return
    
    uploaded = 0
    for video_name in videos:
        video_path = os.path.join(GAMEPLAY_FOLDER, video_name)
        txt_name = video_name.replace('.mp4', '.txt')
        txt_path = os.path.join(GAMEPLAY_FOLDER, txt_name)
        
        if not os.path.exists(txt_path):
            print(f"⚠️  No metadata: {video_name}")
            continue
        
        metadata = parse_metadata(txt_path)
        if metadata:
            result = upload_video(video_path, metadata)
            if result:
                uploaded += 1
        print()
    
    print(f"✅ {uploaded}/{len(videos)} uploaded to YouTube + Drive")

if __name__ == "__main__":
    upload_all()
