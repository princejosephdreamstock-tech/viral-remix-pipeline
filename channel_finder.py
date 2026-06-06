#!/usr/bin/env python3
"""
Channel Finder — Finds successful faceless YouTube channels with low competition
"""
import requests, json, os, re
from datetime import datetime

def find_channels_in_niche(niche):
    """Search YouTube for faceless channels in a niche"""
    print(f"🔍 Searching: {niche}")
    
    # YouTube search via web scraping
    search_url = f"https://www.youtube.com/results?search_query={niche}+automation+shorts"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        # Extract channel IDs from search results
        channel_ids = re.findall(r'"/channel/(UC[\w-]+)"', r.text)
        return list(set(channel_ids))[:10]
    except:
        return []

def get_channel_stats(channel_id):
    """Get channel subscriber count and recent video performance"""
    # YouTube doesn't expose this easily without API, so we estimate
    return {
        'channel_id': channel_id,
        'url': f'https://youtube.com/channel/{channel_id}',
        'estimated_subs': 'Unknown',
        'niche': 'automation'
    }

def get_video_transcript(video_id):
    """Get transcript of a YouTube video"""
    try:
        url = f"https://youtranscript.com/?v={video_id}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        # Extract transcript text
        text = re.findall(r'<p[^>]*>(.*?)</p>', r.text)
        return ' '.join(text)
    except:
        return None

# Niches that work well with gameplay + voiceover
PROVEN_NICHES = [
    "make money online automation",
    "passive income with AI",
    "side hustle using automation",
    "AI tools for business",
    "automate your income",
    "build a business with no code",
    "online business automation",
    "make money while you sleep",
]

print("=" * 60)
print("  CHANNEL FINDER — Faceless YouTube Niches")
print("=" * 60)
print()

for niche in PROVEN_NICHES:
    channels = find_channels_in_niche(niche)
    if channels:
        print(f"\n📺 {niche}: {len(channels)} channels found")
        for channel_id in channels[:3]:
            stats = get_channel_stats(channel_id)
            print(f"   {stats['url']}")

# Save results
os.makedirs('data/youtube', exist_ok=True)
filename = f"data/youtube/channels_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
with open(filename, 'w') as f:
    json.dump({'niches': PROVEN_NICHES}, f, indent=2)

print(f"\n💾 Saved to {filename}")
print("\nNext step: Pick a niche, find a video, get its transcript, spin it, record your voiceover.")
