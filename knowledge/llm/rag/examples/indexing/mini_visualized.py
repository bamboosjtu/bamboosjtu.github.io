import torch
import torch.nn as nn
import torch.nn.functional as F


"""
输入：图像 [B, 3, 224, 224] + 文本 [B, T]
                    ↓
        ┌─────────────────────┐
        │   分别编码           │
        │  图像 → Patch Embedding │
        │  文本 → Token Embedding │
        └─────────────────────┘
                    ↓
        [CLS] + 图像Tokens + 文本Tokens 拼接
                    ↓
              共享Transformer编码
                    ↓
              输出统一向量 [B, D]
"""


class VisualizedMini(nn.Module):
    def __init__(
        self, vocab_size=10000, img_size=224, patch_size=16, dim=256, depth=4, heads=8
    ):
        super().__init__()

        # ---------- 文本部分 ----------
        """
        作用：这是文本的“分词器”后续步骤。它将输入的整数 ID（如 [101, 2398, 2023]）转换为稠密的向量。
        输出形状：[Batch_Size, Sequence_Length, dim]。比如输入一句话有 10 个词，这里就会变成 10 个 dim 维的向量。
        """
        self.text_embed = nn.Embedding(vocab_size, dim)

        # ---------- 图像部分 ----------
        """
        作用：这是图像的“分词器”。它不像文本那样按词切分，而是将整张图片切分成一个个小方块。
            输入图像 224x224，patch_size=16，意味着图像会被切分成 14x14 = 196 个图块。
            这个卷积层将每个 16x16 的像素块展平并映射成一个长度为 dim 的向量。
        输出形状：[Batch_Size, dim, 14, 14]，后续会被处理成序列形式。
        """
        self.patch_embed = nn.Conv2d(
            in_channels=3, out_channels=dim, kernel_size=patch_size, stride=patch_size
        )

        # ---------- 特殊Token与位置编码 ----------
        """
        作用：这是一个可学习的向量，类似于 BERT 中的 [CLS] 标记。
        目的：在序列的最前面添加这个 token。经过 Transformer 处理后，这个 token 会“吸收”整个序列（图像+文本）的信息。最终我们只取这个 token 的输出作为整个图文对的全局表示向量。
        """
        num_patches = (img_size // patch_size) ** 2
        self.cls_token = nn.Parameter(torch.zeros(1, 1, dim))
        """
        作用：因为 Transformer 本身不具备顺序概念（它是并行处理所有输入的），我们需要显式地告诉模型每个 token 在序列中的位置。
        长度计算：1 (CLS token) + num_patches (图像图块数量) + 128 (预留的文本最大长度)。
        注意：这里硬编码了文本最大长度 128，实际工程中通常会动态处理或设得更大。
        """
        self.pos_embed = nn.Parameter(torch.zeros(1, 1 + num_patches + 128, dim))

        # ---------- 融合 Transformer ----------
        """
        作用：这是模型的核心“大脑”。它接收由 CLS、图像 token、文本 token 拼接成的长序列，通过自注意力机制让图像和文本信息进行深度的交互与融合。
        """
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=dim,
            nhead=heads,
            dim_feedforward=dim * 4,
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=depth)
        self.norm = nn.LayerNorm(dim)

    def encode_image(self, images):
        # [B, 3, 224, 224] -> [B, 196, 256]
        x = self.patch_embed(images)  
        x = x.flatten(2).transpose(1, 2)  
        return x

    def encode_text(self, input_ids):
        # [B, T] -> [B, T, D]
        return self.text_embed(input_ids)  

    def forward(self, images, input_ids):
        B = images.size(0) # 获取批次大小 Batch Size

        # 1. 分别获取图文 Token
        img_tokens = self.encode_image(images)   # [B, 196, 256]
        txt_tokens = self.encode_text(input_ids) # [B, T, 256]

        # 2. 准备 CLS Token 并扩展到 Batch 大小
        cls = self.cls_token.expand(B, -1, -1)

        # 3. 拼接序列：[CLS] + [Image Patches...] + [Text Tokens...]
        x = torch.cat([cls, img_tokens, txt_tokens], dim=1) # [B, 1 + 196 + T, 256]

        # 4. 添加位置编码
         # 截取 pos_embed 的前 N 个位置，加到输入上
        x = x + self.pos_embed[:, : x.size(1)]
        
        # 5. 输入 Transformer 让图像和文字互相“对话”
        x = self.encoder(x)

        # 6. 提取 CLS Token 的输出作为全局表示
        cls_out = self.norm(x[:, 0])

        # 7. L2 归一化（重要！）
        # 这使得向量模长为1，计算余弦相似度时只需做点积
        return F.normalize(cls_out, dim=-1)


if __name__ == "__main__":
    model = VisualizedMini()

    images = torch.randn(2, 3, 224, 224)
    input_ids = torch.randint(0, 10000, (2, 20))

    embedding = model(images, input_ids)

    print(embedding.shape)  # torch.Size([2, 256])
