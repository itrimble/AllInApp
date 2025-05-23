# All-In Podcast Reprocessor (MVP)

This project is an MVP for reprocessing the All-In Podcast. It includes functionality to fetch episodes, process audio, and transcribe speech to text. Future enhancements will include summarization, script generation, TTS, and artwork generation.

## Project Structure

```
AllInApp/
├── main.py                 # Main orchestration script for the MVP pipeline
├── config.py               # Configuration settings (paths, URLs, etc.)
├── rss_feed.py             # Handles RSS feed fetching and parsing
├── audio_processing.py     # Handles audio download and conversion
├── transcription.py        # Handles audio transcription via Whisper.cpp
├── data/                   # Directory for storing data (audio, transcripts, etc.)
│   ├── .gitkeep
│   └── processed.json      # Tracks processed episode IDs
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
    ```
    *(Note: The `requirements.txt` is inside the `AllInApp` directory).*

4.  **Compile Whisper.cpp:**
    - Clone the `whisper.cpp` repository from `https://github.com/ggerganov/whisper.cpp`.
    - Follow their instructions to compile it.
    - Place the compiled `main` executable into the `AllInApp/whisper.cpp/` directory. The path should be `AllInApp/whisper.cpp/main`.
    - Ensure `WHISPER_EXECUTABLE_PATH` in `AllInApp/config.py` points to this executable.

5.  **Download Whisper Model:**
    - Download a `ggml` model compatible with `whisper.cpp` (e.g., `ggml-base.en.bin`).
    - Place the model file into the `AllInApp/models/` directory.
    - Ensure `WHISPER_MODEL_PATH` in `AllInApp/config.py` points to this model file.

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

## Usage

This section describes how to run the different parts of the application.

### Running the MVP

The current Minimum Viable Product (MVP) automates the following initial steps of the podcast generation pipeline:
1.  Fetches the latest episode from the configured RSS feed (by default, the All-In Podcast).
2.  Downloads the episode audio.
3.  Transcribes the audio to a text file using Whisper.cpp.

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

*   Console logs showing the progress: fetching feed, downloading audio, transcribing.
*   If successful, you will find:
    *   The downloaded audio saved as `AllInApp/data/latest.wav`.
    *   The generated transcript saved as `AllInApp/data/transcript.txt`.
    *   The `AllInApp/data/processed.json` file will be created or updated to include the ID of the processed episode.
*   A final log message will indicate the path to the transcript file and the successful processing of the episode.

---
*This README is a work in progress and will be updated as the project evolves.*
