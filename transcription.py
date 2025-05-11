import os
import subprocess
import config

def transcribe_audio(audio_file):
    transcript_file = os.path.join(config.DATA_DIR, 'transcript.txt')
    cmd = f"./whisper.cpp/main -f {audio_file} -m {config.WHISPER_MODEL} -o {transcript_file}"
    subprocess.run(cmd, shell=True, check=True)
    with open(transcript_file, 'r') as f:
        transcript = f.read()
    return transcript