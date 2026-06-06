#!/usr/bin/env python3
"""
Watchdog – Automatic daily poster with retry.
Reads per-channel story files, posts one new video per channel per day.
Retries failed uploads every 30 minutes. Never repeats a story.
Usage: python watchdog.py
"""

import os, sys, subprocess, json, pickle, random, asyncio, time, traceback
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

# ─── paths ──────────────────────────────────────────
BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads")
GAMEPLAY_FOLDER = os.path.join(DL_BASE, "gameplay_machine", "long_gameplay")
TTS_DIR = os.path.join(DL_BASE, "remix_machine", "tts")
OUT_DIR = os.path.join(DL_BASE, "remix_machine", "output")
LOG_FILE = os.path.join(BASE_DIR, "watchdog_state.json")

# ─── channel list ───────────────────────────────────
CHANNELS = {
    "joy_1": "Gaming Nightmares",
    "joy_2": "Reddit Talezz",
    "joy_3": "Business Confessions",
    "joy_4": "Love & Lies",
    "joy_5": "Petty Revenge Daily",
    "joy_6": "Creepy Encounters",
}

for d in [TTS_DIR, OUT_DIR]:
    os.makedirs(d, exist_ok=True)

# ─── helpers ────────────────────────────────────────
def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except:
        pass
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def load_channel_files(ch):
    base = os.path.join(DL_BASE, "gameplay_machine", ch, "stories")
    stories_path = os.path.join(base, "stories.txt")
    tags_path = os.path.join(base, "tags.txt")
    desc_path = os.path.join(base, "description.txt")

    if not os.path.exists(stories_path):
        return None, None, None, None

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

    tags = ['Shorts', 'stories']
    if os.path.exists(tags_path):
        with open(tags_path) as f:
            tags = [t.strip() for t in f.read().split(',') if t.strip()]

    desc = "#Shorts #stories"
    if os.path.exists(desc_path):
        with open(desc_path) as f:
            desc = f.read().strip()

    return stories, tags, desc, stories_path

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

def pick_gameplay():
    if not os.path.isdir(GAMEPLAY_FOLDER):
        return None
    vids = [f for f in os.listdir(GAMEPLAY_FOLDER) if f.endswith('.mp4')]
    if not vids:
        return None
    return os.path.join(GAMEPLAY_FOLDER, random.choice(vids))

async def generate_tts(text, out_path):
    try:
        communicate = edge_tts.Communicate(text[:2500], "en-US-JennyNeural")
        await communicate.save(out_path)
        return os.path.exists(out_path) and os.path.getsize(out_path) > 1000
    except:
        return False

def create_video(story, idx):
    tts_path = os.path.join(TTS_DIR, f"wdog_{idx}.mp3")
    text = story['text'].replace('\n', ' ').strip()
    log(f"  TTS for: {story['title'][:50]}...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ok = loop.run_until_complete(generate_tts(text, tts_path))
    loop.close()
    if not ok:
        raise Exception("TTS generation failed")

    gp = pick_gameplay()
    if not gp:
        raise Exception("No gameplay video found")

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
    sp.run(cmd, check=True, capture_output=True, timeout=180)
    if os.path.getsize(out_path) < 50000:
        raise Exception("Output video too small")
    return out_path

def upload_video(ch, video_path, title, tags, desc):
    creds = get_creds(ch)
    yt = build('youtube', 'v3', credentials=creds)
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
    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True, chunksize=1024*1024)
    resp = yt.videos().insert(part='snippet,status', body=body, media_body=media).execute()
    return resp['id']

# ─── state management ───────────────────────────────
def load_state():
    return load_json(LOG_FILE, {})

def save_state(state):
    save_json(LOG_FILE, state)

def get_unposted_story(stories, posted_titles):
    available = [s for s in stories if s['title'] not in posted_titles]
    if not available:
        return None
    return random.choice(available)

# ─── main loop ──────────────────────────────────────
def process_channel(ch):
    state = load_state()
    ch_state = state.setdefault(ch, {"posted": [], "last_post_date": None})
    stories, tags, desc, _ = load_channel_files(ch)
    if not stories:
        log(f"{ch}: No stories file")
        return False

    story = get_unposted_story(stories, ch_state["posted"])
    if not story:
        log(f"{ch}: All stories posted. Reset needed.")
        return False

    log(f"{ch}: Posting '{story['title'][:60]}'")
    video_path = create_video(story, hash(story['title']) % 1000)
    vid_id = upload_video(ch, video_path, story['title'], tags, desc)
    log(f"{ch}: ✅ https://www.youtube.com/watch?v={vid_id}")

    ch_state["posted"].append(story['title'])
    ch_state["last_post_date"] = datetime.now().strftime("%Y-%m-%d")
    save_state(state)
    return True

def run_loop():
    while True:
        state = load_state()
        for ch in CHANNELS:
            ch_state = state.get(ch, {})
            last = ch_state.get("last_post_date")
            today = datetime.now().strftime("%Y-%m-%d")
            if last == today:
                continue  # already posted today

            log(f"Processing {ch}...")
            success = False
            for attempt in range(5):
                try:
                    success = process_channel(ch)
                except Exception as e:
                    log(f"{ch}: attempt {attempt+1} failed ({str(e)[:80]})")
                    time.sleep(30)
                    continue
                if success:
                    break
            if not success:
                log(f"{ch}: ❌ Could not post after retries. Will try later.")

        # Wait 30 minutes before next check
        log("Sleeping 30 minutes...")
        time.sleep(1800)

if __name__ == "__main__":
    log("🐕 Watchdog started. Posting one video per channel per day, retrying on failure.")
    run_loop()
