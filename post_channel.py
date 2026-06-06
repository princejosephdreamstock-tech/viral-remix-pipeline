#!/usr/bin/env python3
"""SIMPLE SINGLE-CHANNEL POSTER – reads stories/tags/desc from channel folder."""
import os, sys, subprocess, json, pickle, random, asyncio
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads")
GAMEPLAY = os.path.join(DL_BASE, "gameplay_machine", "long_gameplay")
TTS_DIR = os.path.join(DL_BASE, "remix_machine", "tts")
OUT_DIR = os.path.join(DL_BASE, "remix_machine", "output")

# ─── CONFIG FOR ALL CHANNELS ────────────────────────────
CHANNEL_KEYS = {
    "joy_20": "The Dark Corner",
    "joy_19": "Malicious Compliance",
    "joy_18": "Cheaters Exposed",
    "joy_17": "Startup Horror Stories",
    "joy_16": "Paranormal Files",
    "joy_15": "Justice Served Daily",
    "joy_14": "Instant Karma Stories",
    "joy_13": "Marriage Drama Daily",
    "joy_12": "Dating Disaster Stories",
    "joy_11": "Boss Level Stories",
    "joy_10": "Career Revenge Daily",
    "joy_9": "Midnight Horror Tales",
    "joy_8": "Scary Story Hour",
    "joy_7": "Horror Stories Daily",
    "joy_1": "Gaming Nightmares",
    "joy_2": "Reddit Talezz",
    "joy_3": "Business Confessions",
    "joy_4": "Love & Lies",
    "joy_5": "Petty Revenge Daily",
    "joy_6": "Creepy Encounters",
}

def load_channel_files(ch):
    """Read stories, tags, description from channel's own folder."""
    base = os.path.join(DL_BASE, "gameplay_machine", ch, "stories")
    stories_path = os.path.join(base, "stories.txt")
    tags_path = os.path.join(base, "tags.txt")
    desc_path = os.path.join(base, "description.txt")

    # Stories
    if not os.path.exists(stories_path):
        print(f"❌ Missing {stories_path}")
        return None, None, None
    with open(stories_path) as f:
        raw = f.read()
    stories = []
    for part in raw.split("===SPLIT==="):
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n')
        title = lines[0].replace('Title: ', '').strip()
        text = ' '.join(lines[1:]).replace('Text: ', '').strip()
        if title and text:
            stories.append({'title': title, 'text': text})
    
    # Tags
    tags = ['Shorts', 'stories']
    if os.path.exists(tags_path):
        with open(tags_path) as f:
            tags = [t.strip() for t in f.read().split(',') if t.strip()]
    
    # Description
    desc = "#Shorts #stories"
    if os.path.exists(desc_path):
        with open(desc_path) as f:
            desc = f.read().strip()
    
    return stories, tags, desc

def get_creds(ch):
    token = os.path.join(BASE_DIR, "channels", ch, "token.pickle")
    secret = os.path.join(BASE_DIR, "channels", ch, "client_secret.json")
    with open(token, 'rb') as f:
        data = pickle.load(f)
    with open(secret) as f:
        s = json.load(f)
    inst = s.get("installed", s)
    if isinstance(data, dict):
        return Credentials(
            token=data['access_token'], refresh_token=data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=inst['client_id'], client_secret=inst['client_secret'],
            scopes=['https://www.googleapis.com/auth/youtube.upload',
                    'https://www.googleapis.com/auth/youtube.readonly']
        )
    return data

async def tts(text, out_path):
    try:
        communicate = edge_tts.Communicate(text[:2500], "en-US-JennyNeural")
        await communicate.save(out_path)
        return os.path.exists(out_path) and os.path.getsize(out_path) > 1000
    except:
        return False

def pick_gameplay():
    if not os.path.isdir(GAMEPLAY):
        return None
    vids = [f for f in os.listdir(GAMEPLAY) if f.endswith('.mp4')]
    if not vids:
        return None
    return os.path.join(GAMEPLAY, random.choice(vids))

def make_video(story, idx):
    tts_path = os.path.join(TTS_DIR, f"vid_{idx}.mp3")
    text = story['text'].replace('\n', ' ').strip()
    print(f"  Generating voice for: {story['title'][:50]}...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ok = loop.run_until_complete(tts(text, tts_path))
    loop.close()
    if not ok:
        print("  TTS failed")
        return None
    
    gp = pick_gameplay()
    if not gp:
        print("  No gameplay found")
        return None
    
    # durations
    import subprocess as sp
    try:
        r = sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", tts_path],
                   capture_output=True, text=True, timeout=10)
        tts_dur = float(r.stdout.strip())
    except:
        tts_dur = 30
    clip_dur = min(tts_dur + 3, 55)
    start = random.randint(0, 180)
    
    safe_title = "".join(c for c in story['title'] if c.isalnum() or c in " -_")[:40]
    out_file = f"{safe_title}_{datetime.now().strftime('%H%M%S')}.mp4"
    out_path = os.path.join(OUT_DIR, out_file)
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", gp,
        "-i", tts_path,
        "-t", str(clip_dur),
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"drawtext=text='STORY TIME':fontsize=48:fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=8:x=(w-text_w)/2:y=(h-text_h)/3:enable='between(t,0,2)',"
        f"drawtext=text='LIKE AND SUBSCRIBE':fontsize=42:fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=8:x=(w-text_w)/2:y=h-text_h-60:enable='between(t,{clip_dur-5},{clip_dur})'[v];"
        f"[0:a]volume=0.3[a1];[1:a]volume=1.5[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "128k", "-threads", "4",
        out_path
    ]
    try:
        sp.run(cmd, check=True, capture_output=True, timeout=180)
        if os.path.getsize(out_path) > 50000:
            print(f"  Created {out_file} ({os.path.getsize(out_path)//1024}KB)")
            return out_file
    except Exception as e:
        print(f"  FFmpeg error: {str(e)[:100]}")
    return None

def upload(ch, video_file, title, tags, desc):
    creds = get_creds(ch)
    yt = build('youtube', 'v3', credentials=creds)
    cinfo = yt.channels().list(part='snippet', mine=True).execute()
    cname = cinfo['items'][0]['snippet']['title']
    print(f"  Uploading to {cname}...")
    
    body = {
        'snippet': {
            'title': title[:90] + " #Shorts",
            'description': desc,
            'tags': tags[:10],
            'categoryId': '20'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    media = MediaFileUpload(video_file, mimetype='video/mp4', resumable=True, chunksize=1024*1024)
    resp = yt.videos().insert(part='snippet,status', body=body, media_body=media).execute()
    vid_id = resp['id']
    print(f"  ✅ https://www.youtube.com/watch?v={vid_id}")
    return vid_id

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CHANNEL_KEYS:
        print("Usage: python post_channel.py [joy_1|joy_2|joy_3|joy_4|joy_5|joy_6] [count]")
        sys.exit(1)
    ch = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    stories, tags, desc = load_channel_files(ch)
    if not stories:
        print("No stories found.")
        sys.exit(1)
    print(f"Channel: {CHANNEL_KEYS[ch]} – {len(stories)} stories loaded")
    print(f"First story: {stories[0]['title'][:60]}")
    
    selected = random.sample(stories, min(count, len(stories)))
    for i, story in enumerate(selected):
        print(f"\n[{i+1}/{len(selected)}] {story['title'][:50]}")
        vf = make_video(story, i)
        if vf:
            upload(ch, os.path.join(OUT_DIR, vf), story['title'], tags, desc)
