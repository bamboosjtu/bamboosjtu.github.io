from sentence_transformers import SentenceTransformer
import numpy as np

# 加载模型（自动下载到本地）
model = SentenceTransformer('BAAI/bge-base-zh-v1.5')

# 编码句子
sentences = ["猫在睡觉", "猫咪在打盹", "股票上涨了"]
embeddings = model.encode(sentences)

# 计算余弦相似度
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 结果：前两个相似度高，第三个低
print(cosine_similarity(embeddings[0], embeddings[1]))  # ~0.86（很相似）
print(cosine_similarity(embeddings[0], embeddings[2]))  # ~0.34（不相似）


from transformers import AutoModel, AutoTokenizer
import torch
import torch.nn.functional as F

tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-base-en-v1.5')
model = AutoModel.from_pretrained('BAAI/bge-base-en-v1.5')

def encode(texts):
    # 1. 分词
    inputs = tokenizer(texts, padding=True, truncation=True, 
                      max_length=512, return_tensors="pt")
    
    # 2. 模型推理
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 3. 取CLS token向量（BGE的方式）
    embeddings = outputs.last_hidden_state[:, 0]  # [batch_size, hidden_dim]
    
    # 4. 归一化（BGE默认做）
    embeddings = F.normalize(embeddings, p=2, dim=1)
    
    return embeddings.numpy()

# 使用
embeddings = encode(["猫在睡觉", "股票上涨了"])