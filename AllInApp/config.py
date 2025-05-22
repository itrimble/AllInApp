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

# Models paths (placeholders, actual model files will be in models/)
WHISPER_MODEL_PATH = os.path.join(MODELS_DIR, 'ggml-base.en.bin')

# Other configurations
PUBLIC_URL = os.getenv('PUBLIC_URL', 'http://localhost:8000/') # Default if not set in .env

# Ensure data and models directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
