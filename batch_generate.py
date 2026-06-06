#!/usr/bin/env python3
"""
Batch Generator + Uploader for CHANNEL 1
Processes voiceovers → generates videos → uploads to YouTube + Drive
"""
import os, subprocess, re, json, pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VOICEOVER_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_machine/voiceovers")
OUTPUT_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_videos")
TOKEN_YT = os.path.expanduser("~/intent-radar/content/gameplay_machine/youtube_token.pickle")
CREDS_YT = os.path.expanduser("~/intent-radar/content/gameplay_machine/youtube_credentials.json")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

voiceovers = sorted([f for f in os.listdir(VOICEOVER_FOLDER) if f.endswith(('.mp3','.wav','.m4a'))])

if not voiceovers:
    print("❌ No voiceovers found")
    exit()

# Authenticate YouTube
with open(TOKEN_YT, 'rb') as f:
    yt_creds = pickle.load(f)
yt = build('youtube', 'v3', credentials=yt_creds)

# Authenticate Drive
DRIVE_TOKEN = os.path.expanduser("~/intent-radar/content/gameplay_machine/channels/channel_2/drive_token.pickle")
drive = None
if os.path.exists(DRIVE_TOKEN):
    with open(DRIVE_TOKEN, 'rb') as f:
        drive_creds = pickle.load(f)
    drive = build('drive', 'v3', credentials=drive_creds)


print(f"🎙️  Found {len(voiceovers)} voiceovers. Uploading to CHANNEL 1\n")

for i, vo in enumerate(voiceovers):
    vo_path = os.path.join(VOICEOVER_FOLDER, vo)
    txt_name = vo.rsplit('.', 1)[0] + '.txt'
    txt_path = os.path.join(VOICEOVER_FOLDER, txt_name)
    
    if not os.path.exists(txt_path):
        print(f"⚠️  No metadata for: {vo}")
        continue
    
    with open(txt_path) as f:
        c = f.read()
    
    title = re.search(r'TITLE:\s*(.+)', c, re.I)
    desc = re.search(r'DESCRIPTION:\s*\n?(.+?)(?=\nTAGS:)', c, re.DOTALL | re.I)
    tags = re.search(r'TAGS:\s*(.+)', c, re.I)
    
    title = title.group(1).strip() if title else vo
    desc = desc.group(1).strip() if desc else ''
    tags = [t.strip() for t in tags.group(1).split(',') if t.strip()] if tags else []
    
    print(f"🎬 [{i+1}/{len(voiceovers)}] {vo[:40]}...")
    print(f"   Title: {title[:60]}")
    
    # Touch voiceover to make it newest
    os.utime(vo_path, None)
    
    # Generate video
    subprocess.run(['python3', 'content/gameplay_machine/engine.py'], capture_output=True)
    
    # Find generated video
    videos = sorted(
        [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp4')],
        key=lambda x: os.path.getmtime(os.path.join(OUTPUT_FOLDER, x)),
        reverse=True
    )
    
    if not videos:
        print("   ❌ No video generated")
        continue
    
    video_path = os.path.join(OUTPUT_FOLDER, videos[0])
    
    # Schedule: tomorrow + i days at 2 PM UTC
    publish_time = datetime.utcnow() + timedelta(days=i+1)
    publish_time = publish_time.replace(hour=14, minute=0, second=0, microsecond=0)
    
    body = {
        'snippet': {
            'title': title[:100],
            'description': desc[:5000],
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
    req = yt.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    res = None
    while res is None:
        st, res = req.next_chunk()
        if st: print(f"   {int(st.progress()*100)}%")
    
    print(f"   ✅ https://youtube.com/watch?v={res['id']}")
    print(f"   📅 Scheduled: {publish_time}")

    # Upload to Drive
    if drive:
        try:
            media2 = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
            uploaded = drive.files().create(body={'name': videos[0]}, media_body=media2, fields='id').execute()
            print(f"   ✅ Drive: https://drive.google.com/file/d/{uploaded.get('id')}/view")
        except Exception as e:
            print(f"   ⚠️  Drive: {e}")

    print()

print(f"✅ All {len(voiceovers)} videos scheduled on Channel 1")
