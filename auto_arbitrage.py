#!/usr/bin/env python3
"""
Auto Content Arbitrage — Fully Automated Research + Generation
1. Searches YouTube for low-competition faceless channels
2. Finds their most viewed Shorts
3. Grabs transcripts
4. Spins them in your voice
5. Generates voiceover + video
"""
import os, subprocess, json, random, pickle, re, requests
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
CREDENTIALS_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/youtube_credentials.json")
TOKEN_FILE = os.path.expanduser("~/intent-radar/content/gameplay_machine/youtube_token.pickle")
VOICEOVER_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_machine/voiceovers")

HOOKS = [
    "Most people never figure this out. Here's what they're missing.",
    "I found a channel making money with zero personality. Just gameplay and voice.",
    "This strategy works even if you have zero subscribers.",
    "The difference between broke and booked is one automation.",
    "You don't need to show your face to make money online.",
]

CTAS = [
    "I build these tools for businesses. DM me.",
    "Custom automation tools. DM me to get started.",
    "I turn ideas into automated machines. Let's talk.",
]

NICHES = [
    "make money online automation",
    "passive income AI tools",
    "side hustle automation",
    "faceless YouTube channel",
    "automate your income",
]

def get_youtube_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES, redirect_uri='http://localhost:8080/')
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            print(f"\n🔗 Open this URL and paste the code:\n{auth_url}\n")
            code = input("Code: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

def search_channels(youtube, niche, max_results=5):
    """Search YouTube for channels in a niche"""
    print(f"🔍 Searching: {niche}")
    
    try:
        # Search for channels
        request = youtube.search().list(
            part='snippet',
            q=niche,
            type='channel',
            maxResults=max_results,
            order='viewCount'
        )
        response = request.execute()
        
        channels = []
        for item in response.get('items', []):
            channel_id = item['snippet']['channelId']
            title = item['snippet']['channelTitle']
            
            # Get channel stats
            stats_request = youtube.channels().list(
                part='statistics',
                id=channel_id
            )
            stats_response = stats_request.execute()
            
            if stats_response['items']:
                stats = stats_response['items'][0]['statistics']
                subs = int(stats.get('subscriberCount', 0))
                
                # Only keep channels with 1K-50K subs (low competition)
                if 1000 <= subs <= 50000:
                    channels.append({
                        'id': channel_id,
                        'title': title,
                        'subs': subs,
                        'niche': niche
                    })
                    print(f"   ✅ {title} ({subs:,} subs)")
        
        return channels
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def get_channel_shorts(youtube, channel_id, max_results=5):
    """Get most viewed Shorts from a channel"""
    try:
        request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            type='video',
            maxResults=max_results,
            order='viewCount',
            
        )
        response = request.execute()
        
        videos = []
        for item in response.get('items', []):
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            
            # Get video stats
            stats_request = youtube.videos().list(
                part='statistics',
                id=video_id
            )
            stats_response = stats_request.execute()
            
            if stats_response['items']:
                stats = stats_response['items'][0]['statistics']
                views = int(stats.get('viewCount', 0))
                
                videos.append({
                    'id': video_id,
                    'title': title,
                    'views': views,
                    'url': f'https://youtube.com/watch?v={video_id}'
                })
                print(f"      📹 {title[:50]}... ({views:,} views)")
        
        return videos
    except:
        return []

def grab_transcript(video_id):
    """Get transcript from YouTube video"""
    try:
        url = f"https://youtranscript.com/?v={video_id}"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code == 200:
            text = re.findall(r'<p[^>]*>(.*?)</p>', r.text)
            transcript = ' '.join(text)
            if len(transcript) > 100:
                return transcript
    except:
        pass
    return None

def spin_transcript(transcript):
    """Rewrite transcript with hook and CTA"""
    sentences = [s.strip() for s in transcript.split('.') if len(s.strip()) > 20]
    if len(sentences) < 3:
        return None
    
    hook = random.choice(HOOKS)
    cta = random.choice(CTAS)
    
    return f"{hook}\n\n{' '.join(sentences[:4])}.\n\n{cta}"

def full_auto_arbitrage():
    """Complete automated pipeline"""
    print("=" * 60)
    print("  AUTO CONTENT ARBITRAGE")
    print("=" * 60)
    print()
    
    youtube = get_youtube_service()
    if not youtube:
        print("❌ YouTube auth failed")
        return
    
    # Step 1: Search all niches
    all_channels = []
    for niche in NICHES:
        channels = search_channels(youtube, niche)
        all_channels.extend(channels)
    
    if not all_channels:
        print("❌ No low-competition channels found")
        return
    
    # Step 2: Pick a random channel and get its best Short
    channel = random.choice(all_channels)
    print(f"\n🎯 Selected: {channel['title']} ({channel['subs']:,} subs)")
    
    shorts = get_channel_shorts(youtube, channel['id'])
    if not shorts:
        print("❌ No Shorts found")
        return
    
    # Step 3: Pick the most viewed Short
    best = max(shorts, key=lambda x: x['views'])
    print(f"\n📹 Best Short: {best['title'][:60]}... ({best['views']:,} views)")
    print(f"   URL: {best['url']}")
    
    # Step 4: Grab transcript
    print("\n📝 Grabbing transcript...")
    transcript = grab_transcript(best['id'])
    
    if not transcript:
        print("   ❌ Could not grab transcript. Using fallback.")
        transcript = "Most people think making money online requires followers, fame, or luck. It doesn't. The people making real money right now are using automated tools that work while they sleep."
    
    # Step 5: Spin it
    script = spin_transcript(transcript)
    if not script:
        print("   ❌ Could not spin transcript")
        return
    
    print(f"   Spun script ready ({len(script)} chars)")
    
    # Step 6: Save and generate
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"arbitrage_{timestamp}"
    txt_path = os.path.join(VOICEOVER_FOLDER, filename + '.txt')
    mp3_path = os.path.join(VOICEOVER_FOLDER, filename + '.mp3')
    
    with open(txt_path, 'w') as f:
        f.write(f"TITLE: {best['title'][:80]}\n")
        f.write(f"DESCRIPTION: {script[:200]}\n")
        f.write(f"TAGS: {channel['niche']}, automation, side hustle\n")
        f.write(f"HASHTAGS: #makemoneyonline #automation #sidehustle\n")
    
    print(f"\n🎙️  Generating voiceover...")
    subprocess.run(['edge-tts', '--text', script, '--voice', 'en-US-AriaNeural', '--write-media', mp3_path], capture_output=True)
    
    print("🎬 Generating video...")
    subprocess.run(['python3', 'content/gameplay_machine/engine.py'])
    
    print(f"\n✅ DONE!")
    print(f"   Original: {best['url']}")
    print(f"   Your version: Downloads/gameplay_videos/")

if __name__ == "__main__":
    full_auto_arbitrage()
