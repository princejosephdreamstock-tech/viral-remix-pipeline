#!/usr/bin/env python3
"""
FULL AUTO — One command generates everything
"""
import os, subprocess, json, random

TOPICS = [
    "how to automate repetitive tasks without coding",
    "how to stop typing invoices into excel manually",
    "how to automate data entry and save hours",
    "how to extract data from pdf to excel",
    "how to send cold emails that get replies",
    "how to find leads without paying for tools",
]

VOICEOVER_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_machine/voiceovers")

def main():
    topic = random.choice(TOPICS)
    print("=" * 50)
    print(f"  TOPIC: {topic}")
    print("=" * 50)
    
    # Create voiceover text file
    filename = topic.lower().replace(' ', '_').replace('?', '')[:50]
    txt_path = os.path.join(VOICEOVER_FOLDER, filename + '.txt')
    mp3_path = os.path.join(VOICEOVER_FOLDER, filename + '.mp3')
    
    scripts = {
        "automate repetitive tasks": "You do the same thing every single day. Copy, paste, format, repeat. For hours. What if I told you there's a way to make your computer do all of that while you focus on things that actually matter? Automation isn't just for developers anymore. You don't need to write code. You just need to know what tools exist. I built a machine on my phone that automates my entire workflow. If I can do it, you can too.",
        
        "typing invoices": "Stop typing invoices into Excel. You're wasting hours every week on something a machine can do in seconds. I built a tool that extracts invoice data automatically. Upload a PDF. Get a clean spreadsheet. No typing. No errors. No wasted time. The first three are free. Link in my bio.",
        
        "data entry": "Data entry is a robot's job. Not yours. Every minute you spend copying numbers from one place to another is a minute you're not spending on things that actually grow your business. I automated my entire data entry workflow with a Python script I wrote on my phone. If I can do it from a phone, you can do it from anywhere.",
        
        "extract data from pdf": "You have a PDF. You need it in Excel. Right now you're probably typing it out manually. Stop. There are tools that do this automatically. I built one myself because I got tired of copy-pasting invoice data. Upload the PDF. Get the spreadsheet. Done.",
        
        "cold emails": "Most cold emails fail because they sound like templates. Nobody wants to reply to a robot. I sent 847 cold emails last month. Got 3 replies. One turned into a demo worth thousands. The secret isn't the volume. It's the timing. You need to reach people when they're actually looking for what you offer. Not when you're ready to sell.",
        
        "find leads": "Everyone tells you to buy expensive lead generation tools. You don't need them. I built a scraper on my phone that finds qualified leads for free. No subscriptions. No API keys. Just Python and knowing where to look. The tools exist. Most people just don't know how to use them."
    }
    
    # Find matching script
    script = None
    for key, value in scripts.items():
        if key in topic.lower():
            script = value
            break
    
    if not script:
        script = "Most people overcomplicate automation. They think they need expensive tools and a computer science degree. You don't. I built an entire business on a phone. No laptop. No office. Just knowing how to make machines do the work for me."
    
    # Save script as text
    with open(txt_path, 'w') as f:
        f.write(f"TITLE: {topic.title()}\n")
        f.write(f"DESCRIPTION: {script[:200]}\n")
        f.write(f"TAGS: automation, tutorial, how to, {filename.replace('_', ', ')}\n")
        f.write(f"HASHTAGS: #automation #tutorial #productivity\n")
    
    print(f"📝 Script saved: {filename}.txt")
    
    # Generate audio with Edge TTS
    print("🎙️  Generating voiceover...")
    result = subprocess.run([
        'edge-tts', '--text', script,
        '--voice', 'en-US-AriaNeural',
        '--write-media', mp3_path
    ], capture_output=True)
    
    if os.path.exists(mp3_path):
        print(f"   ✅ Audio saved: {filename}.mp3")
    else:
        print(f"   ⚠️  Edge TTS failed. Using text file only.")
    
    # Run the video engine
    print("🎬 Generating video...")
    subprocess.run(['python3', 'content/gameplay_machine/engine.py'])
    
    print("\n✅ Done! Check Downloads/gameplay_videos/")
    print("   Upload to YouTube: python3 content/gameplay_machine/youtube_uploader.py")

if __name__ == "__main__":
    main()
