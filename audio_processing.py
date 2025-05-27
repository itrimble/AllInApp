import os
import requests
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError # Specific pydub exception
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

def process_audio(audio_url: str, output_wav_path: str) -> str | None:
    """
    Downloads audio from a URL, converts it to WAV format, and saves it.

    Args:
        audio_url: The URL of the audio file to download.
        output_wav_path: The path to save the converted WAV file.

    Returns:
        The path to the saved WAV file if successful, None otherwise.
    """
    logger.info(f"Starting audio processing for URL: {audio_url} -> {output_wav_path}")

    output_dir = os.path.dirname(output_wav_path)
    if output_dir and not os.path.exists(output_dir): # Check if output_dir is not empty
        try:
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        except OSError as e:
            logger.exception(f"Error creating output directory {output_dir}: {e}")
            return None

    # Define a more unique temporary file path
    temp_audio_file_path = os.path.join(output_dir if output_dir else ".", f"temp_download_{os.path.basename(output_wav_path)}")

    try:
        logger.info(f"Downloading audio from {audio_url} to {temp_audio_file_path}")
        response = requests.get(audio_url, stream=True, timeout=30) # Added timeout
        response.raise_for_status()

        with open(temp_audio_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Audio downloaded successfully to {temp_audio_file_path}")

    except requests.exceptions.Timeout:
        logger.exception(f"Timeout while downloading audio from {audio_url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.exception(f"Error downloading audio from {audio_url}: {e}")
        return None
    except IOError as e:
        logger.exception(f"IOError saving downloaded audio to {temp_audio_file_path}: {e}")
        return None
_bad = "https://example.com/non_existent.mp3" # Invalid URL
    # # test_audio_url_not_audio = "https://www.google.com" # URL not pointing to audio
    #
    # SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # TEST_DATA_DIR = os.path.join(SCRIPT_DIR, "test_data_audio") # Create a specific test_data dir
    # if not os.path.exists(TEST_DATA_DIR):
    #     os.makedirs(TEST_DATA_DIR)
    #
    # LATEST_AUDIO_WAV_TEST = os.path.join(TEST_DATA_DIR, "latest_test_output.wav")
    #
    # logger.info(f"--- Starting Test: process_audio with URL: {test_audio_url} ---")
    # result_path = process_audio(test_audio_url, LATEST_AUDIO_WAV_TEST)
    #
    # if result_path:
    #     logger.info(f"Audio processed and saved to: {result_path}")
    #     if os.path.exists(result_path):
    #         logger.info(f"File confirmed to exist at {result_path}. Size: {os.path.getsize(result_path)} bytes.")
    #     else:
    #         logger.error(f"File NOT found at {result_path} despite successful return!")
    # else:
    #     logger.error("Audio processing failed.")
    #
    # # Example of testing with a bad URL
    # # logger.info(f"--- Starting Test: process_audio with Bad URL: {test_audio_url_bad} ---")
    # # result_path_bad = process_audio(test_audio_url_bad, LATEST_AUDIO_WAV_TEST)
    # # if not result_path_bad:
    # #     logger.info("Audio processing correctly failed for bad URL.")
    # # else:
    # #     logger.error(f"Audio processing succeeded for bad URL, which is unexpected: {result_path_bad}")
    pass
