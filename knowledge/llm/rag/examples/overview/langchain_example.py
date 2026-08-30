import os
from pathlib import Path

# hugging face镜像设置，如果国内环境无法使用启用该设置
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from dotenv import load_dotenv
import json
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import pprint

# import nltk
# nltk.download('punkt', force=True)
# nltk.download('averaged_perceptron_tagger', force=True)

load_dotenv()
markdown_path = Path(__file__).parent.parent / "data/C1/markdown/easy-rl-chapter1.md"


# Step1：Ingest（摄取）：原始文档 → 清洗/切分 → 元数据 → 向量化 → 存储（向量库 + 原文库）
def step1_Ingest(
    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    chunk_size=500,
    chunk_overlap=100,
):
    loader = UnstructuredMarkdownLoader(markdown_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )
    chunks = text_splitter.split_documents(docs)
    lengths = [len(c.page_content) for c in chunks]
    print("num_chunks:", len(chunks))
    print(
        "chunk_len_min/avg/max:",
        min(lengths),
        sum(lengths) // len(lengths),
        max(lengths),
    )

    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    vectorstore = InMemoryVectorStore(embeddings)
    vectorstore.add_documents(chunks)
    return vectorstore


# Step2：Retrieve（检索）：用户问题 → 查询改写/扩展 → 召回（向量/关键词/混合）→ 重排（rerank）
def step2_Retrieve(vectorstore, question, k=3):
    retrieved_docs = vectorstore.similarity_search(question, k)
    # for i, doc in enumerate(retrieved_docs, 1):
    #     meta = getattr(doc, "metadata", {})
    #     preview = doc.page_content[:220].replace("\n", " ")
    #     print(f"[{i}] meta={meta}")
    #     print(preview)
    #     print("-" * 40)
    return retrieved_docs


# Step3：Generate（生成）：把 top-k 证据组织成上下文 → 约束式回答（引用、边界、拒答）
def step3_Generate(retrieved_docs, question):
    prompt = ChatPromptTemplate.from_template(
        """请根据下面提供的上下文信息来回答问题。
    请确保你的回答完全基于这些上下文。
    如果上下文中没有足够的信息来回答问题，请直接告知：“抱歉，我无法根据提供的上下文找到相关信息来回答此问题。”

    上下文:
    {context}

    问题: {question}

    回答:"""
    )

    llm = ChatOpenAI(
        model=os.getenv("SILICONFLOW_MODEL_ID"),
        temperature=0.7,
        max_tokens=4096,
        api_key=os.getenv("SILICONFLOW_API_KEY"),
        base_url=os.getenv("SILICONFLOW_BASE_URL"),
    )
    context = "\n\n".join(doc.page_content for doc in retrieved_docs)
    print(f"Context length: {len(context)}")
    answer = llm.invoke(prompt.format(question=question, context=context))
    return answer, context


def run_minimal():
    question = "文中举了哪些例子？"
    vectorStore = step1_Ingest()
    retrieved_docs = step2_Retrieve(vectorStore, question)
    answer = step3_Generate(retrieved_docs, question)[0]
    print("=== Answer ===")
    print(answer.content)


def run_once(vectorStore, question: str, k: int = 3):
    retrieved_docs = step2_Retrieve(vectorStore, question, k)
    answer, context = step3_Generate(retrieved_docs, question)
    answer_text = answer.content if hasattr(answer, "content") else str(answer)

    # 返回可观测信息（用于错误分析）
    return {
        "question": question,
        "context_chars": len(context),
        "retrieved_previews": [
            d.page_content[:180].replace("\n", " ") for d in retrieved_docs
        ],
        "answer": answer_text,
        "context": context,
    }


def keyword_hit(text: str, keywords: list[str]) -> bool:
    return all(k in text for k in keywords)


def test_k(path: str, k: int = 3):
    """
    top-k: 不同的召回策略。
    """
    total = 0
    ctx_hit = 0
    ans_hit = 0
    vectorStore = step1_Ingest()

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            q = ex["question"]
            expected = ex["expected"]

            out = run_once(vectorStore, q, k=k)

            context_ok = keyword_hit(out["context"], expected)
            answer_ok = keyword_hit(out["answer"], expected)

            total += 1
            ctx_hit += int(context_ok)
            ans_hit += int(answer_ok)

            rows.append(
                {
                    "id": ex.get("id"),
                    "question": q,
                    "expected": expected,
                    "context_ok": context_ok,
                    "answer_ok": answer_ok,
                    "context_chars": out["context_chars"],
                    "answer": out["answer"][:200],
                }
            )

    print("\n=== MINI-EVAL SUMMARY ===")
    print(f"Total: {total}")
    print(f"Context Hit: {ctx_hit}/{total} = {ctx_hit/total:.2f}")
    print(f"Answer  Hit: {ans_hit}/{total} = {ans_hit/total:.2f}")

    # 输出失败样本，方便你定位问题在 retrieval 还是 generation
    print("\n=== FAIL CASES (Answer miss) ===")
    for r in rows:
        if not r["answer_ok"]:
            print(
                f"- {r['id']} | ctx_ok={r['context_ok']} | Q={r['question']} | expected={r['expected']}"
            )
            print(f"  answer_preview={r['answer']}")
    return rows


def test_chunk(path: str, chunk_size: int = 1000, chunk_overlap=200):
    """
    chunk: 不同的切块策略。
    """
    total = 0
    ctx_hit = 0
    ans_hit = 0

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            q = ex["question"]
            expected = ex["expected"]
            vectorStore = step1_Ingest(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            out = run_once(vectorStore, q)

            context_ok = keyword_hit(out["context"], expected)
            answer_ok = keyword_hit(out["answer"], expected)

            total += 1
            ctx_hit += int(context_ok)
            ans_hit += int(answer_ok)

            rows.append(
                {
                    "id": ex.get("id"),
                    "question": q,
                    "expected": expected,
                    "context_ok": context_ok,
                    "answer_ok": answer_ok,
                    "context_chars": out["context_chars"],
                    "answer": out["answer"][:200],
                }
            )

    print("\n=== MINI-EVAL SUMMARY ===")
    print(f"Total: {total}")
    print(f"Context Hit: {ctx_hit}/{total} = {ctx_hit/total:.2f}")
    print(f"Answer  Hit: {ans_hit}/{total} = {ans_hit/total:.2f}")

    # 输出失败样本，方便你定位问题在 retrieval 还是 generation
    print("\n=== FAIL CASES (Answer miss) ===")
    for r in rows:
        if not r["answer_ok"]:
            print(
                f"- {r['id']} | ctx_ok={r['context_ok']} | Q={r['question']} | expected={r['expected']}"
            )
            print(f"  answer_preview={r['answer']}")
    return rows


if __name__ == "__main__":
    # run_minimal()
    # test_k("eval.jsonl", k=3)
    test_chunk("eval.jsonl", chunk_size = 1000, chunk_overlap=200)
