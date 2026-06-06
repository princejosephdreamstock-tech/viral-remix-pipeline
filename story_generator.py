#!/usr/bin/env python3
"""
Auto Story Generator – Unlimited unique Reddit-style stories.
Usage: python story_generator.py <channel> <count>
Example: python story_generator.py joy_1 5
"""

import os, sys, random

TEMPLATES = {
    "revenge": [
        "My {villain} {action}. So I {revenge_action}.",
        "{villain} thought they could {action} without consequences. They were wrong.",
        "After {villain} {action}, I waited {time_period} to get my revenge.",
        "Everyone said I should let it go when {villain} {action}. I did the opposite.",
    ],
    "horror": [
        "I {discovery} and now I can never go back.",
        "There's a {place} that nobody talks about. I found out why.",
        "Last night, I {action} and something {reaction}.",
        "My {object} {creepy_action}. Then it {terrifying_outcome}.",
    ],
    "business": [
        "I worked at {company} for {years} when my boss {betrayal}. Here's what happened next.",
        "The interview started normally until {twist}. I got the job anyway.",
        "Our biggest client was about to leave until I discovered {secret}.",
        "My coworker took credit for my {project}. So I let them present it.",
    ],
    "relationships": [
        "I was married for {years} when I found {discovery} on my partner's phone.",
        "My best friend since childhood {betrayal}. Our friendship didn't survive.",
        "On our wedding day, {event}. I made a decision that changed everything.",
        "The text message said '{message}'. It wasn't meant for me.",
    ],
}

ELEMENTS = {
    "revenge": {
        "villain": ["my neighbor", "my boss", "my roommate", "my landlord", "my ex", "my coworker", "a stranger", "my brother-in-law"],
        "action": ["stole my parking spot", "ate my food", "took credit for my work", "spread lies about me", "refused to pay me back", "parked in my driveway", "stole my Amazon packages", "ruined my wedding"],
        "revenge_action": [
            "got them fired", "took them to small claims court", "let the entire neighborhood know", "waited for the perfect moment to expose them", 
            "used their own rules against them", "cost them their relationship", "had their car towed", "made them regret ever crossing me"
        ],
        "time_period": ["one year", "six months", "three weeks", "an entire summer", "two long years", "just 48 hours"],
    },
    "horror": {
        "discovery": ["found a locked door in my basement", "opened a message from an unknown number", "looked in the mirror at 3 AM", "played an old cassette tape", "checked the attic", "went into the abandoned house"],
        "place": ["house on Elm Street", "room in my basement", "trail in the woods", "floor of my apartment building", "abandoned hospital", "dark tunnel"],
        "creepy_action": ["started whispering my name", "began moving on its own", "showed me something impossible", "started bleeding", "began to glow", "played a recording of my voice"],
        "terrifying_outcome": ["disappeared completely", "showed me my own death", "took someone with it", "never stopped", "became my shadow", "called my phone"],
        "object": ["mirror", "phone", "computer", "old doll", "radio", "painting"],
        "action": ["heard a knock at the door", "checked the basement", "walked home alone", "answered an unknown call", "opened a strange package", "looked out the window"],
        "reaction": ["stared back at me", "was waiting for me", "followed me home", "was already inside", "appeared behind me", "called my name"],
    },
    "business": {
        "company": ["a Fortune 500 company", "a small startup", "the worst office in town", "a family business", "a tech giant", "a marketing agency"],
        "years": ["3 years", "5 years", "a decade", "18 months", "7 long years", "2 years"],
        "betrayal": ["stole my promotion", "took my bonus", "claimed my work as theirs", "fired me for no reason", "lied about me to HR", "gave my client to someone else"],
        "secret": ["a loophole in their contract", "their real budget", "who was actually in charge", "what they really wanted", "a mistake in their competitor's product"],
    },
    "relationships": {
        "years": ["8 years", "12 years", "5 years", "2 years", "15 years", "3 months"],
        "discovery": ["texts I wasn't supposed to see", "photos from a night out", "a secret credit card", "a second phone", "a TikTok account", "messages from someone named 'Alex'"],
        "betrayal": ["slept with my partner", "lied about something huge", "took money from me", "spread rumors about my family", "ghosted me at the worst time"],
        "event": ["the best man's speech went wrong", "my ex showed up uninvited", "the venue double-booked", "someone read a text out loud", "a secret was exposed"],
    },
}

NICHE_MAP = {
    "joy_1": "horror",       # Gaming Nightmares
    "joy_2": "horror",       # Reddit Talezz
    "joy_3": "business",     # Business Confessions
    "joy_4": "relationships", # Love & Lies
    "joy_5": "revenge",      # Petty Revenge Daily
    "joy_6": "horror",       # Creepy Encounters
    "main": "revenge",
    "channel_2": "business",
    "channel_3": "horror",
}

def generate_story(niche):
    template = random.choice(TEMPLATES[niche])
    elements = ELEMENTS[niche]
    
    # Fill ALL placeholders
    story_base = template
    for key, options in elements.items():
        placeholder = "{" + key + "}"
        while placeholder in story_base:
            story_base = story_base.replace(placeholder, random.choice(options), 1)
    
    # Generate a title from the first sentence
    title = story_base.split(".")[0].strip()
    if len(title) > 80:
        title = title[:77] + "..."
    
    # Build full text with hook + body + CTA
    hooks = [
        f"{title}. This really happened. {story_base} Subscribe for more stories.",
        f"I still can't believe this. {story_base} Like and subscribe for more.",
        f"{title}. Here's the full story. {story_base} Follow for more.",
        f"This is the craziest thing that ever happened to me. {story_base} Subscribe!",
    ]
    
    full_text = random.choice(hooks)
    
    return {
        "title": title,
        "text": full_text
    }

def generate_for_channel(ch, count=5):
    niche = NICHE_MAP.get(ch, "revenge")
    stories = []
    for _ in range(count):
        stories.append(generate_story(niche))
    return stories

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python story_generator.py <channel> [count]")
        print("Example: python story_generator.py joy_1 5")
        sys.exit(1)
    
    ch = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    stories = generate_for_channel(ch, count)
    
    for i, s in enumerate(stories):
        print(f"\n--- Story {i+1} ---")
        print(f"Title: {s['title']}")
        print(f"Text: {s['text'][:100]}...")
    
    # Save to channel's stories file
    DL = os.path.expanduser("~/storage/downloads")
    folder = os.path.join(DL, "gameplay_machine", ch, "stories")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "stories.txt")
    
    with open(path, 'w') as f:
        for i, s in enumerate(stories):
            f.write(f"Title: {s['title']}\nText: {s['text']}")
            if i < len(stories) - 1:
                f.write("\n\n===SPLIT===\n\n")
    
    print(f"\n✅ Saved {count} stories to {path}")
