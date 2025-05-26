import spacy
import pytextrank # Though not directly called, it's good for clarity and registers the pipe
import logging
from sentence_transformers import SentenceTransformer
import faiss # To be used for indexing in later steps
import numpy
import json
import os

# Configure logger for this module
logger = logging.getLogger(__name__)

# Global variables to hold loaded models
NLP_PIPELINE = None
SENTENCE_MODEL = None

def load_nlp_pipeline():
    """
    Loads the spaCy model and adds the pytextrank pipeline component.

    Returns:
        The spaCy nlp object with pytextrank added, or None if loading fails.
    """
    global NLP_PIPELINE
    if NLP_PIPELINE is not None:
        return NLP_PIPELINE

    try:
        # Load the spaCy model
        nlp = spacy.load("en_core_web_sm")
        logger.info("Successfully loaded spaCy model 'en_core_web_sm'.")

        # Add pytextrank to the pipeline
        # Check if "textrank" is already in the pipe to avoid adding it multiple times if this func is called again
        if "textrank" not in nlp.pipe_names:
            nlp.add_pipe("textrank")
            logger.info("Added 'textrank' to spaCy pipeline.")
        else:
            logger.info("'textrank' already in spaCy pipeline.")
        
        NLP_PIPELINE = nlp
        logger.info("spaCy pipeline with pytextrank initialized successfully.")
        return NLP_PIPELINE
    except OSError as e:
        logger.error("Failed to load spaCy model 'en_core_web_sm'. This is likely because the model is not downloaded.")
        logger.error("Please download it by running: python -m spacy download en_core_web_sm")
        logger.exception(f"Underlying OSError: {e}") # Log the actual OS error for more details
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred while loading the NLP pipeline: {e}")
        return None

def extract_lessons(transcript_text: str, nlp_pipeline) -> tuple[list[str], list[str]]:
    """
    Extracts key phrases (lessons) and relevant keywords from a transcript using pytextrank.

    Args:
        transcript_text: The input text of the podcast transcript.
        nlp_pipeline: The loaded spaCy pipeline with pytextrank.

    Returns:
        A tuple containing two lists: 
        1.  list_of_lesson_strings: Top N key phrases (lessons).
        2.  list_of_keyword_strings: Unique keywords derived from these lessons.
    """
    if not nlp_pipeline:
        logger.error("NLP pipeline is not loaded. Cannot extract lessons.")
        return [], []
    if not transcript_text:
        logger.warning("Transcript text is empty. Returning empty lessons and keywords.")
        return [], []

    logger.info("Processing transcript to extract lessons and keywords...")
    doc = nlp_pipeline(transcript_text)

    if not doc._.phrases:
        logger.warning("No phrases extracted by pytextrank. Returning empty lessons and keywords.")
        return [], []

    # Extract Lessons (Key Phrases)
    # Sort phrases by rank in descending order and take top N (e.g., 15)
    sorted_phrases = sorted(doc._.phrases, key=lambda p: p.rank, reverse=True)
    top_n_lessons = 15
    extracted_lessons_text = [phrase.text for phrase in sorted_phrases[:top_n_lessons]]
    logger.info(f"Extracted {len(extracted_lessons_text)} lessons (top {top_n_lessons} phrases).")

    # Extract Keywords from these top lessons
    keywords = set()
    max_keywords = 30 # Target maximum number of unique keywords

    for phrase_text in extracted_lessons_text:
        # Re-process the lesson text with the same pipeline to get tokens if not directly available
        # or iterate through phrase.chunks if TextRankPhrase gives direct access to its constituent tokens
        # (doc._.phrases are TextRankPhrase objects, each has .chunks which are spaCy Spans)
        
        # Find the original phrase object to access its chunks
        # This is a bit inefficient; if performance is critical, optimize
        original_phrase_obj = next((p for p in doc._.phrases if p.text == phrase_text), None)
        if not original_phrase_obj:
            continue

        for chunk in original_phrase_obj.chunks: # chunk is a spaCy Span
            for token in chunk:
                if not token.is_stop and not token.is_punct and token.lemma_:
                    keywords.add(token.lemma_.lower())
        
        if len(keywords) >= max_keywords: # Stop if we have enough keywords
            break 
            
    # Ensure we don't exceed max_keywords if the loop finished before break
    final_keywords = list(keywords)[:max_keywords] 
    logger.info(f"Extracted {len(final_keywords)} unique keywords from lessons.")

    return extracted_lessons_text, final_keywords

