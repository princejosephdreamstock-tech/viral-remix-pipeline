#!/usr/bin/env python3
"""
Batch Metadata Parser — One text file for ALL videos
Matches metadata to video by voiceover filename
"""
import os, json, re

VOICEOVER_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_machine/voiceovers")
OUTPUT_FOLDER = os.path.expanduser("~/storage/downloads/gameplay_videos")
MASTER_FILE = os.path.expanduser("~/storage/downloads/gameplay_machine/master_metadata.txt")

def parse_master_file():
    """Parse the master text file into sections by voiceover filename"""
    if not os.path.exists(MASTER_FILE):
        print(f"❌ Master file not found: {MASTER_FILE}")
        print(f"   Create it at: Downloads/gameplay_machine/master_metadata.txt")
        return {}
    
    with open(MASTER_FILE, 'r') as f:
        content = f.read()
    
    # Split by voiceover filename pattern (something.mp3 or something.wav)
    sections = re.split(r'\n(?=\w+\.(?:mp3|wav|m4a)\n)', content)
    
    metadata_map = {}
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
        
        # First line is the voiceover filename
        lines = section.split('\n')
        vo_filename = lines[0].strip()
        section_text = '\n'.join(lines[1:])
        
        data = {}
        
        title_match = re.search(r'TITLE:\s*(.+)', section_text, re.IGNORECASE)
        if title_match:
            data['title'] = title_match.group(1).strip()
        
        desc_match = re.search(r'DESCRIPTION:\s*\n?(.+?)(?=\n[A-Z]+:|\Z)', section_text, re.DOTALL | re.IGNORECASE)
        if desc_match:
            data['description'] = desc_match.group(1).strip().replace('\n', ' ')
        
        tags_match = re.search(r'TAGS:\s*(.+)', section_text, re.IGNORECASE)
        if tags_match:
            data['tags'] = [t.strip() for t in tags_match.group(1).split(',') if t.strip()]
        
        hash_match = re.search(r'HASHTAGS:\s*(.+)', section_text, re.IGNORECASE)
        if hash_match:
            hashtags = hash_match.group(1).strip()
            if ',' in hashtags:
                data['hashtags'] = [h.strip() for h in hashtags.split(',') if h.strip()]
            else:
                data['hashtags'] = [h.strip() for h in hashtags.split() if h.strip()]
        
        if data:
            metadata_map[vo_filename] = data
    
    return metadata_map

def get_voiceover_used_by_video(video_path):
    """Try to determine which voiceover was used for this video by checking recent files"""
    # Get the newest voiceover at the time the video was created
    video_time = os.path.getmtime(video_path)
    
    voiceovers = []
    for f in os.listdir(VOICEOVER_FOLDER):
        if f.endswith(('.mp3', '.wav', '.m4a')):
            vo_path = os.path.join(VOICEOVER_FOLDER, f)
            vo_time = os.path.getmtime(vo_path)
            # Voiceover must have existed before the video
            if vo_time <= video_time:
                voiceovers.append((f, vo_time))
    
    if not voiceovers:
        return None
    
    # Return the newest voiceover that existed when the video was made
    voiceovers.sort(key=lambda x: x[1], reverse=True)
    return voiceovers[0][0]

