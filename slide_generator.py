#!/usr/bin/env python3
"""
Professional Slide Generator v3 — High-retention slides with progress bar, logo, and animations
"""
import os, subprocess, random
from datetime import datetime

VOICEOVER_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_machine/voiceovers")
OUTPUT_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_videos")
SLIDE_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_machine/slides")
os.makedirs(SLIDE_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

THEMES = [
    {"bg": "#0d1117", "text": "#e6edf3", "accent": "#58a6ff", "sub": "#8b949e", "name": "GitHub Dark"},
    {"bg": "#1a1a2e", "text": "#e0e0e0", "accent": "#e94560", "sub": "#a0a0b0", "name": "Dark Red"},
    {"bg": "#0f0f23", "text": "#ffffff", "accent": "#00d4ff", "sub": "#8892b0", "name": "Dark Blue"},
]

def create_slide(text, theme, index, total):
    """Create a slide with progress bar, branding, and proper layout"""
    slide_path = os.path.join(SLIDE_FOLDER, f"slide_{index:03d}.png")
    safe_text = text.replace("'", "'\\''").replace('%', '\\\\%')
    
    # Progress percentage
    progress_pct = int((index + 1) / total * 100)
    progress_width = int(1080 * progress_pct / 100)
    
    cmd = [
        'ffmpeg', '-f', 'lavfi',
        '-i', f"color=c={theme['bg']}:s=1080x1920:d=1",
        '-vf',
        # Progress bar background
        f"drawtext=text='':fontcolor=white:fontsize=1:x=0:y=1900:w=1080:h=4:box=1:boxcolor=white@0.1:boxborderw=0,"
        # Progress bar fill
        f"drawtext=text='':fontcolor=white:fontsize=1:x=0:y=1900:w={progress_width}:h=4:box=1:boxcolor={theme['accent']}:boxborderw=0,"
        # Progress percentage text
        f"drawtext=text='{progress_pct}%':fontcolor={theme['sub']}:fontsize=20:x=1080-text_w-30:y=1860,"
        # Brand text
        f"drawtext=text='@IntentRadar':fontcolor={theme['sub']}:fontsize=20:x=30:y=1860,"
        # Main text
        f"drawtext=text='{safe_text}':fontcolor={theme['text']}:fontsize=42:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-60:box=1:boxcolor={theme['bg']}@0.8:boxborderw=20:line_spacing=15,"
        # Page number
        f"drawtext=text='{index+1}/{total}':fontcolor={theme['accent']}:fontsize=18:x=(w-text_w)/2:y=h-60",
        '-frames:v', '1', '-y', slide_path
    ]
    
    subprocess.run(cmd, capture_output=True)
    return slide_path

def create_title_slide(title, theme):
    """Eye-catching title slide"""
    slide_path = os.path.join(SLIDE_FOLDER, "slide_title.png")
    safe_title = title.replace("'", "'\\''")
    
    cmd = [
        'ffmpeg', '-f', 'lavfi',
        '-i', f"color=c={theme['bg']}:s=1080x1920:d=1",
        '-vf',
        # Large accent bar
        f"drawtext=text='':fontcolor=white:fontsize=1:x=0:y=800:w=1080:h=6:box=1:boxcolor={theme['accent']}:boxborderw=0,"
        # Title
        f"drawtext=text='{safe_title}':fontcolor={theme['text']}:fontsize=52:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-100:box=1:boxcolor={theme['bg']}@0.8:boxborderw=20:line_spacing=15,"
        # Subtitle
        f"drawtext=text='Step-by-Step Guide':fontcolor={theme['sub']}:fontsize=28:"
        f"x=(w-text_w)/2:y=(h-text_h)/2,"
        # Brand
        f"drawtext=text='@IntentRadar':fontcolor={theme['sub']}:fontsize=22:x=30:y=1860",
        '-frames:v', '1', '-y', slide_path
    ]
    
    subprocess.run(cmd, capture_output=True)
    return slide_path

def create_outro_slide(theme):
    """CTA slide that converts"""
    slide_path = os.path.join(SLIDE_FOLDER, "slide_outro.png")
    
    cmd = [
        'ffmpeg', '-f', 'lavfi',
        '-i', f"color=c={theme['bg']}:s=1080x1920:d=1",
        '-vf',
        # Large CTA
        f"drawtext=text='Want This Built For You?':fontcolor={theme['text']}:fontsize=44:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-80,"
        # Sub CTA
        f"drawtext=text='DM me on X or TikTok':fontcolor={theme['accent']}:fontsize=30:"
        f"x=(w-text_w)/2:y=(h-text_h)/2,"
        # Handle
        f"drawtext=text='@IntentRadar':fontcolor={theme['sub']}:fontsize=24:"
        f"x=(w-text_w)/2:y=(h-text_h)/2+50,"
        # Bottom brand
        f"drawtext=text='@IntentRadar':fontcolor={theme['sub']}:fontsize=20:x=30:y=1860",
        '-frames:v', '1', '-y', slide_path
    ]
    
    subprocess.run(cmd, capture_output=True)
    return slide_path

def create_video_from_slides(slides, voiceover_path):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output = os.path.join(OUTPUT_FOLDER, f"pro_{timestamp}.mp4")
    
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                            '-of', 'default=noprint_wrappers=1:nokey=1', voiceover_path],
                           capture_output=True, text=True)
    total_duration = float(result.stdout.strip())
    duration_per_slide = total_duration / len(slides)
    
    clip_files = []
    for i, slide in enumerate(slides):
        clip_path = os.path.join(SLIDE_FOLDER, f"clip_{i:03d}.mp4")
        cmd = [
            'ffmpeg', '-loop', '1', '-i', slide,
            '-c:v', 'libx264', '-t', str(duration_per_slide),
            '-pix_fmt', 'yuv420p', '-vf', 'fps=30',
            '-y', clip_path
        ]
        subprocess.run(cmd, capture_output=True)
        clip_files.append(clip_path)
    
    concat_file = os.path.join(SLIDE_FOLDER, "concat.txt")
    with open(concat_file, 'w') as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")
    
    temp_video = os.path.join(SLIDE_FOLDER, "temp_video.mp4")
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file,
                   '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
                   '-pix_fmt', 'yuv420p', '-y', temp_video], capture_output=True)
    
    subprocess.run(['ffmpeg', '-i', temp_video, '-i', voiceover_path,
                   '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k',
                   '-shortest', '-map', '0:v', '-map', '1:a',
                   '-y', output], capture_output=True)
    
    for clip in clip_files:
        os.remove(clip) if os.path.exists(clip) else None
    os.remove(temp_video) if os.path.exists(temp_video) else None
    
    if os.path.exists(output) and os.path.getsize(output) > 10000:
        print(f"✅ Video: Downloads/gameplay_videos/{os.path.basename(output)}")
        return output
    return None

def generate():
    scripts = sorted([f for f in os.listdir(VOICEOVER_FOLDER) if f.endswith('.txt')],
                    key=lambda x: os.path.getmtime(os.path.join(VOICEOVER_FOLDER, x)), reverse=True)
    if not scripts:
        print("❌ No scripts found")
        return
    
    script_file = os.path.join(VOICEOVER_FOLDER, scripts[0])
    vo_file = os.path.join(VOICEOVER_FOLDER, os.path.basename(script_file).replace('.txt', '.mp3'))
    
    if not os.path.exists(vo_file):
        print(f"❌ Voiceover not found")
        return
    
    with open(script_file) as f:
        paragraphs = [p.strip() for p in f.read().split('\n\n') if p.strip()]
    
    theme = random.choice(THEMES)
    print(f"🎨 {theme['name']} | 📝 {len(paragraphs)} slides")
    
    slides = [create_title_slide(paragraphs[0][:80], theme)]
    for i, p in enumerate(paragraphs[1:5]):
        slides.append(create_slide(p[:200], theme, i, len(paragraphs)))
    slides.append(create_outro_slide(theme))
    
    create_video_from_slides(slides, vo_file)

if __name__ == "__main__":
    generate()
