from gtts import gTTS
import os

def generate_tts(text: str, output_path: str, language: str = 'en'):
    """
    Generates speech from text using gTTS and saves it to an audio file.

    Args:
        text (str): The text to convert to speech.
        output_path (str): The path to save the generated audio file (e.g., 'output.mp3').
        language (str, optional): The language of the text. Defaults to 'en' (English).
    """
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_path)
        print(f"Audio content written to file '{output_path}'")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    # Example usage:
    sample_text = "Hello, this is a test of the text-to-speech function."
    output_file = "output.mp3"
    
    # Create a directory for testing if it doesn't exist
    test_output_dir = "test_audio_output"
    if not os.path.exists(test_output_dir):
        os.makedirs(test_output_dir)
    
    output_file_path = os.path.join(test_output_dir, output_file)

    generate_tts(sample_text, output_file_path)

    # Example with a different language (e.g., Spanish)
    sample_text_es = "Hola, esta es una prueba de la función de texto a voz."
    output_file_es = "output_es.mp3"
    output_file_path_es = os.path.join(test_output_dir, output_file_es)
    generate_tts(sample_text_es, output_file_path_es, language='es')
