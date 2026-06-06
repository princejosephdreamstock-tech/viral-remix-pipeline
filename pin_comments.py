#!/usr/bin/env python3
"""Pin product comments on latest videos."""
import pickle, os, json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = os.path.expanduser("~/intent-radar/content/gameplay_machine")

PRODUCTS = {
    "joy_1": "🎮 Get 'The Ritual to Break a Gaming Curse' → flutterwave.com/pay/7u2ykmotopn6",
    "joy_2": "👻 Get 'Haunted Games You Should NEVER Play' → flutterwave.com/pay/fcsca9335pzu",
    "joy_6": "😱 Get 'My PC Saved Me From a Demon Vol. 2' → flutterwave.com/pay/c8conbls2aw3",
}

for ch, comment_text in PRODUCTS.items():
    token = os.path.join(BASE_DIR, "channels", ch, "token.pickle")
    secret = os.path.join(BASE_DIR, "channels", ch, "client_secret.json")
    
    if not os.path.exists(token):
        print(f"❌ {ch}: No token")
        continue
    
    with open(token, 'rb') as f: data = pickle.load(f)
    with open(secret) as f: s = json.load(f)
    inst = s.get("installed", s)
    
    creds = Credentials(
        token=data['access_token'], refresh_token=data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=inst['client_id'], client_secret=inst['client_secret'],
        scopes=['https://www.googleapis.com/auth/youtube.force-ssl']
    )
    yt = build('youtube', 'v3', credentials=creds)
    
    # Get latest video
    req = yt.search().list(part='snippet', forMine=True, maxResults=1, type='video', order='date').execute()
    if req['items']:
        vid_id = req['items'][0]['id']['videoId']
        title = req['items'][0]['snippet']['title'][:40]
        
        # Post comment
        try:
            comment = yt.commentThreads().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': vid_id,
                        'topLevelComment': {
                            'snippet': {'textOriginal': comment_text}
                        }
                    }
                }
            ).execute()
            comment_id = comment['id']
            
            # Pin it
            yt.comments().setModerationStatus(
                id=comment['snippet']['topLevelComment']['id'],
                moderationStatus='heldForReview',
                banAuthor=False
            ).execute()
            
            print(f"✅ {ch}: Pinned comment on '{title}...'")
        except Exception as e:
            print(f"❌ {ch}: {str(e)[:60]}")
