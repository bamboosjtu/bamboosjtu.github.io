import base64
import io
import random
import sys
import traceback
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import json
from tinydb import Query, TinyDB
import duckdb
import re
import pandas as pd
from dotenv import load_dotenv
import os
from openai import OpenAI
from IPython.display import HTML

load_dotenv()
API_KEY = os.getenv("MODELSCOPE_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_ID = os.getenv("MODEL_ID")
openai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# --------------------------
# print
# --------------------------
def print_html(
    content: Any,
    title: str | None = None,
    is_image: bool = False,
    mode="w",
    output_file="planing.html",
):
    """
    Pretty-print inside a styled card.
    - If is_image=True and content is a string: treat as image path/URL and render <img>.
    - If content is a pandas DataFrame/Series: render as an HTML table.
    - Otherwise (strings/otros): show as code/text in <pre><code>.
    """
    try:
        from html import escape as _escape
    except ImportError:
        _escape = lambda x: x

    def image_to_base64(image_path: str) -> str:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")

    # Render content
    if is_image and isinstance(content, str):
        b64 = image_to_base64(content)
        rendered = f'<img src="data:image/png;base64,{b64}" alt="Image" style="max-width:100%; height:auto; border-radius:8px;">'
    elif isinstance(content, pd.DataFrame):
        rendered = content.to_html(
            classes="pretty-table", index=False, border=0, escape=False
        )
    elif isinstance(content, pd.Series):
        rendered = content.to_frame().to_html(
            classes="pretty-table", border=0, escape=False
        )
    elif isinstance(content, str):
        rendered = f"<pre><code>{_escape(content)}</code></pre>"
    else:
        rendered = f"<pre><code>{_escape(str(content))}</code></pre>"

    css = """
    <style>
    .pretty-card{
      font-family: ui-sans-serif, system-ui;
      border: 2px solid transparent;
      border-radius: 14px;
      padding: 14px 16px;
      margin: 10px 0;
      background: linear-gradient(#fff, #fff) padding-box,
                  linear-gradient(135deg, #3b82f6, #9333ea) border-box;
      color: #111;
      box-shadow: 0 4px 12px rgba(0,0,0,.08);
    }
    .pretty-title{
      font-weight:700;
      margin-bottom:8px;
      font-size:14px;
      color:#111;
    }
    /* 🔒 Solo afecta lo DENTRO de la tarjeta */
    .pretty-card pre, 
    .pretty-card code {
      background: #f3f4f6;
      color: #111;
      padding: 8px;
      border-radius: 8px;
      display: block;
      overflow-x: auto;
      font-size: 13px;
      white-space: pre-wrap;
    }
    .pretty-card img { max-width: 100%; height: auto; border-radius: 8px; }
    .pretty-card table.pretty-table {
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
      color: #111;
    }
    .pretty-card table.pretty-table th, 
    .pretty-card table.pretty-table td {
      border: 1px solid #e5e7eb;
      padding: 6px 8px;
      text-align: left;
    }
    .pretty-card table.pretty-table th { background: #f9fafb; font-weight: 600; }
    </style>
    """

    title_html = f'<div class="pretty-title">{title}</div>' if title else ""
    card = f'<div class="pretty-card">{title_html}{rendered}</div>'

    if mode == "w":
        html_obj = HTML(css + card)
    elif mode == "a":
        html_obj = HTML(card)

    with open(output_file, mode, encoding="utf-8") as f:
        f.write(html_obj.data)


# --------------------------
# database init
# --------------------------
db = TinyDB("store_db.json")
inventory_table = db.table("inventory")
transactions_table = db.table("transactions")


def create_inventory():
    """
    构建太阳镜库存
    """
    random.seed(42)

    sunglasses_data = [
        {
            "item_id": "SG001",
            "name": "Aviator",
            "description": "Originally designed for pilots, these teardrop-shaped lenses with thin metal frames offer timeless appeal. The large lenses provide excellent coverage while the lightweight construction ensures comfort during long wear.",
            "quantity_in_stock": random.randint(3, 25),
            "price": 80,
        },
        {
            "item_id": "SG002",
            "name": "Wayfarer",
            "description": "Featuring thick, angular frames that make a statement, these sunglasses combine retro charm with modern edge. The rectangular lenses and sturdy acetate construction create a confident look.",
            "quantity_in_stock": random.randint(3, 25),
            "price": 95,
        },
        {
            "item_id": "SG003",
            "name": "Mystique",
            "description": "Inspired by 1950s glamour, these frames sweep upward at the outer corners to create an elegant, feminine silhouette. The subtle curves and often embellished temples add sophistication to any outfit.",
            "quantity_in_stock": random.randint(3, 25),
            "price": 70,
        },
        {
            "item_id": "SG004",
            "name": "Sport",
            "description": "Designed for active lifestyles, these wraparound sunglasses feature a single curved lens that provides maximum coverage and wind protection. The lightweight, flexible frames include rubber grips.",
            "quantity_in_stock": random.randint(3, 25),
            "price": 110,
        },
        {
            "item_id": "SG005",
            "name": "Classic",  # renamed from "Round"
            "description": "Classic round profile with minimalist metal frames, offering a timeless and versatile style that fits both casual and formal wear.",
            "quantity_in_stock": random.randint(3, 25),
            "price": 60,  # under $100
        },
        {
            "item_id": "SG006",
            "name": "Moon",  # new entry
            "description": "Oversized round style with bold plastic frames, evoking retro aesthetics with a modern twist.",
            "quantity_in_stock": random.randint(3, 25),
            "price": 120,  # over $100
        },
    ]

    inventory_table.truncate()
    inventory_table.insert_multiple(sunglasses_data)
    return sunglasses_data


def create_transactions(opening_balance=500.00):
    """
    构建初始交易日志
    """
    opening_transaction = {
        "transaction_id": "TXN001",
        "customer_name": "OPENING_BALANCE",
        "transaction_summary": "Daily opening register balance",
        "transaction_amount": opening_balance,
        "balance_after_transaction": opening_balance,
        "timestamp": datetime.now().isoformat(),
    }

    transactions_table.truncate()
    transactions_table.insert(opening_transaction)
    return opening_transaction


def seed_db(db_path="store_db.json"):
    """
    将库存与交易加载到基于 JSON 的存储中
    """
    db = TinyDB(db_path)
    inventory_table = db.table("inventory")
    transactions_table = db.table("transactions")
    create_inventory()  # llena inventory_table
    create_transactions()  # llena transactions_table
    return db, inventory_table, transactions_table


def build_schema_for_table(tbl, table_name: str, k: int = 3) -> str:
    """
    从 TinyDB 表推断列类型、示例值并生成文本 schema。
    """
    rows = tbl.all()
    if not rows:
        return f"TABLE: {table_name} (empty)"

    schema = {}
    for r in rows:
        for k_, v in r.items():
            if k_ not in schema:
                schema[k_] = {"type": type(v).__name__, "examples": []}
            if len(schema[k_]["examples"]) < k and v not in schema[k_]["examples"]:
                schema[k_]["examples"].append(str(v))

    lines = [f"TABLE: {table_name}", "COLUMNS:"]
    for col, info in schema.items():
        ex = f" | examples: {info['examples']}" if info["examples"] else ""
        lines.append(f"  - {col}: {info['type']}{ex}")
    lines.append(f"ROWS: {len(rows)}")
    lines.append(f"PREVIEW (first 3 rows): {rows}")
    return "\n".join(lines)


def build_schema_block(inventory_tbl, transactions_tbl) -> str:
    """
    生成在提示中使用 inventory_db 和 transactions_db 的模式描述。
    """
    inv = build_schema_for_table(inventory_tbl, "inventory_tbl")
    tx = build_schema_for_table(transactions_tbl, "transactions_tbl")
    notes = (
        "NOTES:\n"
        "- inventory_tbl.price is in USD.\n"
        "- inventory_tbl.quantity_in_stock > 0 means available stock.\n"
        "- inventory_tbl.name describes the style (e.g., 'Classic', 'Moon').\n"
        "- transactions_tbl.timestamp is ISO-8601.\n"
    )
    return f"{inv}\n\n{tx}\n\n{notes}"


def get_current_balance(transactions_tbl, default: float = 0.0) -> float:
    """读取交易表最后一笔的余额"""
    txns = transactions_tbl.all()
    return txns[-1].get("balance_after_transaction", default) if txns else default


def next_transaction_id(transactions_tbl, prefix: str = "TXN") -> str:
    """按记录数生成下一个交易 ID"""
    return f"{prefix}{len(transactions_tbl)+1:03d}"


# =========================
# READ tools
# =========================
def t_get_inventory_data(
    con: duckdb.DuckDBPyConnection,
    product_name: Optional[str] = None,
    item_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    DuckDB 查询库存（按 item_id 或名称），返回 DataFrame 与匹配信息。
    """
    if not product_name and not item_id:
        # sin filtros: devolver todo (útil para browse)
        df = con.execute("SELECT * FROM inventory_df").df()
    elif item_id:
        df = con.execute("SELECT * FROM inventory_df WHERE item_id = ?", [item_id]).df()
    else:
        df = con.execute(
            "SELECT * FROM inventory_df WHERE lower(name)=lower(?)", [product_name]
        ).df()
    item = df.iloc[0].to_dict() if len(df) == 1 else None
    return {"rows": df, "match_count": int(len(df)), "item": item}


def t_get_transaction_data(
    con: duckdb.DuckDBPyConnection, mode: str = "last_balance"
) -> dict[str, Any]:
    """
    DuckDB 查询最后一笔交易的余额与 ID。
    """
    if mode == "last_balance":
        df = con.execute(
            "SELECT transaction_id, balance_after_transaction "
            "FROM transaction_df ORDER BY transaction_id DESC LIMIT 1"
        ).df()
        last_id = str(df.iloc[0]["transaction_id"]) if not df.empty else None
        last_bal = (
            float(df.iloc[0]["balance_after_transaction"]) if not df.empty else 0.0
        )
        return {"mode": mode, "last_txn_id": last_id, "last_balance": last_bal}
    return {"mode": mode}


# =========================
# WRITE tools
# =========================
def _next_txn_id(df: pd.DataFrame, prefix: str = "TXN") -> str:
    """
    基于交易 DataFrame 计算下一个交易 ID。
    """
    if df.empty:
        return f"{prefix}001"
    nums = []
    for v in df["transaction_id"].astype(str):
        tail = re.findall(r"(\d+)$", v)
        nums.append(int(tail[0]) if tail else 0)
    nxt = (max(nums) if nums else 0) + 1
    return f"{prefix}{nxt:03d}"


def t_update_inventory(
    inventory_df: pd.DataFrame,
    item_id: str,
    quantity_new: Optional[int] = None,
    delta: Optional[int] = None,
) -> dict[str, Any]:
    """
    按 item_id 更新库存数量（增量或绝对值），返回更新后的 DataFrame 与更新信息。
    """
    if item_id is None:
        return {"error": "item_id_missing"}
    inv = inventory_df.copy()
    inv["item_id"] = inv["item_id"].astype(str)
    mask = inv["item_id"] == str(item_id)
    if not mask.any():
        return {"error": "item_not_found"}
    current = int(inv.loc[mask, "quantity_in_stock"].iloc[0])
    if delta is None and quantity_new is None:
        return {"error": "need_delta_or_quantity_new"}
    new_q = int(quantity_new) if quantity_new is not None else current + int(delta)
    inv.loc[mask, "quantity_in_stock"] = new_q
    return {
        "inventory_df": inv,
        "updated": {"item_id": item_id, "quantity_in_stock": int(new_q)},
    }


def t_append_transaction(
    transaction_df: pd.DataFrame,
    customer_name: str,
    summary: str,
    amount: float,
    txn_prefix: str = "TXN",
) -> dict[str, Any]:
    """
    追加一笔交易并更新余额，返回更新后的 DataFrame 与交易记录。
    """
    out = transaction_df.copy()
    last_bal = (
        float(out["balance_after_transaction"].iloc[-1]) if not out.empty else 0.0
    )
    new_bal = last_bal + float(amount)
    txn_id = _next_txn_id(out, txn_prefix)
    row = {
        "transaction_id": txn_id,
        "customer_name": customer_name,
        "transaction_summary": summary,
        "transaction_amount": float(amount),
        "balance_after_transaction": new_bal,
    }
    out = pd.concat([out, pd.DataFrame([row])], ignore_index=True)
    return {"transaction_df": out, "transaction": row}


# =========================
# 模拟交易
# =========================
def t_propose_transaction(
    con: duckdb.DuckDBPyConnection, customer_name: str, summary: str, amount: float
) -> dict[str, Any]:
    """
    仅计算新增交易后的余额，不修改 DataFrame。
    """
    df = con.execute(
        "SELECT balance_after_transaction FROM transaction_df "
        "ORDER BY transaction_id DESC LIMIT 1"
    ).df()
    last_bal = float(df.iloc[0, 0]) if not df.empty else 0.0
    new_bal = last_bal + float(amount)
    return {
        "transaction_id": "AUTO_TXN",
        "customer_name": customer_name,
        "transaction_summary": summary,
        "transaction_amount": float(amount),
        "balance_after_transaction": new_bal,
    }


# =========================
# Helpers (calculations & validations)
# =========================
def t_compute_total(qty: int, price: float) -> dict[str, Any]:
    """
    按数量与单价计算交易金额（正数）。
    """
    return {"amount": float(qty) * float(price)}


def t_compute_refund(qty: int, price: float) -> dict[str, Any]:
    """
    按数量与单价计算退款金额（负数）。
    """
    return {"amount": -float(qty) * float(price)}


def t_assert_true(value: Any) -> dict[str, Any]:
    ok = bool(value)
    return {"ok": ok}


def t_assert_non_null(value: Any) -> dict[str, Any]:
    return {"ok": value is not None}


def t_assert_gt(value: float, threshold: float) -> dict[str, Any]:
    try:
        return {"ok": float(value) > float(threshold)}
    except Exception:
        return {"ok": False, "reason": "non_numeric"}


def t_assert_nonnegative_stock(
    inventory_df: pd.DataFrame, item_id: str
) -> dict[str, Any]:
    inv = inventory_df
    mask = inv["item_id"].astype(str) == str(item_id)
    if not mask.any():
        return {"ok": False, "reason": "item_not_found"}
    q = int(inv.loc[mask, "quantity_in_stock"].iloc[0])
    return {"ok": q >= 0, "qty": q}


# =========================
# 投影库存
# =========================
def t_project_inventory(
    inventory_df: pd.DataFrame, item_id: str, delta: int
) -> dict[str, Any]:
    """
    库存更新只提供“用 delta 做增量更新”的快捷入口
    """
    return t_update_inventory(inventory_df=inventory_df, item_id=item_id, delta=delta)


# --------------------------
# agent
# --------------------------

PROMPT = """你是一名高级数据助手。通过编写 TINDYDB PYTHON 代码来制定计划。

数据库模式和示例 (只读):
{schema_block}

执行环境 (已导入/已提供):
- 变量: db, inventory_tbl, transactions_tbl  # TinyDB 表对象
- 助手函数: get_current_balance(tbl) -> float, next_transaction_id(tbl, prefix="TXN") -> str
- 自然语言: user_request: str  # 原始用户消息

规划规则 (关键):
- 从 user_request 派生所有过滤器/参数 (形状/关键词, 价格范围 "低于/高于/之间", 库存提及, 数量, 购买/退货意图)。不要硬编码值。
- 使用 Query() 动态构建 TinyDB 查询。如果 user_request 中没有某个约束，则不要应用它。
- 保持保守：如果意图不明确，请执行只读操作 (演习 - DRY RUN)。

交易政策 (硬性规定):
- 不要创建聚合的多项目交易。
- 如果请求包含多个项目，则为每个项目创建单独的交易行。
- 对于每个项目：
  - 计算其自己的单行总计 (unit_price * qty),
  - 插入一笔该金额的交易,
  - 按顺序更新余额 (balance += line_total),
  - 更新该项目的库存。
- 如果任何请求的项目库存不足，不要更改任何数据；回复 STATUS="insufficient_stock"。

人类可读响应要求 (硬性规定):
- 你必须设置一个名为 `answer_text` (str 类型) 的变量，内容为简短、客户友好的句子 (1-2 行)。
- 这个句子是唯一面向用户的消息。没有数据帧/JSON，没有样板式的免责声明。
- 如果没有匹配项，礼貌地说明情况，并提供一个相近的替代方案 (最接近的款式/价格) 或下一步建议。

行动政策:
- 如果请求明确要求改变状态 (购买/采购/退货/补货/调整):
    ACTION="mutate"; SHOULD_MUTATE=True; 执行更改并写入匹配的交易行。
  否则:
    ACTION="read"; SHOULD_MUTATE=False; 模拟并作为演习 (dry run) 简要说明 (仅在日志中)。

失败与边缘情况处理 (必须实现):
- 不要在 Query.test 中捕获外部变量。将它们作为显式参数传递。
- 始终设置一个简短的 `answer_text`。同时设置一个字符串 `STATUS`，其值为以下之一:
  "success", "no_match", "insufficient_stock", "invalid_request", "unsupported_intent"。
- no_match: 没有项目满足过滤器 → 建议风格/价格最接近的，或邀请客户提供不同范围。
- insufficient_stock: 找到项目但库存 < 请求数量 → 说明可用数量，并提供你能满足的最大数量。
- invalid_request: 无法解析基本信息 (例如 购买/退货 的数量) → 简洁地询问缺失的部分。
- unsupported_intent: 该行动超出了商店的能力范围 → 提供最接近的支持替代方案。
- 在所有情况下，保持乐于助人且简洁的语气 (1-2 句话)。仅在 stdout 日志中放入技术细节 (例如 ACTION/DRY RUN)。

输出契约:
- 仅在这些标签之间返回可执行的 Python (没有额外文本):
  <execute_python>
  # 你的 python
  </execute_python>

代码核对清单 (在代码中遵循):
1) 从 user_request 解析意图和约束 (可用正则表达式)。
2) 渐进式构建 TinyDB 条件；查询 inventory_tbl。
3) 如果是变更(mutate)操作: 验证库存, 更新库存, 插入一笔交易 (新 id, 金额, 余额, 时间戳)。
4) 始终设置:
   - `answer_text` (人类可读的句子, 必需),
   - `STATUS` (参见上面的列表)。
   同时向 stdout 打印一个简短的日志, 例如 "LOG: ACTION=read DRY_RUN=True STATUS=no_match"。
