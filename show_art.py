from diffusers import AutoPipelineForText2Image
import torch
import logging
import os # Added for path operations
import config # Import the application's config

# Configure logger for this module
logger = logging.getLogger(__name__)

# Global variable to hold the loaded diffusion model pipeline
DIFFUSION_PIPELINE = None

def load_diffusion_model(model_id: str = None, device: str = "default") -> AutoPipelineForText2Image | None:
    """
    Loads the Stable Diffusion model using AutoPipelineForText2Image.

    Args:
        model_id: The Hugging Face model ID for Stable Diffusion. 
                  Defaults to config.STABLE_DIFFUSION_MODEL_ID if None.
        device: The target device ("default", "cuda", "mps", "cpu"). 
                "default" will auto-detect GPU (CUDA then MPS) or fallback to CPU.

    Returns:
        The loaded Stable Diffusion pipeline, or None if loading fails.
    """
    global DIFFUSION_PIPELINE

    # Use model_id from config if not provided
    if model_id is None:
        model_id = config.STABLE_DIFFUSION_MODEL_ID
    
    # Caching logic: If a pipeline is already loaded with the same model_id and compatible device, return it
    if DIFFUSION_PIPELINE is not None and \
       hasattr(DIFFUSION_PIPELINE, '_model_id') and DIFFUSION_PIPELINE._model_id == model_id:
        current_pipe_device = str(DIFFUSION_PIPELINE.device)
        requested_device_is_compatible = False

        if device == "default":
            # If default is requested and current pipe is not on CPU, it's likely a GPU, so compatible.
            # If current pipe is CPU, "default" might try to load on GPU if available, so re-evaluate.
            if current_pipe_device != "cpu":
                requested_device_is_compatible = True
            # else: let it proceed to device detection and potential reload
        elif device == current_pipe_device:
            requested_device_is_compatible = True

        if requested_device_is_compatible:
            logger.info(f"Returning already loaded Stable Diffusion model '{model_id}' on device: {current_pipe_device}")
            return DIFFUSION_PIPELINE
        else:
            logger.info(f"Requested device '{device}' (resolves to potential diff from '{current_pipe_device}') or model ID change. Will attempt to load/reload model '{model_id}'.")
            # Force unload of current pipeline if device or model_id is different to free VRAM
            if DIFFUSION_PIPELINE is not None:
                logger.info(f"Unloading previous model from {current_pipe_device} to switch model/device.")
                del DIFFUSION_PIPELINE
                DIFFUSION_PIPELINE = None
                if torch.cuda.is_available(): torch.cuda.empty_cache()
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(): torch.mps.empty_cache()


    target_device: str # This will be the actual device string like "cuda", "mps", "cpu"
    if device == "default":
        if torch.cuda.is_available():
            target_device = "cuda"
        elif torch.backends.mps.is_available():
            target_device = "mps"
        else:
            target_device = "cpu"
    else:
        target_device = device

    logger.info(f"Attempting to load Stable Diffusion model '{model_id}' on device: {target_device}")

    try:
        dtype = torch.float16 if target_device != "cpu" else torch.float32
        logger.info(f"Using dtype: {dtype}")

        pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=dtype,
            use_safetensors=True
            # variant="fp16" could be used if model supports it and target_device is CUDA/MPS for faster loading
        )
        pipe = pipe.to(target_device)
        
        # Store the model_id with the pipeline for caching check
        DIFFUSION_PIPELINE = pipe
        DIFFUSION_PIPELINE._model_id = model_id # Custom attribute to store model_id for caching
        
        logger.info(f"Stable Diffusion model '{model_id}' loaded successfully on {target_device}.")
        return DIFFUSION_PIPELINE
    except Exception as e:
        logger.exception(f"Failed to load Stable Diffusion model '{model_id}' on device '{target_device}': {e}")
        # This can happen due to various reasons:
        # - Model ID not found or no internet connection to download.
        # - Insufficient VRAM/RAM.
        # - CUDA/MPS issues if selected.
        # - Specific compatibility issues with the model or diffusers version.
        return None

