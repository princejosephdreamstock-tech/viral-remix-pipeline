#!/usr/bin/env python3
"""
Content Scheduler — Schedules ALL videos at once, one per day
"""
import os, sys, json, pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
CREDENTIALS_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/youtube_credentials.json")
TOKEN_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/youtube_token.pickle")
OUTPUT_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_videos")
SCHEDULE_FILE = os.path.expanduser("~/storage/downloads/gameplay_machine/schedule.json")

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

def schedule_all():
    """Schedule ALL unuploaded videos, one per day starting tomorrow"""
    youtube = get_youtube_service()
    if not youtube:
        return
    
    # Get all videos sorted by creation time
    all_videos = sorted(
        [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp4')],
        key=lambda x: os.path.getmtime(os.path.join(OUTPUT_FOLDER, x))
    )
    
    if not all_videos:
        print("❌ No videos found")
        return
    
    # Load schedule to skip already uploaded
    schedule = {"uploaded": []}
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE) as f:
            schedule = json.load(f)
    
    # Filter out already uploaded videos
    pending = [v for v in all_videos if v not in schedule.get('uploaded', [])]
    
    if not pending:
        print("✅ All videos already scheduled")
        return
    
    print(f"📋 {len(pending)} videos to schedule\n")
    
    tomorrow = datetime.utcnow() + timedelta(days=1)
    
    for i, video_name in enumerate(pending):
        video_path = os.path.join(OUTPUT_FOLDER, video_name)
        
        # Load SEO metadata
        seo_path = video_path.replace('.mp4', '_seo.json')
        title = video_name.replace('.mp4', '').replace('_', ' ')[:100]
        description = "Automated content. #shorts"
        tags = ["shorts", "automation"]
        
        if os.path.exists(seo_path):
            with open(seo_path) as f:
                seo = json.load(f)
                title = seo.get('title', title)
                description = seo.get('description', description)
                tags = seo.get('tags', tags)
        
        # Schedule: tomorrow + i days at 8 PM EST
        publish_time = tomorrow + timedelta(days=i)
        publish_time = publish_time.replace(hour=20, minute=0, second=0, microsecond=0)
        
        body = {
            'snippet': {
                'title': title[:100],
                'description': description[:5000],
                'tags': tags[:20],
                'categoryId': '28'
            },
            'status': {
                'privacyStatus': 'private',
                'publishAt': publish_time.isoformat() + 'Z',
                'madeForKids': False
            }
        }
        
        media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
        
        print(f"📤 Day {i+1}: {video_name[:40]}...")
        print(f"   Title: {title[:60]}")
        print(f"   Scheduled: {publish_time.strftime('%Y-%m-%d %H:%M')} UTC")
        
        try:
            request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"   Uploading: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            print(f"   ✅ Scheduled! https://youtube.com/watch?v={video_id}")
            
            schedule['uploaded'].append(video_name)
            with open(SCHEDULE_FILE, 'w') as f:
                json.dump(schedule, f, indent=2)
                
        except Exception as e:
            print(f"   ❌ {e}")
        
        print()
    
    print(f"✅ {len(pending)} videos scheduled over {len(pending)} days")
    print(f"   First video goes live: {tomorrow.strftime('%Y-%m-%d %H:%M')} UTC")

if __name__ == "__main__":
    schedule_all()