def load_sentence_model():
    """
    Loads the SentenceTransformer model.

    Returns:
        The SentenceTransformer model object, or None if loading fails.
    """
    global SENTENCE_MODEL
    if SENTENCE_MODEL is not None:
        logger.info("SentenceTransformer model already loaded.")
        return SENTENCE_MODEL

    model_name = 'all-MiniLM-L6-v2'
    try:
        logger.info(f"Loading SentenceTransformer model: {model_name}...")
        SENTENCE_MODEL = SentenceTransformer(model_name)
        logger.info(f"SentenceTransformer model '{model_name}' loaded successfully.")
        return SENTENCE_MODEL
    except Exception as e:
        logger.exception(f"An error occurred while loading SentenceTransformer model '{model_name}': {e}")
        # This could be due to network issues if downloading, or other Hugging Face Hub/cache problems.
        return None

def build_context(current_lessons_text: list[str], sentence_model, faiss_index_path: str, past_lessons_json_path: str, top_k_similar: int = 3) -> list[str]:
    """
    Builds context by finding past lessons related to current lessons using FAISS.
    Updates the FAISS index and past lessons store with the current lessons.

    Args:
        current_lessons_text: A list of new lesson strings to find context for and add to the store.
        sentence_model: The loaded SentenceTransformer model.
        faiss_index_path: Path to the FAISS index file.
        past_lessons_json_path: Path to the JSON file storing past lesson strings.
        top_k_similar: Number of similar past lessons to retrieve for context.

    Returns:
        A list of related past lesson strings for context.
    """
    if not sentence_model:
        logger.error("Sentence model is not loaded. Cannot build context.")
        return []

    embedding_dimension = sentence_model.get_sentence_embedding_dimension()
    index = None
    past_lessons_data = []

    try:
        if os.path.exists(faiss_index_path) and os.path.exists(past_lessons_json_path):
            logger.info(f"Loading existing FAISS index from {faiss_index_path} and lessons from {past_lessons_json_path}")
            index = faiss.read_index(faiss_index_path)
            with open(past_lessons_json_path, 'r') as f:
                past_lessons_data = json.load(f)
            # Sanity check for dimension mismatch
            if index.d != embedding_dimension:
                logger.warning(f"FAISS index dimension ({index.d}) mismatch with model dimension ({embedding_dimension}). Re-initializing index.")
                index = faiss.IndexFlatL2(embedding_dimension)
                past_lessons_data = [] # Data associated with old index is no longer valid
        else:
            logger.info("No existing FAISS index or lessons file found. Creating new ones.")
            index = faiss.IndexFlatL2(embedding_dimension)
            past_lessons_data = []
    except Exception as e:
        logger.exception(f"Error loading FAISS index or past lessons. Re-initializing. Error: {e}")
        index = faiss.IndexFlatL2(embedding_dimension) # Fallback to new index
        past_lessons_data = []


    related_context_lessons_set = set() # Use a set to ensure uniqueness initially

    if current_lessons_text and index.ntotal > 0:
        logger.info(f"Finding related context for {len(current_lessons_text)} new lessons from {index.ntotal} past lessons.")
        try:
            # Encode all current lessons once
            current_lesson_embeddings = sentence_model.encode(current_lessons_text)
            
            # Search for similar past lessons for each current lesson
            # FAISS search works on a batch of vectors
            # D: distances, I: indices
            D, I = index.search(numpy.array(current_lesson_embeddings).astype(numpy.float32), k=top_k_similar)

            for i in range(len(current_lessons_text)): # For each current lesson's search result
                for j, idx in enumerate(I[i]): # For each similar item found for current_lessons_text[i]
                    if idx != -1: # FAISS returns -1 if fewer than k items exist or for padding
                        # Ensure the found index is valid for past_lessons_data
                        if 0 <= idx < len(past_lessons_data):
                             # Check if the found lesson is not one of the current_lessons_text (if they were already added in a previous run)
                            if past_lessons_data[idx] not in current_lessons_text:
                                related_context_lessons_set.add(past_lessons_data[idx])
                        else:
                            logger.warning(f"FAISS returned index {idx} which is out of bounds for past_lessons_data (size {len(past_lessons_data)}). Skipping.")
            
            logger.info(f"Found {len(related_context_lessons_set)} unique related past lessons for context.")
        except Exception as e:
            logger.exception(f"Error during FAISS search: {e}")
    elif not current_lessons_text:
        logger.info("No current lessons provided to find context for.")
    else: # index.ntotal == 0
        logger.info("FAISS index is empty. No past lessons to search for context.")

    # Update FAISS Index and Past Lessons Store with current_lessons_text
    if current_lessons_text:
        logger.info(f"Updating FAISS index and lesson store with {len(current_lessons_text)} new lessons.")
        try:
            new_embeddings_to_add = sentence_model.encode(current_lessons_text)
            index.add(numpy.array(new_embeddings_to_add).astype(numpy.float32))
            past_lessons_data.extend(current_lessons_text) # Add new lessons to the list

            # Ensure directories exist before writing
            faiss_dir = os.path.dirname(faiss_index_path)
            json_dir = os.path.dirname(past_lessons_json_path)
            if faiss_dir: os.makedirs(faiss_dir, exist_ok=True)
            if json_dir: os.makedirs(json_dir, exist_ok=True)

            faiss.write_index(index, faiss_index_path)
            with open(past_lessons_json_path, 'w') as f:
                json.dump(past_lessons_data, f, indent=2)
            logger.info(f"FAISS index saved to {faiss_index_path} (new total: {index.ntotal}). Past lessons saved to {past_lessons_json_path}.")
        except Exception as e:
            logger.exception(f"Error updating FAISS index or past lessons store: {e}")
            # Note: If this fails, past_lessons_data might be extended in memory but not saved.
            # Consider transactional saving or more complex error recovery if critical.

    return list(related_context_lessons_set) # Return unique lessons


