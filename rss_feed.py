import feedparser
import json
import os
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

def fetch_latest_episode(feed_url: str, processed_json_path: str) -> tuple[str | None, str | None]:
    """
    Fetches the latest episode from an RSS feed that hasn't been processed yet.

    Args:
        feed_url: The URL of the RSS feed.
        processed_json_path: Path to the JSON file storing processed episode IDs.

    Returns:
        A tuple containing the audio URL and title of the latest new episode.
        Returns (None, None) if no new episode is found or an error occurs.
    """
    logger.info(f"Fetching feed from {feed_url}")

    processed_episode_ids = set()
    processed_json_dir = os.path.dirname(processed_json_path)

    if os.path.exists(processed_json_path):
        try:
            with open(processed_json_path, 'r') as f:
                processed_episode_ids = set(json.load(f))
            logger.info(f"Loaded {len(processed_episode_ids)} processed episode IDs from {processed_json_path}")
        except (json.JSONDecodeError, IOError) as e: # Catch both JSON and IO errors for reading
            logger.exception(f"Error reading or decoding {processed_json_path}. Starting with an empty set. Error: {e}")
            # Ensure directory exists in case the file was corrupt/empty and needs to be rewritten
            if processed_json_dir and not os.path.exists(processed_json_dir):
                try:
                    os.makedirs(processed_json_dir)
                except OSError as dir_e:
                    logger.exception(f"Could not create directory {processed_json_dir} for processed episodes file: {dir_e}")
                    return None, None # Cannot proceed if we can't ensure directory
    else:
        logger.info(f"No processed episodes file found at {processed_json_path}. Starting fresh.")
        # Ensure directory for processed_json_path exists
        if processed_json_dir and not os.path.exists(processed_json_dir):
            try:
                os.makedirs(processed_json_dir)
                logger.info(f"Created directory for processed episodes file: {processed_json_dir}")
            except OSError as e:
                logger.exception(f"Could not create directory {processed_json_dir} for processed episodes file: {e}")
                return None, None # Cannot proceed if we can't create directory

    feed = feedparser.parse(feed_url)

    if feed.bozo:
        # feed.bozo is 1 if the feed is not well-formed XML, 0 otherwise.
        # feed.bozo_exception contains the exception that feedparser raised.
        logger.error(f"Error parsing RSS feed from {feed_url}. Bozo exception: {feed.bozo_exception}")
        return None, None

    if not feed.entries:
        logger.info(f"No entries found in the RSS feed at {feed_url}.")
        return None, None

    logger.info(f"Found {len(feed.entries)} entries in the feed from {feed_url}.")

    for entry in feed.entries:
        episode_id = entry.get('id', entry.get('link'))
        if not episode_id:
            logger.warning(f"Could not find a unique ID for entry titled: '{entry.get('title', 'Unknown Title')}'. Skipping.")
            continue
            
        if episode_id not in processed_episode_ids:
            logger.info(f"Found new episode: '{entry.title}' (ID: {episode_id})")
            audio_url = None
            for enclosure in entry.get('enclosures', []):
                if 'audio' in enclosure.get('type', '').lower(): # Check if 'type' exists and is audio
                    audio_url = enclosure.href
                    break
            
            if audio_url:
                episode_title = entry.get('title', 'Untitled Episode') # Default title if not found
                
                processed_episode_ids.add(episode_id)
                try:
                    with open(processed_json_path, 'w') as f:
                        json.dump(list(processed_episode_ids), f, indent=4)
                    logger.info(f"Updated processed episodes file: {processed_json_path} with episode ID: {episode_id}")
                except IOError as e:
                    logger.exception(f"Could not write updated list of processed episode IDs to {processed_json_path}: {e}")
                    # If we can't write, we shouldn't return this as a "new" episode next time.
                    # For now, we proceed with returning it but log the error using logger.exception for stack trace.
                    # A more robust solution might involve not adding to processed_episode_ids in memory if write fails,
                    # or attempting a rollback, but that adds complexity.
                    # For MVP, logging the error and continuing is acceptable.

                return audio_url, episode_title
            else:
                logger.warning(f"No audio URL found in enclosures for new episode: '{entry.title}' (ID: {episode_id}). Enclosures: {entry.get('enclosures')}")
        else:
            logger.debug(f"Episode '{entry.title}' (ID: {episode_id}) already processed. Skipping.")

    logger.info(f"No new, unprocessed episodes found in feed: {feed_url}.")
    return None, None

if __name__ == '__main__':
    # This is for testing the module directly
    # You'll need to import config and set it up correctly if you run this standalone
    # For now, we're focusing on the function implementation.
    
    # Example (assuming config.py is in the same parent directory or PYTHONPATH is set):
    # To run this test, you would typically do:
    # 1. Ensure config.py is accessible (e.g., by being in the parent directory of AllInApp
    #    or by adjusting PYTHONPATH)
    # 2. Create dummy data/processed.json if needed or let the script create it.
    
    # Example of how you might call it:
    # logging.basicConfig(level=logging.DEBUG) # Setup basic config for testing this module directly
    # import sys
    # # Assuming this script is in AllInApp and config.py is in the parent directory
    # sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Adjust if your structure is different
    # try:
    #     from AllInApp.config import RSS_FEED_URL, PROCESSED_JSON, DATA_DIR
    #     # Ensure the DATA_DIR (where PROCESSED_JSON is stored) exists for the test
    #     if DATA_DIR and not os.path.exists(DATA_DIR): # Check if DATA_DIR is not empty
    #         os.makedirs(DATA_DIR)
            
    #     logger.info(f"Testing with Feed URL: {RSS_FEED_URL}")
    #     logger.info(f"Using Processed JSON: {PROCESSED_JSON}")
        
    #     audio_url, title = fetch_latest_episode(RSS_FEED_URL, PROCESSED_JSON)
        
    #     if audio_url and title:
    #         logger.info(f"Latest episode: {title}")
    #         logger.info(f"Audio URL: {audio_url}")
    #     else:
    #         logger.info("No new episodes found or error occurred during direct test.")

    # except ImportError:
    #     logger.error("Could not import config.py for testing. Ensure it's in the correct location or PYTHONPATH is set.")
    # except Exception as e:
    #     logger.exception(f"An error occurred during direct testing of rss_feed.py: {e}")
    pass