def apply_metadata_to_video(video_path):
    """Match video to its voiceover, find metadata, apply it"""
    video_name = os.path.basename(video_path)
    
    # Find which voiceover was used
    vo_filename = get_voiceover_used_by_video(video_path)
    
    if not vo_filename:
        print(f"❌ Could not determine voiceover for {video_name}")
        return None
    
    print(f"📹 Video: {video_name}")
    print(f"🎙️  Voiceover used: {vo_filename}")
    
    # Look up metadata
    all_metadata = parse_master_file()
    
    if vo_filename not in all_metadata:
        print(f"❌ No metadata found for {vo_filename}")
        print(f"   Add a section starting with '{vo_filename}' in master_metadata.txt")
        return None
    
    metadata = all_metadata[vo_filename]
    
    # Save metadata alongside video
    seo_path = video_path.replace('.mp4', '_seo.json')
    with open(seo_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata applied!")
    print(f"   Title: {metadata.get('title', 'N/A')}")
    print(f"   Tags: {len(metadata.get('tags', []))} tags")
    print(f"   Hashtags: {len(metadata.get('hashtags', []))} hashtags")
    
    return seo_path

def process_all_videos():
    """Apply metadata to all videos in the output folder"""
    all_metadata = parse_master_file()
    
    if not all_metadata:
        print("❌ No metadata found. Create master_metadata.txt first.")
        print(f"   Location: {MASTER_FILE}")
        return
    
    print(f"📋 Loaded metadata for {len(all_metadata)} voiceovers")
    print(f"   Files: {', '.join(all_metadata.keys())}")
    print()
    
    videos = sorted(
        [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp4')],
        key=lambda x: os.path.getmtime(os.path.join(OUTPUT_FOLDER, x))
    )
    
    for video in videos:
        video_path = os.path.join(OUTPUT_FOLDER, video)
        apply_metadata_to_video(video_path)
        print()

def create_sample_master_file():
    """Create a sample master metadata file with instructions"""
    sample = """excel_automation.mp3
TITLE: How to Automate Tasks in Excel Without Coding
DESCRIPTION: Learn how to automate repetitive Excel tasks without writing any code. This simple method saves hours every week.
TAGS: excel, automation, excel tutorial, automate tasks, productivity, microsoft excel
HASHTAGS: #excel #automation #productivity

cold_email_tips.mp3
TITLE: My Cold Email Strategy After Sending 10,000 Emails
DESCRIPTION: Here's exactly what I learned about cold email after sending thousands of messages. Real numbers, real results.
TAGS: cold email, email outreach, sales, lead generation, b2b sales
HASHTAGS: #coldemail #sales #leadgeneration

python_automation.mp3
TITLE: Automate Any Task With Python — Beginner Friendly
DESCRIPTION: You don't need to be a developer to automate your work. Here's how to use Python scripts to save hours every day.
TAGS: python, coding, automation, python tutorial, scripting, productivity
HASHTAGS: #python #coding #automation

invoice_extraction.mp3
TITLE: How to Extract Invoice Data to Excel Automatically
DESCRIPTION: Stop manually typing invoices into spreadsheets. This tool extracts vendor, dates, totals, and line items in seconds.
TAGS: invoice, data extraction, excel, bookkeeping, small business, automation
HASHTAGS: #invoice #automation #smallbusiness

business_automation.mp3
TITLE: 5 Tasks Every Business Should Automate Today
DESCRIPTION: These are the most common repetitive tasks that businesses waste time on. Automate them and focus on growth.
TAGS: business, automation, productivity, workflow, time management, efficiency
HASHTAGS: #business #automation #productivity
"""
    
    with open(MASTER_FILE, 'w') as f:
        f.write(sample)
    
    print(f"✅ Sample master file created: {MASTER_FILE}")
    print(f"   Edit it with your own voiceover filenames and metadata.")
    print(f"   Each section starts with the voiceover filename on its own line.")
    print(f"   Then TITLE:, DESCRIPTION:, TAGS:, HASHTAGS: for that voiceover.")
    print(f"   Next voiceover filename starts a new section.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        create_sample_master_file()
    elif len(sys.argv) > 1 and sys.argv[1] == "all":
        process_all_videos()
    else:
        # Process just the latest video
        videos = sorted(
            [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp4')],
            key=lambda x: os.path.getmtime(os.path.join(OUTPUT_FOLDER, x)),
            reverse=True
        )
        if videos:
            apply_metadata_to_video(os.path.join(OUTPUT_FOLDER, videos[0]))
        else:
            print("❌ No videos found")