if __name__ == '__main__':
    # Configure basic logging for direct script execution/testing
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("--- Testing NLP Pipeline Initialization ---")
    nlp_pipeline_instance = load_nlp_pipeline()
    lessons = [] # Initialize lessons here to ensure it's available

    if nlp_pipeline_instance:
        logger.info("NLP pipeline loaded successfully for testing.")
        
        pytextrank_test_text = (
            "This is a sample text for pytextrank. It mentions several important concepts and ideas. "
            "Artificial intelligence is a key topic. Machine learning provides the foundation for many AI systems. "
            "Natural Language Processing allows machines to understand human language."
        )
        logger.info(f"PyTextRank Test text: \"{pytextrank_test_text}\"")
        doc_pytextrank = nlp_pipeline_instance(pytextrank_test_text)
        if doc_pytextrank._.phrases:
            logger.info(f"Extracted PyTextRank test phrases (top 3): {[phrase.text for phrase in doc_pytextrank._.phrases[:3]]}")
        else:
            logger.warning("No phrases extracted in the pytextrank test.")
        
        logger.info("--- Attempting to load NLP pipeline again (should use cached) ---")
        nlp_pipeline_instance_2 = load_nlp_pipeline()
        if nlp_pipeline_instance_2:
            logger.info("Second load attempt for NLP pipeline successful.")
        else:
            logger.error("Second load attempt for NLP pipeline failed.")

        logger.info("--- Testing extract_lessons ---")
        sample_transcript = (
            "Welcome to the All-In Podcast, episode 123. Today, we dive deep into the future of AI. "
            "Generative models are transforming content creation. We'll discuss large language models like GPT-3 and their impact. "
            "Another key topic is the ethical implications of AI. Bias in AI is a significant concern."
        )
        lessons, keywords = extract_lessons(sample_transcript, nlp_pipeline_instance) # Assign to outer scope lessons
        logger.info(f"Extracted {len(lessons)} lessons: {lessons}")
        logger.info(f"Extracted {len(keywords)} keywords: {keywords}")
            
    else:
        logger.error("NLP pipeline loading failed during testing. See previous errors for details.")

    logger.info("--- Testing SentenceTransformer Model Loading ---")
    sentence_model_instance = load_sentence_model() # Renamed to avoid conflict
    if sentence_model_instance:
        logger.info("SentenceTransformer model loaded successfully for testing.")
        try:
            sample_embedding = sentence_model_instance.encode(["This is a test sentence."])
            if sample_embedding is not None and len(sample_embedding) > 0:
                 logger.info(f"Sample embedding dimension: {len(sample_embedding[0])}")
            else:
                logger.warning("Sample embedding generation returned None or empty.")
        except Exception as e:
            logger.exception(f"Error during sample sentence encoding: {e}")
        
        logger.info("--- Attempting to load SentenceTransformer model again (should use cached) ---")
        sentence_model_instance_2 = load_sentence_model()
        if sentence_model_instance_2:
            logger.info("Second load attempt for SentenceTransformer model successful.")
        else:
            logger.error("Second load attempt for SentenceTransformer model failed.")

        # Test build_context
        if lessons: # Check if lessons were extracted
            TEST_DATA_DIR = "test_data_nlp" # More specific dir for these test files
            TEST_FAISS_PATH = os.path.join(TEST_DATA_DIR, "test_faiss.index")
            TEST_PAST_LESSONS_PATH = os.path.join(TEST_DATA_DIR, "test_past_lessons.json")

            if not os.path.exists(TEST_DATA_DIR):
                os.makedirs(TEST_DATA_DIR)
            
            if os.path.exists(TEST_FAISS_PATH): os.remove(TEST_FAISS_PATH)
            if os.path.exists(TEST_PAST_LESSONS_PATH): os.remove(TEST_PAST_LESSONS_PATH)

            logger.info("--- Test Run 1: Building context (initial) ---")
            # Use a subset of extracted lessons or define new ones for clarity
            initial_lessons_for_context = lessons[:2] if lessons else ["AI is transformative.", "Machine learning is key."] 
            if not initial_lessons_for_context: initial_lessons_for_context = ["Fallback initial lesson if extract_lessons was empty"]
            
            context1 = build_context(initial_lessons_for_context, sentence_model_instance, TEST_FAISS_PATH, TEST_PAST_LESSONS_PATH)
            logger.info(f"Initial context found: {context1} (should be empty as index was just created)")
            
            # Check FAISS index size after first run
            if os.path.exists(TEST_FAISS_PATH):
                try:
                    index_run1 = faiss.read_index(TEST_FAISS_PATH)
                    logger.info(f"FAISS index size after run 1: {index_run1.ntotal}")
                except Exception as e_faiss:
                    logger.exception(f"Error reading FAISS index after run 1: {e_faiss}")
            else:
                logger.warning(f"FAISS index file {TEST_FAISS_PATH} not found after run 1.")


            logger.info("--- Test Run 2: Building context (with existing index) ---")
            new_lessons_for_context = ["Generative AI is new.", "AI ethics are important.", "Machine learning models need data."]
            context2 = build_context(new_lessons_for_context, sentence_model_instance, TEST_FAISS_PATH, TEST_PAST_LESSONS_PATH)
            logger.info(f"Context found for new lessons: {context2}")
            
            if os.path.exists(TEST_FAISS_PATH):
                try:
                    index_run2 = faiss.read_index(TEST_FAISS_PATH)
                    logger.info(f"FAISS index size after run 2: {index_run2.ntotal}")
                except Exception as e_faiss:
                    logger.exception(f"Error reading FAISS index after run 2: {e_faiss}")
            else:
                logger.warning(f"FAISS index file {TEST_FAISS_PATH} not found after run 2.")

            if os.path.exists(TEST_PAST_LESSONS_PATH):
                try:
                    with open(TEST_PAST_LESSONS_PATH, 'r') as f:
                        logger.info(f"Contents of {TEST_PAST_LESSONS_PATH} after run 2: {json.load(f)}")
                except Exception as e_json:
                     logger.exception(f"Error reading past lessons JSON {TEST_PAST_LESSONS_PATH}: {e_json}")
            else:
                logger.warning(f"Past lessons JSON file {TEST_PAST_LESSONS_PATH} not found after run 2.")
        else:
            logger.warning("Skipping build_context test as no lessons were extracted earlier.")
            
    else: # sentence_model_instance failed to load
        logger.error("SentenceTransformer model loading failed during testing. See previous errors for details.")
