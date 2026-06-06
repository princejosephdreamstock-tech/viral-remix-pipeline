#!/usr/bin/env python3
"""
Daily Post - Posts ONE video per channel per day + auto backup to Drive.
Usage: python daily_post.py [main|channel_2|all]
"""

import os, json, sys, subprocess
from datetime import datetime

DL_BASE = os.path.expanduser("~/storage/downloads/gameplay_machine")
BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")

CHANNELS = {
    "main": {
        "name": "Iam Jay",
        "folder": os.path.join(DL_BASE, "channel_main", "gameplay"),
        "posted_log": os.path.join(BASE_DIR, "posted_main.json")
    },
    "channel_2": {
        "name": "Channel 2",
        "folder": os.path.join(DL_BASE, "channel_2", "gameplay"),
        "posted_log": os.path.join(BASE_DIR, "channels", "channel_2", "posted_videos.json")
    }
}

def load_posted(log_path):
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            return json.load(f)
    return []

def save_posted(log_path, posted_list):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(posted_list, f, indent=2)

def get_available_videos(folder, posted):
    if not os.path.exists(folder):
        return []
    all_vids = sorted([f for f in os.listdir(folder) if f.endswith('.mp4')])
    return [v for v in all_vids if v not in posted]

def daily_post(channel_key=None):
    print(f"\n{'='*50}")
    print(f"  DAILY POST - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    
    if channel_key and channel_key != "all":
        channels_to_run = {channel_key: CHANNELS[channel_key]}
    else:
        channels_to_run = CHANNELS
    
    any_posted = False
    
    for key, ch in channels_to_run.items():
        print(f"\n  📺 {ch['name']}")
        
        posted = load_posted(ch["posted_log"])
        available = get_available_videos(ch["folder"], posted)
        
        print(f"     Already posted: {len(posted)}")
        print(f"     Available: {len(available)}")
        
        if not available:
            print(f"     ❌ No new videos to post")
            continue
        
        next_video = available[0]
        print(f"     ▶️  Posting: {next_video[:50]}...")
        
        posted.append(next_video)
        save_posted(ch["posted_log"], posted)
        print(f"     ✅ Posted and logged")
        
        # Upload to YouTube
        script = os.path.join(BASE_DIR, "upload_channel.py")
        subprocess.run(["python", script, key], capture_output=True, text=True)
        print(f"     ✅ Upload scheduled")
        
        any_posted = True
    
    # Auto backup to Drive if anything was posted
    if any_posted:
        print(f"\n  ☁️  Running Drive backup...")
        backup_script = os.path.join(BASE_DIR, "backup_to_drive.py")
        subprocess.run(["python", backup_script], capture_output=True, text=True)
    
    print(f"\n{'='*50}")
    print(f"  Done. Next post: tomorrow")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python daily_post.py [main|channel_2|all]")
        sys.exit(1)
    daily_post(sys.argv[1])
