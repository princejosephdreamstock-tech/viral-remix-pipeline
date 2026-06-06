#!/usr/bin/env python3
"""Gameplay Machine - Web Dashboard"""
import os, json, subprocess, sys
from datetime import datetime
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
DL_BASE = os.path.expanduser("~/storage/downloads/gameplay_machine")

CHANNELS = {
    "main": {"name": "Iam Jay", "folder": os.path.join(DL_BASE, "channel_main", "gameplay")},
    "channel_2": {"name": "ai tools for marketers", "folder": os.path.join(DL_BASE, "channel_2", "gameplay")}
}

HTML = """
<!DOCTYPE html>
<html><head>
<title>Gameplay Machine</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f0f;color:#fff;font-family:system-ui;padding:15px;max-width:600px;margin:auto}
h1{text-align:center;margin:15px 0;color:#ff4444}
.card{background:#1a1a1a;border-radius:12px;padding:15px;margin:10px 0}
.card h2{margin-bottom:10px}
.stat{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #333}
.stat:last-child{border:none}
.btn{display:block;width:100%;padding:14px;margin:8px 0;border:none;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer}
.btn-upload{background:#ff4444;color:#fff}
.btn-refresh{background:#333;color:#fff}
.btn-home{background:#444;color:#fff}
input[type=file]{display:none}
.file-label{display:block;width:100%;padding:14px;margin:8px 0;background:#2a2a2a;color:#ccc;border-radius:8px;text-align:center;font-size:14px;cursor:pointer}
.message{background:#1a3a1a;color:#4f4;padding:10px;border-radius:8px;margin:10px 0}
</style></head><body>
<h1>🎮 Gameplay Machine</h1>
{% if msg %}<div class="message">{{msg}}</div>{% endif %}
{% for key, ch in channels.items() %}
<div class="card">
<h2>{{ch.name}}</h2>
<div class="stat"><span>Videos in folder:</span><span>{{ch.vids|length}}</span></div>
<div class="stat"><span>Unprocessed:</span><span>{{ch.unprocessed|length}}</span></div>
<div class="stat"><span>Processed:</span><span>{{ch.processed|length}}</span></div>
<form method="POST" action="/upload" style="display:inline">
<input type="hidden" name="channel" value="{{key}}">
<button class="btn btn-upload" type="submit">📤 Upload & Schedule</button>
</form>
<form method="POST" action="/upload" enctype="multipart/form-data">
<input type="hidden" name="channel" value="{{key}}">
<label class="file-label" for="file_{{key}}">📁 Add Video File</label>
<input id="file_{{key}}" type="file" name="video" accept="video/mp4" onchange="this.form.submit()">
</form>
</div>
{% endfor %}
<a href="/"><button class="btn btn-refresh">🔄 Refresh</button></a>
</body></html>
"""

@app.route("/")
def home():
    msg = request.args.get("msg", "")
    channels = {}
    for key, ch in CHANNELS.items():
        folder = ch["folder"]
        os.makedirs(folder, exist_ok=True)
        all_vids = [f for f in os.listdir(folder) if f.endswith('.mp4')]
        processed_file = os.path.expanduser(f"~/intent-radar/content/gameplay_machine/{'processed_videos.json' if key == 'main' else 'channels/' + key + '/processed_videos.json'}")
        processed = json.load(open(processed_file)) if os.path.exists(processed_file) else []
        channels[key] = {
            "name": ch["name"],
            "vids": all_vids,
            "processed": processed,
            "unprocessed": [v for v in all_vids if v not in processed]
        }
    return render_template_string(HTML, channels=channels, msg=msg)

@app.route("/upload", methods=["POST"])
def upload():
    ch = request.form.get("channel", "main")
    
    # File upload
    if "video" in request.files:
        file = request.files["video"]
        if file.filename:
            folder = CHANNELS[ch]["folder"]
            os.makedirs(folder, exist_ok=True)
            file.save(os.path.join(folder, file.filename))
            return redirect(f"/?msg=Added: {file.filename}")
    
    # Trigger upload script
    script = os.path.expanduser("~/intent-radar/content/gameplay_machine/upload_channel.py")
    result = subprocess.run([sys.executable, script, ch], capture_output=True, text=True)
    return redirect(f"/?msg=Upload complete! Check terminal for details.")

if __name__ == "__main__":
    print("\n" + "="*40)
    print("  Gameplay Machine Web Dashboard")
    print("  Open: http://localhost:5050")
    print("="*40 + "\n")
    app.run(host="0.0.0.0", port=5050, debug=False)
