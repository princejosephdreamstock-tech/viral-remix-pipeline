#!/usr/bin/env python3
"""
Reddit Stories Pipeline - Edge TTS + Gameplay Background
Natural voice narration, Subway Surfers gameplay, hook + outro.
Usage: python reddit_pipeline.py <channel> [count]
"""

import os, sys, subprocess, json, pickle, random, asyncio
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads")
GAMEPLAY_FOLDER = os.path.join(DL_BASE, "gameplay_machine", "long_gameplay")
TTS_FOLDER = os.path.join(DL_BASE, "remix_machine", "tts")
OUTPUT_FOLDER = os.path.join(DL_BASE, "remix_machine", "output")
STORIES_FILE = os.path.join(DL_BASE, "remix_machine", "stories_joy2.txt")

UPLOAD_HOUR, UPLOAD_MINUTE, MAX_PER_RUN = 14, 0, 10

CHANNELS = {
    "main": {
        "name": "Iam Jay", "token": os.path.join(BASE_DIR, "youtube_token.pickle"),
        "secret": os.path.join(BASE_DIR, "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "processed_reddit.json"),
        "tags": ['Shorts', 'reddit', 'stories', 'viral'], "desc": "#Shorts #reddit #stories"
    },
    "channel_2": {
        "name": "AI Tools", "token": os.path.join(BASE_DIR, "channels", "channel_2", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "channel_2", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "channel_2", "processed_reddit.json"),
        "tags": ['Shorts', 'business', 'stories', 'motivation'], "desc": "#Shorts #business #stories"
    },
    
    "joy_1": {
        "name": "Gaming Nightmares", "token": os.path.join(BASE_DIR, "channels", "joy_1", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "joy_1", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "joy_1", "processed_reddit.json"),
        "tags": ['Shorts', 'gaming', 'stories', 'funny'], "desc": "#Shorts #gaming #stories"
    },
    "joy_2": {
        "name": "Reddit Talezz", "token": os.path.join(BASE_DIR, "channels", "joy_2", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "joy_2", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "joy_2", "processed_reddit.json"),
        "tags": ['Shorts', 'reddit', 'stories', 'aita'], "desc": "#Shorts #reddit #stories"
    },
    "joy_3": {
        "name": "Business Confessions", "token": os.path.join(BASE_DIR, "channels", "joy_3", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "joy_3", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "joy_3", "processed_reddit.json"),
        "tags": ['Shorts', 'business', 'stories', 'entrepreneur'], "desc": "#Shorts #business #stories"
    },
    "joy_4": {
        "name": "Love & Lies", "token": os.path.join(BASE_DIR, "channels", "joy_4", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "joy_4", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "joy_4", "processed_reddit.json"),
        "tags": ['Shorts', 'relationships', 'stories', 'dating'], "desc": "#Shorts #relationships #stories"
    },
    "joy_5": {
        "name": "Petty Revenge Daily", "token": os.path.join(BASE_DIR, "channels", "joy_5", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "joy_5", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "joy_5", "processed_reddit.json"),
        "tags": ['Shorts', 'revenge', 'stories', 'justice'], "desc": "#Shorts #revenge #stories"
    },
    "joy_6": {
        "name": "Creepy Encounters", "token": os.path.join(BASE_DIR, "channels", "joy_6", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "joy_6", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "joy_6", "processed_reddit.json"),
        "tags": ['Shorts', 'scary', 'stories', 'creepy'], "desc": "#Shorts #scary #stories"
    },
    "channel_3": {
        "name": "Minecraft Jay", "token": os.path.join(BASE_DIR, "channels", "channel_3", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "channel_3", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "channel_3", "processed_reddit.json"),
        "tags": ['Shorts', 'reddit', 'stories', 'viral'], "desc": "#Shorts #reddit #stories"
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
    print(f"\n{'='*45}\n  {title}\n{'='*45}")

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
        if title and text:
            stories.append({'title': title, 'text': text})
    return stories

def load_tags(ch):
    """Load tags from channel folder."""
    tag_path = os.path.join(DL_BASE, "gameplay_machine", ch, "stories", "tags.txt")
    if os.path.exists(tag_path):
        with open(tag_path) as f:
            return [t.strip() for t in f.read().split(",") if t.strip()]
    return ['Shorts', 'reddit', 'stories']

def load_desc(ch):
    """Load description from channel folder."""
    desc_path = os.path.join(DL_BASE, "gameplay_machine", ch, "stories", "description.txt")
    if os.path.exists(desc_path):
        with open(desc_path) as f:
            return f.read().strip()
    return "#Shorts #stories"

def get_gameplay():
    if not os.path.exists(GAMEPLAY_FOLDER):
        return None
    videos = [f for f in os.listdir(GAMEPLAY_FOLDER) if f.endswith('.mp4')]
    if not videos:
        return None
    return os.path.join(GAMEPLAY_FOLDER, random.choice(videos))

async def generate_tts(text, output_path):
    """Generate natural TTS using Edge TTS."""
    try:
        text = text[:1000]  # Limit length
        communicate = edge_tts.Communicate(text, "en-US-JennyNeural")
        await communicate.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
            return output_path
    except:
        pass
    return None

def create_video_sync(story, index):
    """Wrapper to run async TTS then create video."""
    tts_path = os.path.join(TTS_FOLDER, f"story_{index}.mp3")
    
    # Generate TTS
    text = story['text'][:800].replace('\n', ' ').strip()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(generate_tts(text, tts_path))
    loop.close()
    
    if not result:
        log("TTS failed!")
        return None
    
    gameplay = get_gameplay()
    if not gameplay:
        log("No gameplay!")
        return None
    
    # Get TTS duration
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "default=noprint_wrappers=1:nokey=1", tts_path],
                          capture_output=True, text=True, timeout=10)
        tts_dur = float(r.stdout.strip())
    except:
        tts_dur = 30
    
    clip_dur = min(tts_dur + 3, 55)
    start = random.randint(0, 180)
    
    safe_title = "".join(c for c in story['title'] if c.isalnum() or c in " -_")[:40]
    output_file = f"story_{safe_title}_{datetime.now().strftime('%H%M%S')}.mp4"
    output_path = os.path.join(OUTPUT_FOLDER, output_file)
    
    log(f"  {story['title'][:50]}...")
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", gameplay,
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
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        size = os.path.getsize(output_path)
        if size > 10000:
            log(f"  Created: {output_file} ({size//1024}KB)")
            return {"file": output_file, "title": story['title']}
    except Exception as e:
        log(f"  FFmpeg error: {str(e)[:100]}")
    
    return None

def upload_and_schedule(ch, videos):
    cfg = CHANNELS[ch]
    banner(f"UPLOADING TO {cfg['name']}")
    
    if not videos:
        print("  No videos")
        return 0
    
    try:
        creds = load_creds(ch)
        yt = build('youtube', 'v3', credentials=creds)
        cinfo = yt.channels().list(part='snippet', mine=True).execute()
        cname = cinfo['items'][0]['snippet']['title']
        print(f"  Channel: {cname}")
    except Exception as e:
        log(f"Auth error: {e}")
        return 0
    
    try:
        req = yt.search().list(part='snippet', forMine=True, maxResults=50, type='video', order='date').execute()
        scheduled = []
        for item in req.get('items', []):
            v = yt.videos().list(part='status', id=item['id']['videoId']).execute()
            if v['items'] and v['items'][0]['status']['privacyStatus'] == 'private':
                if 'publishAt' in v['items'][0]['status']:
                    scheduled.append(v['items'][0]['status']['publishAt'])
    except:
        scheduled = []
    
    print(f"  Scheduled: {len(scheduled)}")
    
    processed = safe_json(cfg["processed"])
    uploaded = 0
    
    for i, vid in enumerate(videos):
        if uploaded >= MAX_PER_RUN:
            break
        
        vpath = os.path.join(OUTPUT_FOLDER, vid['file'])
        if not os.path.exists(vpath):
            continue
        
        day = 1
        sd = None
        while day <= 365:
            c = datetime.utcnow() + timedelta(days=day)
            c = c.replace(hour=UPLOAD_HOUR, minute=UPLOAD_MINUTE, second=0, microsecond=0)
            if c.isoformat() + 'Z' not in scheduled:
                sd = c
                break
            day += 1
        
        if not sd:
            break
        
        # Clean title - max 100 chars
        title = vid['title'][:85]
        body = {
            'snippet': {
                'title': f"{title} #Shorts",
                'description': cfg["desc"],
                'tags': cfg["tags"],
                'categoryId': '20'
            },
            'status': {
                'privacyStatus': 'private',
                'publishAt': sd.isoformat() + 'Z',
                'selfDeclaredMadeForKids': False
            }
        }
        
        print(f"  [{i+1}] {title[:50]}... -> {sd.strftime('%Y-%m-%d %H:%M UTC')}")
        
        try:
            media = MediaFileUpload(vpath, mimetype='video/mp4', resumable=True, chunksize=1024*1024)
            response = yt.videos().insert(part='snippet,status', body=body, media_body=media).execute()
            if response and 'id' in response:
                processed.append(vid['file'])
                scheduled.append(sd.isoformat() + 'Z')
                uploaded += 1
        except Exception as e:
            err = str(e)
            if "quota" in err.lower() or "uploadLimitExceeded" in err.lower():
                print(f"    Quota reached.")
                break
            print(f"    Failed: {err[:80]}")
    
    safe_save(cfg["processed"], processed)
    print(f"\n  Uploaded: {uploaded} to {cname}")
    return uploaded

def run_pipeline(ch, count=3):
    subprocess.run(["pkill", "-f", "proxy"], capture_output=True)
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
        os.environ.pop(var, None)
    
    start = datetime.now()
    cfg = CHANNELS[ch]
    print(f"\n{'='*50}")
    print(f"  REDDIT STORIES PIPELINE - {cfg['name']}")
    print(f"  Voice: Jenny (Edge TTS)")
    print(f"  {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}")
    
    all_stories = load_stories()
    if not all_stories:
        print(f"\n  No stories found in {STORIES_FILE}")
        return
    
    print(f"\n  Loaded {len(all_stories)} stories")
    selected = random.sample(all_stories, min(count, len(all_stories)))
    
    banner("CREATING VIDEOS")
    videos = []
    for i, story in enumerate(selected):
        print(f"\n  [{i+1}/{len(selected)}]")
        vid = create_video_sync(story, i)
        if vid:
            videos.append(vid)
    
    print(f"\n  Created: {len(videos)}/{len(selected)} videos")
    uploaded = upload_and_schedule(ch, videos) if videos else 0
    
    end = datetime.now()
    print(f"\n{'='*50}")
    print(f"  {len(selected)} stories / {len(videos)} videos / {uploaded} uploaded")
    print(f"  Time: {(end-start).total_seconds()/60:.1f} min")
    print(f"{'='*50}")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CHANNELS:
        print("Usage: python reddit_pipeline.py [main|channel_2|channel_3] [count]")
        sys.exit(1)
    run_pipeline(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
