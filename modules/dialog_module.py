import torch
from transformers import AutoTokenizer, AutoModelWithLMHead
from util.censore import is_obscene
import hashlib

class DialogConfig:
    tokenizer = AutoTokenizer.from_pretrained('tinkoff-ai/ruDialoGPT-medium')
    model = AutoModelWithLMHead.from_pretrained('tinkoff-ai/ruDialoGPT-medium')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _ = model.to(device)

    @staticmethod
    def generate(
        inputs,
        top_k=10,
        top_p=0.95,
        num_beams=3,
        num_return_sequences=1,
        do_sample=True,
        no_repeat_ngram_size=3,
        temperature=1.8,
        repetition_penalty=1.4,
        length_penalty=1.0,
        eos_token_id=50257,
        max_new_tokens=40
        ):
        
        generated_token_ids = DialogConfig.model.generate(
            **inputs,
            top_k=top_k,
            top_p=top_p,
            num_beams=num_beams,
            num_return_sequences=num_return_sequences,
            do_sample=do_sample,
            no_repeat_ngram_size=no_repeat_ngram_size,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
            length_penalty=length_penalty,
            eos_token_id=eos_token_id,
            max_new_tokens=max_new_tokens
        )
        
        generated_result = [DialogConfig.tokenizer.decode(sample_token_ids) for sample_token_ids in generated_token_ids][0]
        
        return generated_result
    

def generate_conversation_response(conversation):
    inputs = DialogConfig.tokenizer(' '.join(conversation), return_tensors='pt').to(DialogConfig.device)
    
    temperature = 1.8
    generated_result = None
    while generated_result is None:
        generated_result = is_obscene(DialogConfig.generate(inputs, temperature=temperature))
        temperature *= 0.9
    
    return generated_result