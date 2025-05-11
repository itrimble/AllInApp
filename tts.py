import os
import numpy as np
import soundfile as sf
from TTS.utils.synthesizer import Synthesizer
import config

def script_to_audio(script):
    synth1 = Synthesizer(config.TTS_MODEL_ADAM)  # Adam's voice
    synth2 = Synthesizer(config.TTS_MODEL_JOHN)  # John's voice
    lines = script.split('\n')
    audio_parts = []
    for line in lines:
        if line.startswith("Adam:"):
            wav = synth1.tts(line.replace("Adam:", "").strip())
        elif line.startswith("John:"):
            wav = synth2.tts(line.replace("John:", "").strip())
        else:
            continue
        if wav:
            audio_parts.append(wav)
    full_audio = np.concatenate(audio_parts)
    audio_file = os.path.join(config.DATA_DIR, 'episode.wav')
    sf.write(audio_file, full_audio, samplerate=22050)
    return audio_file