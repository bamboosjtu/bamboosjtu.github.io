import os
from pathlib import Path

from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter, SentenceWindowNodeParser

# $env:HF_ENDPOINT="https://hf-mirror.com"
load_dotenv()

# 0.1 配置 Settings.llm 和 Settings.embed_model 
Settings.embed_model = HuggingFaceEmbedding("BAAI/bge-small-zh-v1.5")
Settings.llm = OpenAILike(
    model=os.getenv("SILICONFLOW_MODEL_ID"),
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    api_base=os.getenv("SILICONFLOW_BASE_URL"),
    is_chat_model=True,
)

# 0.2 加载文档
documents = SimpleDirectoryReader(
    input_files=[Path(__file__).parent.parent / "data/C3/pdf/IPCC_AR6_WGII_Chapter03.pdf"]
).load_data()


# 1. 索引阶段
# 1.1 句子窗口索引
node_parser = SentenceWindowNodeParser.from_defaults(
    window_size=3,
    window_metadata_key="window",
    original_text_metadata_key="original_text",
)
sentence_nodes = node_parser.get_nodes_from_documents(documents)
sentence_index = VectorStoreIndex(sentence_nodes)
sentence_query_engine = sentence_index.as_query_engine(
    similarity_top_k=2,
    node_postprocessors=[
        MetadataReplacementPostProcessor(target_metadata_key="window")
    ],
)

# 1.2 常规分块索引 (对比)
base_parser = SentenceSplitter(chunk_size=512)
base_nodes = base_parser.get_nodes_from_documents(documents)
base_index = VectorStoreIndex(base_nodes)
base_query_engine = base_index.as_query_engine(similarity_top_k=2)


# 2. 检索阶段
query = "What are the concerns surrounding the AMOC?"
print(f"查询: {query}\n")

print("--- 句子窗口检索结果 ---")
window_response = sentence_query_engine.query(query)
print(f"回答: {window_response}\n")

print("--- 常规检索结果 ---")
base_response = base_query_engine.query(query)
print(f"回答: {base_response}\n")
