#!/usr/bin/env python3
"""
Viral Pipeline - TTS + Text Overlay + Outro (Monetization Safe)
Downloads viral clips, adds TTS commentary, text overlays, and outro.
Usage: python viral_pipeline.py <channel> [count]
"""

import os, sys, subprocess, json, pickle, random
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads")
REMIX_INPUT = os.path.join(DL_BASE, "remix_machine", "input")
REMIX_OUTPUT = os.path.join(DL_BASE, "remix_machine", "output")
DRIVE_BACKUP = os.path.join(DL_BASE, "remix_machine", "drive_backup")
TTS_OUTPUT = os.path.join(DL_BASE, "remix_machine", "tts")

UPLOAD_HOUR, UPLOAD_MINUTE, MAX_PER_RUN = 14, 0, 10

CHANNELS = {
    "main": {
        "name": "Iam Jay", "token": os.path.join(BASE_DIR, "youtube_token.pickle"),
        "secret": os.path.join(BASE_DIR, "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "processed_videos.json"),
        "queries": ["roblox funny moments", "roblox viral", "CaseOh roblox"],
        "tags": ['Shorts', 'roblox', 'viral', 'gaming'], "desc": "#Shorts #roblox"
    },
    "channel_2": {
        "name": "AI Tools", "token": os.path.join(BASE_DIR, "channels", "channel_2", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "channel_2", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "channel_2", "processed_videos.json"),
        "queries": ["ai tools for marketing", "best ai tools 2026"],
        "tags": ['Shorts', 'ai', 'aitools', 'marketing'], "desc": "#Shorts #aitools"
    },
    "channel_3": {
        "name": "Minecraft Jay", "token": os.path.join(BASE_DIR, "channels", "channel_3", "token.pickle"),
        "secret": os.path.join(BASE_DIR, "channels", "channel_3", "client_secret.json"),
        "processed": os.path.join(BASE_DIR, "channels", "channel_3", "processed_videos.json"),
        "queries": ["minecraft funny moments", "minecraft build hacks", "minecraft survival"],
        "tags": ['Shorts', 'minecraft', 'gaming', 'viral'], "desc": "#Shorts #minecraft"
    }
}

# TTS hooks
TTS_HOOK = "Make sure to like and subscribe for more"
OUTRO_TEXT = "LIKE & SUBSCRIBE"

for d in [REMIX_INPUT, REMIX_OUTPUT, DRIVE_BACKUP, TTS_OUTPUT]:
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

# ============ TTS ============

def generate_tts():
    """Generate TTS audio file using espeak."""
    output_file = os.path.join(TTS_OUTPUT, f"tts_{datetime.now().strftime('%H%M%S')}.wav")
    
    try:
        subprocess.run(["pkg", "install", "espeak", "-y"], capture_output=True, timeout=30)
        subprocess.run([
            "espeak", "-w", output_file,
            "-s", "160", "-p", "45",
            TTS_HOOK
        ], check=True, capture_output=True, timeout=15)
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 500:
            return output_file
    except:
        pass
    
    return None

# ============ YOUTUBE HUNT ============

def hunt_videos(ch, count):
    cfg = CHANNELS[ch]
    banner(f"STEP 1: FINDING VIRAL VIDEOS - {cfg['name']}")
    
    query = random.choice(cfg["queries"])
    print(f"  Search: {query}")
    
    try:
        creds = load_creds(ch)
        yt = build('youtube', 'v3', credentials=creds)
        req = yt.search().list(part='snippet', q=query, maxResults=min(count*2, 50),
                               type='video', videoDuration='short', order='viewCount').execute()
        results = []
        for item in req.get('items', []):
            vid_id = item['id']['videoId']
            try:
                vid = yt.videos().list(part='contentDetails,statistics', id=vid_id).execute()
                if vid['items']:
                    dur = vid['items'][0]['contentDetails']['duration']
                    if 'M' not in dur or dur == 'PT1M':
                        results.append({'id': vid_id, 'title': item['snippet']['title'],
                                        'url': f'https://www.youtube.com/watch?v={vid_id}'})
            except:
                pass
        
        for f in os.listdir(REMIX_INPUT):
            try:
                os.remove(os.path.join(REMIX_INPUT, f))
            except:
                pass
        
        downloaded = []
        for i, v in enumerate(results[:count]):
            out = os.path.join(REMIX_INPUT, f"{v['id']}.mp4")
            print(f"  [{i+1}/{min(count, len(results))}] {v['title'][:40]}...")
            try:
                subprocess.run([
                    "yt-dlp", "-f", "best[height<=1080]",
                    "--user-agent", "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
                    "--socket-timeout", "20", "--retries", "2", "--no-playlist",
                    "--output", out, v['url']
                ], capture_output=True, text=True, timeout=90)
                
                if os.path.exists(out) and os.path.getsize(out) > 2000:
                    downloaded.append(v)
                    print(f"    OK")
            except:
                pass
        
        print(f"  Downloaded {len(downloaded)} videos")
        return downloaded
    except Exception as e:
        log(f"Error: {e}")
        return []

# ============ REMIX: TTS + TEXT + OUTRO ============

def remix_one(v):
    """Remix with TTS voiceover, text overlay, and outro."""
    vid_id = v['id']
    
    for f in os.listdir(REMIX_INPUT):
        if vid_id in f:
            input_path = os.path.join(REMIX_INPUT, f)
            break
    else:
        return None
    
    if not os.path.exists(input_path):
        return None
    
    safe_title = "".join(c for c in v['title'] if c.isalnum() or c in " -_")[:35]
    output_file = f"tts_{safe_title}_{datetime.now().strftime('%H%M%S')}.mp4"
    output_path = os.path.join(REMIX_OUTPUT, output_file)
    
    # Generate TTS
    tts_path = generate_tts()
    has_tts = tts_path is not None
    
    # Video filter: transform + text overlays
    HOOK_TEXT = "WAIT FOR IT..."
    
    vf = (
        "crop=ih*9/16:ih,"
        "scale=1080:1920,"
        "eq=contrast=1.03:saturation=1.03,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"drawtext=text='{HOOK_TEXT}':fontsize=52:fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=10:x=(w-text_w)/2:y=(h-text_h)/3:enable='between(t,0,3)',"
        f"drawtext=text='{OUTRO_TEXT}':fontsize=46:fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=10:x=(w-text_w)/2:y=h-text_h-60:enable='between(t,50,55)'"
    )
    
    if has_tts:
        # Mix TTS with original audio
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(random.randint(0, 30)),
            "-i", input_path,
            "-i", tts_path,
            "-t", "55",
            "-vf", vf,
            "-filter_complex",
            "[0:a]atempo=1.03,volume=0.8[a1];[1:a]volume=1.5,adelay=3000[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "128k", "-threads", "4",
            output_path
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(random.randint(0, 30)),
            "-i", input_path,
            "-t", "55",
            "-vf", vf,
            "-af", "atempo=1.03",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "128k", "-threads", "4",
            output_path
        ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        features = ["TTS+outro" if has_tts else "outro"]
        return {"file": output_file, "title": v['title'], "features": features}
    except Exception as e:
        log(f"Remix failed: {str(e)[:80]}")
        return None

def remix_all(videos):
    banner("STEP 2: TTS + TEXT + OUTRO REMIX")
    
    subprocess.run(["pkg", "install", "espeak", "-y"], capture_output=True)
    
    results = []
    for i, v in enumerate(videos):
        print(f"\n  [{i+1}/{len(videos)}] {v['title'][:40]}...")
        r = remix_one(v)
        if r:
            results.append(r)
            size = os.path.getsize(os.path.join(REMIX_OUTPUT, r['file'])) // (1024*1024)
            print(f"    OK ({size}MB) | {', '.join(r['features'])}")
    
    print(f"\n  Remixed: {len(results)}/{len(videos)}")
    return results

# ============ UPLOAD ============

def upload_and_schedule(ch, remixed):
    cfg = CHANNELS[ch]
    banner(f"STEP 3: UPLOADING TO {cfg['name']}")
    
    if not remixed:
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
    
    print(f"  Already scheduled: {len(scheduled)}")
    
    processed = safe_json(cfg["processed"])
    uploaded = 0
    
    for i, vid in enumerate(remixed):
        if uploaded >= MAX_PER_RUN:
            break
        
        vpath = os.path.join(REMIX_OUTPUT, vid['file'])
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
        
        title = vid['title'][:85]
        body = {
            'snippet': {
                'title': f"{title} #Shorts",
                'description': cfg["desc"],
                'tags': cfg["tags"] + ['reaction', 'commentary'],
                'categoryId': '20'
            },
            'status': {
                'privacyStatus': 'private',
                'publishAt': sd.isoformat() + 'Z',
                'selfDeclaredMadeForKids': False
            }
        }
        
        print(f"  [{i+1}] {title[:45]}... → {sd.strftime('%Y-%m-%d %H:%M UTC')}")
        
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
            print(f"    Failed: {err[:50]}")
    
    safe_save(cfg["processed"], processed)
    print(f"\n  Uploaded: {uploaded} to {cname}")
    return uploaded

def cleanup():
    for f in os.listdir(REMIX_INPUT):
        try:
            os.remove(os.path.join(REMIX_INPUT, f))
        except:
            pass

def run_pipeline(ch, count=5):
    subprocess.run(["pkill", "-f", "proxy"], capture_output=True)
    for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']:
        os.environ.pop(var, None)
    
    start = datetime.now()
    cfg = CHANNELS[ch]
    print(f"\n{'='*50}")
    print(f"  VIRAL PIPELINE - {cfg['name']}")
    print(f"  TTS + Text Overlay + Outro")
    print(f"  {start.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*50}")
    
    videos = hunt_videos(ch, count)
    if not videos:
        print("\n  Nothing found.")
        return
    
    for v in videos:
        for f in os.listdir(REMIX_INPUT):
            if v['id'] in f:
                src = os.path.join(REMIX_INPUT, f)
                dst = os.path.join(DRIVE_BACKUP, f)
                if not os.path.exists(dst):
                    subprocess.run(["cp", src, dst], capture_output=True)
    print("  Originals backed up")
    
    remixed = remix_all(videos)
    uploaded = upload_and_schedule(ch, remixed) if remixed else 0
    cleanup()
    
    end = datetime.now()
    print(f"\n{'='*50}")
    print(f"  {len(videos)}↓ / {len(remixed)}⟳ / {uploaded}↑")
    print(f"  Time: {(end-start).total_seconds()/60:.1f} min")
    print(f"{'='*50}")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CHANNELS:
        print("Usage: python viral_pipeline.py [main|channel_2|channel_3] [count]")
        sys.exit(1)
    run_pipeline(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 5)
