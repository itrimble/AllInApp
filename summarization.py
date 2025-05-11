import torch
from transformers import pipeline
import config

def summarize_script(script):
    summarizer = pipeline("summarization", model=config.BART_MODEL, device=0 if torch.cuda.is_available() else -1)
    summary = summarizer(script, max_length=150, min_length=50, do_sample=False)[0]["summary_text"]
    return summary