#!/usr/bin/env python3
"""
Auto Upload — Finds ANY video + matching .txt in gameplay folder and uploads to YouTube + Drive
"""
import pickle, os, re
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_YT = os.path.expanduser("~/intent-radar/content/gameplay_machine/channels/channel_2/token.pickle")
TOKEN_DRIVE = os.path.expanduser("~/intent-radar/content/gameplay_machine/channels/channel_2/drive_token.pickle")
GAMEPLAY = os.path.expanduser("~/storage/downloads/gameplay_machine/gameplay")

# Find the first .mp4 that has a matching .txt and hasn't been uploaded yet
videos = sorted(
    [f for f in os.listdir(GAMEPLAY) if f.endswith('.mp4')],
    key=lambda x: os.path.getmtime(os.path.join(GAMEPLAY, x)),
    reverse=True
)

uploaded = False
for video in videos:
    txt_file = video.replace('.mp4', '.txt')
    txt_path = os.path.join(GAMEPLAY, txt_file)
    video_path = os.path.join(GAMEPLAY, video)
    
    if not os.path.exists(txt_path):
        continue
    
    # Parse metadata
    with open(txt_path) as f:
        c = f.read()
    
    title = re.search(r'TITLE:\s*(.+)', c, re.I)
    desc = re.search(r'DESCRIPTION:\s*\n?(.+?)(?=\n[A-Z]+:|\Z)', c, re.DOTALL | re.I)
    tags = re.search(r'TAGS:\s*(.+)', c, re.I)
    
    if not title:
        continue
    
    title = title.group(1).strip()
    desc = desc.group(1).strip().replace('\n', ' ') if desc else ''
    tags = [t.strip() for t in tags.group(1).split(',') if t.strip()] if tags else []
    
    print(f"📤 Found: {video}")
    print(f"   Title: {title[:60]}")
    
    # Upload to YouTube
    try:
        with open(TOKEN_YT, 'rb') as f:
            yt_creds = pickle.load(f)
        yt = build('youtube', 'v3', credentials=yt_creds)
        
        body = {
            'snippet': {
                'title': title[:100],
                'description': desc[:5000],
                'tags': tags[:20],
                'categoryId': '28'
            },
            'status': {
                'privacyStatus': 'public',
                'madeForKids': False
            }
        }
        
        media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
        req = yt.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        res = None
        while res is None:
            st, res = req.next_chunk()
            if st: print(f"   YouTube: {int(st.progress()*100)}%")
        print(f"   ✅ YouTube: https://youtube.com/watch?v={res['id']}")
    except Exception as e:
        print(f"   ❌ YouTube: {e}")
    
    # Upload to Drive
    try:
        with open(TOKEN_DRIVE, 'rb') as f:
            drive_creds = pickle.load(f)
        drive = build('drive', 'v3', credentials=drive_creds)
        
        media2 = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
        uploaded_file = drive.files().create(body={'name': video}, media_body=media2, fields='id').execute()
        print(f"   ✅ Drive: https://drive.google.com/file/d/{uploaded_file.get('id')}/view")
    except Exception as e:
        print(f"   ❌ Drive: {e}")
    
    uploaded = True
    break

if not uploaded:
    print("❌ No videos with matching .txt metadata found.")
