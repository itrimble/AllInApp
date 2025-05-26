import subprocess
import os
import logging
import shutil # For robust file moving
from typing import Optional

# Configure logger for this module
logger = logging.getLogger(__name__)

def transcribe_audio(wav_file_path: str, transcript_output_path: str, whisper_executable_path: str, whisper_model_path: str) -> Optional[str]:
    """
    Transcribes an audio file using whisper.cpp and saves the transcript.

    Args:
        wav_file_path: Path to the input WAV audio file.
        transcript_output_path: Path to save the final transcript text file.
        whisper_executable_path: Path to the whisper.cpp main executable.
        whisper_model_path: Path to the whisper.cpp model file.

    Returns:
        The path to the saved transcript file if successful, None otherwise.
    """
    logger.info(f"Starting transcription for: {wav_file_path} to {transcript_output_path}")

    if not os.path.exists(wav_file_path):
        logger.error(f"Input WAV file not found: {wav_file_path}")
        return None
    if not os.path.exists(whisper_executable_path):
        logger.error(f"Whisper executable not found: {whisper_executable_path}")
        return None
    if not os.path.exists(whisper_model_path):
        logger.error(f"Whisper model not found: {whisper_model_path}")
        return None

    whisper_cwd = os.path.dirname(whisper_executable_path) or None # Use None if dirname is empty

    command = [
        os.path.abspath(whisper_executable_path), # Ensure executable path is absolute
        "-m", os.path.abspath(whisper_model_path), # Ensure model path is absolute
        "-f", os.path.abspath(wav_file_path),
        "-otxt",
        "-nt" # No timestamps
    ]

    logger.info(f"Executing Whisper.cpp command: {' '.join(command)}")
    if whisper_cwd:
        logger.info(f"Whisper.cpp CWD: {os.path.abspath(whisper_cwd)}")
    else:
        logger.info("Whisper.cpp CWD: Current process CWD (executable likely in PATH)")


    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=whisper_cwd, timeout=300) # Added timeout (5 mins)

        if result.returncode != 0:
            logger.error(f"Whisper.cpp transcription failed for {wav_file_path} with return code {result.returncode}")
            logger.error(f"Whisper.cpp stderr:\n{result.stderr}")
            logger.error(f"Whisper.cpp stdout:\n{result.stdout}")
            return None
        
        logger.info(f"Whisper.cpp executed successfully for {wav_file_path}.")
        # Log first few lines of stdout for context, if any significant output is expected beyond status
        if result.stdout.strip():
             logger.debug(f"Whisper.cpp stdout (first 200 chars):\n{result.stdout.strip()[:200]}")


        # Primary assumption: output file is wav_file_path + ".txt"
        # This is because whisper.cpp -f <input_file> -otxt creates <input_file>.txt in the CWD of whisper.cpp
        # If whisper_cwd is set, it's there. If whisper_cwd is None (main in PATH), it's in Python's CWD.
        # The simplest is to assume whisper.cpp creates it next to the *original* input file if paths are absolute.
        # However, the -f flag for whisper.cpp takes the filename, and it creates output relative to its own CWD.
        
        # Let's assume whisper.cpp creates the .txt file in its own CWD (whisper_cwd).
        # The output name will be based on the *basename* of the input file.
        input_filename_base = os.path.basename(wav_file_path)
        generated_transcript_filename = f"{input_filename_base}.txt"
        
        # Path where whisper.cpp is expected to create the transcript file
        generated_transcript_path_in_process_cwd = os.path.join(whisper_cwd if whisper_cwd else os.getcwd(), generated_transcript_filename)

        if not os.path.exists(generated_transcript_path_in_process_cwd):
            logger.error(f"Expected transcript file not found at {generated_transcript_path_in_process_cwd} after whisper.cpp execution.")
            logger.error("Please check whisper.cpp output behavior and CWD settings. Files in CWD:", os.listdir(whisper_cwd if whisper_cwd else os.getcwd()))
            return None
        else:
            logger.info(f"Found generated transcript at: {generated_transcript_path_in_process_cwd}")

        target_transcript_dir = os.path.dirname(transcript_output_path)
        if target_transcript_dir and not os.path.exists(target_transcript_dir):
            try:
                os.makedirs(target_transcript_dir, exist_ok=True)
                logger.info(f"Created target directory for transcript: {target_transcript_dir}")
            except OSError as e:
                logger.exception(f"OSError creating target directory {target_transcript_dir} for transcript: {e}")
                return None
        
        shutil.move(generated_transcript_path_in_process_cwd, transcript_output_path)
        logger.info(f"Transcript moved from {generated_transcript_path_in_process_cwd} to {transcript_output_path}")

        return transcript_output_path

    except subprocess.TimeoutExpired:
        logger.exception(f"Whisper.cpp transcription timed out for {wav_file_path} after 300 seconds.")
        return None
    except FileNotFoundError: # For whisper_executable_path itself not found by subprocess.run
        logger.exception(f"Error running subprocess for whisper.cpp. Ensure WHISPER_EXECUTABLE_PATH ('{whisper_executable_path}') is correct and executable.")
        return None
    except (subprocess.SubprocessError, OSError) as e: # Catch other subprocess or OS errors (e.g. permissions)
        logger.exception(f"Subprocess or OS error during transcription of {wav_file_path}: {e}")
        return None
    except (IOError, shutil.Error) as e: # Specific errors for file operations (move)
        logger.exception(f"File operation error (e.g. move) for transcript of {wav_file_path}: {e}")
        return None
    except Exception as e: # Catch-all for truly unexpected errors
        logger.exception(f"An unexpected error occurred during transcription of {wav_file_path}: {e}")
        return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # This assumes whisper.cpp/main and the model are in specific relative paths
    # and that a test WAV file exists.
    # You'd typically get these paths from config.py or environment variables for testing.
    
    # Example paths (adjust if your project structure is different or use config)
    # SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    # PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Assuming AllInApp is one level down from project root
    # TEST_DATA_DIR = os.path.join(SCRIPT_DIR, "test_data_transcription") # Specific test data dir
    # TEST_WAV_PATH = os.path.join(TEST_DATA_DIR, "latest_test.wav") 
    # TRANSCRIPT_PATH_TEST = os.path.join(TEST_DATA_DIR, "transcript_test.txt")
    # WHISPER_EXEC_PATH_TEST = os.path.join(PROJECT_ROOT, "whisper.cpp", "main") 
    # WHISPER_MODEL_PATH_TEST = os.path.join(PROJECT_ROOT, "models", "ggml-base.en.bin")
    #
    # if not os.path.exists(TEST_DATA_DIR):
    #     os.makedirs(TEST_DATA_DIR)
    #
    # # Ensure a dummy test WAV file exists for testing purposes
    # if not os.path.exists(TEST_WAV_PATH):
    #     try:
    #         with open(TEST_WAV_PATH, "w") as f: f.write("dummy wav data for path testing")
    #         logger.info(f"Created dummy test WAV file: {TEST_WAV_PATH}")
    #     except IOError as e:
    #         logger.exception(f"Failed to create dummy WAV file for testing: {e}")
    #
    # logger.info(f"Checking for Whisper Executable at: {os.path.abspath(WHISPER_EXEC_PATH_TEST)}")
    # logger.info(f"Checking for Whisper Model at: {os.path.abspath(WHISPER_MODEL_PATH_TEST)}")
    #
    # if not os.path.exists(WHISPER_EXEC_PATH_TEST) or not os.path.exists(WHISPER_MODEL_PATH_TEST):
    #    logger.error(f"Whisper executable or model not found. Please check paths.")
    #    logger.error(f"Expected Executable: {os.path.abspath(WHISPER_EXEC_PATH_TEST)}")
    #    logger.error(f"Expected Model: {os.path.abspath(WHISPER_MODEL_PATH_TEST)}")
    # else:
    #    logger.info("Whisper executable and model found. Attempting transcription...")
    #    result_path = transcribe_audio(TEST_WAV_PATH, TRANSCRIPT_PATH_TEST, WHISPER_EXEC_PATH_TEST, WHISPER_MODEL_PATH_TEST)
    #    if result_path:
    #        logger.info(f"Transcription test successful. Output: {result_path}")
    #        try:
    #            with open(result_path, 'r') as f: 
    #                content = f.read()
    #                if content:
    #                    logger.info(f"Transcript content (first 100 chars): {content[:100]}")
    #                else:
    #                    logger.warning(f"Transcript file {result_path} is empty (this might be expected for dummy wav).")
    #        except IOError as e:
    #            logger.exception(f"Error reading transcript file {result_path}: {e}")
    #    else:
    #        logger.error("Transcription test failed.")
    pass
