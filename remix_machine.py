#!/usr/bin/env python3
"""
YouTube-to-YouTube Remix Machine
Downloads viral Shorts, applies 7-layer remix, outputs clean video.
Usage: python remix_machine.py <search_term> [count]
Example: python remix_machine.py "ai tools" 3
"""

import os, sys, random, subprocess, json
from datetime import datetime
from pathlib import Path

BASE = os.path.expanduser("~/storage/downloads/remix_machine")
INPUT = os.path.join(BASE, "input")
OUTPUT = os.path.join(BASE, "output")
MUSIC = os.path.join(BASE, "music")
BG = os.path.join(BASE, "bg_footage")
LOG = os.path.join(BASE, "remix_log.json")

TARGET_W = 1080
TARGET_H = 1920

# Aggressive remix presets
CROP_PERCENT = random.uniform(6, 10)      # Crop edges
ZOOM_PERCENT = random.uniform(102, 106)   # Zoom in
SPEED_FACTOR = random.choice([0.95, 0.96, 1.04, 1.05])
FLIP = random.choice([True, False])
CONTRAST = random.uniform(1.04, 1.10)
SATURATION = random.uniform(1.04, 1.08)
BRIGHTNESS = random.uniform(-0.04, 0.04)
HUE = random.uniform(-3, 3)
PITCH_SHIFT = random.uniform(0.7, 1.3)

OVERLAY_TEXTS = [
    "Wait for it... ",
    "This changes everything ",
    "You need to see this ",
    "Game changer ",
    "Mind blown ",
    "Watch till the end ",
    "This is insane ",
    "The results are crazy "
]

os.makedirs(INPUT, exist_ok=True)
os.makedirs(OUTPUT, exist_ok=True)
os.makedirs(MUSIC, exist_ok=True)
os.makedirs(BG, exist_ok=True)

def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def download_videos(search_term, count=3):
    """Download top Shorts from YouTube search."""
    log(f"Searching YouTube for: {search_term}")
    
    search_query = f"ytsearch{count}:{search_term} shorts"
    
    cmd = [
        "yt-dlp",
        "--max-downloads", str(count),
        "--max-filesize", "100M",
        "--match-filter", "duration < 65",
        "--format", "mp4[height>=720]",
        "--no-playlist",
        "--output", os.path.join(INPUT, "%(title)s.%(ext)s"),
        search_query
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    files = [f for f in os.listdir(INPUT) if f.endswith('.mp4')]
    log(f"Downloaded {len(files)} videos")
    return files

def get_background_music():
    """Get random background music or generate silence."""
    music_files = [f for f in os.listdir(MUSIC) if f.endswith(('.mp3', '.wav', '.m4a'))]
    if music_files:
        return os.path.join(MUSIC, random.choice(music_files))
    return None

def remix_video(input_file):
    """Apply all 7 layers and output remixed video."""
    input_path = os.path.join(INPUT, input_file)
    name = Path(input_file).stem
    output_file = f"remixed_{name}_{datetime.now().strftime('%H%M%S')}.mp4"
    output_path = os.path.join(OUTPUT, output_file)
    
    log(f"Remixing: {input_file[:50]}...")
    
    # Build FFmpeg filter chain
    filters = []
    
    # Layer 1: Crop edges (break edge detection)
    crop_w = int(TARGET_W * (100 - CROP_PERCENT) / 100)
    crop_h = int(TARGET_H * (100 - CROP_PERCENT) / 100)
    filters.append(f"crop={crop_w}:{crop_h}")
    
    # Layer 2: Zoom back to fill (break pixel matching)
    filters.append(f"scale={TARGET_W}:{TARGET_H}")
    
    # Layer 3: Flip randomly (break orientation matching)
    if FLIP:
        filters.append("hflip")
    
    # Layer 4: Color grading (break color fingerprint)
    filters.append(f"eq=contrast={CONTRAST}:saturation={SATURATION}:brightness={BRIGHTNESS}")
    filters.append(f"hue=h={HUE}")
    
    # Layer 5: Overlay text captions
    text = random.choice(OVERLAY_TEXTS)
    font_size = random.randint(36, 56)
    y_pos = random.randint(TARGET_H - 300, TARGET_H - 100)
    filters.append(f"drawtext=text='{text}':fontsize={font_size}:fontcolor=white@0.9:x=(w-text_w)/2:y={y_pos}:borderw=2:bordercolor=black@0.5")
    
    # Layer 6: Border/frame
    border_color = random.choice(["white", "black"])
    border_size = random.randint(4, 12)
    filters.append(f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2:color={border_color}@0.3")
    
    vf_chain = ",".join(filters)
    
    # Layer 7: Audio transformation
    audio_filters = []
    
    # Speed + pitch shift
    atempo = min(SPEED_FACTOR, 2.0)
    audio_filters.append(f"atempo={atempo}")
    
    # Pitch shift using asetrate
    sample_rate = 44100 * PITCH_SHIFT
    audio_filters.append(f"asetrate={int(sample_rate)}")
    
    af_chain = ",".join(audio_filters)
    
    # Build command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_chain,
        "-af", af_chain,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-t", "58",  # Ensure under 60 seconds
        output_path
    ]
    
    # Add background music if available
    bg_music = get_background_music()
    if bg_music:
        # Mix original audio with background music
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-i", bg_music,
            "-vf", vf_chain,
            "-filter_complex",
            f"[0:a]{af_chain},volume=1.0[a1];[1:a]volume=0.25[a2];[a1][a2]amix=inputs=2:duration=shortest",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-t", "58",
            output_path
        ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        log(f"  Remixed → {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        log(f"  Failed: {e.stderr.decode()[:100] if e.stderr else 'Unknown'}")
        return None

def process_all(search_term, count=3):
    """Download and remix everything."""
    log("="*50)
    log("REMAP MACHINE STARTED")
    log(f"Search: {search_term}")
    log(f"Count: {count}")
    log("="*50)
    
    # Download
    files = download_videos(search_term, count)
    
    if not files:
        log("No videos downloaded. Check search term.")
        return []
    
    # Remix each
    remixed = []
    for f in files:
        output = remix_video(f)
        if output:
            remixed.append(output)
    
    # Save log
    log_data = {
        "date": datetime.now().isoformat(),
        "search": search_term,
        "downloaded": len(files),
        "remixed": len(remixed),
        "files": remixed
    }
    with open(LOG, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    log("="*50)
    log(f"COMPLETE: {len(remixed)} videos ready in output/")
    log(f"Next: Copy to channel folder and run upload_channel.py")
    log("="*50)
    
    return remixed

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remix_machine.py <search_term> [count]")
        print("Example: python remix_machine.py 'ai tools marketing' 3")
        print("\nOutput goes to: ~/storage/downloads/remix_machine/output/")
        sys.exit(1)
    
    search = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    remixed = process_all(search, count)
    
    if remixed:
        print("\nRemixed videos:")
        for r in remixed:
            print(f"  {r}")
        print(f"\nCopy to channel for upload:")
        print(f"  cp ~/storage/downloads/remix_machine/output/*.mp4 ~/storage/downloads/gameplay_machine/channel_2/gameplay/")
        print(f"  cd ~/intent-radar/content/gameplay_machine")
        print(f"  python upload_channel.py channel_2")
