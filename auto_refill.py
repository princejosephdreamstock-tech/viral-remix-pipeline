#!/usr/bin/env python3
"""
Auto-Refill Monitor - Watches folders and alerts when empty
Usage: python auto_refill.py [--daemon]
"""

import os, json, time, sys
from datetime import datetime

DL_BASE = os.path.expanduser("~/storage/downloads/gameplay_machine")
LOG_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/refill_alerts.log")

CHANNELS = {
    "main": {
        "folder": os.path.join(DL_BASE, "channel_main", "gameplay"),
        "name": "Iam Jay"
    },
    "channel_2": {
        "folder": os.path.join(DL_BASE, "channel_2", "gameplay"),
        "name": "Channel 2"
    }
}

LOW_THRESHOLD = 3       # Alert when unprocessed videos drop below this
EMPTY_THRESHOLD = 0     # Critical alert when completely empty
CHECK_INTERVAL = 3600   # Check every 1 hour (in daemon mode)

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")

def check_channels():
    """Check all channels and return alerts."""
    alerts = []
    
    for key, ch in CHANNELS.items():
        folder = ch["folder"]
        
        if not os.path.exists(folder):
            alerts.append({
                "channel": key,
                "name": ch["name"],
                "level": "MISSING",
                "msg": f"Folder missing: {folder}"
            })
            continue
        
        # Count videos
        all_vids = [f for f in os.listdir(folder) if f.endswith('.mp4')]
        total = len(all_vids)
        
        # Check processed
        processed_file = os.path.expanduser(
            f"~/intent-radar/content/gameplay_machine/{'processed_videos.json' if key == 'main' else 'channels/' + key + '/processed_videos.json'}"
        )
        processed = json.load(open(processed_file)) if os.path.exists(processed_file) else []
        unprocessed = len([v for v in all_vids if v not in processed])
        
        if total == 0:
            alerts.append({
                "channel": key,
                "name": ch["name"],
                "level": "EMPTY",
                "msg": f"COMPLETELY EMPTY - No .mp4 files at all"
            })
        elif unprocessed == 0:
            alerts.append({
                "channel": key,
                "name": ch["name"],
                "level": "DRAINED",
                "msg": f"All {total} videos already processed. Add new footage."
            })
        elif unprocessed <= LOW_THRESHOLD:
            alerts.append({
                "channel": key,
                "name": ch["name"],
                "level": "LOW",
                "msg": f"Only {unprocessed} unprocessed videos left (out of {total} total)"
            })
        else:
            alerts.append({
                "channel": key,
                "name": ch["name"],
                "level": "OK",
                "msg": f"Healthy: {unprocessed} unprocessed, {total} total"
            })
    
    return alerts

def print_banner():
    print("\n" + "="*55)
    print("  GAMEPLAY MACHINE - AUTO REFILL MONITOR")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*55)

def print_alerts(alerts):
    empty_count = 0
    low_count = 0
    
    for a in alerts:
        icon = {"OK": "✅", "LOW": "⚠️", "DRAINED": "🔴", "EMPTY": "🚨", "MISSING": "❌"}.get(a["level"], "❓")
        print(f"  {icon} {a['name']}: {a['msg']}")
        
        if a["level"] in ("EMPTY", "DRAINED"):
            empty_count += 1
        elif a["level"] == "LOW":
            low_count += 1
    
    print("-"*55)
    
    if empty_count > 0:
        print(f"  🚨 {empty_count} channel(s) EMPTY - UPLOADS STOPPED")
        print(f"  Add .mp4 files to:")
        for a in alerts:
            if a["level"] in ("EMPTY", "DRAINED"):
                folder = CHANNELS[a["channel"]]["folder"]
                print(f"    {folder}")
    elif low_count > 0:
        print(f"  ⚠️ {low_count} channel(s) running low")
    else:
        print(f"  ✅ All channels healthy")
    
    print("="*55 + "\n")

def run_once():
    """Single check."""
    print_banner()
    alerts = check_channels()
    print_alerts(alerts)
    return alerts

def run_daemon():
    """Run continuously, checking every hour."""
    print("\n  Auto-refill monitor starting (checks every hour)")
    print("  Press Ctrl+C to stop\n")
    
    while True:
        alerts = check_channels()
        
        # Only log if there's an issue or it's the first check of the day
        has_issue = any(a["level"] in ("EMPTY", "DRAINED", "LOW", "MISSING") for a in alerts)
        
        if has_issue:
            print_banner()
            print_alerts(alerts)
            for a in alerts:
                if a["level"] != "OK":
                    log(f"{a['level']}: {a['name']} - {a['msg']}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    if "--daemon" in sys.argv or "-d" in sys.argv:
        run_daemon()
    else:
        run_once()
