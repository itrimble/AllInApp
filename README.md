# All In Podcast App - Modular Version

The All In Podcast App is a Python application that generates podcast episodes based on the latest episode of the ["All-In" podcast](https://feeds.megaphone.fm/all-in). It automates fetching episodes, transcribing audio, extracting lessons, generating scripts with AI, converting scripts to audio using voice cloning, creating show art, and producing an RSS feed. The modular design separates functionality into distinct modules, enhancing maintainability, testability, and scalability.

## Features

- Fetches the latest "All-In" episode via RSS.
- Downloads and converts audio to WAV using [pydub](https://github.com/jiaaro/pydub).
- Transcribes audio with [Whisper.cpp](https://github.com/ggerganov/whisper.cpp).
- Extracts lessons and keywords using [spaCy](https://spacy.io/) and [pytextrank](https://github.com/DerwenAI/pytextrank).
- Builds context from past lessons with [sentence-transformers](https://www.sbert.net/) and [FAISS](https://github.com/facebookresearch/faiss).
- Generates scripts and titles using GPT-Neo from [transformers](https://huggingface.co/docs/transformers/index).
- Converts scripts to audio with [Coqui TTS](https://coqui.ai/docs/) using voice cloning.
- Creates show art with [Stable Diffusion](https://huggingface.co/CompVis/stable-diffusion-v1-4).
- Summarizes scripts for show notes with BART.
- Manages episode files and generates an RSS feed with [feedgen](https://github.com/lkiesow/python-feedgen).

## Project Structure

- `main.py`: Orchestrates the podcast generation process.
- `config.py`: Stores configuration settings and constants.
- `rss_feed.py`: Fetches and processes the RSS feed.
- `audio_processing.py`: Downloads and converts audio files.
- `transcription.py`: Transcribes audio using Whisper.cpp.
- `nlp_analysis.py`: Extracts lessons and keywords using NLP.
- `script_generation.py`: Generates podcast script and title.
- `tts.py`: Converts script to audio using voice cloning.
- `show_art.py`: Generates show art using Stable Diffusion.
- `summarization.py`: Summarizes script for show notes.
- `file_management.py`: Manages episode files and RSS feed.
- `requirements.txt`: Lists Python dependencies.
- `.env`: Environment variables (e.g., `PUBLIC_URL`, `RSS_FEED_URL`).
- `.gitignore`: Excludes temporary and large files.
- `data/`: Stores generated files (ignored in Git).
- `models/`: Stores model files (ignored in Git).

## Prerequisites

- **Python 3.8+**: Install from [Python Downloads](https://www.python.org/downloads/).
- **FFmpeg**: Install via `brew install ffmpeg` (macOS), `sudo apt-get install ffmpeg` (Ubuntu), or download from [FFmpeg](https://ffmpeg.org/download.html).
- **Whisper.cpp**: For audio transcription, available at [Whisper.cpp GitHub](https://github.com/ggerganov/whisper.cpp).
- **Reference Audio**: Clean WAV files of Adam Curry and John C. Dvorak (e.g., extracted from [No Agenda Show](https://www.noagendashow.net/) using [Audacity](https://www.audacityteam.org/)).
- **Internet Connection**: Required for downloading models and accessing the RSS feed.
- **Hardware**: GPU (NVIDIA or Apple Silicon) recommended for faster model processing; CPU supported but slower. Minimum 16GB RAM.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/all-in-podcast-app.git
   cd all-in-podcast-app
   ```
   *Replace `yourusername` with the actual repository owner.*

2. **Set Up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   For GPU support (NVIDIA), install a CUDA-compatible PyTorch version:
   ```bash
   pip install torch==2.1.1 --index-url https://download.pytorch.org/whl/cu121
   ```

4. **Install spaCy Model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Set Up Whisper.cpp**:
   - Clone and build:
     ```bash
     git clone https://github.com/ggerganov/whisper.cpp.git
     cd whisper.cpp
     make
     ```
   - Download model:
     ```bash
     ./models/download-ggml-model.sh base.en
     ```
   - Move to project:
     ```bash
     mv main ../all-in-podcast-app/whisper.cpp/main
     mv models/ggml-base.en.bin ../all-in-podcast-app/models/
     cd ../all-in-podcast-app
     ```

6. **Prepare Reference Audio**:
   - Obtain 10-30 second WAV clips of Adam Curry and John C. Dvorak (e.g., from "No Agenda" episodes).
   - Use [Audacity](https://www.audacityteam.org/) to extract clean audio segments.
   - Place in `data/` as `adam_reference.wav` and `john_reference.wav`.

7. **Configure Environment**:
   - Copy `.env.example` to `.env` (or create `.env`):
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` to set:
     ```
     PUBLIC_URL=http://yourserver.com/
     RSS_FEED_URL=https://feeds.megaphone.fm/all-in
     ```

8. **Create Directories**:
   ```bash
   mkdir -p data models
   ```

## Usage

Run the main script to generate a podcast episode:
```bash
python main.py
```

### What It Does

- Fetches the latest "All-In" episode from the RSS feed.
- Downloads and converts audio to WAV.
- Transcribes audio using Whisper.cpp.
- Extracts lessons and keywords with spaCy and pytextrank.
- Builds context from past lessons using sentence embeddings and FAISS.
- Generates a script and title with GPT-Neo.
- Converts the script to audio using Coqui TTS with voice cloning.
- Creates show art with Stable Diffusion.
- Summarizes the script for show notes with BART.
- Saves episode files and updates an RSS feed.

### Output

- **Episode Files**: Audio (`episode_N.wav`) and art (`show_art_N.jpg`) in `data/`.
- **Metadata**: Episode details in `data/episodes.json`.
- **RSS Feed**: Generated at `podcast.xml`.

Host files at `PUBLIC_URL` to make the podcast accessible via a podcast client.

## Troubleshooting

- **Dependency Errors**: Reinstall dependencies:
  ```bash
  pip install -r requirements.txt --force-reinstall
  ```
- **Whisper.cpp Issues**: Ensure `whisper.cpp/main` is executable (`chmod +x whisper.cpp/main`) and `ggml-base.en.bin` is in `models/`.
- **Missing Audio Files**: Verify `adam_reference.wav` and `john_reference.wav` are in `data/`.
- **Slow Performance**: Use a GPU-enabled machine or reduce model sizes (e.g., use a smaller GPT-Neo model).
- **Model Download Fails**: Check internet connectivity and disk space (~10GB needed for models).
- **RSS Feed Errors**: Verify `RSS_FEED_URL` in `.env` and ensure the feed is accessible.

## Notes

- **Performance**: A GPU (NVIDIA or Apple Silicon) significantly speeds up model processing (e.g., Stable Diffusion, TTS). CPU execution is slower but functional.
- **Legal Considerations**: Generating audio mimicking real individuals (e.g., Adam Curry, John C. Dvorak) may raise legal or ethical concerns. Consult legal experts before public distribution and label content as synthetic or parody if shared.
- **Model Downloads**: Models like Stable Diffusion, BART, and XTTS download automatically on first run, requiring an internet connection.
- **File Formats**: Outputs WAV audio for simplicity. To use MP3, modify `tts.py` and `file_management.py` to support MP3 encoding with FFmpeg.
- **Periodic Execution**: Schedule the app with a cron job for regular episode checks:
  ```bash
  0 0 * * * /path/to/venv/bin/python /path/to/all-in-podcast-app/main.py
  ```

## Testing

Test the app by running `main.py` with a known episode. Verify:
- Output files in `data/` (`episode_N.wav`, `show_art_N.jpg`).
- Metadata in `data/episodes.json`.
- RSS feed (`podcast.xml`) compatibility with a podcast client.

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit changes (`git commit -m 'Add YourFeature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

Please include tests and update documentation as needed.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or support, contact the repository maintainers or open an issue on GitHub.

---

*Generated on May 11, 2025*