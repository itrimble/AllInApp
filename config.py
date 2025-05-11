import os

# Constants and Paths
DATA_DIR = 'data'
MODELS_DIR = 'models'
PROCESSED_FILE = os.path.join(DATA_DIR, 'processed.json')
EPISODES_FILE = os.path.join(DATA_DIR, 'episodes.json')
RSS_FILE = 'podcast.xml'
PUBLIC_URL = 'http://:8000/'  # Replace with your actual public URL
WHISPER_MODEL = os.path.join(MODELS_DIR, 'ggml-base.en.bin')
TTS_MODEL_ADAM = 'path/to/tacotron2-DDC'  # Replace with actual path to Adam's TTS model
TTS_MODEL_JOHN = 'path/to/glow-tts'      # Replace with actual path to John's TTS model
STABLE_DIFFUSION_MODEL = 'CompVis/stable-diffusion-v1-4'
BART_MODEL = 'facebook/bart-large-cnn'
SENTENCE_TRANSFORMER_MODEL = 'BAAI/bge-small-en-v1.5'
RSS_FEED_URL = 'https://feeds.megaphone.fm/all-in'

# Ensure data directory exists
def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)