import torch
from transformers import AutoTokenizer, AutoModelWithLMHead


class DialogConfig:
    tokenizer = AutoTokenizer.from_pretrained('tinkoff-ai/ruDialoGPT-medium')
    model = AutoModelWithLMHead.from_pretrained('tinkoff-ai/ruDialoGPT-medium')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _ = model.to(device)


def generate_conversation_response(conversation):
    inputs = DialogConfig.tokenizer(' '.join(conversation), return_tensors='pt').to(DialogConfig.device)
    generated_token_ids = DialogConfig.model.generate(
        **inputs,
        top_k=10,
        top_p=0.95,
        num_beams=3,
        num_return_sequences=1,
        do_sample=True,
        no_repeat_ngram_size=3,
        temperature=1.4,
        repetition_penalty=1.4,
        length_penalty=1.0,
        eos_token_id=50257,
        max_new_tokens=40
    )
    context_with_response = [DialogConfig.tokenizer.decode(sample_token_ids) for sample_token_ids in generated_token_ids]
    
    return context_with_response[0]