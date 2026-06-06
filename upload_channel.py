#!/usr/bin/env python3
"""Universal Channel Upload Script - Usage: python upload_channel.py <channel>"""

import pickle, os, random, json, sys, hashlib, time
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

KEYWORDS = {
    "main": [
        "roblox", "vr roblox", "roblox vr", "roblox gay", "vin roblox", "roblox vin",
        "roblox voz", "robloxvr", "free korblox roblox", "roblox rant", "film roblox",
        "roblox story", "roblox edits", "roblox rants", "drama roblox", "roblox erwin",
        "erwin roblox", "funny roblox", "scary roblox", "roblox short", "roblox trend",
        "roblox movie", "roblox baddie", "caylus roblox", "roblox shorts", "calaca roblox",
        "roblox tiktok", "tiktok roblox", "roblox avatar", "avatar roblox", "roblox cringe",
        "foltyn roblox", "roblox foltyn", "roblox gaming", "roblox stories", "roblox tiktoks",
        "roblox tik toks", "roblox espanol"
    ],
    "channel_2": [
        "ai tools for marketing", "best ai tools for marketing",
        "ai tools for marketing 2025", "ai tools for marketing 2026",
        "ai tools for smma", "ai tools for visual marketing",
        "ai tools for digital marketing", "ai tools for social media marketing",
        "best ai tools for sales and marketing", "best ai tools for digital marketing",
        "best ai tools for social media marketing", "ai tools for research",
        "best ai tools for sales", "best free ai tools for social media marketing",
        "ai tools for content creators", "ai tools for business"
    ],
    "channel_3": [
        "minecraft", "minecraft shorts", "minecraft funny moments",
        "minecraft build hacks", "minecraft survival", "minecraft mods",
        "minecraft challenge", "minecraft speedrun", "minecraft viral",
        "minecraft tiktok", "minecraft gameplay", "minecraft bedrock",
        "minecraft java", "minecraft creative", "minecraft redstone",
        "minecraft house build", "minecraft memes", "minecraft pvp"
    ],
    "channel_3": [
        "{} INSANE MINECRAFT {} #shorts",
        "BEST {} MOMENTS EVER #minecraft #shorts",
        "{} BUILD HACKS {} #minecraft",
        "FUNNY MINECRAFT {} FAILS #{}",
        "I CANT BELIEVE THIS {} #shorts",
        "MINECRAFT {} SPEEDRUN {} #shorts",
        "{} SURVIVAL TIPS {} #minecraft",
        "FREE {} MINECRAFT {} #shorts"
    ]
}

TITLE_TEMPLATES = {
    "main": [
        "{} INSANE {} MOMENTS #shorts",
        "BEST {} CLIPS EVER #{} #shorts",
        "{} SCARY {} COMPILATION",
        "FUNNY {} FAILS #{} #roblox",
        "I CANT BELIEVE THIS {} #shorts",
        "{} DRAMA EXPOSED #roblox",
        "{} VR IS CRAZY #vr #shorts",
        "FREE {} #roblox #shorts"
    ],
    "channel_2": [
        "TOP 5 {} FOR 2026 #shorts",
        "BEST {} IN 2026 #aitools #shorts",
        "{} YOU NEED TO KNOW #shorts",
        "HOW TO USE {} FOR BUSINESS #shorts",
        "{} TUTORIAL 2026 #shorts",
        "{} VS TRADITIONAL MARKETING #shorts",
        "SAVE TIME WITH {} #shorts",
        "FREE {} FOR CONTENT CREATORS #shorts"
    ],
    "channel_3": [
        "minecraft", "minecraft shorts", "minecraft funny moments",
        "minecraft build hacks", "minecraft survival", "minecraft mods",
        "minecraft challenge", "minecraft speedrun", "minecraft viral",
        "minecraft tiktok", "minecraft gameplay", "minecraft bedrock",
        "minecraft java", "minecraft creative", "minecraft redstone",
        "minecraft house build", "minecraft memes", "minecraft pvp"
    ],
    "channel_3": [
        "{} INSANE MINECRAFT {} #shorts",
        "BEST {} MOMENTS EVER #minecraft #shorts",
        "{} BUILD HACKS {} #minecraft",
        "FUNNY MINECRAFT {} FAILS #{}",
        "I CANT BELIEVE THIS {} #shorts",
        "MINECRAFT {} SPEEDRUN {} #shorts",
        "{} SURVIVAL TIPS {} #minecraft",
        "FREE {} MINECRAFT {} #shorts"
    ]
}

DESCRIPTIONS = {"main": "Roblox Shorts", "channel_2": "Best AI tools for marketing and business growth"}

UPLOAD_HOUR, UPLOAD_MINUTE, MAX_RUN = 14, 0, 10
MAX_RETRIES, RETRY_DELAY = 3, 5

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads/gameplay_machine")

CHANNELS = {
    "main": {"token": os.path.join(BASE_DIR, "youtube_token.pickle"), "processed": os.path.join(BASE_DIR, "processed_videos.json"), "videos": os.path.join(DL_BASE, "channel_main", "gameplay"), "name": "Iam Jay"},
    "channel_2": {"token": os.path.join(BASE_DIR, "channels", "channel_2", "token.pickle"), "processed": os.path.join(BASE_DIR, "channels", "channel_2", "processed_videos.json"), "videos": os.path.join(DL_BASE, "channel_2", "gameplay"), "name": "Channel 2"}
}

GLOBAL_PROCESSED_FILE = os.path.join(BASE_DIR, "global_processed.json")
FAILED_LOG = os.path.join(BASE_DIR, "failed_uploads.json")

