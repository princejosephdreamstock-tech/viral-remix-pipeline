#!/usr/bin/env python3
"""Usage: python status.py - Shows complete machine status at a glance"""
import pickle, os, json
from datetime import datetime
from googleapiclient.discovery import build

BASE = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads/gameplay_machine")

CHANNELS = {
    "main": {
        "token": os.path.join(BASE, "youtube_token.pickle"),
        "processed": os.path.join(BASE, "processed_videos.json"),
        "videos": os.path.join(DL_BASE, "channel_main", "gameplay"),
        "name": "Iam Jay"
    },
    "channel_2": {
        "token": os.path.join(BASE, "channels", "channel_2", "token.pickle"),
        "processed": os.path.join(BASE, "channels", "channel_2", "processed_videos.json"),
        "videos": os.path.join(DL_BASE, "channel_2", "gameplay"),
        "name": "Channel 2"
    }
}

def get_scheduled_videos(youtube):
    """Fetch all private/scheduled videos from YouTube."""
    try:
        req = youtube.search().list(
            part="snippet",
            forMine=True,
            maxResults=50,
            type="video",
            order="date"
        )
        res = req.execute()
        scheduled = []
        for item in res.get("items", []):
            vid = youtube.videos().list(
                part="status,snippet",
                id=item["id"]["videoId"]
            ).execute()
            if vid["items"]:
                status = vid["items"][0]["status"]
                if status["privacyStatus"] == "private" and "publishAt" in status:
                    scheduled.append({
                        "title": vid["items"][0]["snippet"]["title"],
                        "publish_at": status["publishAt"]
                    })
        return scheduled
    except Exception as e:
        return f"ERROR: {e}"

def check_channel(ch_key, ch_cfg):
    """Check one channel's full status."""
    print(f"\n{'='*55}")
    print(f"  {ch_cfg['name']} ({ch_key})")
    print(f"{'='*55}")
    
    yt = None
    
    # 1. Token status
    if os.path.exists(ch_cfg["token"]):
        try:
            with open(ch_cfg["token"], 'rb') as f:
                creds = pickle.load(f)
            if creds.valid:
                print("  Token:       VALID")
            elif creds.expired and creds.refresh_token:
                print("  Token:       EXPIRED (auto-refresh possible)")
            else:
                print("  Token:       EXPIRED (re-auth required)")
            
            yt = build('youtube', 'v3', credentials=creds)
            cinfo = yt.channels().list(part='snippet,statistics', mine=True).execute()
            item = cinfo['items'][0]
            print(f"  Channel:     {item['snippet']['title']}")
            print(f"  Subscribers: {item['statistics'].get('subscriberCount', 'hidden')}")
            print(f"  Total views: {item['statistics'].get('viewCount', '0')}")
            print(f"  Videos:      {item['statistics'].get('videoCount', '0')}")
            
            # Scheduled videos
            scheduled = get_scheduled_videos(yt)
            if isinstance(scheduled, list):
                print(f"  Scheduled:   {len(scheduled)} videos queued")
                if scheduled:
                    pub_times = [s["publish_at"] for s in scheduled if "publish_at" in s]
                    if pub_times:
                        next_pub = min(pub_times)
                        dt = datetime.fromisoformat(next_pub.replace("Z", "+00:00"))
                        print(f"  Next publish: {dt.strftime('%Y-%m-%d %H:%M UTC')}")
                        print(f"  Coverage:     {len(scheduled)} days of content")
            else:
                print(f"  Scheduled:   {scheduled}")
        except Exception as e:
            print(f"  Token:       ERROR - {str(e)[:80]}")
    else:
        print("  Token:       MISSING")
    
    # 2. Video inventory
    if os.path.exists(ch_cfg["videos"]):
        all_vids = [f for f in os.listdir(ch_cfg["videos"]) if f.endswith('.mp4')]
        processed = json.load(open(ch_cfg["processed"])) if os.path.exists(ch_cfg["processed"]) else []
        unprocessed = [v for v in all_vids if v not in processed]
        
        print(f"  Video folder: .../gameplay_machine/{'channel_main' if ch_key == 'main' else ch_key}/gameplay")
        print(f"  Total .mp4:   {len(all_vids)}")
        print(f"  Processed:    {len(processed)}")
        print(f"  Unprocessed:  {len(unprocessed)}")
        
        if not all_vids:
            print("  WARNING:      No videos in folder!")
        elif not unprocessed:
            print("  WARNING:      All videos processed. Add new footage.")
    else:
        print(f"  Video folder: MISSING")
        print(f"  Fix: mkdir -p {ch_cfg['videos']}")
    
    # 3. Processed log
    if os.path.exists(ch_cfg["processed"]):
        processed = json.load(open(ch_cfg["processed"]))
        print(f"  Processed log: {len(processed)} total entries")

# ==================== MAIN ====================
print("\n" + "="*55)
print("  GAMEPLAY MACHINE STATUS")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
print("="*55)

for key, cfg in CHANNELS.items():
    check_channel(key, cfg)

print(f"\n{'='*55}")
print("  SUMMARY")
print(f"{'='*55}")

# Count unprocessed
total_unprocessed = 0
for key, cfg in CHANNELS.items():
    if os.path.exists(cfg["videos"]):
        all_v = [f for f in os.listdir(cfg["videos"]) if f.endswith('.mp4')]
        processed = json.load(open(cfg["processed"])) if os.path.exists(cfg["processed"]) else []
        total_unprocessed += len([v for v in all_v if v not in processed])

active_tokens = sum(1 for k,c in CHANNELS.items() if os.path.exists(c["token"]))
print(f"  Channels with tokens: {active_tokens}/2")
print(f"  Unprocessed videos:   {total_unprocessed}")
print(f"  Status:               {'READY' if total_unprocessed > 0 else 'NEEDS FOOTAGE'}")

if total_unprocessed == 0:
    print(f"\n  ACTION: Add .mp4 files to:")
    print(f"    ~/storage/downloads/gameplay_machine/channel_main/gameplay/")
    print(f"    ~/storage/downloads/gameplay_machine/channel_2/gameplay/")
else:
    print(f"\n  ACTION: python upload_channel.py main")
    print(f"          python upload_channel.py channel_2")

print("="*55)
