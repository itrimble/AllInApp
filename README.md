# All-In Podcast Reprocessor (MVP)

This project is an MVP for reprocessing the All-In Podcast. It includes functionality to fetch episodes, process audio, and transcribe speech to text. Future enhancements will include summarization, script generation, TTS, and artwork generation.

## Features (MVP + Planned)

The current MVP pipeline includes:
*   **RSS Feed Fetching:** Retrieves the latest episode from a specified RSS feed (e.g., All-In Podcast).
*   **Audio Processing:** Downloads episode audio and converts it to a standard WAV format.
*   **Transcription:** Transcribes the audio content to text using `whisper.cpp`.
*   **Lesson Extraction:** Pulls insights, key phrases (lessons), and keywords from the transcript using spaCy and pytextrank.
*   **Context Building:** Identifies related past lessons to provide context for new content. This is achieved by generating sentence embeddings for lessons using Sentence-Transformers and performing similarity searches with a FAISS index that stores embeddings of previously processed lessons. The system maintains a persistent store of past lesson texts and their corresponding FAISS index.
*   **Show Art Generation:** Creates custom podcast cover art using Stable Diffusion (via the `diffusers` library). The art is generated based on a prompt, which can be derived from the episode's title or other content. The default model is `CompVis/stable-diffusion-v1-4` but can be configured.
*   **Text-to-Speech (TTS):** Generates audio from the episode transcript using gTTS.

Future planned features include:
*   Automated Summarization
*   AI-Assisted Script Generation

## Project Structure

```
AllInApp/
├── main.py                 # Main orchestration script for the MVP pipeline
├── config.py               # Configuration settings (paths, URLs, etc.)
├── rss_feed.py             # Handles RSS feed fetching and parsing
├── audio_processing.py     # Handles audio download and conversion
├── transcription.py        # Handles audio transcription via Whisper.cpp
├── tts.py                  # Handles Text-to-Speech generation
├── data/                   # Directory for storing data (audio, transcripts, etc.)
│   ├── .gitkeep
│   ├── processed.json      # Tracks processed episode IDs
│   └── tts_audio/          # Directory for storing generated TTS audio files
│       └── .gitkeep
├── models/                 # Directory for storing ML models (e.g., Whisper model)
│   └── .gitkeep
├── whisper.cpp/            # Expected location for whisper.cpp source and compiled 'main'
│   └── main                # Compiled whisper.cpp executable
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variable configuration
├── .env                    # Actual environment variable configuration (gitignored)
└── README.md               # This README file
```

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r AllInApp/requirements.txt
    python -m spacy download en_core_web_sm # For NLP analysis (Lesson Extraction)
    ```
    *(Note: The `requirements.txt` is inside the `AllInApp` directory). Ensure it includes `gTTS`.*

    *(Note: The previously mentioned Python version constraint for TTS primarily concerned the Coqui TTS library. `gTTS` is generally more flexible with Python versions.)*

4.  **Compile Whisper.cpp:**
    - Clone the `whisper.cpp` repository from `https://github.com/ggerganov/whisper.cpp`.
    - Follow their instructions to compile it.
    - Place the compiled `main` executable into the `AllInApp/whisper.cpp/` directory. The path should be `AllInApp/whisper.cpp/main`.
    - Ensure `WHISPER_EXECUTABLE_PATH` in `AllInApp/config.py` points to this executable.

5.  **Download Whisper Model:**
    - Download a `ggml` model compatible with `whisper.cpp` (e.g., `ggml-base.en.bin`).
    - Place the model file into the `AllInApp/models/` directory.
    - Ensure `WHISPER_MODEL_PATH` in `AllInApp/config.py` points to this model file.

6.  **Stable Diffusion (for Show Art):**
    - A GPU (NVIDIA with CUDA, or Apple Silicon with MPS) is highly recommended for generating show art in a reasonable time. CPU generation is supported but will be significantly slower.
    - The selected Stable Diffusion model (default: `CompVis/stable-diffusion-v1-4` as set in `AllInApp/config.py`) will be downloaded automatically (approx. 4-5GB) on the first run that utilizes the show art feature. This requires an internet connection. Subsequent runs will use the cached model.

## Configuration

1.  **Environment Variables:**
    - Copy the example environment file:
      ```bash
      cp AllInApp/.env.example AllInApp/.env
      ```
    - Edit `AllInApp/.env` to set your desired `RSS_FEED_URL` and `PUBLIC_URL` (though `PUBLIC_URL` is not used by the MVP).

2.  **Configuration File (`AllInApp/config.py`):**
    - Review `AllInApp/config.py` for default paths and settings. Most paths are relative to the `AllInApp` directory.
    - Ensure `WHISPER_EXECUTABLE_PATH` and `WHISPER_MODEL_PATH` are correctly set if you've placed the whisper executable or model in non-default locations relative to the `AllInApp` directory.
    - Note the `TTS_OUTPUT_PATH` (defaulting to `AllInApp/data/tts_audio/`) and `TTS_LANGUAGE` (defaulting to `en`) settings for Text-to-Speech functionality.

## Usage

This section describes how to run the different parts of the application.

### Running the MVP

The current Minimum Viable Product (MVP) automates the following initial steps of the podcast generation pipeline:
1.  Fetches the latest episode from the configured RSS feed (e.g., the All-In Podcast).
2.  Downloads the episode audio and converts it to WAV format.
3.  Transcribes the audio to a text file using `whisper.cpp`.
4.  Performs NLP analysis on the transcript to:
    *   Extract key phrases (lessons) and keywords using `spaCy` and `pytextrank`.
    *   Build context by finding related past lessons using `Sentence-Transformers` and a `FAISS` index.
    *   Updates the FAISS index and a JSON store of past lessons.
5.  Generates Text-to-Speech (TTS) audio from the transcript.
6.  Generates show art using Stable Diffusion based on the episode title.

**Prerequisites for MVP:**

*   Ensure your Python virtual environment is active and all dependencies are installed as per the "Setup" section:
    ```bash
    pip install -r AllInApp/requirements.txt
    ```
*   Confirm that `whisper.cpp` is compiled and the `main` executable is located at `AllInApp/whisper.cpp/main`. The path should be correctly set as `WHISPER_EXECUTABLE_PATH` in `AllInApp/config.py`.
*   Ensure the Whisper model (e.g., `ggml-base.en.bin`) is present in `AllInApp/models/` and `WHISPER_MODEL_PATH` in `config.py` points to it.
*   If you haven't already, copy `AllInApp/.env.example` to `AllInApp/.env` and customize `RSS_FEED_URL` in `AllInApp/.env` if needed.

**To run the MVP:**

Execute the main script from the project's root directory:
```bash
python AllInApp/main.py
```

**Expected Output:**

*   Console logs showing the progress: fetching feed, downloading audio, transcribing, and performing NLP analysis.
*   If successful, you will find these files created/updated in the `AllInApp/data/` directory:
    *   `latest.wav`: The downloaded and processed audio for the latest episode.
    *   `transcript.txt`: The generated transcript for the latest episode.
    *   `processed.json`: Updated with the ID of the processed episode.
    *   `faiss_index.bin`: The FAISS index, created or updated with the lessons from the current episode.
    *   `past_lessons.json`: The JSON store of past lessons, created or updated.
    *   `tts_audio/<episode_title>_tts.mp3`: The generated TTS audio file for the episode.
    *   `show_art.jpg`: Custom cover art generated for the episode.
*   A final log message will indicate successful processing, including paths to outputs and summaries of NLP analysis, TTS generation, and show art generation.

---
*This README is a work in progress and will be updated as the project evolves.*
