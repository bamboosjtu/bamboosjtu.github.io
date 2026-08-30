import os

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


load_dotenv()


# 1. 准备中文语料库
texts = [
    "《流浪地球》是2019年上映的中国科幻电影，由郭帆执导，吴京、屈楚萧等主演。",
    "故事设定在太阳即将毁灭的近未来，人类为了生存开启了流浪地球计划，旨在寻找新家园。",
    "该电影在中国电影史上具有重要意义，展现了宏大的视觉效果和核心的家国情怀。",
    "电影中，人类试图通过在地球表面建造巨大的行星发动机来推动地球离开太阳系。",
]

# 2. 保持原嵌入模型
embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# 3. 创建向量数据库
db = FAISS.from_texts(texts, embedding_model)

# 4. 使用局域网 LM Studio 作为生成模型（OpenAI 兼容接口）
llm = ChatOpenAI(
    api_key=os.getenv("LMSTUDIO_API_KEY", "lm-studio"),
    base_url=os.getenv("LMSTUDIO_BASE_URL", "http://192.168.31.252:1234/v1"),
    model=os.getenv("LMSTUDIO_MODEL_ID", "qwen/qwen3-8b"),
    temperature=0.2,
)

# 5. 定义 RAG 提示词模板
template = """
相关背景信息: {context}

请根据上方提供的信息，简洁地回答下列问题: {question}"""

prompt = PromptTemplate(template=template, input_variables=["context", "question"])

# 6. 构建并运行 RAG 流程
rag = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=db.as_retriever(),
    chain_type_kwargs={"prompt": prompt},
)

response = rag.invoke("《流浪地球》的主旨是什么？")
print(response["result"])
