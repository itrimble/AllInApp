import json
import os
from feedparser import parse
import config

def fetch_latest_episode():
    feed = parse(config.RSS_FEED_URL)
    if not feed.entries:
        print("No episodes found in RSS feed.")
        return None
    latest_episode = feed.entries[0]
    guid = latest_episode.guid
    if os.path.exists(config.PROCESSED_FILE):
        with open(config.PROCESSED_FILE, 'r') as f:
            processed = json.load(f)
        if guid in processed:
            print("Latest episode already processed.")
            return None
    return latest_episode

def mark_as_processed(guid):
    if os.path.exists(config.PROCESSED_FILE):
        with open(config.PROCESSED_FILE, 'r') as f:
            processed = json.load(f)
    else:
        processed = []
    processed.append(guid)
    with open(config.PROCESSED_FILE, 'w') as f:
        json.dump(processed, f)