import collections
import pprint
import torch

sd = torch.load("models/bge/Visualized_base_en_v1.5.pth", map_location="cpu")
print(type(sd), len(sd))

prefix = collections.Counter(k.split(".")[0] for k in sd.keys())
print(prefix)

print("has bge_embeddings?", any(k.startswith("bge_embeddings") for k in sd.keys()))
print("has model_visual?", any(k.startswith("model_visual") for k in sd.keys()))
print("has visual_proj?", any(k.startswith("visual_proj") for k in sd.keys()))

keys = list(sd.keys())
pprint.pprint(keys)