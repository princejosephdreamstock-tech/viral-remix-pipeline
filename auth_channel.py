#!/usr/bin/env python3
"""Usage: python auth_channel.py <channel> - Manual code exchange"""
import pickle, os, sys, json, subprocess, urllib.parse

SCOPES = 'https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly'

BASE = os.path.expanduser("~/intent-radar/content/gameplay_machine")

CHANNELS = {
    "main": {
        "secret": os.path.join(BASE, "client_secret.json"),
        "token": os.path.join(BASE, "youtube_token.pickle")
    },
    "channel_2": {
        "secret": os.path.join(BASE, "channels", "channel_2", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "channel_2", "token.pickle")
    },
    "joy_1": {"secret": os.path.join(BASE, "client_secret_joy.json"), "token": os.path.join(BASE, "channels", "joy_1", "token.pickle")},
    "joy_2": {"secret": os.path.join(BASE, "client_secret_joy.json"), "token": os.path.join(BASE, "channels", "joy_2", "token.pickle")},
    "joy_3": {"secret": os.path.join(BASE, "client_secret_joy.json"), "token": os.path.join(BASE, "channels", "joy_3", "token.pickle")},
    "joy_4": {"secret": os.path.join(BASE, "client_secret_joy.json"), "token": os.path.join(BASE, "channels", "joy_4", "token.pickle")},
    "joy_5": {"secret": os.path.join(BASE, "client_secret_joy.json"), "token": os.path.join(BASE, "channels", "joy_5", "token.pickle")},
    "joy_6": {"secret": os.path.join(BASE, "client_secret_joy.json"), "token": os.path.join(BASE, "channels", "joy_6", "token.pickle")},
        "joy_1": {
        "secret": os.path.join(BASE, "channels", "joy_1", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_1", "token.pickle")
    },
    "joy_2": {
        "secret": os.path.join(BASE, "channels", "joy_2", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_2", "token.pickle")
    },
    "joy_3": {
        "secret": os.path.join(BASE, "channels", "joy_3", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_3", "token.pickle")
    },
    "joy_4": {
        "secret": os.path.join(BASE, "channels", "joy_4", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_4", "token.pickle")
    },
    "joy_5": {
        "secret": os.path.join(BASE, "channels", "joy_5", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_5", "token.pickle")
    },
    "joy_6": {
        "secret": os.path.join(BASE, "channels", "joy_6", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_6", "token.pickle")
    },
    "joy_7": {
        "secret": os.path.join(BASE, "channels", "joy_7", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_7", "token.pickle")
    },
    "joy_8": {
        "secret": os.path.join(BASE, "channels", "joy_8", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_8", "token.pickle")
    },
    "joy_9": {
        "secret": os.path.join(BASE, "channels", "joy_9", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_9", "token.pickle")
    },
    "joy_10": {
        "secret": os.path.join(BASE, "channels", "joy_10", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_10", "token.pickle")
    },
    "joy_11": {
        "secret": os.path.join(BASE, "channels", "joy_11", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_11", "token.pickle")
    },
    "joy_12": {
        "secret": os.path.join(BASE, "channels", "joy_12", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_12", "token.pickle")
    },
    "joy_13": {
        "secret": os.path.join(BASE, "channels", "joy_13", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_13", "token.pickle")
    },
    "joy_14": {
        "secret": os.path.join(BASE, "channels", "joy_14", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_14", "token.pickle")
    },
    "joy_15": {
        "secret": os.path.join(BASE, "channels", "joy_15", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_15", "token.pickle")
    },
    "joy_16": {
        "secret": os.path.join(BASE, "channels", "joy_16", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_16", "token.pickle")
    },
    "joy_17": {
        "secret": os.path.join(BASE, "channels", "joy_17", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_17", "token.pickle")
    },
    "joy_18": {
        "secret": os.path.join(BASE, "channels", "joy_18", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_18", "token.pickle")
    },
    "joy_19": {
        "secret": os.path.join(BASE, "channels", "joy_19", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_19", "token.pickle")
    },
    "joy_20": {
        "secret": os.path.join(BASE, "channels", "joy_20", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "joy_20", "token.pickle")
    },
    "channel_3": {
        "secret": os.path.join(BASE, "channels", "channel_3", "client_secret.json"),
        "token": os.path.join(BASE, "channels", "channel_3", "token.pickle")
    }
}

if len(sys.argv) < 2 or sys.argv[1] not in CHANNELS:
    print("Usage: python auth_channel.py [main|channel_2|channel_3|joy_1..joy_20]")
    sys.exit(1)

ch = sys.argv[1]
cfg = CHANNELS[ch]

if not os.path.exists(cfg["secret"]):
    print(f"ERROR: client_secret.json not found at {cfg['secret']}")
    sys.exit(1)

with open(cfg["secret"]) as f:
    secret = json.load(f)

installed = secret.get("installed", secret)
client_id = installed["client_id"]
client_secret = installed["client_secret"]
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

params = {
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "scope": SCOPES,
    "response_type": "code",
    "access_type": "offline",
    "prompt": "consent"
}
auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

print("\n" + "="*55)
print("  1. Open this URL in your browser:")
print("="*55)
print(auth_url)
print("="*55)
print("\n  2. Sign in and authorize")
print("  3. Paste the code below:\n")

code = input("  Enter authorization code: ").strip()

post_data = {
    "code": code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code"
}

curl_cmd = [
    "curl", "-s", "-X", "POST", "https://oauth2.googleapis.com/token",
    "-d", urllib.parse.urlencode(post_data),
    "-H", "Content-Type: application/x-www-form-urlencoded"
]

result = subprocess.run(curl_cmd, capture_output=True, text=True)
token_data = json.loads(result.stdout)

if "error" in token_data:
    print(f"\nERROR: {token_data['error']}")
    print(token_data.get("error_description", ""))
    sys.exit(1)

print(f"\nToken obtained! Expires in: {token_data.get('expires_in', '?')} seconds")

os.makedirs(os.path.dirname(cfg["token"]), exist_ok=True)
with open(cfg["token"], 'wb') as f:
    pickle.dump(token_data, f)

print(f"Token saved for {ch}")
