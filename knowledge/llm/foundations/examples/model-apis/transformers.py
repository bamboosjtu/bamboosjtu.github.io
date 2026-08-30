import os
from transformers import AutoTokenizer, AutoModelForCausalLM

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

tokenizer = AutoTokenizer.from_pretrained(
    "Qwen/Qwen3-0.6B", trust_remote_code=True, 
)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-0.6B",
    torch_dtype="auto",
    device_map="auto",
    trust_remote_code=True,
    tie_word_embeddings=False,  # 在早期的模型设计中，为了节省显存，模型的**输入层（Embedding）和输出层（LM Head）**通常共享同一组权重（即“权重绑定”）。
)

prompt = "<|system|>\n你是一个有用的个人助手。<|end|>\n<|user|>\n解释一下transformers。<|end|>\n<|assistant|>\n"
print("------------------模型输入向量化------------------")
input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
print(input_ids)
for id in input_ids[0]:
    print(tokenizer.decode(id))

output_ids = model.generate(input_ids, max_new_tokens=120)
print("------------------模型输出向量化------------------")
print(tokenizer.decode(output[0]))
print(output_ids)
for id in output_ids[0]:
    print(tokenizer.decode(id))