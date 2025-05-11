import os
import spacy
import pytextrank
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

class NLPAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.add_pipe("textrank")
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        self.past_embeddings_file = os.path.join(data_dir, 'past_embeddings.npy')
        self.past_lessons_file = os.path.join(data_dir, 'past_lessons.txt')

    def extract_lessons_and_keywords(self, transcript):
        doc = self.nlp(transcript)
        lessons = [phrase.text for phrase in doc._.textrank.summary(limit_sentences=5)]
        keywords = [phrase.text for phrase in doc._.phrases[:5]]
        return lessons, keywords

    def build_context(self, lessons):
        embeddings = self.model.encode(lessons)
        if os.path.exists(self.past_embeddings_file):
            past_embeddings = np.load(self.past_embeddings_file)
            index = faiss.IndexFlatL2(past_embeddings.shape[1])
            index.add(past_embeddings)
            D, I = index.search(embeddings, k=3)
            with open(self.past_lessons_file, 'r') as f:
                past_lessons = f.read().splitlines()
            related_lessons = [past_lessons[i] for i in I[0] if i < len(past_lessons)]
        else:
            related_lessons = []
        with open(self.past_lessons_file, 'a') as f:
            f.write("\n".join(lessons) + "\n")
        if 'past_embeddings' in locals():
            np.save(self.past_embeddings_file, np.vstack([past_embeddings, embeddings]))
        else:
            np.save(self.past_embeddings_file, embeddings)
        return related_lessons