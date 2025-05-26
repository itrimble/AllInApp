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

Future planned features include:
*   Automated Summarization
*   AI-Assisted Script Generation
*   Text-to-Speech (TTS) for generated content

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

## Quick Setup

### Automated Setup (Recommended)

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/itrimble/AllInApp.git
    cd AllInApp
    ```

2.  **Run the Setup Script:**
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

This script will automatically:
- Install all Python dependencies
- Download the spaCy English model
- Clone and compile Whisper.cpp
- Download the Whisper base English model
- Create necessary directories

### Manual Setup

If you prefer manual setup or the automated script fails:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/itrimble/AllInApp.git
    cd AllInApp
    ```

2.  **Install Python Dependencies:**
    ```bash
    python3 -m pip install --user -r requirements.txt
    python3 -m spacy download en_core_web_sm
    ```

3.  **Install Whisper.cpp:**
    ```bash
    git clone https://github.com/ggerganov/whisper.cpp.git
    cd whisper.cpp
    make
    cd ..
    ```

4.  **Download Whisper Model:**
    ```bash
    mkdir -p models
    curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin -o models/ggml-base.en.bin
    ```

5.  **Create Data Directory:**
    ```bash
    mkdir -p data
    ```

### GPU Acceleration (Optional)

- **NVIDIA GPUs:** Ensure CUDA is installed for faster Stable Diffusion
- **Apple Silicon:** MPS acceleration is automatically used
- **CPU Only:** All features work but image generation will be slower

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
1.  Fetches the latest episode from the configured RSS feed (e.g., the All-In Podcast).
2.  Downloads the episode audio and converts it to WAV format.
3.  Transcribes the audio to a text file using `whisper.cpp`.
4.  Performs NLP analysis on the transcript to:
    *   Extract key phrases (lessons) and keywords using `spaCy` and `pytextrank`.
    *   Build context by finding related past lessons using `Sentence-Transformers` and a `FAISS` index.
    *   Updates the FAISS index and a JSON store of past lessons.
5.  Generates show art using Stable Diffusion based on the episode title.

**Prerequisites for MVP:**

*   Run the setup script first: `./setup.sh`
*   Or manually ensure all dependencies are installed as per the "Setup" section
*   Whisper.cpp should be compiled at `whisper.cpp/build/bin/whisper-cli`
*   Whisper model should be at `models/ggml-base.en.bin`

**To run the MVP:**

Execute the main script:
```bash
python3 main.py
```

**Expected Output:**

*   Console logs showing the progress: fetching feed, downloading audio, transcribing, and performing NLP analysis.
*   If successful, you will find these files created/updated in the `data/` directory:
    *   `latest.wav`: The downloaded and processed audio for the latest episode.
    *   `transcript.txt`: The generated transcript for the latest episode.
    *   `processed.json`: Updated with the ID of the processed episode.
    *   `faiss_index.bin`: The FAISS index, created or updated with the lessons from the current episode.
    *   `past_lessons.json`: The JSON store of past lessons, created or updated.
    *   `show_art.jpg`: Custom cover art generated for the episode.
*   A final log message will indicate successful processing, including paths to outputs and summaries of NLP analysis and show art generation.

## Requirements

- **Python 3.9+** (Python 3.10+ recommended for full type hint support)
- **macOS/Linux/Windows** (tested on macOS ARM64)
- **4GB+ RAM** (8GB+ recommended for Stable Diffusion)
- **Internet connection** for model downloads and RSS feeds
- **Git** for cloning repositories
- **Build tools** (Xcode Command Line Tools on macOS, build-essential on Linux)

## Troubleshooting

### Common Issues

1. **Python Version:** Use Python 3.9 or later. Check with `python3 --version`
2. **Missing Build Tools:** Install Xcode Command Line Tools on macOS: `xcode-select --install`
3. **Whisper.cpp Compilation:** Ensure you have a C++ compiler and make installed
4. **Model Download:** Large models require stable internet connection
5. **Memory Issues:** Stable Diffusion requires significant RAM/VRAM

### Getting Help

1. Check the console output for detailed error messages
2. Ensure all dependencies are properly installed
3. Verify file paths in `config.py` match your setup
4. Run the setup script again if issues persist

---
*This README is a work in progress and will be updated as the project evolves.*
