#!/usr/bin/env python3
"""Run post_channel.py for multiple channels in one go."""
import subprocess, sys, os

ALL_CHANNELS = ["joy_1","joy_2","joy_3","joy_4","joy_5","joy_6"]
SCRIPT = os.path.join(os.path.dirname(__file__), "post_channel.py")

if len(sys.argv) > 1:
    # If arguments are numbers, treat as count for all channels
    if sys.argv[1].isdigit():
        count = sys.argv[1]
        channels = ALL_CHANNELS
    else:
        # Otherwise, list specific channels, last arg is count if digit
        channels = [a for a in sys.argv[1:] if not a.isdigit()]
        count = next((a for a in sys.argv[1:] if a.isdigit()), "3")
else:
    channels = ALL_CHANNELS
    count = "3"

print(f"Starting batch post: {len(channels)} channels, {count} videos each\n")

for ch in channels:
    print(f"=== {ch} ===")
    try:
        subprocess.run(["python", SCRIPT, ch, count], check=True, timeout=3600)
    except Exception as e:
        print(f"❌ {ch} failed: {e}")
    print()
