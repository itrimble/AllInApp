import os
import torch
from diffusers import StableDiffusionPipeline
import config

def generate_show_art(keywords):
    pipe = StableDiffusionPipeline.from_pretrained(config.STABLE_DIFFUSION_MODEL, torch_dtype=torch.float16).to("mps")
    keyword_str = ", ".join(keywords)
    image = pipe(f"Podcast cover art featuring {keyword_str}").images[0]
    art_file = os.path.join(config.DATA_DIR, 'show_art.jpg')
    image.save(art_file)
    return art_file