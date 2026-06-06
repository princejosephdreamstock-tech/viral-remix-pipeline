#!/usr/bin/env python3
"""
Posting Engine — Direct extraction (no AI, no API, no generic output)
"""
import os, subprocess, json, re
from datetime import datetime
from collections import Counter

OUTPUT_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_videos")

def transcribe_audio(video_path):
    print("🎙️  Transcribing...")
    audio_path = video_path.replace('.mp4', '.wav')
    subprocess.run(['ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                   '-ar', '16000', '-ac', '1', audio_path, '-y'], capture_output=True)
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = r.record(source)
        text = r.recognize_google(audio)
        os.remove(audio_path)
        return text.strip()
    except:
        os.remove(audio_path) if os.path.exists(audio_path) else None
        return ""

def extract_keywords(text):
    """Extract meaningful keywords from text"""
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                  'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your',
                  'this', 'that', 'these', 'those', 'and', 'but', 'or', 'so',
                  'if', 'then', 'than', 'just', 'about', 'now', 'very', 'really'}
    
    words = re.findall(r'[a-zA-Z]{4,}', text.lower())
    meaningful = [w for w in words if w not in stop_words]
    
    # Count frequency
    counter = Counter(meaningful)
    return [word for word, count in counter.most_common(10)]

def generate_details(transcript):
    if not transcript:
        return None
    
    print("🧠 Extracting directly from transcript...")
    
    # First sentence = hook
    sentences = re.split(r'[.!?]+', transcript)
    hook = sentences[0].strip()[:120] if sentences else transcript[:120]
    
    # First 150 chars = caption
    caption = transcript[:150].strip()
    if len(transcript) > 150:
        caption = caption.rsplit(' ', 1)[0] + "..."
    
    # Extract actual keywords from the transcript
    keywords = extract_keywords(transcript)
    
    # Map keywords to hashtags
    hashtag_map = {
        'automation': 'automation', 'automate': 'automation',
        'code': 'coding', 'coding': 'coding', 'python': 'python',
        'build': 'buildinpublic', 'building': 'buildinpublic',
        'machine': 'ai', 'ai': 'ai', 'artificial': 'ai',
        'data': 'data', 'tool': 'saas', 'saas': 'saas',
        'software': 'saas', 'business': 'business',
        'email': 'coldemail', 'cold': 'coldemail',
        'lead': 'leadgeneration', 'leads': 'leadgeneration',
        'video': 'contentcreation', 'content': 'contentcreation',
        'tiktok': 'tiktok', 'social': 'socialmedia',
        'phone': 'mobile', 'app': 'saas', 'startup': 'startup',
        'developer': 'coding', 'engineer': 'coding',
        'scraper': 'webscraping', 'scraping': 'webscraping',
        'client': 'business', 'clients': 'business',
        'money': 'business', 'revenue': 'business',
        'sales': 'sales', 'marketing': 'marketing',
    }
    
    hashtags = []
    for word in keywords:
        if word in hashtag_map and hashtag_map[word] not in hashtags:
            hashtags.append(hashtag_map[word])
    
    # Ensure at least 3 hashtags
    defaults = ['buildinpublic', 'automation', 'coding']
    for tag in defaults:
        if tag not in hashtags:
            hashtags.append(tag)
    
    return {
        "tiktok_caption": caption,
        "hashtags": hashtags[:5],
        "hook_text": hook,
        "keywords_found": keywords
    }

def process_video(video_path=None):
    if not video_path:
        videos = sorted(
            [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp4')],
            key=lambda x: os.path.getmtime(os.path.join(OUTPUT_FOLDER, x)),
            reverse=True
        )
        if not videos:
            print("❌ No videos")
            return
        video_path = os.path.join(OUTPUT_FOLDER, videos[0])
    
    print(f"📹 {os.path.basename(video_path)}")
    
    transcript = transcribe_audio(video_path)
    if not transcript:
        print("❌ No transcript")
        return
    
    print(f"   Transcript: {transcript[:120]}...")
    
    details = generate_details(transcript)
    
    details_path = video_path.replace('.mp4', '_details.json')
    with open(details_path, 'w') as f:
        json.dump(details, f, indent=2)
    
    print(f"\n✅ Saved")
    print(f"\n📱 CAPTION (from your words):")
    print(f"   {details['tiktok_caption']}")
    print(f"\n🏷️  HASHTAGS (from your keywords):")
    print(f"   {' '.join('#' + t for t in details['hashtags'])}")
    print(f"\n💬 HOOK (your first sentence):")
    print(f"   {details['hook_text']}")
    print(f"\n🔑 Keywords detected: {', '.join(details['keywords_found'][:8])}")

if __name__ == "__main__":
    process_video()
