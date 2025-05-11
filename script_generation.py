import torch
from transformers import pipeline
import config

def generate_script_and_title(lessons, related_lessons):
    generator = pipeline("text-generation", model="EleutherAI/gpt-neo-1.3B", device=0 if torch.cuda.is_available() else -1)
    prompt = (
        f"Create a podcast script in the style of Adam Curry and John C. Dvorak discussing these lessons: {lessons}. "
        f"Include witty banter, a subtle mystery element, and distinct personalities for each host. "
        f"End with a cliffhanger or intriguing question. Reference past discussions: {related_lessons}."
    )
    script = generator(prompt, max_length=500, num_return_sequences=1)[0]["generated_text"]
    title_prompt = f"Generate a catchy title for a podcast episode discussing these lessons: {lessons}"
    title = generator(title_prompt, max_length=50, num_return_sequences=1)[0]["generated_text"].strip().split('\n')[0]
    return script, title