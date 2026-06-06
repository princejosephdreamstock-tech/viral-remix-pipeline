#!/usr/bin/env python3
"""
Gameplay Machine - Video Generator (Channel-Aware)
Usage: python engine.py <channel>
Example: python engine.py main
         python engine.py channel_2
"""

import os, sys, random, subprocess
from datetime import datetime

DL_BASE = os.path.expanduser("~/storage/downloads/gameplay_machine")

CHANNELS = {
    "main": {
        "gameplay": os.path.join(DL_BASE, "channel_main", "gameplay"),
        "voiceovers": os.path.join(DL_BASE, "channel_main", "voiceovers"),
        "generated": os.path.join(DL_BASE, "channel_main", "generated"),
        "name": "Iam Jay"
    },
    "channel_2": {
        "gameplay": os.path.join(DL_BASE, "channel_2", "gameplay"),
        "voiceovers": os.path.join(DL_BASE, "channel_2", "voiceovers"),
        "generated": os.path.join(DL_BASE, "channel_2", "generated"),
        "name": "Channel 2"
    }
}

# Shorts requirements
MIN_DURATION = 15   # seconds
MAX_DURATION = 58   # seconds (safe under 60)
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920

def get_video_duration(filepath):
    """Get duration of a video file using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception:
        return None

def get_video_resolution(filepath):
    """Get width and height of a video file using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=s=x:p=0",
            filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        w, h = result.stdout.strip().split("x")
        return int(w), int(h)
    except Exception:
        return None, None

def generate_video(ch, count=1):
    """Generate shorts for a specific channel."""
    cfg = CHANNELS[ch]
    
    # Create folders
    os.makedirs(cfg["gameplay"], exist_ok=True)
    os.makedirs(cfg["voiceovers"], exist_ok=True)
    os.makedirs(cfg["generated"], exist_ok=True)
    
    print(f"\nChannel: {cfg['name']} ({ch})")
    print(f"Gameplay folder: {cfg['gameplay']}")
    print(f"Voiceover folder: {cfg['voiceovers']}")
    
    # Get source gameplay videos
    gameplay_videos = [f for f in os.listdir(cfg["gameplay"]) if f.endswith('.mp4')]
    if not gameplay_videos:
        print("ERROR: No .mp4 source videos in gameplay folder")
        print(f"Add some long gameplay clips to {cfg['gameplay']}")
        return 0
    
    print(f"Source clips available: {len(gameplay_videos)}")
    
    # Get voiceovers (optional)
    voiceovers = []
    if os.path.exists(cfg["voiceovers"]):
        voiceovers = [f for f in os.listdir(cfg["voiceovers"]) if f.endswith(('.mp3', '.wav', '.m4a'))]
    
    generated = 0
    for i in range(count):
        # Pick random source
        source_file = random.choice(gameplay_videos)
        source_path = os.path.join(cfg["gameplay"], source_file)
        
        # Validate source
        duration = get_video_duration(source_path)
        if duration is None:
            print(f"  Skipping {source_file}: can't read duration")
            continue
        
        if duration < MIN_DURATION + 5:
            print(f"  Skipping {source_file}: too short ({duration:.0f}s, need >{MIN_DURATION+5}s)")
            continue
        
        # Calculate clip
        clip_duration = random.randint(MIN_DURATION, min(MAX_DURATION, int(duration) - 5))
        max_start = int(duration) - clip_duration
        start_time = random.randint(5, max(6, max_start))
        
        # Output filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_name = f"gen_{ch}_{timestamp}_{i+1}.mp4"
        output_path = os.path.join(cfg["generated"], output_name)
        
        # Build FFmpeg command
        vf_filter = (
            f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", source_path,
            "-t", str(clip_duration),
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
        ]
        
        # Add audio
        if voiceovers and random.random() > 0.5:
            vo_file = random.choice(voiceovers)
            vo_path = os.path.join(cfg["voiceovers"], vo_file)
            cmd.extend(["-i", vo_path, "-c:a", "aac", "-shortest"])
            audio_source = f" + voiceover: {vo_file}"
        else:
            cmd.extend(["-c:a", "aac"])
            audio_source = "(original audio)"
        
        cmd.append(output_path)
        
        print(f"\n  [{i+1}/{count}] Generating short...")
        print(f"  Source: {source_file} (duration: {duration:.0f}s)")
        print(f"  Clip: {start_time}s -> {start_time+clip_duration}s ({clip_duration}s)")
        print(f"  Audio: {audio_source}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Move to gameplay folder for upload
            final_path = os.path.join(cfg["gameplay"], output_name)
            os.rename(output_path, final_path)
            
            print(f"  SUCCESS -> {output_name}")
            
            # Validate output
            gen_dur = get_video_duration(final_path)
            gen_w, gen_h = get_video_resolution(final_path)
            if gen_dur:
                print(f"  Output: {gen_dur:.0f}s, {gen_w}x{gen_h}")
            
            generated += 1
            
        except subprocess.CalledProcessError as e:
            print(f"  FAILED: {e.stderr.decode()[:100] if e.stderr else 'Unknown error'}")
            # Clean up failed output
            if os.path.exists(output_path):
                os.remove(output_path)
    
    print(f"\nGenerated {generated}/{count} shorts for {cfg['name']}")
    print(f"They're ready in {cfg['gameplay']}")
    print("Run: python upload_channel.py " + ch)
    
    return generated

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CHANNELS:
        print("Usage: python engine.py [main|channel_2] [count]")
        print("  count: number of shorts to generate (default: 1)")
        print("\nExamples:")
        print("  python engine.py main")
        print("  python engine.py main 5")
        print("  python engine.py channel_2 3")
        sys.exit(1)
    
    ch = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    generate_video(ch, count)
