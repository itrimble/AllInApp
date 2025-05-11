import config
from rss_feed import fetch_latest_episode, mark_as_processed
from audio_processing import download_audio
from transcription import transcribe_audio
from nlp_analysis import NLPAnalyzer
from script_generation import generate_script_and_title
from tts import script_to_audio
from show_art import generate_show_art
from summarization import summarize_script
from file_management import get_next_episode_number, save_episode_files, update_episodes_json, generate_rss_feed

def main():
    # Initialize NLPAnalyzer with data directory
    nlp_analyzer = NLPAnalyzer(config.DATA_DIR)
    
    # Fetch the latest episode
    latest_episode = fetch_latest_episode()
    if latest_episode is None:
        return
    
    try:
        # Download and process audio
        audio_file = download_audio(latest_episode)
        transcript = transcribe_audio(audio_file)
        
        # Extract lessons and keywords
        lessons, keywords = nlp_analyzer.extract_lessons_and_keywords(transcript)
        
        # Build context from past lessons
        related_lessons = nlp_analyzer.build_context(lessons)
        
        # Generate script and title
        script, title = generate_script_and_title(lessons, related_lessons)
        
        # Convert script to audio
        audio_file = script_to_audio(script)
        
        # Generate show art
        art_file = generate_show_art(keywords)
        
        # Summarize script for show notes
        show_notes = summarize_script(script)
        
        # Manage episode files and data
        episode_number = get_next_episode_number()
        audio_file, art_file = save_episode_files(episode_number, audio_file, art_file)
        update_episodes_json(episode_number, title, audio_file, art_file, show_notes)
        generate_rss_feed()
        
        # Mark the episode as processed
        mark_as_processed(latest_episode.guid)
        
        print(f"Episode {episode_number}: '{title}' generated successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()