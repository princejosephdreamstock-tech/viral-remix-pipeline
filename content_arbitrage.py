#!/usr/bin/env python3
"""
Content Arbitrage Machine
1. You paste a YouTube video URL
2. It grabs the transcript
3. Spins it in your voice
4. Generates voiceover
5. Creates video with gameplay
"""
import os, subprocess, json, re, requests, random
from datetime import datetime

VOICEOVER_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_machine/voiceovers")

# Proven hooks
HOOKS = [
    "Most people never figure this out. Here's what they're missing.",
    "I found a channel making money with zero personality. Just gameplay and voice.",
    "This strategy works even if you have zero subscribers. Here's why.",
    "You don't need to show your face to make money online. Proof below.",
    "The difference between broke and booked is one automation. Let me show you.",
]

# Proven CTAs
CTAS = [
    "I build these tools for businesses. DM me if you want one.",
    "If you need this for your business, I can build it.",
    "Custom automation tools. DM me to get started.",
    "I turn ideas into automated machines. Let's talk.",
]

def grab_transcript(video_url):
    """Grab transcript from a YouTube video"""
    print(f"📹 Grabbing transcript from: {video_url[:60]}...")
    
    # Use youtube-transcript-api or youtranscript
    video_id = None
    if 'v=' in video_url:
        video_id = video_url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in video_url:
        video_id = video_url.split('youtu.be/')[1].split('?')[0]
    
    if not video_id:
        print("❌ Could not extract video ID")
        return None
    
    # Try multiple transcript sources
    sources = [
        f"https://youtranscript.com/?v={video_id}",
        f"https://youtubetranscript.com/?v={video_id}",
    ]
    
    for url in sources:
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                # Extract text from HTML
                text = re.findall(r'<p[^>]*>(.*?)</p>', r.text)
                transcript = ' '.join(text)
                if len(transcript) > 100:
                    return transcript
        except:
            pass
    
    print("❌ Could not grab transcript. Try a different video.")
    return None

def spin_transcript(transcript):
    """Rewrite transcript with unique hook and CTA"""
    sentences = [s.strip() for s in transcript.split('.') if len(s.strip()) > 20]
    
    if len(sentences) < 3:
        return None
    
    hook = random.choice(HOOKS)
    cta = random.choice(CTAS)
    
    # Take the best parts
    script = f"{hook}\n\n"
    script += ' '.join(sentences[:4]) + '.\n\n'
    script += f"{cta}"
    
    return script[:500]

def create_video_from_transcript(video_url):
    """Full pipeline: grab transcript → spin → voiceover → video"""
    print("=" * 50)
    print("  CONTENT ARBITRAGE MACHINE")
    print("=" * 50)
    print()
    
    # Step 1: Grab transcript
    transcript = grab_transcript(video_url)
    if not transcript:
        print("Using fallback script instead...")
        transcript = "Most people think making money online requires followers, fame, or luck. It doesn't. The people making real money right now are using automated tools that work while they sleep. I built one on my phone that scrapes leads, sends emails, and finds buyers automatically. No course. No guru. Just a machine that runs 24/7."
    
    print(f"   Original: {transcript[:100]}...")
    
    # Step 2: Spin it
    script = spin_transcript(transcript)
    print(f"   Spun: {script[:100]}...")
    
    # Step 3: Save script
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"arbitrage_{timestamp}"
    txt_path = os.path.join(VOICEOVER_FOLDER, filename + '.txt')
    mp3_path = os.path.join(VOICEOVER_FOLDER, filename + '.mp3')
    
    with open(txt_path, 'w') as f:
        f.write(f"TITLE: How to Make Money Online With Automation\n")
        f.write(f"DESCRIPTION: {script[:200]}\n")
        f.write(f"TAGS: make money online, automation, side hustle, passive income\n")
        f.write(f"HASHTAGS: #makemoneyonline #automation #sidehustle\n")
    
    print(f"📝 Script saved: {filename}.txt")
    
    # Step 4: Generate voiceover
    print("🎙️  Generating voiceover...")
    subprocess.run([
        'edge-tts', '--text', script,
        '--voice', 'en-US-AriaNeural',
        '--write-media', mp3_path
    ], capture_output=True)
    
    if os.path.exists(mp3_path):
        print(f"   ✅ Voiceover saved: {filename}.mp3")
    else:
        print("   ⚠️  Edge TTS failed. Script saved as text only.")
    
    # Step 5: Generate video
    print("🎬 Generating video...")
    subprocess.run(['python3', 'content/gameplay_machine/engine.py'])
    
    print("\n✅ Done! Check Downloads/gameplay_videos/")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        create_video_from_transcript(sys.argv[1])
    else:
        print("Usage: python3 content/gameplay_machine/content_arbitrage.py 'YOUTUBE_VIDEO_URL'")
        print("\nExample:")
        print("  python3 content/gameplay_machine/content_arbitrage.py 'https://youtube.com/watch?v=xxxxx'")
        print("\nThe machine will:")
        print("  1. Grab the transcript from that video")
        print("  2. Rewrite it in a unique voice")
        print("  3. Add your hook and CTA")
        print("  4. Generate voiceover with Edge TTS")
        print("  5. Create the video with gameplay background")
