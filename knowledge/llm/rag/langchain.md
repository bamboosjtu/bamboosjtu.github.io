# LangChain 框架

LangChain 的定位是"组件层"——把模型、提示词、文档加载、切分、向量库、检索器标准化为可拼装的积木。这套抽象在 **RAG 场景**价值最大：一条链路里的每个环节都有现成组件和统一接口。智能体编排（图、状态、恢复）已由 LangGraph 与专用框架承担，见[智能体的演进](knowledge/llm/agents/agent-evolution)。

RAG 链路本身的技术原理见[RAG 技术](knowledge/llm/rag/rag-techniques)，本文只讲工具箱。

## 一、最小上手

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

class TopicInfo(BaseModel):
    task_name: str = Field(description="概念名称")
    description: str = Field(description="概述解释")
    example: str = Field(description="代码示例")


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个黑客松教练。请用简洁、准确的方式回答。"),
        ("human", "请总结概念：{topic}"),
    ]
)

structured_llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL_ID"),
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
).with_structured_output(TopicInfo)

chain = prompt | structured_llm

result = chain.invoke({"topic": "LangChain 中的 ChatPromptTemplate"})
print(result)
```

要点：

- `ChatPromptTemplate` 组合 System/Human 消息；
- `.with_structured_output(PydanticModel)` 直接拿到结构化对象；
- `prompt | llm` 是 LCEL 管道语法——所有组件实现统一的 Runnable 接口（`.invoke() / .batch() / .stream()`），因此可以任意串联、并行、分支。

## 二、包生态地图

| 包名 | 安装命令 | 职责 |
| --- | --- | --- |
| **langchain-core** | `pip install langchain-core` | 最底层抽象：BaseChatModel、BaseRetriever、BaseTool 等接口基类，不依赖具体服务 |
| **langchain** | `pip install langchain` | 核心框架：Chains、Agents、Memory 等高层抽象与预置实现 |
| **langchain-community** | `pip install langchain-community` | 社区集成集合（大量第三方 Loader、Tool、VectorStore） |
| **langchain-text-splitters** | `pip install langchain-text-splitters` | 文本切分算法（Recursive、Token、Markdown、Code 等） |

### 核心模块速查

| 目录 | 核心基类/导出 | 职责 |
| --- | --- | --- |
| `language_models/` | `BaseChatModel`, `BaseLLM` | 语言模型抽象 |
| `messages/` | `AIMessage`, `HumanMessage`, `SystemMessage`, `ToolMessage` | 消息类型体系 |
| `prompts/` | `ChatPromptTemplate`, `FewShotPromptTemplate` | 提示词模板系统 |
| `output_parsers/` | `StrOutputParser`, `JsonOutputParser`, `PydanticOutputParser` | 输出解析 |
| `tools/` | `BaseTool`, `tool` 装饰器 | 工具抽象 |
| `runnables/` | `Runnable`, `RunnableSequence`, `RunnableParallel` | **LCEL 核心**，统一调用接口 |
| `documents/` | `Document` | 文档数据模型（page_content + metadata） |
| `embeddings/` | `Embeddings` | 嵌入模型抽象 |
| `vectorstores/` | `VectorStore` | 向量库抽象（`add_texts`, `similarity_search`） |
| `retrievers/` | `BaseRetriever` | 检索器抽象 |

## 三、RAG 关键组件

### 1. 文档加载

`document_loaders` 把 PDF、网页、Word、数据库记录统一转成 `Document`：

```python
from langchain_community.document_loaders import WebBaseLoader
loader = WebBaseLoader("https://example.com")
docs = loader.load()
```

加载后的清洗（去页眉页脚、保留章节结构）是工程经验活，官方教程常略过，但切块与召回的质量都取决于这一步。

### 2. 文本切分

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(docs)
```

通用场景从 `RecursiveCharacterTextSplitter` 开始（优先按段落/换行等自然边界切）。切分策略的原理讨论见[RAG 技术](knowledge/llm/rag/rag-techniques)。

### 3. 嵌入与向量存储

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector

embedding_models = OpenAIEmbeddings(model=os.getenv("LLM_EMBEDDING_ID"),
                                    base_url=os.getenv("LLM_BASE_URL"),
                                    api_key=os.getenv("LLM_API_KEY"))

db = PGVector.from_documents(chunks, embedding_models,
                             connection_string="postgresql+psycopg2://postgres:***@localhost:5432/postgres")
```

向量库选型与索引原理见[RAG 技术](knowledge/llm/rag/rag-techniques)。常用向量库包：`langchain-chroma / -faiss / -qdrant / -milvus / -pgvector / -elasticsearch` 等。

查询阶段的检索器用法：

```python
retriever = db.as_retriever()
docs = retriever.invoke("what is langchain?")
```

查询改写、路由、混合检索等进阶手段见[RAG 技术](knowledge/llm/rag/rag-techniques)。

## 四、模型集成商

按需安装对应的 provider 包：`langchain-openai`、`langchain-anthropic`、`langchain-google-genai`、`langchain-ollama`（本地）、`langchain-huggingface`、`langchain-cohere` 等。

本地模型的典型接法（HuggingFace Pipeline）：

```python
# pip install langchain-huggingface transformers torch
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

model_name = "./models/Qwen/Qwen3-0___6B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer,
                max_new_tokens=200, temperature=0.3)

hf_llm = HuggingFacePipeline(pipeline=pipe)
print(hf_llm.invoke("请用3句话解释什么是LangChain？"))
```

## 五、安装清单与观测

```bash
pip install -U langchain-openai        # 或其他 provider 包
pip install -U langchain langchain-core langchain-community
pip install -U langgraph               # 需要状态化编排时
```

- 生产环境建议配合 **LangSmith** 做 tracing、debug 与评估；
- **langserve** 可将 Chain 部署为 REST API。

实践代码：[`examples/overview/langchain_example.py`](./examples/overview/langchain_example.py ":include")。
