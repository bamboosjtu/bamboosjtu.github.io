import cohere
import faiss
import numpy as np
import pandas as pd
from tqdm import tqdm
import os
import re
from dotenv import load_dotenv

load_dotenv()

COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
co = cohere.Client(COHERE_API_KEY)


# 1. 准备文本
text = """
《星际穿越》（Interstellar）是一部于 2014 年上映的史诗级科幻电影，由克里斯托弗·诺兰执导、制片并参与编剧。影片汇聚了马修·麦康纳、安妮·海瑟薇、杰西卡·查斯坦、比尔·欧文、艾伦·伯斯汀、马特·达蒙以及迈克尔·凯恩等实力派演员，共同演绎了一场震撼人心的宇宙探索之旅。

故事背景设定在一个人类为生存而挣扎的反乌托邦未来，讲述了一组宇航员为了寻找人类的新家园，毅然穿越土星附近的一个虫洞，开启了跨越星际的壮阔征程。克里斯托弗·诺兰与其兄弟乔纳森·诺兰共同创作了剧本，其灵感最早源于乔纳森在 2007 年开发的一个剧本构思。

在科学严谨性方面，加州理工学院理论物理学家、2017 年诺贝尔物理学奖得主基普·索恩（Kip Thorne）不仅担任了执行制片人，还作为科学顾问深度参与其中，并撰写了配套科普书籍《星际穿越中的科学》。影片的视觉呈现同样考究，摄影指导霍伊特·范·霍特玛采用 35 毫米胶片（Panavision 变形格式）和 IMAX 70 毫米胶片进行拍摄。

主体拍摄工作于 2013 年底启动，取景地跨越了加拿大阿尔伯塔、冰岛以及洛杉矶。为了追求极致的质感，影片大量使用了实景特效和微缩模型，数字特效则由 Double Negative 公司协助打造。

《星际穿越》于 2014 年 10 月 26 日在洛杉矶首映。在美国发行时，影片首先推出了胶片版本，随后扩展至数字放映场馆。该片在全球范围内获得了超过 6.77 亿美元的票房收入，若计入后续重映，总票房则高达 7.73 亿美元，成为 2014 年全球票房第十高的电影。

影片凭借演员的出色表现、导演水平、剧本深度、震撼配乐、视觉特效以及宏大的主题和情感厚度收获了广泛赞誉。许多天文学家也对其科学准确性以及对理论天体物理学的精准刻画表示赞赏。自上映以来，《星际穿越》积累了一大批狂热粉丝，被许多科幻专家公认为影史最伟大的科幻电影之一。在第 87 届奥斯卡金像奖中，它获得了包括最佳视觉效果奖在内的五项提名，并最终斩获殊荣。"""

texts = [s.strip() for s in re.split(r"[。！？]\s*", text) if s.strip()]
print("================文本切分开始================")
for i,t in enumerate(texts):
    print(f"{i}:\t{t}")


# 2. 向量化
print("================向量化结束================")
response = co.embed(
    texts=texts,
    input_type="search_document",
    model="embed-multilingual-v3.0",
).embeddings

embeds = np.array(response)
print(embeds.shape)


# 3. 构建搜索索引
dim = embeds.shape[1]
doc_embeds = np.float32(embeds.copy())
faiss.normalize_L2(doc_embeds)
index = faiss.IndexFlatIP(dim)
print(index.is_trained)
index.add(doc_embeds)


# 4. 通过索引进行搜索
print("================相似度检索================")
def search(query, number_of_results=3):
    # 1. 获取查询的嵌入向量
    query_embed = co.embed(
        texts=[query],
        input_type="search_query",
        model="embed-multilingual-v3.0",
    ).embeddings[0]
    query_embed = np.float32([query_embed])
    if query_embed.shape[1] != index.d:
        raise ValueError(f"Embedding dim mismatch: query={query_embed.shape[1]}, index={index.d}")
    faiss.normalize_L2(query_embed)
    # 2. 直接检索最近邻（不使用重排序）
    scores, similar_item_ids = index.search(query_embed, number_of_results)
    # 3. 格式化结果
    texts_np = np.array(texts) # 将文本列表转换为numpy数组以便索引
    results = pd.DataFrame(
        {
            "texts": texts_np[similar_item_ids[0]],
            "score": scores[0],
        }
    )
    # 4. 打印并返回结果
    print(f"Query:'{query}'\nNearest neighbors:")
    return results



query = "这部电影在科学严谨性方面究竟达到了怎样的水准？"
results = search(query, number_of_results=3)
print(results)