def generate_show_art(prompt: str, output_image_path: str, diffusion_pipeline, num_inference_steps: int = 50, guidance_scale: float = 7.5) -> str | None:
    """
    Generates show art using the provided Stable Diffusion pipeline and saves it.

    Args:
        prompt: The text prompt to generate the image from.
        output_image_path: The path to save the generated image.
        diffusion_pipeline: The loaded Stable Diffusion model pipeline.
        num_inference_steps: Number of denoising steps.
        guidance_scale: Scale for classifier-free guidance.

    Returns:
        The path to the saved image if successful, None otherwise.
    """
    if not diffusion_pipeline:
        logger.error("Diffusion pipeline is not loaded. Cannot generate show art.")
        return None

    logger.info(f"Generating show art with prompt: '{prompt}'...")
    logger.info(f"Parameters: steps={num_inference_steps}, guidance={guidance_scale}")

    try:
        # Generate the image
        image = diffusion_pipeline(
            prompt, 
            num_inference_steps=num_inference_steps, 
            guidance_scale=guidance_scale
        ).images[0]
        logger.info("Image generation successful.")
    except Exception as e:
        logger.exception(f"Stable Diffusion inference failed for prompt '{prompt}': {e}")
        return None

    try:
        # Save the image
        output_dir = os.path.dirname(output_image_path)
        if output_dir: # Ensure directory exists only if output_image_path includes a directory
            os.makedirs(output_dir, exist_ok=True)
        
        image.save(output_image_path)
        logger.info(f"Show art saved to: {output_image_path}")
        return output_image_path
    except Exception as e:
        logger.exception(f"Failed to save image to {output_image_path}: {e}")
        return None

if __name__ == '__main__':
    # Configure basic logging for direct script execution/testing
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    pipeline_to_test_generation = None # Will be set by a successful load attempt

    logger.info("--- Testing Stable Diffusion Model Loading (Default Device) ---")
    pipeline_default = load_diffusion_model()
    if pipeline_default:
        logger.info(f"Test (Default): Model loaded successfully on device: {pipeline_default.device}")
        pipeline_to_test_generation = pipeline_default # Use this for generation test
        
        logger.info("--- Testing Stable Diffusion Model Loading (Default Device - Cached) ---")
        pipeline_default_cached = load_diffusion_model()
        if pipeline_default_cached:
            logger.info(f"Test (Default - Cached): Model loaded successfully on device: {pipeline_default_cached.device}")
        else:
            logger.error("Test (Default - Cached): Failed to load model from cache.")
    else:
        logger.error("Test (Default): Failed to load model with default device selection. Trying CPU next for generation test.")
        logger.info("--- Testing Stable Diffusion Model Loading (CPU Device for generation fallback) ---")
        pipeline_cpu_fallback = load_diffusion_model(device="cpu")
        if pipeline_cpu_fallback:
            logger.info(f"Test (CPU Fallback): Model loaded successfully on device: {pipeline_cpu_fallback.device}")
            pipeline_to_test_generation = pipeline_cpu_fallback
        else:
            logger.error("Test (CPU Fallback): Failed to load model on CPU. Cannot test generation.")

    # Test image generation if a pipeline was successfully loaded
    if pipeline_to_test_generation:
        logger.info("--- Testing show art generation ---")
        TEST_PROMPT = "A vibrant abstract representation of AI in podcasting, podcast cover art"
        
        # Create a test_images directory if it doesn't exist for the test output
        # This should be relative to where the script is run from, or use absolute paths from config for real app
        TEST_OUTPUT_DIR = "test_show_art_output" 
        if not os.path.exists(TEST_OUTPUT_DIR):
            try:
                os.makedirs(TEST_OUTPUT_DIR)
                logger.info(f"Created test output directory: {TEST_OUTPUT_DIR}")
            except OSError as e:
                logger.exception(f"Could not create test output directory {TEST_OUTPUT_DIR}: {e}")
                TEST_OUTPUT_DIR = "." # Fallback to current directory

        TEST_OUTPUT_IMAGE_PATH = os.path.join(TEST_OUTPUT_DIR, "test_show_art.png")

        # Use fewer steps for faster testing if desired
        generated_image_path = generate_show_art(
            TEST_PROMPT, 
            TEST_OUTPUT_IMAGE_PATH, 
            pipeline_to_test_generation,
            num_inference_steps=5 # Reduced for faster testing; default is 50
        )
        if generated_image_path:
            logger.info(f"Test: Show art generated and saved to {generated_image_path}")
            if os.path.exists(generated_image_path):
                logger.info(f"File confirmed at {generated_image_path}, size: {os.path.getsize(generated_image_path)} bytes.")
            else:
                logger.error(f"File NOT found at {generated_image_path} despite function success!")
        else:
            logger.error("Test: Failed to generate or save show art.")
    else:
        logger.warning("Skipping show art generation test as no diffusion pipeline was successfully loaded.")

    # Example of loading a different model ID (will trigger re-load)
    # logger.info("--- Testing Stable Diffusion Model Loading (Different Model ID) ---")
    # pipeline_other = load_diffusion_model(model_id="runwayml/stable-diffusion-v1-5")
    # if pipeline_other:
    #     logger.info(f"Test (Other Model): Model 'runwayml/stable-diffusion-v1-5' loaded successfully on device: {pipeline_other.device}")
    # else:
    #     logger.error("Test (Other Model): Failed to load 'runwayml/stable-diffusion-v1-5'.")
