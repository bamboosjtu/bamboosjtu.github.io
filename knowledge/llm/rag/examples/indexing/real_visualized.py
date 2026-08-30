from pathlib import Path
import open_clip
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoConfig, AutoTokenizer
from PIL import Image


def filter_state_dict(sd, prefixes):
    """只保留以 prefixes 开头的 keys"""
    return {k: v for k, v in sd.items() if any(k.startswith(p) for p in prefixes)}


class VisualizedReal(nn.Module):
    """
    真实 BGE + 真实 open_clip EVA tokens + 加载 .pth（仅 BGE+visual_proj）
    """

    def __init__(self):
        super().__init__()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # ---- 1) 文本侧：真实 BGE（HF 标准）----
        bge_name = "BAAI/bge-base-en-v1.5"
        cfg = AutoConfig.from_pretrained(bge_name)
        bge = AutoModel.from_config(cfg)  # 只创建结构
        self.bge_embeddings = bge.embeddings
        self.bge_encoder = bge.encoder
        self.bge_pooler = bge.pooler  # 有权重但通常不用

        # tokenizer（encode_text 时用）
        self.tokenizer = AutoTokenizer.from_pretrained(bge_name)

        # ---- 2) 视觉侧：真实 EVA（必须与 .pth 版本一致）----
        # 这里必须用与你 .pth 匹配的参数：img_size/patch_size/embed_dim/depth/heads 等
        # m：CustomTextCLIP
        #   m.visual：open_clip.timm_model.TimmModel
        #     m.visual.trunk：timm.models.eva.Eva
        #     m.visual.trunk.forward_features 存在 ✅
        #     m.visual.trunk.cls_token 也存在（说明是 ViT-style token 序列）
        eva_name = "EVA02-B-16"
        eva_pretrained = "merged2b_s8b_b131k"
        clip_model, _, preprocess = open_clip.create_model_and_transforms(
            eva_name, pretrained=eva_pretrained
        )
        self.model_visual = clip_model.eval()
        self.preprocess_val = preprocess

        # ---- 3) 跨模态投影 ----
        self.visual_proj = nn.Linear(768, 768)

        # ---- 4) 加载 .pth ----
        pth_path = (
            Path(__file__).parent.parent / "models" / "bge" / "Visualized_base_en_v1.5.pth"
        )
        sd = torch.load(pth_path, map_location="cpu")
        sd_use = filter_state_dict(
            sd,
            prefixes=("bge_embeddings.", "bge_encoder.", "bge_pooler.", "visual_proj."),
        )
        missing, unexpected = self.load_state_dict(sd_use, strict=False)

        print("[load .pth] missing (first 20):", missing[:20])
        print("[load .pth] unexpected (first 20):", unexpected[:20])

        self.to(self.device).eval()

    @torch.no_grad()
    def encode_text(self, text: str) -> torch.Tensor:
        batch = self.tokenizer([text], return_tensors="pt", padding=True, truncation=True).to(self.device)
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"].to(torch.float32)
        token_type_ids = torch.zeros_like(input_ids)

        x = self.bge_embeddings(input_ids=input_ids, token_type_ids=token_type_ids)
        out = self.bge_encoder(x, attention_mask=attention_mask)[0]  # [B,T,C]
        emb = out[:, 0]  # CLS
        return F.normalize(emb, dim=-1)
    
    @torch.no_grad()
    def encode_image_tokens(self, image_tensor: torch.Tensor) -> torch.Tensor:
        """
        image_tensor: [B,3,224,224]，应先用 self.preprocess_val 处理
        返回: [B,196,768] patch tokens (drop CLS) 并投影到 BGE space
        """
        tok = self.model_visual.visual.trunk.forward_features(image_tensor)  # [B,197,768]
        patch = tok[:, 1:, :]                                                # [B,196,768]
        patch = self.visual_proj(patch)                                      # [B,196,768]
        return patch

    @torch.no_grad()
    def encode_image(self, image_tensor: torch.Tensor) -> torch.Tensor:
        img_patch = self.encode_image_tokens(image_tensor)  # [B,196,768]

        # 用一个“空文本CLS”来当融合CLS：复用 bge_embeddings 的 [CLS] token embedding
        # 最稳的做法：直接从 tokenizer 造一个只含 [CLS] 的输入
        batch = self.tokenizer([""], return_tensors="pt", padding=True, truncation=True).to(self.device)
        input_ids = batch["input_ids"][:, :1]  # 只保留 CLS
        token_type_ids = torch.zeros_like(input_ids)

        cls = self.bge_embeddings(input_ids=input_ids, token_type_ids=token_type_ids)  # [B,1,768]

        fused = torch.cat([cls, img_patch], dim=1)  # [B,1+196,768]
        fused_mask = torch.ones((fused.size(0), fused.size(1)), device=self.device, dtype=torch.float32)

        out = self.bge_encoder(fused, attention_mask=fused_mask)[0]
        emb = out[:, 0]
        return F.normalize(emb, dim=-1)


    @torch.no_grad()
    def encode_mm(self, image_tensor: torch.Tensor, text: str) -> torch.Tensor:
        """
        最小融合版： [BGE_CLS] + [IMG_PATCH] + [TEXT_TOKENS]
        """
        # 1) 图像 patch tokens
        img_patch = self.encode_image_tokens(image_tensor)  # [B,196,768]

        # 2) 文本 tokens
        batch = self.tokenizer([text], return_tensors="pt", padding=True, truncation=True).to(self.device)
        input_ids = batch["input_ids"]
        attention_mask = batch["attention_mask"].to(torch.float32)
        token_type_ids = torch.zeros_like(input_ids)

        txt = self.bge_embeddings(input_ids=input_ids, token_type_ids=token_type_ids)  # [B,T,768]
        cls = txt[:, :1, :]       # [B,1,768]
        txt_wo_cls = txt[:, 1:, :]  # [B,T-1,768]

        # 3) 拼接
        fused = torch.cat([cls, img_patch, txt_wo_cls], dim=1)  # [B, 1+196+T-1, 768]

        # 4) mask（最简：img_patch 全 1 + 原 attention_mask）
        img_mask = torch.ones((fused.size(0), img_patch.size(1)),
                              device=self.device, dtype=attention_mask.dtype)
        fused_mask = torch.cat([img_mask, attention_mask], dim=1)

        out = self.bge_encoder(fused, attention_mask=fused_mask)[0]
        emb = out[:, 0]  # fused CLS
        return F.normalize(emb, dim=-1)


if __name__=='__main__':
    model = VisualizedReal()

    image_dir = Path(__file__).parent.parent / "data" / "C3" / "imgs" 
    img = Image.open(image_dir / "datawhale01.png").convert("RGB")
    x = model.preprocess_val(img).unsqueeze(0).to(model.device)

    t = "datawhale开源组织的logo"
    with torch.no_grad():
        e_text = model.encode_text(t)
        e_img  = model.encode_image(x)
        e_mm   = model.encode_mm(x, t)

    print(e_text.shape, e_img.shape, e_mm.shape)  # 都应是 [1,768]（或你配置的dim）
    print("sim(text, mm):", (e_text @ e_mm.T).item())
    print("sim(img,  mm):", (e_img  @ e_mm.T).item())
    print("sim(text,  mimgm):", (e_text  @ e_img.T).item())
