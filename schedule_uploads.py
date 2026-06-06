#!/usr/bin/env python3
"""
Channel 2 Scheduler — Uploads to YouTube + Google Drive
Video 1: Today | Video 2: Tomorrow
"""
import os, pickle, re
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES_YT = ['https://www.googleapis.com/auth/youtube.upload']
TOKEN_YT = os.path.expanduser("~/intent-radar/content/gameplay_machine/channels/channel_2/token.pickle")
TOKEN_DRIVE = os.path.expanduser("~/intent-radar/content/gameplay_machine/channels/channel_2/drive_token.pickle")
GAMEPLAY = os.path.expanduser("~/storage/downloads/gameplay_machine/gameplay")

def get_youtube():
    creds = None
    if os.path.exists(TOKEN_YT):
        with open(TOKEN_YT, 'rb') as f: creds = pickle.load(f)
    if creds and creds.valid:
        return build('youtube', 'v3', credentials=creds)
    print("❌ YouTube not authenticated")
    return None

def get_drive():
    creds = None
    if os.path.exists(TOKEN_DRIVE):
        with open(TOKEN_DRIVE, 'rb') as f: creds = pickle.load(f)
    if creds and creds.valid:
        return build('drive', 'v3', credentials=creds)
    print("⚠️  Drive not authenticated")
    return None

def parse_meta(txt_path):
    if not os.path.exists(txt_path): return None
    with open(txt_path) as f: c = f.read()
    d = {}
    m = re.search(r'TITLE:\s*(.+)', c, re.I)
    if m: d['title'] = m.group(1).strip()
    m = re.search(r'DESCRIPTION:\s*\n?(.+?)(?=\n[A-Z]+:|\Z)', c, re.DOTALL | re.I)
    if m: d['desc'] = m.group(1).strip().replace('\n', ' ')
    m = re.search(r'TAGS:\s*(.+)', c, re.I)
    if m: d['tags'] = [t.strip() for t in m.group(1).split(',') if t.strip()]
    return d

def upload_to_drive(path):
    drive = get_drive()
    if not drive: return
    try:
        media = MediaFileUpload(path, mimetype='video/mp4', resumable=True)
        f = drive.files().create(body={'name': os.path.basename(path)}, media_body=media, fields='id').execute()
        print(f"   ✅ Drive: https://drive.google.com/file/d/{f.get('id')}/view")
    except Exception as e:
        print(f"   ⚠️  Drive: {e}")

def upload_video(path, meta, schedule=None):
    yt = get_youtube()
    if not yt: return
    body = {
        'snippet': {
            'title': meta.get('title', '')[:100],
            'description': meta.get('desc', '')[:5000],
            'tags': meta.get('tags', [])[:20],
            'categoryId': '28'
        },
        'status': {
            'privacyStatus': 'private' if schedule else 'public',
            'madeForKids': False
        }
    }
    if schedule:
        body['status']['publishAt'] = schedule.isoformat() + 'Z'
    
    media = MediaFileUpload(path, mimetype='video/mp4', resumable=True)
    print(f"📤 {os.path.basename(path)}")
    if schedule: print(f"   Scheduled: {schedule}")
    try:
        req = yt.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        res = None
        while res is None:
            st, res = req.next_chunk()
            if st: print(f"   {int(st.progress()*100)}%")
        print(f"   ✅ https://youtube.com/watch?v={res['id']}")
        upload_to_drive(path)
    except Exception as e:
        print(f"   ❌ {e}")

# === RUN ===
print("=" * 50)
print("  CHANNEL 2 UPLOADER")
print("=" * 50)

# Video 1 — Today
v1 = os.path.join(GAMEPLAY, "EU_AI_Act__Human_Oversight.mp4")
t1 = v1.replace('.mp4', '.txt')
if os.path.exists(v1):
    m1 = parse_meta(t1)
    if m1:
        print("\n🚀 VIDEO 1 — TODAY")
        upload_video(v1, m1)
else:
    print("❌ Video 1 not found")

# Video 2 — Tomorrow
v2 = os.path.join(GAMEPLAY, "Article_14__Human_Oversight.mp4")
t2 = v2.replace('.mp4', '.txt')
if os.path.exists(v2):
    m2 = parse_meta(t2)
    if m2:
        tomorrow = datetime.utcnow() + timedelta(days=1)
        pub = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        print("\n⏰ VIDEO 2 — TOMORROW")
        upload_video(v2, m2, schedule=pub)
else:
    print("❌ Video 2 not found")
