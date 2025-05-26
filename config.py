import os

# Project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data and Models directories
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# RSS Feed URL
RSS_FEED_URL = "https://feeds.megaphone.fm/all-in"

# Reference audio files (placeholders, actual files will be in data/)
ADAM_REFERENCE_AUDIO = os.path.join(DATA_DIR, 'adam_reference.wav')
JOHN_REFERENCE_AUDIO = os.path.join(DATA_DIR, 'john_reference.wav')

# Output file paths (placeholders)
LATEST_AUDIO_WAV = os.path.join(DATA_DIR, 'latest.wav')
TRANSCRIPT_TXT = os.path.join(DATA_DIR, 'transcript.txt')
PAST_EMBEDDINGS_NPY = os.path.join(DATA_DIR, 'past_embeddings.npy')
EPISODE_AUDIO_WAV = os.path.join(DATA_DIR, 'episode.wav')
SHOW_ART_JPG = os.path.join(DATA_DIR, 'show_art.jpg')
EPISODES_JSON = os.path.join(DATA_DIR, 'episodes.json')
PROCESSED_JSON = os.path.join(DATA_DIR, 'processed.json') # To track processed episodes

# FAISS index and past lessons store for NLP context building
FAISS_INDEX_PATH = os.path.join(DATA_DIR, 'faiss_index.bin')
PAST_LESSONS_PATH = os.path.join(DATA_DIR, 'past_lessons.json')

# Models paths (placeholders, actual model files will be in models/)
WHISPER_MODEL_PATH = os.path.join(MODELS_DIR, 'ggml-base.en.bin')

# Path to the compiled whisper.cpp main executable
# Assumes whisper.cpp compiled 'main' is in AllInApp/whisper.cpp/main
WHISPER_CPP_DIR = os.path.join(BASE_DIR, 'whisper.cpp')
WHISPER_EXECUTABLE_PATH = os.path.join(WHISPER_CPP_DIR, 'main')

# Stable Diffusion settings
STABLE_DIFFUSION_MODEL_ID = "CompVis/stable-diffusion-v1-4"
# For other potential models, see Hugging Face Hub, e.g.:
# STABLE_DIFFUSION_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
# STABLE_DIFFUSION_MODEL_ID = "runwayml/stable-diffusion-v1-5"

# Other configurations
PUBLIC_URL = os.getenv('PUBLIC_URL', 'http://localhost:8000/') # Default if not set in .env

# Ensure data and models directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
