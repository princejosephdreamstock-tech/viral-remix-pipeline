#!/usr/bin/env python3
"""
Long-Form Reddit Stories Pipeline
Full story narration, looped gameplay, captions, hook + outro.
Horizontal 1920x1080, no #Shorts.
Usage: python longform_pipeline.py <channel> [count]
"""

import os, sys, subprocess, json, pickle, random, asyncio
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads")
GAMEPLAY_FOLDER = os.path.join(DL_BASE, "gameplay_machine", "long_gameplay")
TTS_FOLDER = os.path.join(DL_BASE, "remix_machine", "tts")
OUTPUT_FOLDER = os.path.join(DL_BASE, "remix_machine", "output")
STORIES_FILE = os.path.join(DL_BASE, "remix_machine", "stories.txt")

CHANNELS = {
    "main": {
        "name": "Iam Jay",
        "token": os.path.join(BASE_DIR, "youtube_token.pickle"),
        "secret": os.path.join(BASE_DIR, "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "processed_longform.json"),
        "tags": ['reddit', 'stories', 'storytime', 'aita', 'redditstories'],
        "desc": "Reddit stories with gameplay.\n\nSubscribe for more Reddit stories!"
    },
    "channel_2": {
        "name": "AI Tools",
        "token": os.path.join(BASE_DIR, "channels", "channel_2", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "channel_2", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "channel_2", "processed_longform.json"),
        "tags": ['business', 'stories', 'entrepreneur', 'success'],
        "desc": "Business stories with gameplay.\n\nSubscribe for more!"
    },
    "channel_3": {
        "name": "Minecraft Jay",
        "token": os.path.join(BASE_DIR, "channels", "channel_3", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "channel_3", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "channel_3", "processed_longform.json"),
        "tags": ['reddit', 'stories', 'gaming', 'storytime'],
        "desc": "Reddit gaming stories with gameplay.\n\nSubscribe for more!"
    }
}

for d in [TTS_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(d, exist_ok=True)

def safe_json(path, default=[]):
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return json.load(open(path))
    except:
        pass
    return default

def safe_save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        json.dump(data, open(path, 'w'))
    except:
        pass

def log(msg):
    print(f"  {msg}")

def banner(title):
    print(f"\n{'='*50}\n  {title}\n{'='*50}")

def load_creds(ch):
    cfg = CHANNELS[ch]
    data = pickle.load(open(cfg["token"], 'rb'))
    s = json.load(open(cfg["secret"]))
    installed = s.get("installed", s)
    if isinstance(data, dict):
        return Credentials(
            token=data['access_token'], refresh_token=data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=installed['client_id'], client_secret=installed['client_secret'],
            scopes=['https://www.googleapis.com/auth/youtube.upload',
                    'https://www.googleapis.com/auth/youtube.readonly']
        )
    return data

def load_stories():
    if not os.path.exists(STORIES_FILE):
        return []
    with open(STORIES_FILE) as f:
        content = f.read()
    raw = content.split("===SPLIT===")
    stories = []
    for r in raw:
        r = r.strip()
        if not r:
            continue
        lines = r.split('\n')
        title = lines[0].replace('Title: ', '').strip()
        text = ' '.join(lines[1:]).replace('Text: ', '').strip()
        if title and len(text) > 300:
            stories.append({'title': title, 'text': text})
    return stories

def get_gameplay():
    if not os.path.exists(GAMEPLAY_FOLDER):
        return None
    videos = [f for f in os.listdir(GAMEPLAY_FOLDER) if f.endswith('.mp4')]
    if not videos:
        return None
    return os.path.join(GAMEPLAY_FOLDER, random.choice(videos))

async def generate_tts(text, output_path):
    """Natural voice TTS with Edge."""
    try:
        communicate = edge_tts.Communicate(text[:3000], "en-US-JennyNeural")
        await communicate.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return True
    except:
        pass
    return False

def create_longform(story, index):
    """Create long-form video with looped gameplay, TTS, captions."""
    
    # Step 1: Generate TTS
    tts_path = os.path.join(TTS_FOLDER, f"lf_{index}.mp3")
    text = story['text'][:2500].replace('\n', ' ').strip()
    
    log(f"  Generating TTS ({len(text)} chars)...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ok = loop.run_until_complete(generate_tts(text, tts_path))
    loop.close()
    
    if not ok:
        log("  TTS failed!")
        return None
    
    # Get TTS duration
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", tts_path],
                          capture_output=True, text=True, timeout=10)
        tts_dur = float(r.stdout.strip())
    except:
        tts_dur = 120
    
    video_dur = tts_dur + 10  # Hook (3s) + outro (7s)
    
    # Get gameplay
    gameplay = get_gameplay()
    if not gameplay:
        log("  No gameplay!")
        return None
    
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", gameplay],
                          capture_output=True, text=True, timeout=10)
        gp_dur = float(r.stdout.strip())
    except:
        gp_dur = 420
    
    loops = max(1, int(video_dur / gp_dur) + 1)
    
    safe_title = "".join(c for c in story['title'] if c.isalnum() or c in " -_")[:60]
    output_file = f"LF_{safe_title}_{datetime.now().strftime('%H%M%S')}.mp4"
    output_path = os.path.join(OUTPUT_FOLDER, output_file)
    
    log(f"  Duration: {video_dur:.0f}s ({video_dur/60:.1f} min)")
    log(f"  Gameplay loops: {loops}")
    
    # Build simple, reliable FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", str(loops), "-i", gameplay,
        "-i", tts_path,
        "-t", str(video_dur),
        "-filter_complex",
        f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"drawtext=text='STORY TIME':fontsize=60:fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=10:x=(w-text_w)/2:y=(h-text_h)/3:enable='between(t,0,3)',"
        f"drawtext=text='SUBSCRIBE FOR MORE STORIES':fontsize=46:fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=10:x=(w-text_w)/2:y=h-text_h-180:enable='between(t,{video_dur-7},{video_dur})'[v];"
        f"[0:a]volume=0.25[a1];[1:a]volume=1.5[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "128k", "-threads", "4",
        output_path
    ]
    
    try:
        log(f"  Encoding {video_dur:.0f}s...")
        result = subprocess.run(cmd, check=True, capture_output=True, timeout=900)
        size = os.path.getsize(output_path) / (1024*1024)
        log(f"  Done: {output_file} ({size:.1f}MB)")
        return {"file": output_file, "title": story['title'], "duration": video_dur}
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode()[-200:] if e.stderr else "Unknown"
        log(f"  FFmpeg error: {err}")
    except subprocess.TimeoutExpired:
        log(f"  Timeout! Video too long.")
    
    return None

