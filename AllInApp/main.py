import logging
import config # Import the configuration
from rss_feed import fetch_latest_episode
from audio_processing import process_audio
from transcription import transcribe_audio
from nlp_analysis import (
    load_nlp_pipeline, 
    extract_lessons, 
    load_sentence_model, 
    build_context
)
from show_art import load_diffusion_model, generate_show_art
from tts import generate_tts # Import for TTS
import os # For path manipulation
import json # For reading transcript

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

    # Step 4: NLP Analysis
    logger.info(f"--- Step 4: Starting NLP Analysis for '{episode_title}' ---")

    # a. Read Transcript Text
    transcript_text = ""
    logger.info(f"Reading transcript from: {transcript_path}")
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
        if not transcript_text.strip():
            logger.warning(f"Transcript file {transcript_path} is empty or contains only whitespace. Skipping NLP analysis.")
            # Log completion without NLP
            logger.info(f"===== Partially Processed Episode (empty transcript): '{episode_title}' =====")
            logger.info(f"Transcript available at: {transcript_path}. NLP analysis skipped due to empty content.")
            return
    except Exception as e:
        logger.exception(f"Failed to read transcript file {transcript_path}. Cannot proceed with NLP analysis.")
        return

    # b. Load NLP Pipeline (spaCy + pytextrank)
    logger.info("Loading NLP pipeline (spaCy, pytextrank)...")
    nlp = load_nlp_pipeline()
    if not nlp:
        logger.error("Failed to load NLP pipeline. Cannot proceed with NLP analysis.")
        return

    # c. Extract Lessons and Keywords
    logger.info("Extracting lessons and keywords...")
    lessons, keywords = extract_lessons(transcript_text, nlp)
    if not lessons:
        logger.warning("No lessons extracted from transcript. NLP analysis might yield limited results.")
        # Still proceed, as keywords might be present or context building might be useful even with few lessons.
    else:
        logger.info(f"Extracted {len(lessons)} lessons. Preview (first 3): {lessons[:3]}")
    
    if not keywords:
        logger.warning("No keywords extracted from transcript.")
    else:
        logger.info(f"Extracted {len(keywords)} keywords. Preview (first 5): {keywords[:5]}")
    
    # d. Load Sentence Model
    logger.info("Loading sentence model...")
    sentence_model = load_sentence_model()
    if not sentence_model:
        logger.error("Failed to load sentence model. Cannot proceed with context building.")
        return

    # e. Build Context
    # Ensure FAISS_INDEX_PATH and PAST_LESSONS_PATH are defined in config
    if not hasattr(config, 'FAISS_INDEX_PATH') or not hasattr(config, 'PAST_LESSONS_PATH'):
        logger.error("FAISS_INDEX_PATH or PAST_LESSONS_PATH not defined in config.py. Cannot build context.")
        # Log completion without context building
        logger.info(f"===== Partially Processed Episode (missing FAISS/PastLessons config): '{episode_title}' =====")
        logger.info(f"Transcript at: {transcript_path}. Lessons/Keywords extracted. Context building skipped.")
        return

    logger.info("Building context from past lessons...")
    related_context = build_context(lessons, sentence_model, config.FAISS_INDEX_PATH, config.PAST_LESSONS_PATH)
    if related_context:
        logger.info(f"Found {len(related_context)} related context items. Preview (first 3): {related_context[:3]}")
    else:
        logger.info("No related context found or built for this episode.")

    logger.info(f"===== Successfully Processed Episode with NLP Analysis: '{episode_title}' =====")
    logger.info(f"Final transcript available at: {transcript_path}")
    logger.info(f"Lessons extracted: {len(lessons)}, Keywords extracted: {len(keywords)}")
    logger.info(f"Related context items found: {len(related_context)}")

    # Step 5: Generate TTS Audio
    logger.info(f"--- Step 5: Generating TTS Audio for '{episode_title}' ---")
    if not hasattr(config, 'TTS_OUTPUT_PATH') or not hasattr(config, 'TTS_LANGUAGE'):
        logger.error("TTS_OUTPUT_PATH or TTS_LANGUAGE not defined in config.py. Skipping TTS generation.")
    elif not transcript_text.strip():
        logger.warning(f"Transcript text is empty for '{episode_title}'. Skipping TTS generation.")
    else:
        try:
            tts_filename = f"{episode_title.replace(' ', '_').lower()}_tts.mp3" # Create a safe filename
            tts_output_filepath = os.path.join(config.TTS_OUTPUT_PATH, tts_filename)
            
            # Ensure the output directory exists
            if not os.path.exists(config.TTS_OUTPUT_PATH):
                os.makedirs(config.TTS_OUTPUT_PATH)
                logger.info(f"Created TTS output directory: {config.TTS_OUTPUT_PATH}")

            logger.info(f"Generating TTS audio for '{episode_title}'...")
            generate_tts(transcript_text, tts_output_filepath, config.TTS_LANGUAGE)
            logger.info(f"Successfully generated TTS audio for '{episode_title}'. Saved to: {tts_output_filepath}")
        except Exception as e:
            logger.exception(f"Error during TTS generation for '{episode_title}'. Error: {e}")
            # Log completion without TTS
            logger.info(f"===== Partially Processed Episode (TTS failed): '{episode_title}' =====")
            logger.info(f"Transcript at: {transcript_path}. Lessons/Keywords extracted. TTS generation failed.")


    # Step 6: Generate Show Art
    logger.info(f"--- Step 6: Generating Show Art for '{episode_title}' ---")
    diffusion_model = None # Initialize to None
    if not hasattr(config, 'SHOW_ART_JPG'):
        logger.warning("config.SHOW_ART_JPG not defined. Skipping show art generation.")
    else:
        # a. Load Diffusion Model
        logger.info("Loading Stable Diffusion model for show art generation...")
        diffusion_model = load_diffusion_model() # Uses defaults
        if not diffusion_model:
            logger.error("Failed to load Stable Diffusion model. Skipping show art generation for this episode.")
        
        # b. Construct Prompt & c. Generate Show Art (if model loaded)
        if diffusion_model:
            if episode_title:
                prompt = f"Podcast show art for an episode titled: '{episode_title}'. Style: vibrant, abstract, tech-themed, digital art."
                logger.info(f"Using prompt for show art: {prompt}")
                
                logger.info("Generating show art...")
                show_art_path = generate_show_art(prompt, config.SHOW_ART_JPG, diffusion_model)
                if show_art_path:
                    logger.info(f"Show art generated and saved to: {show_art_path}")
                    logger.info(f"===== Episode Fully Processed (including Show Art): '{episode_title}' =====")
                else:
                    logger.error("Failed to generate show art.")
                    logger.info(f"===== Episode Processed (NLP complete, Show Art failed): '{episode_title}' =====")
            else:
                logger.warning("Episode title not available. Skipping show art generation as prompt cannot be formed.")
                logger.info(f"===== Episode Processed (NLP complete, Show Art skipped - no title): '{episode_title}' =====")
        else: # diffusion_model was not loaded
             logger.info(f"===== Episode Processed (NLP complete, Show Art skipped - model load fail): '{episode_title}' =====")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        # This is a last-resort catch-all for unexpected errors in the pipeline itself
        logger.critical(f"Unhandled critical error in run_pipeline: {e}", exc_info=True)
