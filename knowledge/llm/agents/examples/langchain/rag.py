from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
import os

LLM_EMBEDDING_ID = os.getenv("LLM_EMBEDDING_ID")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")


# 索引构建阶段
loader = WebBaseLoader("https://www.langchain.com/")
docs = loader.load()


splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
)
chunks = splitter.split_documents(docs)


embedding_models = OpenAIEmbeddings(
    model=LLM_EMBEDDING_ID,
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)
embeddings = embedding_models.embed_documents([chunk.page_content for chunk in chunks])

CONNECTION_STRING = "postgresql+psycopg2://postgres:victory@localhost:5432/postgres"

db = PGVector.from_documents(
    chunks, embedding_models, connection_string=CONNECTION_STRING
)

# 查询生成阶段
retriever = db.as_retriever()
retriever.invoke("what is langchain.")