def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f)

def load_token(token_path):
    """Load token - handles both dict and Credentials object formats."""
    with open(token_path, 'rb') as f:
        data = pickle.load(f)
    
    if isinstance(data, dict):
        creds = Credentials(
            token=data['access_token'],
            refresh_token=data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id='YOUR_CLIENT_ID',
            client_secret='YOUR_CLIENT_SECRET',
            scopes=['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly']
        )
        return creds
    return data

def load_global_processed():
    return set(load_json(GLOBAL_PROCESSED_FILE, []))

def save_global_processed(ps):
    save_json(GLOBAL_PROCESSED_FILE, list(ps))

def load_failed():
    return load_json(FAILED_LOG, {})

def save_failed(fd):
    save_json(FAILED_LOG, fd)

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_scheduled_times(youtube):
    try:
        req = youtube.videos().list(part="status", mine=True, maxResults=50, order="date")
        res = req.execute()
        return [item["status"]["publishAt"] for item in res.get("items", []) if item["status"]["privacyStatus"] == "private" and "publishAt" in item["status"]]
    except:
        return []

def find_next_available_slot(scheduled_times):
    day_offset = 1
    while day_offset <= 365:
        candidate = datetime.utcnow() + timedelta(days=day_offset)
        candidate = candidate.replace(hour=UPLOAD_HOUR, minute=UPLOAD_MINUTE, second=0, microsecond=0)
        if candidate.isoformat() + 'Z' not in scheduled_times:
            return candidate
        day_offset += 1
    return None

def gen_title(ch):
    kw = KEYWORDS[ch]
    t = random.choice(TITLE_TEMPLATES[ch])
    return t.format(random.choice(kw).upper(), random.choice(kw).upper())[:100]

def gen_tags(ch):
    return random.sample(KEYWORDS[ch], min(10, len(KEYWORDS[ch])))

def gen_description(ch):
    kw = KEYWORDS[ch]
    base = DESCRIPTIONS.get(ch, "Gaming Shorts")
    hashtags = ' '.join(['#' + k.replace(' ', '') for k in random.sample(kw, min(5, len(kw)))])
    return f"{base}\n\n{hashtags} #shorts"

def upload_single_video(yt, video_path, vf, ch, scheduled_times):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            sd = find_next_available_slot(scheduled_times)
            if sd is None:
                return False, "no_slots"
            
            body = {
                'snippet': {'title': gen_title(ch), 'description': gen_description(ch), 'tags': gen_tags(ch), 'categoryId': '20'},
                'status': {'privacyStatus': 'private', 'publishAt': sd.isoformat() + 'Z'}
            }
            
            media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
            yt.videos().insert(part='snippet,status', body=body, media_body=media).execute()
            scheduled_times.append(sd.isoformat() + 'Z')
            return True, None
            
        except HttpError as e:
            error_reason = str(e)
            if "uploadLimitExceeded" in error_reason or "quota" in error_reason.lower():
                return False, "quota"
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return False, "error"
        except Exception as e:
            if "Connection" in str(e) or "Timeout" in str(e):
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    return False, "connection"
            return False, "error"
    return False, "max_retries"

def upload_videos(ch):
    cfg = CHANNELS[ch]
    
    if not os.path.exists(cfg["token"]):
        print(f"No token for {cfg['name']}. Run: python auth_channel.py {ch}")
        return
    
    creds = load_token(cfg["token"])
    yt = build('youtube', 'v3', credentials=creds)
    cinfo = yt.channels().list(part='snippet', mine=True).execute()
    cname = cinfo['items'][0]['snippet']['title']
    
    print(f"\n{'='*50}")
    print(f"Channel: {cname} ({cfg['name']})")
    print(f"{'='*50}")
    
    global_processed = load_global_processed()
    os.makedirs(cfg["videos"], exist_ok=True)
    
    all_vids = sorted([f for f in os.listdir(cfg["videos"]) if f.endswith('.mp4')])
    processed = load_json(cfg["processed"], [])
    
    queue = []
    skipped = []
    for v in all_vids:
        if v in processed:
            continue
        vpath = os.path.join(cfg["videos"], v)
        if get_file_hash(vpath) in global_processed:
            skipped.append(v)
            continue
        queue.append(v)
    
    if skipped:
        print(f"Skipped {len(skipped)} duplicates")
    
    if not queue:
        print("No new videos to upload.")
        return
    
    print(f"Queue: {len(queue)} videos")
    scheduled_times = get_scheduled_times(yt)
    print(f"Already scheduled: {len(scheduled_times)}")
    
    success = 0
    for i, vf in enumerate(queue[:MAX_RUN]):
        vpath = os.path.join(cfg["videos"], vf)
        sd = find_next_available_slot(scheduled_times)
        print(f"[{i+1}/{min(len(queue), MAX_RUN)}] {vf[:45]}... -> {sd.strftime('%Y-%m-%d %H:%M UTC') if sd else 'NO SLOT'}")
        
        ok, reason = upload_single_video(yt, vpath, vf, ch, scheduled_times)
        if ok:
            processed.append(vf)
            global_processed.add(get_file_hash(vpath))
            success += 1
        elif reason == "quota":
            print("  Quota reached. Stopping.")
            break
        else:
            print(f"  Failed: {reason}")
    
    save_json(cfg["processed"], processed)
    save_global_processed(global_processed)
    print(f"\nDone: {success} scheduled to {cname}")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CHANNELS:
        print("Usage: python upload_channel.py [main|channel_2|channel_3]")
        sys.exit(1)
    upload_videos(sys.argv[1])
