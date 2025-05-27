# All-In App Module

This directory contains the core application logic for the All-In Podcast Reprocessor.

## Features

The `AllInApp` module provides the following functionalities:
*   **RSS Feed Fetching:** Retrieves the latest episode from a specified RSS feed.
*   **Audio Processing:** Downloads episode audio and converts it to a standard WAV format.
*   **Transcription:** Transcribes the audio content to text using `whisper.cpp`.
*   **Lesson Extraction:** Pulls insights, key phrases (lessons), and keywords from the transcript using spaCy and pytextrank.
*   **Context Building:** Identifies related past lessons to provide context for new content using Sentence-Transformers and FAISS.
*   **Text-to-Speech (TTS):** Generates audio from the episode transcript using gTTS.
*   **Show Art Generation:** Creates custom podcast cover art using Stable Diffusion.

## Project Structure

```
AllInApp/
├── main.py                 # Main orchestration script for the pipeline
├── config.py               # Configuration settings (paths, URLs, etc.)
├── rss_feed.py             # Handles RSS feed fetching
├── audio_processing.py     # Handles audio download and conversion
├── transcription.py        # Handles audio transcription
├── nlp_analysis.py         # Handles lesson extraction and context building
├── tts.py                  # Handles Text-to-Speech generation
├── show_art.py             # Handles show art generation
├── data/                   # Directory for storing data (audio, transcripts, TTS output, etc.)
│   ├── .gitkeep
│   ├── processed.json      # Tracks processed episode IDs
│   ├── tts_audio/          # Directory for storing generated TTS audio files
│   │   └── .gitkeep
│   └── ...                 # Other data files like audio, transcripts
├── models/                 # Directory for storing ML models (e.g., Whisper model)
│   └── .gitkeep
├── whisper.cpp/            # Expected location for whisper.cpp and compiled 'main'
│   └── main                # Compiled whisper.cpp executable
├── requirements.txt        # Python dependencies for the app
├── .env.example            # Example environment variable configuration
├── .env                    # Actual environment variable configuration (gitignored)
└── README.md               # This README file
```

## Setup

1.  **Navigate to the `AllInApp` directory if you are working specifically within it.** Most commands in the main README assume you are in the project root.

2.  **Python Virtual Environment:**
    Ensure you are using the project's virtual environment. If you are in the project root:
    ```bash
    source ../venv/bin/activate  # Adjust path if your venv is elsewhere
    ```

3.  **Install Dependencies:**
    Dependencies are listed in `AllInApp/requirements.txt`.
    ```bash
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm # For NLP analysis
    ```
    Ensure `gTTS` is included in `requirements.txt` for Text-to-Speech functionality. *(Note: `gTTS` is generally compatible with recent Python 3 versions.)*

4.  **Whisper.cpp:**
    - Compile `whisper.cpp` and place the `main` executable in `AllInApp/whisper.cpp/main`.
    - Download a `ggml` model to `AllInApp/models/`.
    - Configure paths in `config.py`.

5.  **Stable Diffusion (for Show Art):**
    - Model will be downloaded automatically on first use. GPU recommended.

## Configuration

1.  **Environment Variables (`AllInApp/.env`):**
    - Set `RSS_FEED_URL` and `PUBLIC_URL`.

2.  **Configuration File (`AllInApp/config.py`):**
    - Review paths for `DATA_DIR`, `MODELS_DIR`.
    - `WHISPER_EXECUTABLE_PATH`, `WHISPER_MODEL_PATH`.
    - `STABLE_DIFFUSION_MODEL_ID`.
    - `TTS_OUTPUT_PATH`: Specifies where generated TTS audio files are stored (e.g., `AllInApp/data/tts_audio/`).
    - `TTS_LANGUAGE`: Sets the language for TTS generation (e.g., `en`).

## Usage

The main pipeline is run via `main.py`. From the project root directory:
```bash
python AllInApp/main.py
```

**Pipeline Steps:**
1.  Fetches the latest episode.
2.  Processes audio to WAV.
3.  Transcribes audio to text.
4.  Performs NLP analysis (lessons, keywords, context).
5.  Generates TTS audio from the transcript and saves it to `data/tts_audio/`.
6.  Generates show art.

**Expected Outputs in `AllInApp/data/`:**
*   `latest.wav`: Processed episode audio.
*   `transcript.txt`: Episode transcript.
*   `faiss_index.bin`, `past_lessons.json`: For NLP context.
*   `tts_audio/<episode_title>_tts.mp3`: Generated TTS audio.
*   `show_art.jpg`: Generated cover art.
*   `processed.json`: Updated list of processed episodes.

Logs in the console detail these steps.
---
*This README provides an overview of the `AllInApp` module.*
