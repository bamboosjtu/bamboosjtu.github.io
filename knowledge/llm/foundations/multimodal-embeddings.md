# Visualized-BGE

## 一、 总体架构

| 组件                | 是否预训练       | 是否独立模型          |
| ------------------- | ---------------- | --------------------- |
| BGE                 | 是               | 是，文本 backbone     |
| EVA-CLIP Vision     | 是               | 是，视觉 backbone     |
| Visualized_BGE 整体 | 是（联合训练过） | 不是一个全新 backbone |

```
         ┌───────────────┐
text ───▶│ BGE Embedding │
         └───────────────┘
                  │
image ─▶ EVA-CLIP Vision ─▶ Linear Projection
                  │
                  ▼
          ┌────────────────┐
          │  BGE Encoder   │
          │ (共享的)        │
          └────────────────┘
                  ▼
               pooling
                  ▼
              embedding
```

### 0. 参数快照

`Visualized_base_en_v1.5.pth`（Visualized-BGE）是一个“完整的多模态模型 checkpoint（参数级）”，但不提供结构和运行协议。

```python
Counter({'model_visual': 287, 'bge_encoder': 192, 'bge_embeddings': 5, 'bge_pooler': 2, 'visual_proj': 2})
```

- `bge_embeddings.*` ：BGE 的 embedding 层
- `bge_encoder.*`：完整的 BGE Transformer 主干，典型 12 层 Transformer encoder 结构（QKV + FFN + LN）。
- `bge_pooler.*`：BERT 风格的 pooler（CLS → tanh(linear)
- `model_visual.visual.*`：EVA-CLIP 的视觉 ViT 参数，并且至少有 blocks 0~11，基本对应 base 级别的 12 层。
- `visual_proj.*`：视觉 token → BGE hidden space 的投影层，跨模态对齐的桥梁
- 不包含：
  - tokenizer / config 等：运行必需的“非参数资产”
  - BERT encoder 和 EVA-CLIP ViT 的模型结构

### 1. BGE

#### 1) 模型结构

BGE = 一个标准的 BERT 类 Transformer 编码器模型

```
 ├── Embedding Layer：token_ids -> [B, T, 768]
 │        │
 │        ├── word_embeddings (nn.Embedding)
 │        ├── position_embeddings (nn.Embedding)
 │        ├── token_type_embeddings (nn.Embedding)
 │        └── LayerNorm
 ├── Transformer Encoder Stack (12 layers for base)：[B, T, 768] -> hidden_size, num_heads, intermediate_size = 768, 12, 3072 -> [B, T, 768]
 │        ├──Layer_i
 │             ├── SelfAttention
 │             │     ├── Q = Linear(768→768)
 │             │     ├── K = Linear(768→768)
 │             │     ├── V = Linear(768→768)
 │             │     ├── Attention
 │             │     └── Output Linear + LayerNorm
 │             │
 │             └── FeedForward
 │                   ├── Linear(768→3072)
 │                   ├── GELU
 │                   ├── Linear(3072→768)
 │                   └── LayerNorm
 └── Pooler（可选）
```

#### 2) 文本 backbone

`BAAI/bge-base-en-v1.5`是标准化的 Hugging Face Transformers 模型。底层骨架是经典的 BERT (Bidirectional Encoder Representations from Transformers) 架构，它是一个纯粹的 Encoder-only（仅编码器） 结构。

```python
bge_name = 'BAAI/bge-base-en-v1.5'
tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-base-en-v1.5')
model = AutoModel.from_pretrained('BAAI/bge-base-en-v1.5')
```

- `bge_embeddings`（原料初加工层）
  - 作用： 把文字变成“没有灵魂”的初始数字。
  - 细节： 包含词向量表（Word）、位置向量表（Position）和段落类型表（Segment）三张表。它把输入文本查表并求和，变成一组基础向量。
- `bge_encoder`（深度理解加工车间）
  - 作用： 理解上下文。
  - 细节： bge模型的核心，由 12 层 Transformer Block 组成。每一层都在利用“自注意力机制（Self-Attention）”让单词之间互相打招呼，相同token在不同上下文中的含义可能不同。
- `bge_pooler`（成品打包层）
  - 作用： 总结陈词。
  - 细节： 编码器输出的是每一个词的向量，但bge输出需要的是代表整句话的一个向量。Pooler 通常会提取句首特殊标记 [CLS] 的向量，经过一次全连接层和激活函数，输出最终那串 768 维的“语义指纹”。

### 2. EVA-CLIP

#### 1) 模型结构

`EVA-CLIP`的视觉部分是一个 ViT（Vision Transformer）

```
 │
 ├── Patch Embedding(Conv2d)：[B, 3, 224, 224] -> nn.Conv2d(3, hidden_dim, kernel_size=16, stride=16) -> [B, N, 768]
 ├── Positional Embedding
 ├── Transformer Blocks：[B, N, 768] -> [B, 1+N, 768]
 │        ├──Block_i
 │             ├── Multi-Head Attention
 │             ├── MLP
 │             └── LayerNorm / LayerScale
 └── (可选) Mean Pooling / CLS Token 输出
```

