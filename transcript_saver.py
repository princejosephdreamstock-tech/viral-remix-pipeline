#!/usr/bin/env python3
"""
Transcript Saver — Extracts audio, transcribes, saves as .doc
"""
import os, subprocess
from datetime import datetime

OUTPUT_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_videos")
DOC_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_videos/transcripts")
os.makedirs(DOC_FOLDER, exist_ok=True)

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

def save_transcript(video_path=None):
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
    
    transcript = transcribe_audio(video_path)
    if not transcript:
        print("❌ No transcript")
        return
    
    # Save as .doc (plain text with .doc extension)
    doc_name = os.path.basename(video_path).replace('.mp4', '_transcript.doc')
    doc_path = os.path.join(DOC_FOLDER, doc_name)
    
    with open(doc_path, 'w') as f:
        f.write(transcript)
    
    print(f"✅ Saved: {doc_name}")
    print(f"   {transcript[:150]}...")

def save_all():
    """Transcribe all videos in the folder"""
    videos = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp4') and not f.endswith('_details.json')]
    for v in videos:
        save_transcript(os.path.join(OUTPUT_FOLDER, v))
        print()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        save_all()
    else:
        save_transcript()
