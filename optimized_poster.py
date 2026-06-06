#!/usr/bin/env python3
"""
A/B Testing Poster – learns the best hook/outro/title for each channel.
Usage: python optimized_poster.py <channel> [count]
"""

import os, sys, subprocess, json, pickle, random, asyncio, time
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads")
GAMEPLAY_FOLDER = os.path.join(DL_BASE, "gameplay_machine", "long_gameplay")
TTS_DIR = os.path.join(DL_BASE, "remix_machine", "tts")
OUT_DIR = os.path.join(DL_BASE, "remix_machine", "output")
AB_STATE_FILE = os.path.join(BASE_DIR, "ab_test_state.json")

CHANNELS = {
    "joy_1": "Gaming Nightmares",
    "joy_2": "Reddit Talezz",
    "joy_3": "Business Confessions",
    "joy_4": "Love & Lies",
    "joy_5": "Petty Revenge Daily",
    "joy_6": "Creepy Encounters",
}

# ─── A/B Test Variants ────────────────────────────
HOOK_VARIANTS = [
    "STORY TIME",
    "WAIT FOR IT...",
    "YOU WON'T BELIEVE THIS",
    "THIS ACTUALLY HAPPENED",
    "TRUE STORY",
    "UNBELIEVABLE STORY",
]

OUTRO_VARIANTS = [
    "LIKE AND SUBSCRIBE",
    "SUBSCRIBE FOR MORE",
    "LIKE FOR MORE STORIES",
    "FOLLOW FOR DAILY STORIES",
    "SUBSCRIBE IF YOU DARE",
    "MORE STORIES ON THIS CHANNEL",
]

TITLE_SUFFIXES = [
    " #Shorts",
    " #Reddit #Shorts",
    " #StoryTime #Shorts",
    " #ViralStory #Shorts",
    " #TrueStory #Shorts",
    " #MustWatch #Shorts",
]

# ─── helpers ──────────────────────────────────────
def load_json(path, default):
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return json.load(open(path))
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

def create_video(story, hook, outro):
    idx = random.randint(0, 99999)
    tts_path = os.path.join(TTS_DIR, f"ab_{idx}.mp3")
    text = story['text'].replace('\n', ' ').strip()
    log(f"  Voice: {story['title'][:50]}...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ok = loop.run_until_complete(generate_tts(text, tts_path))
    loop.close()
    if not ok:
        raise Exception("TTS failed")
    gp = pick_gameplay()
    if not gp:
        raise Exception("No gameplay")
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
    out_file = f"ab_{safe_title}_{datetime.now().strftime('%H%M%S')}.mp4"
    out_path = os.path.join(OUT_DIR, out_file)

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", gp,
        "-i", tts_path,
        "-t", str(clip_dur),
        "-filter_complex",
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"drawtext=text='{hook}':fontsize=48:fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=8:x=(w-text_w)/2:y=(h-text_h)/3:enable='between(t,0,2)',"
        f"drawtext=text='{outro}':fontsize=42:fontcolor=white:box=1:boxcolor=red@0.8:boxborderw=8:x=(w-text_w)/2:y=h-text_h-60:enable='between(t,{clip_dur-5},{clip_dur})'[v];"
        f"[0:a]volume=0.3[a1];[1:a]volume=1.5[a2];[a1][a2]amix=inputs=2:duration=first[aout]",
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "128k", "-threads", "4",
        out_path
    ]
    sp.run(cmd, check=True, capture_output=True, timeout=180)
    if os.path.getsize(out_path) < 50000:
        raise Exception("Output too small")
    return out_path

