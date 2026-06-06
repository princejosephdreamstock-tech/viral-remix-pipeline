#!/usr/bin/env python3
"""
Buffer GraphQL Uploader — Schedule TikTok posts
"""
import requests, json
from datetime import datetime, timedelta

ACCESS_TOKEN = "oij0PhqikzHRtcv1cKNA4i7YK-cSTMnQXMBlbRphePf"
API_URL = "https://api.buffer.com"

def graphql(query, variables=None):
    """Make a GraphQL request to Buffer"""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    r = requests.post(API_URL, headers=headers, json=payload)
    return r.json()

# Step 1: Get organization and channels
print("=" * 50)
print("  BUFFER GRAPHQL — FINDING CHANNELS")
print("=" * 50)

result = graphql("""
query {
  organization {
    id
    name
    channels {
      id
      service
      name
    }
  }
}
""")

print(json.dumps(result, indent=2))

# Extract TikTok channel ID from the response
if 'data' in result and result['data']:
    org = result['data'].get('organization', {})
    channels = org.get('channels', [])
    
    tiktok_id = None
    for ch in channels:
        if ch.get('service', '').lower() == 'tiktok':
            tiktok_id = ch['id']
            print(f"\n✅ TikTok channel: {ch['name']} (ID: {tiktok_id})")
            break
    
    if tiktok_id:
        print("\n📤 Scheduling 5 posts...\n")
        titles = [
            "Stop the Account Lockout Cycle",
            "Stop Getting Banned: Professional Setup",
            "The Persona Blueprint: Trust & Authority",
            "The Client Handling Playbook: Stay in Control",
            "The Cashout & Security Playbook",
        ]
        
        for i, title in enumerate(titles):
            scheduled = datetime.utcnow() + timedelta(days=i+1)
            scheduled = scheduled.replace(hour=14, minute=0, second=0)
            
            mutation = """
            mutation CreatePost($input: PostCreateInput!) {
              postCreate(input: $input) {
                post {
                  id
                  text
                  scheduledAt
                }
              }
            }
            """
            
            variables = {
                "input": {
                    "channelId": tiktok_id,
                    "text": title,
                    "scheduledAt": scheduled.isoformat() + "Z"
                }
            }
            
            result = graphql(mutation, variables)
            
            if 'data' in result:
                print(f"   ✅ [{i+1}/5] {title[:50]}... → {scheduled}")
            else:
                print(f"   ❌ [{i+1}/5] {result.get('errors', 'Unknown error')}")
            print()
    else:
        print("\n❌ No TikTok channel found. Connect TikTok to Buffer first.")
else:
    print(f"\n❌ API Error: {result}")
