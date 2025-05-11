import os
import json
import uuid
from datetime import datetime
from feedgen.feed import FeedGenerator
import config

def get_next_episode_number():
    if os.path.exists(config.EPISODES_FILE):
        with open(config.EPISODES_FILE, 'r') as f:
            episodes = json.load(f)
        if episodes:
            return max([ep['number'] for ep in episodes]) + 1
    return 1

def save_episode_files(episode_number, audio_file, art_file):
    new_audio_file = os.path.join(config.DATA_DIR, f'episode_{episode_number}.wav')
    new_art_file = os.path.join(config.DATA_DIR, f'show_art_{episode_number}.jpg')
    os.rename(audio_file, new_audio_file)
    os.rename(art_file, new_art_file)
    return new_audio_file, new_art_file

def update_episodes_json(episode_number, title, audio_file, art_file, show_notes):
    if os.path.exists(config.EPISODES_FILE):
        with open(config.EPISODES_FILE, 'r') as f:
            episodes = json.load(f)
    else:
        episodes = []
    guid = str(uuid.uuid4())
    pub_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    episodes.append({
        "number": episode_number,
        "title": title,
        "audio_file": audio_file,
        "art_file": art_file,
        "description": show_notes,
        "guid": guid,
        "pubDate": pub_date
    })
    with open(config.EPISODES_FILE, 'w') as f:
        json.dump(episodes, f, indent=4)

def generate_rss_feed():
    with open(config.EPISODES_FILE, 'r') as f:
        episodes = json.load(f)
    fg = FeedGenerator()
    fg.title("Local Podcast Feed")
    fg.link(href=config.PUBLIC_URL + config.RSS_FILE, rel="self")
    fg.description("Automated podcast feed")
    fg.image(config.PUBLIC_URL + 'cover_art.jpg')  # Assuming a cover art exists
    for ep in episodes:
        fe = fg.add_entry()
        fe.title(f"Episode {ep['number']}: {ep['title']}")
        fe.itunes_title(ep['title'])
        fe.itunes_episode(str(ep['number']))
        fe.enclosure(config.PUBLIC_URL + os.path.basename(ep['audio_file']), 0, "audio/wav")
        fe.itunes_image(config.PUBLIC_URL + os.path.basename(ep['art_file']))
        fe.description(ep['description'])
        fe.guid(ep['guid'])
        fe.pubDate(ep['pubDate'])
    fg.rss_file(config.RSS_FILE)