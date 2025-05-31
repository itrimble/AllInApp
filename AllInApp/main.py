import logging
import config # Import the configuration
from rss_feed import fetch_latest_episode
from audio_processing import process_audio
from transcription import transcribe_audio
from nlp_analysis import (
    load_nlp_pipeline, 
    extract_lessons, 
    load_sentence_model, 
    build_context
)
from show_art import load_diffusion_model, generate_show_art
import time

from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.console import Console

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
console = Console()

def run_pipeline():
    logger.info("===== Podcast Processing Pipeline (Rich UI) =====")

    progress_columns = [
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
        TimeElapsedColumn(),
    ]

    with Progress(*progress_columns, console=console, transient=False, refresh_per_second=10) as progress:
        pipeline_total_steps = 5
        pipeline_task_id = progress.add_task("[bold dodger_blue1]Overall Pipeline Progress", total=pipeline_total_steps, start=False)

        episode_title = "Unknown Episode"

        progress.start_task(pipeline_task_id)

        # --- Step 1: Fetch RSS Feed ---
        rss_task_id = progress.add_task("1. Fetching RSS Feed", total=1, start=False)
        audio_url, fetched_episode_title = None, None
        step_1_success = False
        try:
            progress.start_task(rss_task_id)
            logger.info("--- Step 1: Fetching RSS feed ---")
            audio_url, fetched_episode_title = fetch_latest_episode(config.RSS_FEED_URL, config.PROCESSED_JSON)

            if fetched_episode_title:
                episode_title = fetched_episode_title

            if not audio_url or not fetched_episode_title:
                logger.info("No new episodes found or error in fetching.")
                progress.update(rss_task_id, completed=1, description="[yellow]! 1. RSS Feed: No new episodes")
                progress.update(pipeline_task_id, completed=pipeline_total_steps, description=f"[bold yellow]Overall Progress (Pipeline Halted: No new episodes)")
                return
            logger.info(f"Successfully fetched new episode: '{episode_title}' from {audio_url}")
            progress.update(rss_task_id, completed=1, description=f"[green]✓ 1. RSS Feed Fetched: {episode_title[:30]}...")
            step_1_success = True
        except Exception as e:
            logger.exception(f"Critical error during RSS feed fetching. Error: {e}")
            progress.update(rss_task_id, completed=1, description="[red]✗ 1. RSS Feed: Critical Error")
            progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Pipeline Halted at RSS)")
            return
        finally:
            if not progress.tasks[rss_task_id].finished:
                 progress.update(rss_task_id, completed=1, description="[yellow]! 1. RSS Feed: Finalized with error/unknown")
            if step_1_success:
                progress.update(pipeline_task_id, advance=1)

        # --- Step 2: Process Audio ---
        audio_task_id = progress.add_task(f"2. Processing Audio: {episode_title[:20]}...", total=1, start=False)
        wav_file_path = None
        step_2_success = False
        try:
            progress.start_task(audio_task_id)
            logger.info(f"--- Step 2: Processing audio for '{episode_title}' ---")
            wav_file_path = process_audio(audio_url, config.LATEST_AUDIO_WAV)
            if not wav_file_path:
                logger.error(f"Audio processing failed for '{episode_title}'.")
                progress.update(audio_task_id, completed=1, description="[red]✗ 2. Audio Processing: Failed")
                progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Pipeline Halted at Audio Processing)")
                return
            logger.info(f"Successfully processed audio. WAV file saved to: {wav_file_path}")
            progress.update(audio_task_id, completed=1, description="[green]✓ 2. Audio Processing Complete")
            step_2_success = True
        except Exception as e:
            logger.exception(f"Critical error during audio processing for '{episode_title}'. Error: {e}")
            progress.update(audio_task_id, completed=1, description="[red]✗ 2. Audio Processing: Critical Error")
            progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Pipeline Halted at Audio Processing)")
            return
        finally:
            if not progress.tasks[audio_task_id].finished:
                progress.update(audio_task_id, completed=1, description="[yellow]! 2. Audio Processing: Finalized with error/unknown")
            if step_2_success:
                progress.update(pipeline_task_id, advance=1)

        # --- Step 3: Transcribe Audio ---
        transcribe_task_id = progress.add_task(f"3. Transcribing: {episode_title[:20]}...", total=1, start=False)
        transcript_path = None
        step_3_success = False
        if not hasattr(config, 'WHISPER_EXECUTABLE_PATH') or not config.WHISPER_EXECUTABLE_PATH or \
           not hasattr(config, 'WHISPER_MODEL_PATH') or not config.WHISPER_MODEL_PATH:
            logger.error("Whisper paths not configured in config.py.")
            progress.start_task(transcribe_task_id)
            progress.update(transcribe_task_id, completed=1, description="[red]✗ 3. Transcription: Whisper Misconfigured")
            progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Pipeline Halted: Transcription Misconfigured)")
            return
        try:
            progress.start_task(transcribe_task_id)
            logger.info(f"--- Step 3: Transcribing audio for '{episode_title}' ---")
            transcript_path = transcribe_audio(
                wav_file_path, config.TRANSCRIPT_TXT,
                config.WHISPER_EXECUTABLE_PATH, config.WHISPER_MODEL_PATH
            )
            if not transcript_path:
                logger.error(f"Audio transcription failed for '{episode_title}'.")
                progress.update(transcribe_task_id, completed=1, description="[red]✗ 3. Transcription: Failed")
                progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Pipeline Halted at Transcription)")
                return
            logger.info(f"Successfully transcribed audio. Transcript saved to: {transcript_path}")
            progress.update(transcribe_task_id, completed=1, description="[green]✓ 3. Transcription Complete")
            step_3_success = True
        except Exception as e:
            logger.exception(f"Critical error during audio transcription for '{episode_title}'. Error: {e}")
            progress.update(transcribe_task_id, completed=1, description="[red]✗ 3. Transcription: Critical Error")
            progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Pipeline Halted at Transcription)")
            return
        finally:
            if not progress.tasks[transcribe_task_id].finished:
                 progress.update(transcribe_task_id, completed=1, description="[yellow]! 3. Transcription: Finalized with error/unknown")
            if step_3_success:
                progress.update(pipeline_task_id, advance=1)

        # --- Step 4: NLP Analysis ---
        nlp_task_id = progress.add_task(f"4. NLP Analysis: {episode_title[:20]}...", total=1, start=False)
        step_4_success = False
        try:
            progress.start_task(nlp_task_id)
            logger.info(f"--- Step 4: Starting NLP Analysis for '{episode_title}' ---")

            transcript_text = ""
            if not transcript_path:
                logger.error("NLP Analysis: Transcript path is missing.")
                progress.update(nlp_task_id, completed=1, description="[red]✗ 4. NLP Analysis: Transcript Path Missing")
                progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Halted at NLP: Missing Transcript Path)")
                return

            logger.info(f"Reading transcript from: {transcript_path}")
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    transcript_text = f.read()
            except Exception as e:
                logger.exception(f"Failed to read transcript file {transcript_path}.")
                progress.update(nlp_task_id, completed=1, description="[red]✗ 4. NLP Analysis: Read Transcript Error")
                progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Halted at NLP Transcript Read)")
                return

            if not transcript_text.strip():
                logger.warning(f"Transcript file {transcript_path} is empty. Skipping NLP analysis.")
                progress.update(nlp_task_id, completed=1, description="[yellow]! 4. NLP Analysis: Empty Transcript")
                step_4_success = True
            else:
                logger.info("Loading NLP pipeline (spaCy, pytextrank)...")
                nlp = load_nlp_pipeline()
                if not nlp:
                    logger.error("Failed to load NLP pipeline.")
                    progress.update(nlp_task_id, completed=1, description="[red]✗ 4. NLP Analysis: Pipeline Load Fail")
                    progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Halted at NLP Load)")
                    return

                logger.info("Extracting lessons and keywords...")
                lessons, keywords = extract_lessons(transcript_text, nlp)
                logger.info(f"Extracted {len(lessons)} lessons, {len(keywords)} keywords.")

                logger.info("Loading sentence model...")
                sentence_model = load_sentence_model()
                if not sentence_model:
                    logger.error("Failed to load sentence model.")
                    progress.update(nlp_task_id, completed=1, description="[red]✗ 4. NLP Analysis: Sentence Model Fail")
                    progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Halted at Sentence Model)")
                    return

                if not hasattr(config, 'FAISS_INDEX_PATH') or not hasattr(config, 'PAST_LESSONS_PATH'):
                    logger.warning("FAISS_INDEX_PATH or PAST_LESSONS_PATH not defined in config.py. Skipping context building.")
                    if not progress.tasks[nlp_task_id].finished:
                         progress.update(nlp_task_id, description="[yellow]! 4. NLP Analysis: FAISS Config Missing (Context Skipped)")
                else:
                    logger.info("Building context from past lessons...")
                    related_context = build_context(lessons, sentence_model, config.FAISS_INDEX_PATH, config.PAST_LESSONS_PATH)
                    logger.info(f"Found {len(related_context)} related context items.")

                if not progress.tasks[nlp_task_id].finished :
                    progress.update(nlp_task_id, completed=1, description="[green]✓ 4. NLP Analysis Complete")
                step_4_success = True
        except Exception as e:
            logger.exception(f"Critical error during NLP Analysis for '{episode_title}'. Error: {e}")
            if not progress.tasks[nlp_task_id].finished:
                progress.update(nlp_task_id, completed=1, description="[red]✗ 4. NLP Analysis: Critical Error")
            progress.update(pipeline_task_id, completed=pipeline_total_steps, description="[bold red]Overall Progress (Halted at NLP)")
            return
        finally:
            if not progress.tasks[nlp_task_id].finished:
                progress.update(nlp_task_id, completed=1, description="[yellow]! 4. NLP Analysis: Finalized with error/unknown")
            if step_4_success:
                progress.update(pipeline_task_id, advance=1)

        # --- Step 5: Generate Show Art ---
        art_task_id = progress.add_task(f"5. Generating Show Art: {episode_title[:20]}...", total=1, start=False)
        step_5_success = False
        try:
            progress.start_task(art_task_id)
            logger.info(f"--- Step 5: Generating Show Art for '{episode_title}' ---")

            if not hasattr(config, 'SHOW_ART_JPG'):
                logger.warning("config.SHOW_ART_JPG not defined. Skipping show art generation.")
                progress.update(art_task_id, completed=1, description="[yellow]! 5. Show Art: Config Missing")
            elif not episode_title or episode_title == "Unknown Episode":
                logger.warning("Episode title not available or valid. Skipping show art generation.")
                progress.update(art_task_id, completed=1, description="[yellow]! 5. Show Art: No Title for Prompt")
            else:
                logger.info("Loading Stable Diffusion model for show art generation...")
                diffusion_model = load_diffusion_model()
                if not diffusion_model:
                    logger.error("Failed to load Stable Diffusion model. Skipping show art generation.")
                    progress.update(art_task_id, completed=1, description="[yellow]! 5. Show Art: Model Load Fail")
                else:
                    prompt = f"Podcast show art for an episode titled: '{episode_title}'. Style: vibrant, abstract, tech-themed, digital art."
                    logger.info(f"Using prompt for show art: {prompt}")
                    logger.info("Generating show art...")
                    show_art_path = generate_show_art(prompt, config.SHOW_ART_JPG, diffusion_model)
                    if show_art_path:
                        logger.info(f"Show art generated and saved to: {show_art_path}")
                        progress.update(art_task_id, completed=1, description="[green]✓ 5. Show Art Generated")
                    else:
                        logger.error("Failed to generate show art.")
                        progress.update(art_task_id, completed=1, description="[red]✗ 5. Show Art: Generation Failed")

            if not progress.tasks[art_task_id].finished:
                 progress.update(art_task_id, completed=1, description="[yellow]! 5. Show Art: Skipped/Not Generated")
            step_5_success = True
        except Exception as e:
            logger.exception(f"Critical error during Show Art Generation for '{episode_title}'. Error: {e}")
            if not progress.tasks[art_task_id].finished:
                progress.update(art_task_id, completed=1, description="[red]✗ 5. Show Art: Critical Error")
        finally:
            if not progress.tasks[art_task_id].finished:
                progress.update(art_task_id, completed=1, description="[yellow]! 5. Show Art: Finalized with error/unknown")
            if step_5_success:
                progress.update(pipeline_task_id, advance=1)
        
        current_overall_completed = progress.tasks[pipeline_task_id].completed
        if not progress.tasks[pipeline_task_id].finished:
            if current_overall_completed == pipeline_total_steps:
                all_steps_ok = True
                for task_idx in range(1, len(progress.tasks)):
                    task = progress.tasks[task_idx]
                    if task.description.startswith("[red]"):
                        all_steps_ok = False
                        break
                if all_steps_ok:
                    progress.update(pipeline_task_id, description="[bold green]✓ Overall Pipeline Completed Successfully!")
                else:
                    progress.update(pipeline_task_id, description="[bold yellow]! Overall Pipeline Completed with some issues/failures.")
            else:
                 progress.update(pipeline_task_id, description=f"[bold red]✗ Overall Pipeline Halted Early (completed {current_overall_completed}/{pipeline_total_steps} steps).")

        logger.info(f"===== Pipeline Run Finished for Episode: '{episode_title}' =====")
        console.print("\nPipeline processing finished. Review output above.", style="bold blue")

if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        console.print("\n[bold orange_red1]Pipeline interrupted by user. Exiting.[/bold orange_red1]")
    except Exception as e:
        logger.critical(f"Unhandled critical error at top level: {e}", exc_info=True)
        console.print(f"[bold red]FATAL ERROR: {e}[/bold red]")
