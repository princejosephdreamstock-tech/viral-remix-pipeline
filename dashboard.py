#!/usr/bin/env python3
"""
Analytics Dashboard – one-screen overview of all channels.
Usage: python dashboard.py
"""

import os, json, pickle, sys
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")

# All channels – add new ones here
ALL_CHANNELS = {
    "joy_20": {"name": "The Dark Corner", "token": "channels/joy_20/token.pickle", "secret": "channels/joy_20/client_secret.json"},
    "joy_19": {"name": "Malicious Compliance", "token": "channels/joy_19/token.pickle", "secret": "channels/joy_19/client_secret.json"},
    "joy_18": {"name": "Cheaters Exposed", "token": "channels/joy_18/token.pickle", "secret": "channels/joy_18/client_secret.json"},
    "joy_17": {"name": "Startup Horror Stories", "token": "channels/joy_17/token.pickle", "secret": "channels/joy_17/client_secret.json"},
    "joy_16": {"name": "Paranormal Files", "token": "channels/joy_16/token.pickle", "secret": "channels/joy_16/client_secret.json"},
    "joy_15": {"name": "Justice Served Daily", "token": "channels/joy_15/token.pickle", "secret": "channels/joy_15/client_secret.json"},
    "joy_14": {"name": "Instant Karma Stories", "token": "channels/joy_14/token.pickle", "secret": "channels/joy_14/client_secret.json"},
    "joy_13": {"name": "Marriage Drama Daily", "token": "channels/joy_13/token.pickle", "secret": "channels/joy_13/client_secret.json"},
    "joy_12": {"name": "Dating Disaster Stories", "token": "channels/joy_12/token.pickle", "secret": "channels/joy_12/client_secret.json"},
    "joy_11": {"name": "Boss Level Stories", "token": "channels/joy_11/token.pickle", "secret": "channels/joy_11/client_secret.json"},
    "joy_10": {"name": "Career Revenge Daily", "token": "channels/joy_10/token.pickle", "secret": "channels/joy_10/client_secret.json"},
    "joy_9": {"name": "Midnight Horror Tales", "token": "channels/joy_9/token.pickle", "secret": "channels/joy_9/client_secret.json"},
    "joy_8": {"name": "Scary Story Hour", "token": "channels/joy_8/token.pickle", "secret": "channels/joy_8/client_secret.json"},
    "joy_7": {"name": "Horror Stories Daily", "token": "channels/joy_7/token.pickle", "secret": "channels/joy_7/client_secret.json"},
    "main":   {"name": "Iam Jay",            "token": "youtube_token.pickle",                         "secret": "client_secret.json"},
    "channel_2": {"name": "AI Tools",        "token": "channels/channel_2/token.pickle",              "secret": "channels/channel_2/client_secret.json"},
    "channel_3": {"name": "Minecraft Jay",   "token": "channels/channel_3/token.pickle",              "secret": "channels/channel_3/client_secret.json"},
    "joy_1":   {"name": "Gaming Nightmares", "token": "channels/joy_1/token.pickle",                 "secret": "channels/joy_1/client_secret.json"},
    "joy_2":   {"name": "Reddit Talezz",     "token": "channels/joy_2/token.pickle",                 "secret": "channels/joy_2/client_secret.json"},
    "joy_3":   {"name": "Business Confessions","token": "channels/joy_3/token.pickle",               "secret": "channels/joy_3/client_secret.json"},
    "joy_4":   {"name": "Love & Lies",       "token": "channels/joy_4/token.pickle",                 "secret": "channels/joy_4/client_secret.json"},
    "joy_5":   {"name": "Petty Revenge Daily","token": "channels/joy_5/token.pickle",                "secret": "channels/joy_5/client_secret.json"},
    "joy_6":   {"name": "Creepy Encounters", "token": "channels/joy_6/token.pickle",                 "secret": "channels/joy_6/client_secret.json"},
}

def get_creds(ch_key):
    cfg = ALL_CHANNELS[ch_key]
    token_path = os.path.join(BASE_DIR, cfg["token"])
    secret_path = os.path.join(BASE_DIR, cfg["secret"])
    if not os.path.exists(token_path):
        return None
    with open(token_path, 'rb') as f:
        data = pickle.load(f)
    with open(secret_path) as f:
        s = json.load(f)
    inst = s.get("installed", s)
    if isinstance(data, dict):
        return Credentials(
            token=data['access_token'], refresh_token=data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=inst['client_id'], client_secret=inst['client_secret'],
            scopes=['https://www.googleapis.com/auth/youtube.readonly']
        )
    return data

def fetch_channel_stats(ch_key):
    creds = get_creds(ch_key)
    if not creds:
        return None
    yt = build('youtube', 'v3', credentials=creds)
    try:
        # Channel stats
        ch = yt.channels().list(part='snippet,statistics', mine=True).execute()
        item = ch['items'][0]
        stats = item['statistics']
        snippet = item['snippet']

        # Recent videos (last 5)
        videos = []
        req = yt.search().list(part='snippet', forMine=True, maxResults=5,
                               type='video', order='date').execute()
        for v in req.get('items', []):
            vid_id = v['id']['videoId']
            vid = yt.videos().list(part='statistics,snippet', id=vid_id).execute()
            if vid['items']:
                vstats = vid['items'][0]['statistics']
                videos.append({
                    'title': vid['items'][0]['snippet']['title'][:60],
                    'views': int(vstats.get('viewCount', 0)),
                    'likes': int(vstats.get('likeCount', 0)),
                    'comments': int(vstats.get('commentCount', 0)),
                })
        return {
            'name': snippet['title'],
            'subs': stats.get('subscriberCount', 'hidden'),
            'views': stats.get('viewCount', '0'),
            'videos': stats.get('videoCount', '0'),
            'recent': videos
        }
    except Exception as e:
        return {'error': str(e)[:80]}

# ─── display ───────────────────────────────────────
def print_dashboard():
    print(f"\n{'='*70}")
    print(f"  📊 YOUTUBE DASHBOARD – {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")
    total_views = 0
    total_subs = 0
    active = 0

    for key, cfg in ALL_CHANNELS.items():
        data = fetch_channel_stats(key)
        if not data:
            print(f"  ⚠️  {cfg['name']:25} – No token")
            continue
        if 'error' in data:
            print(f"  ❌ {cfg['name']:25} – {data['error']}")
            continue

        active += 1
        subs = data.get('subs', '?')
        views = int(data.get('views', 0))
        vids = data.get('videos', 0)
        total_views += views
        if subs != 'hidden':
            try:
                total_subs += int(subs)
            except:
                pass

        print(f"\n  {'─'*60}")
        print(f"  🎬 {data['name']}")
        print(f"     Subs: {subs}  |  Views: {views:,}  |  Videos: {vids}")
        recent = data.get('recent', [])
        if recent:
            print(f"     Recent videos:")
            for r in recent[:3]:
                print(f"       {r['views']:>8,} views | {r['title'][:45]}")

    print(f"\n{'='*70}")
    print(f"  Active channels: {active}")
    print(f"  Total views: {total_views:,}")
    print(f"  Total subs: {total_subs:,}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    print_dashboard()