#### 2) 视觉 backbone

`EVA-CLIP`延续了 OpenAI 提出的 CLIP 经典架构，其核心思想是：让图片和文字在同一个数学空间里“相遇”。它由两个平行的部分组成：

- 视觉塔 (Image Encoder)： 负责看图。EVA-CLIP 的核心亮点就在这里——它使用了 EVA-ViT (Vision Transformer)。
- 文本塔 (Text Encoder)： 负责识字。通常是一个类似 BERT 或 RoBERTa 的 Transformer 架构。

```python
# pip install open_clip_torch torchvision
import open_clip
model, _, preprocess = open_clip.create_model_and_transforms('EVA02-B-16', pretrained='merged2b_s8b_b131k')
model.eval()  # 设置为评估模式
```

- 图像经过 preprocess 后喂给 model_visual.encode_image()
- 得到 patch tokens
- 再通过 visual_proj 对齐到 BGE hidden 维度

### 3. patch tokens + CLS 融合

1. image → EVA-CLIP → patch tokens
2. text → BGE embedding
3. 拼接：
   [BGE_CLS] + [IMAGE_PATCHES] + [TEXT_TOKENS]
4. 再走 BGE Transformer encoder

#### 1) 视觉→文本空间投影层

- `self.visual_proj = nn.Linear(hidden_dim, hidden_dim)`
- 把视觉 token 投到 BGE 的 hidden dim（base=768），与文本 token 拼接
- 再送进 同一个 BGE encoder

#### 2) 池化与归一化

- `sentence_embedding()` 支持 `cls` 或 `mean` pooling
- 默认 `normlized=True`，输出会 `F.normalize(..., dim=-1)`

#### 3) 相似度

- `compute_similarity()` 就是矩阵乘：$q @ p^T$
- 默认输出已归一化，即 **cosine similarity** 的实现形式。

## 二、 推理接口

`encode()` 只是个路由器：传 text 就走 text 分支；传 image 就走 image/mm 分支。

### 1. 纯文本

`encode_text(texts)`本质是“标准 BERT encoder”：

1. `bge_embeddings(input_ids, position_ids, token_type_ids)` 得到 `[B, T, C]`
2. 构造 attention mask（把 padding 位置变成 `-inf`）
3. `bge_encoder(embedding_output, attention_mask=extended_attention_mask)` 得到 `sequence_output`
4. pooling（CLS 或 mean）→ normalize

> `nn.Embedding + nn.TransformerEncoder + pooling + normalize`

### 2. 纯图像

`encode_image(images)`不是一个独立的“视觉 embedding head”：

- 给每张图配一个空文本 `[""]`，然后走 `encode_mm(images, prompts)`
- 实际上是“图 + 空 prompt 的多模态编码”，所以做 `img_emb_1 @ img_emb_2.T` 本质是在 mm-space 里比较“图像语义”

### 3. 图文融合

`encode_mm(images, texts)`把视觉 patch tokens 当作“中间 token”插进 BGE 序列里，position ids 和 attention mask 也要对齐

1. 图像 tokens（EVA 输出）:  
   [IMG_CLS] [IMG_1] [IMG_2] ... [IMG_N]
2. 去掉 IMG_CLS 后:  
   [IMG_1] [IMG_2] ... [IMG_N]
3. 文本 tokens（BGE embeddings）:  
   [TXT_CLS] [TXT_1] [TXT_2] ... [TXT_M]
4. 最终拼接序列（送入 BGE encoder）:  
   [TXT_CLS] [IMG_1] [IMG_2] ... [IMG_N] [TXT_1] [TXT_2] ... [TXT_M]

```
  Tokens:
  [TXT_CLS] [IMG_1] [IMG_2] ... [IMG_N] [TXT_1] [TXT_2] ... [TXT_M]

  Position IDs:
     0        1        2   ...    N     N+1     N+2   ...   N+M

  Attention Mask:
     1        1        1   ...    1      t1      t2   ...   tM
```

## 三、安装和使用

[Visualized-BGE的Hugging Face主页](https://huggingface.co/BAAI/bge-visualized)。

## 附录

### 1. encoder结构

encode(text) 一般包含以下步骤

1. Tokenizer

```python
# "hello world" → [101, 7592, 2088, 102]
text = "什么是 RAG？"
tokenizer = AutoTokenizer.from_pretrained(model_name)
inputs = tokenizer(text, return_tensors="pt")
# inputs 看起来像这样：{'input_ids': tensor([[101, 123, 456, 102]]), 'attention_mask': tensor([[1, 1, 1, 1]])}
```

2. Embedding Layer（词嵌入）

```python
# token ids → token embeddings
model = AutoModel.from_pretrained(model_name)
outputs = model(**inputs)
```

3. Transformer Encoder（多层）

```
token embeddings → contextualized embeddings
```

4. Pooling：CLS pooling / mean pooling

```python
vector = outputs.last_hidden_state[:, 0, :]
```

5. Normalize（常见于检索模型）：L2 normalize

### 2. Visualized-BGE结构

[mini_visualized.py](./examples/indexing/mini_visualized.py ":include :type=code python")