def upload_video(ch, video_path, title, tags, desc, suffix):
    creds = get_creds(ch)
    yt = build('youtube', 'v3', credentials=creds)
    full_title = title[:80] + suffix
    body = {
        'snippet': {
            'title': full_title,
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

def fetch_video_stats(ch, video_ids):
    """Get view counts for specific video IDs."""
    if not video_ids:
        return {}
    creds = get_creds(ch)
    yt = build('youtube', 'v3', credentials=creds)
    stats = {}
    try:
        req = yt.videos().list(part='statistics', id=','.join(video_ids)).execute()
        for item in req.get('items', []):
            stats[item['id']] = int(item['statistics'].get('viewCount', 0))
    except:
        pass
    return stats

def update_ab_state(ch, hook, outro, suffix, video_id):
    """Record an A/B test trial."""
    state = load_json(AB_STATE_FILE, {})
    if ch not in state:
        state[ch] = {"trials": [], "best_hook": None, "best_outro": None, "best_suffix": None}
    state[ch]["trials"].append({
        "video_id": video_id,
        "hook": hook,
        "outro": outro,
        "title_suffix": suffix,
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    save_json(AB_STATE_FILE, state)

def choose_variants(ch):
    """Pick hook/outro/suffix using past performance if available."""
    state = load_json(AB_STATE_FILE, {})
    ch_state = state.get(ch, {})
    # Default random
    hook = random.choice(HOOK_VARIANTS)
    outro = random.choice(OUTRO_VARIANTS)
    suffix = random.choice(TITLE_SUFFIXES)

    # If we have >10 trials, analyze and use best
    trials = ch_state.get("trials", [])
    if len(trials) >= 10:
        # For simplicity, pick the most recently best performing hook
        # In a real system we'd analyze view data.
        # Here we'll just return the stored best if exists.
        if ch_state.get("best_hook"):
            hook = ch_state["best_hook"]
        if ch_state.get("best_outro"):
            outro = ch_state["best_outro"]
        if ch_state.get("best_suffix"):
            suffix = ch_state["best_suffix"]

    return hook, outro, suffix

def evaluate_and_set_best(ch):
    """Analyze recent trials and set best variants based on views."""
    state = load_json(AB_STATE_FILE, {})
    ch_state = state.get(ch, {})
    trials = ch_state.get("trials", [])
    if len(trials) < 10:
        return

    # Get view counts for all trial videos
    video_ids = [t["video_id"] for t in trials]
    stats = fetch_video_stats(ch, video_ids)

    # Aggregate views by hook, outro, suffix
    hook_views = {}
    outro_views = {}
    suffix_views = {}
    for t in trials:
        vid = t["video_id"]
        views = stats.get(vid, 0)
        hook_views[t["hook"]] = hook_views.get(t["hook"], 0) + views
        outro_views[t["outro"]] = outro_views.get(t["outro"], 0) + views
        suffix_views[t["title_suffix"]] = suffix_views.get(t["title_suffix"], 0) + views

    if hook_views:
        best_hook = max(hook_views, key=hook_views.get)
        ch_state["best_hook"] = best_hook
    if outro_views:
        best_outro = max(outro_views, key=outro_views.get)
        ch_state["best_outro"] = best_outro
    if suffix_views:
        best_suffix = max(suffix_views, key=suffix_views.get)
        ch_state["best_suffix"] = best_suffix

    save_json(AB_STATE_FILE, state)
    log(f"{ch}: Best hook='{best_hook}', outro='{best_outro}', suffix='{best_suffix}'")

def process_channel(ch, count):
    stories, tags, desc, _ = load_channel_files(ch)
    if not stories:
        log(f"{ch}: No stories")
        return

    for i in range(count):
        story = random.choice(stories)
        hook, outro, suffix = choose_variants(ch)
        log(f"{ch}: Posting with hook='{hook}', outro='{outro}', suffix='{suffix}'")
        try:
            video_path = create_video(story, hook, outro)
            vid_id = upload_video(ch, video_path, story['title'], tags, desc, suffix)
            update_ab_state(ch, hook, outro, suffix, vid_id)
            log(f"{ch}: ✅ https://www.youtube.com/watch?v={vid_id}")
        except Exception as e:
            log(f"{ch}: ❌ {str(e)[:80]}")

    # After posting, evaluate performance if enough data
    evaluate_and_set_best(ch)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CHANNELS:
        print("Usage: python optimized_poster.py [channel] [count]")
        sys.exit(1)
    ch = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    process_channel(ch, count)
