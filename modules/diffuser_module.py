from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import torch
from deep_translator import GoogleTranslator
from diffusers.pipelines.stable_diffusion import safety_checker
import hashlib
import random

class DiffuserConfig:
    model_id = "stabilityai/stable-diffusion-2-1-base"
    pipe = None
    neg_prompt = None
    
    
def init_diffuser():
    def sc(self, clip_input, images) :
        return images, [False for i in images]

    safety_checker.StableDiffusionSafetyChecker.forward = sc
    
    pipe = StableDiffusionPipeline.from_pretrained(DiffuserConfig.model_id, torch_dtype=torch.float16)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda")
    DiffuserConfig.pipe = pipe
    
    with open('data/neg_prompt.txt', 'r') as fin:
        DiffuserConfig.neg_prompt = fin.read()

        
def generate_image_response(base_text):
    prompt = base_text.lower().replace('сгенерируй', '').replace('создай', '')
    
    if DiffuserConfig.pipe is None:
        init_diffuser()

    return generate_image(prompt)


def generate_image(prompt):
    prompt = GoogleTranslator(source='ru', target='en').translate(prompt)
    guidance_scale = 10
    num_inference_steps = 50
    image = DiffuserConfig.pipe(prompt, guidance_scale=guidance_scale,
                                num_inference_steps=num_inference_steps,
                                negative_prompt=DiffuserConfig.neg_prompt
                               ).images[0]
    
    file_name = hashlib.sha256(str(random.random()).encode()).hexdigest()
    file_path = f'data/generated_images/{file_name}.jpeg'
    image.save(file_path)
    
    with open('data/generated_images/params.csv', 'a') as params:
        params.write(f'{file_name}; {prompt}; {DiffuserConfig.neg_prompt}; {guidance_scale}; {num_inference_steps}\n')
    
    return image, file_path