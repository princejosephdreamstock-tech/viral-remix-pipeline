#!/usr/bin/env python3
"""
Buffer Direct Upload — Uses Buffer's REST API directly
"""
import requests, json
from datetime import datetime, timedelta

ACCESS_TOKEN = "oij0PhqikzHRtcv1cKNA4i7YK-cSTMnQXMBlbRphePf"
BUFFER_URL = "https://api.bufferapp.com/1"

# Step 1: Get profiles
print("Getting profiles...")
r = requests.get(f"{BUFFER_URL}/profiles.json?access_token={ACCESS_TOKEN}")
print(f"Status: {r.status_code}")

if r.status_code == 200:
    profiles = r.json()
    print(f"\nFound {len(profiles)} profiles:")
    for p in profiles:
        print(f"  ID: {p['id']} | {p['service'].upper()} | {p.get('formatted_username', 'Unknown')}")
    
    # Find TikTok
    tiktok = None
    for p in profiles:
        if p.get('service', '').lower() in ['tiktok', 'tiktok_business']:
            tiktok = p
            break
    
    if not tiktok:
        # Maybe TikTok is listed differently
        print("\nAvailable services:")
        for p in profiles:
            print(f"  {p['service']}")
        
        # Try the first profile anyway
        if profiles:
            tiktok = profiles[0]
            print(f"\n⚠️  No TikTok found. Testing with: {tiktok['service']}")
    
    if tiktok:
        print(f"\n✅ Using: {tiktok['service']} (ID: {tiktok['id']})")
        
        # Step 2: Create a test post
        print("\n📤 Creating test post...")
        
        data = {
            'access_token': ACCESS_TOKEN,
            'profile_ids[]': tiktok['id'],
            'text': 'Test post from API ' + datetime.now().strftime('%H:%M'),
            'now': 'true'
        }
        
        r = requests.post(f"{BUFFER_URL}/updates/create.json", data=data)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            result = r.json()
            print(f"✅ Success!")
            print(f"   Post ID: {result.get('id')}")
            print(f"   Status: {result.get('status')}")
            print(f"\n   Check Buffer: https://publish.buffer.com")
            
            # Schedule 5 posts
            print("\n📤 Scheduling 5 posts...")
            titles = [
                "Stop the Account Lockout Cycle",
                "Stop Getting Banned: Professional Setup",
                "The Persona Blueprint: Trust & Authority",
                "The Client Handling Playbook: Stay in Control",
                "The Cashout & Security Playbook",
            ]
            
            for i, title in enumerate(titles):
                scheduled = datetime.utcnow() + timedelta(days=i+1, hours=1)
                scheduled_str = scheduled.strftime('%Y-%m-%dT%H:%M:00')
                
                data = {
                    'access_token': ACCESS_TOKEN,
                    'profile_ids[]': tiktok['id'],
                    'text': title[:150],
                    'scheduled_at': scheduled_str
                }
                
                r = requests.post(f"{BUFFER_URL}/updates/create.json", data=data)
                if r.status_code == 200:
                    print(f"   ✅ [{i+1}/5] Scheduled: {scheduled_str}")
                else:
                    print(f"   ❌ [{i+1}/5] {r.text[:100]}")
        else:
            print(f"❌ Error: {r.text}")
else:
    print(f"❌ Failed: {r.text}")
