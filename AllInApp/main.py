import logging
import config # Import the configuration
from rss_feed import fetch_latest_episode
from audio_processing import process_audio
from transcription import transcribe_audio

# Configure basic logging for the application
# This should be the only place where basicConfig is called.
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()] # Ensures logs go to console
)
logger = logging.getLogger(__name__) # Get a logger for this module (main)

def run_pipeline():
    """
    Main pipeline function to fetch, process, and transcribe a podcast episode.
    """
    logger.info("===== Starting Podcast Processing Pipeline =====")

    # Step 1: Fetch RSS Feed
    logger.info("--- Step 1: Fetching RSS feed ---")
    try:
        audio_url, episode_title = fetch_latest_episode(config.RSS_FEED_URL, config.PROCESSED_JSON)
        if not audio_url or not episode_title:
            logger.info("No new episodes found or error in fetching. Pipeline run completed.")
            return
        logger.info(f"Successfully fetched new episode: '{episode_title}' from {audio_url}")
    except Exception as e:
        logger.exception(f"Critical error during RSS feed fetching. Exiting pipeline. Error: {e}")
        return

    # Step 2: Process Audio
    logger.info(f"--- Step 2: Processing audio for '{episode_title}' ---")
    try:
        wav_file_path = process_audio(audio_url, config.LATEST_AUDIO_WAV) 
        if not wav_file_path:
            logger.error(f"Audio processing failed for '{episode_title}'. See previous logs for details. Exiting pipeline for this episode.")
            return
        logger.info(f"Successfully processed audio. WAV file saved to: {wav_file_path}")
    except Exception as e:
        logger.exception(f"Critical error during audio processing for '{episode_title}'. Exiting pipeline. Error: {e}")
        return

    # Step 3: Transcribe Audio
    logger.info(f"--- Step 3: Transcribing audio for '{episode_title}' ---")
    # Ensure WHISPER_EXECUTABLE_PATH and WHISPER_MODEL_PATH are correctly set in config.py
    if not hasattr(config, 'WHISPER_EXECUTABLE_PATH') or not config.WHISPER_EXECUTABLE_PATH or \
       not hasattr(config, 'WHISPER_MODEL_PATH') or not config.WHISPER_MODEL_PATH:
        logger.error("WHISPER_EXECUTABLE_PATH or WHISPER_MODEL_PATH is not defined or empty in config.py.")
        logger.error("Please define them. Example: WHISPER_EXECUTABLE_PATH = os.path.join(BASE_DIR, 'whisper.cpp', 'main')")
        logger.error("Pipeline cannot continue without Whisper paths.")
        return
    
    try:
        transcript_path = transcribe_audio(
            wav_file_path,
            config.TRANSCRIPT_TXT, 
            config.WHISPER_EXECUTABLE_PATH,
            config.WHISPER_MODEL_PATH
        )
        if not transcript_path:
            logger.error(f"Audio transcription failed for '{episode_title}'. See previous logs for details. Exiting pipeline for this episode.")
            return
        logger.info(f"Successfully transcribed audio. Transcript saved to: {transcript_path}")
    except Exception as e:
        logger.exception(f"Critical error during audio transcription for '{episode_title}'. Exiting pipeline. Error: {e}")
        return

    logger.info(f"===== Successfully Processed Episode: '{episode_title}' =====")
    logger.info(f"Final transcript available at: {transcript_path}")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        # This is a last-resort catch-all for unexpected errors in the pipeline itself
        logger.critical(f"Unhandled critical error in run_pipeline: {e}", exc_info=True)
