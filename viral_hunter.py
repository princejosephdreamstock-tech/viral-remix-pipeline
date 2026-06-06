#!/usr/bin/env python3
"""
Viral Hunter - Uses YouTube API to find viral videos
No scraping, no rate limits, no proxies needed.
Usage: python viral_hunter.py <channel> [count]
"""

import os, sys, json, pickle, random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")

SEARCHES = {
    "main": [
        "roblox funny moments", "roblox viral compilation",
        "roblox scary moments", "CaseOh roblox"
    ],
    "channel_2": [
        "ai tools for marketing", "best ai tools 2026",
        "ai marketing hacks"
    ],
    "channel_3": [
        "minecraft funny moments", "minecraft build hacks",
        "minecraft survival viral", "minecraft speedrun"
    ]
}

def load_creds(ch):
    if ch == "main":
        token = os.path.join(BASE_DIR, "youtube_token.pickle")
        secret = os.path.join(BASE_DIR, "client_secret.json")
    else:
        token = os.path.join(BASE_DIR, "channels", ch, "token.pickle")
        secret = os.path.join(BASE_DIR, "channels", ch, "client_secret.json")
    
    with open(token, 'rb') as f:
        data = pickle.load(f)
    with open(secret) as f:
        s = json.load(f)
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

def search_videos(ch, count=10):
    """Search YouTube for viral Shorts using the API."""
    creds = load_creds(ch)
    yt = build('youtube', 'v3', credentials=creds)
    
    query = random.choice(SEARCHES[ch])
    print(f"  Searching: {query}")
    
    results = []
    
    # Search for Shorts
    req = yt.search().list(
        part='snippet',
        q=query,
        maxResults=min(count, 50),
        type='video',
        videoDuration='short',  # Only Shorts (<4 min)
        order='viewCount',      # Most popular first
        relevanceLanguage='en'
    ).execute()
    
    for item in req.get('items', []):
        vid_id = item['id']['videoId']
        title = item['snippet']['title']
        channel_title = item['snippet']['channelTitle']
        
        # Get video details (duration, views)
        vid = yt.videos().list(
            part='contentDetails,statistics',
            id=vid_id
        ).execute()
        
        if vid['items']:
            duration = vid['items'][0]['contentDetails']['duration']
            views = vid['items'][0]['statistics'].get('viewCount', '0')
            
            # Only include videos under 60 seconds (PT1M = 1 minute)
            if 'M' not in duration or duration == 'PT1M':
                results.append({
                    'id': vid_id,
                    'title': title,
                    'channel': channel_title,
                    'views': int(views),
                    'url': f'https://www.youtube.com/watch?v={vid_id}'
                })
    
    # Sort by views
    results.sort(key=lambda x: x['views'], reverse=True)
    
    print(f"  Found {len(results)} Shorts")
    for r in results[:5]:
        print(f"    {r['views']:,} views - {r['title'][:50]}")
    
    return results[:count]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python viral_hunter.py [main|channel_2|channel_3] [count]")
        sys.exit(1)
    ch = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    results = search_videos(ch, count)
    json.dump(results, open(os.path.join(BASE_DIR, "hunt_results.json"), 'w'), indent=2)
    print(f"\nSaved {len(results)} results to hunt_results.json")
