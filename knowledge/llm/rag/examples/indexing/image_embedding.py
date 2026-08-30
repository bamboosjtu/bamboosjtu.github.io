import pprint
import open_clip
import torch
from pathlib import Path
from PIL import Image

pprint.pprint(open_clip.list_pretrained())

# 1. 创建模型和预处理变换
model, _, preprocess = open_clip.create_model_and_transforms('EVA02-B-16', pretrained='merged2b_s8b_b131k')
model.eval()  # 设置为评估模式

# 2. 加载图像和准备文本
image_dir = Path(__file__).parent.parent / "data" / "C3" / "imgs" 
image1 = preprocess(Image.open(image_dir / "datawhale01.png")).unsqueeze(0) # 添加batch维度
image2 = preprocess(Image.open(image_dir / "datawhale02.png")).unsqueeze(0) # 添加batch维度
text = open_clip.tokenize(["a dog", "a whale", "a car"])
images = torch.cat([image1, image2], dim=0)

# 3. 计算图像和文本的特征向量
with torch.no_grad(), torch.cuda.amp.autocast():
    image_features = model.encode_image(images)
    text_features = model.encode_text(text)

# 归一化特征向量（对于计算余弦相似度很重要）
image_features /= image_features.norm(dim=-1, keepdim=True)
text_features /= text_features.norm(dim=-1, keepdim=True)

# 4. 计算相似度 (文本-图像)
# scale 是模型学习到的温度参数
text_probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)


print("Label probs:", text_probs) # 输出每个文本描述与图像匹配的概率
# Label probs: tensor([[2.4113e-06, 9.9997e-01, 2.3555e-05],
#                     [5.1588e-05, 9.9988e-01, 6.9136e-05]])