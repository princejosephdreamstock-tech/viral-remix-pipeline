#!/usr/bin/env python3
"""
YouTube Uploader — Reads SEO metadata and uploads with full details
"""
import os, sys, json, pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDENTIALS_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/youtube_credentials.json")
TOKEN_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/youtube_token.pickle")
OUTPUT_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_videos")

def get_youtube_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES, redirect_uri='http://localhost:8080/')
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            print(f"\n🔗 Open this URL and paste the code:\n{auth_url}\n")
            code = input("Code: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

def upload_video(video_path):
    """Upload video with SEO metadata from _seo.json file"""
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return None
    
    youtube = get_youtube_service()
    if not youtube:
        return None
    
    # Try to load SEO metadata
    seo_path = video_path.replace('.mp4', '_seo.json')
    title = None
    description = None
    tags = None
    
    if os.path.exists(seo_path):
        with open(seo_path) as f:
            seo = json.load(f)
            title = seo.get('title')
            description = seo.get('description')
            tags = seo.get('tags')
            print(f"📝 Loaded SEO: {title}")
    
    # Fallbacks
    if not title:
        title = os.path.basename(video_path).replace('.mp4', '').replace('_', ' ')
    if not description:
        description = "Automated content creation. #shorts #automation"
    if not tags:
        tags = ["shorts", "automation"]
    
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
    print(f"   Tags: {', '.join(tags[:5])}")
    
    try:
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   {int(status.progress() * 100)}%")
        
        video_id = response['id']
        print(f"\n✅ https://youtube.com/watch?v={video_id}")
        return video_id
    except Exception as e:
        print(f"❌ {e}")
        return None

if __name__ == "__main__":
    videos = sorted(
        [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp4')],
        key=lambda x: os.path.getmtime(os.path.join(OUTPUT_FOLDER, x)),
        reverse=True
    )
    
    if not videos:
        print("❌ No videos found")
        sys.exit(1)
    
    # Upload the latest video
    latest = os.path.join(OUTPUT_FOLDER, videos[0])
    upload_video(latest)
