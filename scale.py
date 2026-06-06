#!/usr/bin/env python3
"""
Channel Scaling Engine – Create a new channel instantly.
Usage: python scale.py <key> <niche> <display_name>
Example: python scale.py joy_7 horror "Horror Stories Daily"
"""

import os, sys, json, shutil, subprocess

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")
DL_BASE = os.path.expanduser("~/storage/downloads")
GAMEPLAY_SOURCE = os.path.join(DL_BASE, "gameplay_machine", "long_gameplay")

NICHE_CONFIG = {
    "horror": {
        "tags": "gaming,horror,scary,creepy,stories,scary stories,gaming horror",
        "desc": "Horror stories that will keep you up at night. Subscribe for more!",
        "story_template": "horror"
    },
    "business": {
        "tags": "business,revenge,career,money,success,corporate,justice,business stories",
        "desc": "Business revenge stories that will make you quit your job. Subscribe!",
        "story_template": "business"
    },
    "relationships": {
        "tags": "relationships,dating,marriage,divorce,cheating,love,breakup,toxic",
        "desc": "Love, betrayal, and relationship drama. Subscribe for more!",
        "story_template": "relationships"
    },
    "revenge": {
        "tags": "revenge,petty,justice,karma,satisfying,revenge stories,comeuppance",
        "desc": "Petty revenge stories so satisfying you'll binge them all. Subscribe!",
        "story_template": "revenge"
    },
}

def create_channel(key, niche, name):
    if niche not in NICHE_CONFIG:
        print(f"Unknown niche: {niche}")
        print(f"Available: {list(NICHE_CONFIG.keys())}")
        return

    cfg = NICHE_CONFIG[niche]

    # 1. Create folders
    folders = [
        os.path.join(DL_BASE, "gameplay_machine", key, "gameplay"),
        os.path.join(DL_BASE, "gameplay_machine", key, "stories"),
        os.path.join(DL_BASE, "gameplay_machine", key, "products"),
        os.path.join(BASE_DIR, "channels", key),
    ]
    for f in folders:
        os.makedirs(f, exist_ok=True)

    # 2. Copy gameplay (link to shared folder)
    # Just note where gameplay is; all channels share long_gameplay

    # 3. Generate stories
    from story_generator import generate_for_channel
    # Temporarily add new key to NICHE_MAP
    import story_generator
    story_generator.NICHE_MAP[key] = niche
    stories = generate_for_channel(key, 5)
    story_path = os.path.join(DL_BASE, "gameplay_machine", key, "stories", "stories.txt")
    with open(story_path, 'w') as f:
        for i, s in enumerate(stories):
            f.write(f"Title: {s['title']}\nText: {s['text']}")
            if i < len(stories) - 1:
                f.write("\n\n===SPLIT===\n\n")
    print(f"✅ Stories generated: {story_path}")

    # 4. Create tags & description
    with open(os.path.join(DL_BASE, "gameplay_machine", key, "stories", "tags.txt"), 'w') as f:
        f.write(cfg["tags"])
    with open(os.path.join(DL_BASE, "gameplay_machine", key, "stories", "description.txt"), 'w') as f:
        f.write(cfg["desc"])

    # 5. Copy OAuth template (user must authenticate)
    secret_src = os.path.join(BASE_DIR, "channels", "joy_1", "client_secret.json")
    if os.path.exists(secret_src):
        shutil.copy(secret_src, os.path.join(BASE_DIR, "channels", key, "client_secret.json"))
        print(f"✅ OAuth template copied. Authenticate with: python auth_channel.py {key}")

    # 6. Update post_channel.py
    post_ch_path = os.path.join(BASE_DIR, "post_channel.py")
    if os.path.exists(post_ch_path):
        with open(post_ch_path) as f:
            content = f.read()
        old = "CHANNEL_KEYS = {"
        new_entry = f'CHANNEL_KEYS = {{\n    "{key}": "{name}",'
        content = content.replace(old, new_entry, 1)
        with open(post_ch_path, 'w') as f:
            f.write(content)
        print(f"✅ Added to post_channel.py")

    # 7. Update dashboard.py
    dash_path = os.path.join(BASE_DIR, "dashboard.py")
    if os.path.exists(dash_path):
        with open(dash_path) as f:
            content = f.read()
        old = 'ALL_CHANNELS = {'
        new_entry = f'ALL_CHANNELS = {{\n    "{key}": {{"name": "{name}", "token": "channels/{key}/token.pickle", "secret": "channels/{key}/client_secret.json"}},'
        content = content.replace(old, new_entry, 1)
        with open(dash_path, 'w') as f:
            f.write(content)
        print(f"✅ Added to dashboard.py")

    print(f"\n🎉 Channel '{name}' ({key}) created successfully!")
    print(f"   Niche: {niche}")
    print(f"   Stories: 5 generated")
    print(f"   Next step: python auth_channel.py {key}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python scale.py <key> <niche> <display_name>")
        print("Niche options: horror, business, relationships, revenge")
        print("Example: python scale.py joy_7 horror 'Horror Stories Daily'")
        sys.exit(1)
    create_channel(sys.argv[1], sys.argv[2], sys.argv[3])
