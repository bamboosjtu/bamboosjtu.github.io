import os
from pathlib import Path
import json

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.openai_like import OpenAILike
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

load_dotenv()
docs = SimpleDirectoryReader(
    input_files=[Path(__file__).parent.parent / "data/C1//markdown/easy-rl-chapter1.md"]
).load_data()

Settings.embed_model = HuggingFaceEmbedding("BAAI/bge-small-zh-v1.5")

index = VectorStoreIndex.from_documents(docs)

Settings.llm = OpenAILike(
    model=os.getenv("SILICONFLOW_MODEL_ID"),
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    api_base=os.getenv("SILICONFLOW_BASE_URL"),
    is_chat_model=True,
)

def run_minimal():
    query_engine = index.as_query_engine()
    print(query_engine.get_prompts())
    print(query_engine.query("文中举了哪些例子?"))


def hit_all(text: str, keywords: list[str]) -> bool:
    return all(k in text for k in keywords)


def run_once(question: str, top_k: int = 3):
    qe = index.as_query_engine(similarity_top_k=top_k)
    resp = qe.query(question)
    answer = str(resp)

    # context: 拼接所有检索到的 node 文本（作为“检索证据”）
    nodes_text = []
    for sn in resp.source_nodes:
        node = sn.node
        text = node.get_text() if hasattr(node, "get_text") else node.text
        nodes_text.append(text)
    context = "\n\n".join(nodes_text)

    return answer, context, resp


def eval_file(path: str, top_k: int = 3):
    total = ctx_hit = ans_hit = 0
    fails = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            ex = json.loads(line)
            qid = ex.get("id")
            q = ex["question"]
            expected = ex["expected"]

            answer, context, resp = run_once(q, top_k=top_k)

            ctx_ok = hit_all(context, expected)
            ans_ok = hit_all(answer, expected)

            total += 1
            ctx_hit += int(ctx_ok)
            ans_hit += int(ans_ok)

            if not ans_ok:
                fails.append((qid, ctx_ok, q, expected, answer[:220], resp))

    print("\n=== MINI-EVAL SUMMARY (LlamaIndex) ===")
    print(f"Total: {total}")
    print(f"Context Hit: {ctx_hit}/{total} = {ctx_hit/total:.2f}")
    print(f"Answer  Hit: {ans_hit}/{total} = {ans_hit/total:.2f}")

    if fails:
        print("\n=== FAIL CASES (Answer miss) ===")
        for qid, ctx_ok, q, expected, ans_preview, resp in fails:
            print(f"- {qid} | ctx_ok={ctx_ok} | Q={q} | expected={expected}")
            print(f"  answer_preview={ans_preview}")
            print("---- sources ----")
            for sn in resp.source_nodes[:5]:
                text = sn.node.get_text()
                print("score=", getattr(sn, "score", None), " | ", text[:200].replace("\n"," "))


# 用法
if __name__ == "__main__":
    eval_file("eval.jsonl", top_k=5)