def upload_video(ch, vid):
    """Upload a single video."""
    cfg = CHANNELS[ch]
    
    try:
        creds = load_creds(ch)
        yt = build('youtube', 'v3', credentials=creds)
        cinfo = yt.channels().list(part='snippet', mine=True).execute()
        cname = cinfo['items'][0]['snippet']['title']
    except Exception as e:
        log(f"Auth error: {e}")
        return False
    
    vpath = os.path.join(OUTPUT_FOLDER, vid['file'])
    if not os.path.exists(vpath):
        log(f"File missing: {vid['file']}")
        return False
    
    title = vid['title'][:90]
    mins = int(vid.get('duration', 600) / 60)
    
    body = {
        'snippet': {
            'title': title,
            'description': cfg["desc"],
            'tags': cfg["tags"],
            'categoryId': '20'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }
    
    try:
        media = MediaFileUpload(vpath, mimetype='video/mp4', resumable=True, chunksize=1024*1024*5)
        response = yt.videos().insert(part='snippet,status', body=body, media_body=media).execute()
        vid_id = response.get('id', 'NO ID')
        log(f"  Uploaded: https://www.youtube.com/watch?v={vid_id}")
        return True
    except Exception as e:
        log(f"  Upload failed: {str(e)[:80]}")
        return False

def run_pipeline(ch, count=1):
    # Kill proxy
    subprocess.run(["pkill", "-f", "proxy"], capture_output=True)
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
        os.environ.pop(var, None)
    
    start = datetime.now()
    cfg = CHANNELS[ch]
    print(f"\n{'='*55}")
    print(f"  LONG-FORM REDDIT STORIES - {cfg['name']}")
    print(f"  Voice: Jenny Neural (Edge TTS)")
    print(f"  Format: 1920x1080 Horizontal")
    print(f"  {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}")
    
    stories = load_stories()
    if not stories:
        print(f"\n  No stories in {STORIES_FILE}")
        return
    
    print(f"\n  Loaded {len(stories)} stories")
    selected = random.sample(stories, min(count, len(stories)))
    
    banner("CREATING LONG-FORM VIDEO")
    processed = safe_json(cfg["processed"])
    uploaded = 0
    
    for i, story in enumerate(selected):
        print(f"\n  [{i+1}/{len(selected)}] {story['title'][:60]}")
        vid = create_longform(story, i)
        if vid:
            if upload_video(ch, vid):
                processed.append(vid['file'])
                uploaded += 1
    
    safe_save(cfg["processed"], processed)
    
    end = datetime.now()
    print(f"\n{'='*55}")
    print(f"  Done: {uploaded}/{len(selected)} uploaded")
    print(f"  Time: {(end-start).total_seconds()/60:.1f} min")
    print(f"{'='*55}")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CHANNELS:
        print("Usage: python longform_pipeline.py [main|channel_2|channel_3] [count]")
        sys.exit(1)
    run_pipeline(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1)
