import os
import requests
from pydub import AudioSegment
import config

def download_audio(episode):
    audio_url = episode.enclosures[0].href
    mp3_file = os.path.join(config.DATA_DIR, 'latest.mp3')
    response = requests.get(audio_url)
    with open(mp3_file, 'wb') as f:
        f.write(response.content)
    wav_file = os.path.join(config.DATA_DIR, 'latest.wav')
    audio = AudioSegment.from_mp3(mp3_file)
    audio.export(wav_file, format='wav')
    return wav_file