5) 可选: 如果有用的话设置 `answer_rows` 或 `answer_json`，但 `answer_text` 是强制性的。

语气示例 (用于 `answer_text`):
- 成功: "是的，我们有经典款太阳镜，这是一款圆形镜框，售价60美元。"
- 无匹配: "我们目前没有100美元以下的圆形镜框库存，但我们的 Moon圆形镜框有货，售价120美元。"
- 库存不足: "Classic款我们只剩下1副了；我可以为您预留。"
- 无效请求: "我可以处理这个——请问您想购买多少副？"
- 不支持的意图: "我们不能翻新镜框，但我可以推荐类似的新款式。"

约束条件:
- 使用 TinyDB Query 进行过滤。仅在需要时使用标准库导入。
- 保持代码清晰，并使用编号步骤进行注释。

用户请求:
{question}
"""


def generate_llm_code(
    prompt: str,
    inventory_tbl,
    transactions_tbl,
    temperature: float = 0.2,
) -> str:
    """
    请求 LLM 生成一个“带代码的计划”响应。
    返回完整的助手内容 (包括周围的文本和标签)。
    实际的代码提取稍后在 execute_generated_code 中进行。
    """
    schema_block = build_schema_block(inventory_tbl, transactions_tbl)
    prompt = PROMPT.format(schema_block=schema_block, question=prompt)

    resp = openai_client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {
                "role": "system",
                "content": "你编写安全、注释良好的 TinyDB 代码来处理数据问题和更新。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        stream=False,
        extra_body={"enable_thinking": False},
    )
    content = resp.choices[0].message.content or ""

    return content


def _extract_execute_block(text: str) -> str:
    """
    返回 <execute_python>...</execute_python> 标签内的 Python 代码。
    如果未找到标签，则假定 'text' 已经是原始 Python 代码。
    """
    if not text:
        raise RuntimeError("空内容被传递给代码执行器。")
    m = re.search(
        r"<execute_python>(.*?)</execute_python>", text, re.DOTALL | re.IGNORECASE
    )
    return m.group(1).strip() if m else text.strip()


def execute_generated_code(
    code_or_content: str,
    *,
    db,
    inventory_tbl,
    transactions_tbl,
    user_request: Optional[str] = None,
) -> Dict[str, Any]:
    """
    在受控的命名空间中执行代码。
    接受原始 Python 代码 或 包含 <execute_python> 标签的完整内容。
    返回最小化的产物：stdout、error 和提取的答案。
    """
    # 在此处提取代码 (现在是集中处理)
    code = _extract_execute_block(code_or_content)

    SAFE_GLOBALS = {
        "Query": Query,
        "get_current_balance": get_current_balance,
        "next_transaction_id": next_transaction_id,
        "user_request": user_request or "",
    }
    SAFE_LOCALS = {
        "db": db,
        "inventory_tbl": inventory_tbl,
        "transactions_tbl": transactions_tbl,
    }

    # 捕获从被执行代码产生的 stdout
    _stdout_buf, _old_stdout = io.StringIO(), sys.stdout
    sys.stdout = _stdout_buf
    err_text = None
    try:
        exec(code, SAFE_GLOBALS, SAFE_LOCALS)
    except Exception:
        err_text = traceback.format_exc()
    finally:
        sys.stdout = _old_stdout
    printed = _stdout_buf.getvalue().strip()

    # 提取由生成代码设置的可能答案
    answer = (
        SAFE_LOCALS.get("answer_text")
        or SAFE_LOCALS.get("answer_rows")
        or SAFE_LOCALS.get("answer_json")
    )

    return {
        "code": code,  # <- 已经没有标签了
        "stdout": printed,
        "error": err_text,
        "answer": answer,
        "transactions_tbl": transactions_tbl.all(),  # 供检查
        "inventory_tbl": inventory_tbl.all(),  # 供检查
    }


if __name__ == "__main__":
    db, inventory_tbl, transactions_tbl = seed_db()
    print_html(
        build_schema_block(inventory_tbl, transactions_tbl), title="表结构", mode="w"
    )
    print_html(json.dumps(inventory_tbl.all(), indent=2), title="库存表", mode="a")
    print_html(json.dumps(transactions_tbl.all(), indent=2), title="交易表", mode="a")

    # 场景1：查找商品（非llm）
    Item = Query()
    round_sunglasses = inventory_tbl.search(
        (Item.description.test(lambda v: " round " in ((v or "").lower())))
        | (Item.name.test(lambda v: " round " in ((v or "").lower())))
    )
    print_html(json.dumps(round_sunglasses, indent=2), title="库存状态", mode="a")

    prompt_round = "你们是否有库存中的 Classic 的太阳镜，且价格低于 100 美元？"

    # 场景1：查找商品（llm）
    full_content_round = generate_llm_code(
        prompt_round,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
    )

    print_html(full_content_round, title="以代码为计划（完整响应）", mode="a")

    result = execute_generated_code(
        full_content_round,
        db=db,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
        user_request=prompt_round,
    )

    print_html(
        result["answer"] or result["error"], title="计划执行 · 提取的答案", mode="a"
    )

    # 场景2：退货商品（非llm）
    Item = Query()  # 创建 Query 对象以引用字段（例如 Item.name、Item.description）

    aviators = inventory_tbl.search((Item.name == "Aviator"))

    print_html(
        json.dumps(aviators, indent=2),
        title="库存状态：退货前的 Aviator 太阳镜",
        mode="a",
    )
    print_html(
        json.dumps(transactions_tbl.all(), indent=2), title="退货前的交易表", mode="a"
    )

    prompt_aviator = "退回我上周购买的 2 副 Aviator 太阳镜。"

    full_content_aviator = generate_llm_code(
        prompt_aviator,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
    )

    print_html(full_content_aviator, title="以代码为计划（完整响应）", mode="a")

    result = execute_generated_code(
        full_content_aviator,
        db=db,
        inventory_tbl=inventory_tbl,
        transactions_tbl=transactions_tbl,
        user_request=prompt_aviator,
    )
    print_html(
        result["answer"] or result["error"], title="计划执行 · 提取的答案", mode="a"
    )
    print_html(json.dumps(inventory_tbl.all(), indent=2), title="库存表", mode="a")
    print_html(json.dumps(transactions_tbl.all(), indent=2), title="交易表", mode="a")
