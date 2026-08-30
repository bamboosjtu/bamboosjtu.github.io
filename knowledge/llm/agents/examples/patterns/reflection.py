from typing import Any
from dotenv import load_dotenv
import os
import pandas as pd
import json
import sqlite3
from openai import OpenAI
import re
import requests
import base64
from IPython.display import HTML
import matplotlib.pyplot as plt

load_dotenv()
API_KEY = os.getenv("MODELSCOPE_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_ID = os.getenv("MODEL_ID")
openai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# --------------------------
# Tool
# --------------------------
def upload_image(image_path: str) -> str:
    url = "https://uguu.se/upload"
    with open(image_path, "rb") as f:
        files = {"files[]": (image_path.split("\\")[-1], f)}
        resp = requests.post(url, files=files, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # 典型返回：{"success":true,"files":[{"url":"https://uguu.se/xxxx.png", ...}]}
    return data["files"][0]["url"]


def load_data(file_name):
    df = pd.read_csv(file_name)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    return df


def get_schema(db_path: str) -> str:
    """
    Return only the schema that the agent should use: 'transactions' table.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(transactions)")
    rows = cur.fetchall()
    conn.close()
    return "table name: transactions\n" + "\n".join([f"{r[1]} ({r[2]})" for r in rows])


# --------------------------
# agent
# --------------------------
def get_llm_response(prompt):
    resp = (
        openai_client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            stream=False,
            extra_body={"enable_thinking": False},
        )
        .choices[0]
        .message.content
    )
    return resp


def example1(file_name):
    # 1. 加载数据
    df = load_data(file_name)
    tracks = []

    instruction = "使用 coffee_sales.csv 中的数据，创建一张对比 2024 与 2025 年第一季度咖啡销售的图表。"
    out_path_v1 = "example1_chart_v1.png"
    out_path_v2 = "example1_chart_v2.png"

    # 2. 生成数据可视化V1代码
    print(f"调用llm生成...")
    code_v1 = generate_chart_code(
        instruction=instruction,
        out_path_v1=out_path_v1,
    )
    tracks.append(output_html(code_v1, title="Round 1：LLM 输出的首版代码", init=True))

    # 3. 执行V1代码，生成图片
    result = parse_and_execute(code_v1, df)
    print(f"解析代码并执行成功。")
    tracks.append(output_html(out_path_v1, title="Round 1：图片输出", is_image=True))

    # 4. 反思V1代码、结果，生成V2代码
    print(f"开始上传图床。")
    chart_url = upload_image(out_path_v1)
    print(f"图床外链：{chart_url}")

    print(f"调用llm反思...")
    resp = reflect_chart_code(
        chart_path=chart_url,
        code_v1=code_v1,  # 传入原始代码作为上下文
        instruction=instruction,
        out_path_v2=out_path_v2,
    )

    # 5. 执行V2代码，生成图片
    feedback, code_v2 = parse_and_improve(resp)
    tracks.append(output_html(feedback, title="Refelction 2：LLM 输出的评审意见"))
    tracks.append(output_html(code_v2, title="Refelction 2：LLM 优化后的输出代码"))

    result = parse_and_execute(code_v2, df)
    print(f"解析代码并执行成功。")
    tracks.append(
        output_html(out_path_v2, title="Refelction 2：图片输出", is_image=True)
    )

    with open("example1.html", "w", encoding="utf-8") as f:
        f.write("\n".join(tracks))


def generate_chart_code(instruction: str, out_path_v1: str) -> str:
    """生成使用 matplotlib 绘图的 Python 代码，并用标签包裹返回。"""

    prompt = f"""
    你是一位数据可视化专家。

    请*严格*按以下格式返回你的答案：

    <execute_python>
    # 在此填写有效的 Python 代码
    </execute_python>

    不要添加任何解释，仅包含上述标签与代码。

    代码需基于名为 'df' 的 DataFrame 生成可视化，其列包括：
    - date (M/D/YY)
    - time (HH:MM)
    - cash_type (card 或 cash)
    - card (string)
    - price (number)
    - coffee_name (string)
    - quarter (1-4)
    - month (1-12)
    - year (YYYY)

    用户指令：{instruction}

    代码要求：
    1. 假设 DataFrame 已加载为 'df'。
    2. 使用 matplotlib 进行绘图。
    3. 添加清晰的标题、坐标轴标签，并在需要时添加图例。
    4. 将图像以 '{out_path_v1}' 保存，dpi=300。
    5. 不要调用 plt.show()。
    6. 使用 plt.close() 关闭所有图。
    7. 补充所有必要的 import 语句。

    仅返回包含在 <execute_python> 标签中的代码。
    """
    response = get_llm_response(prompt)
    return response


def reflect_chart_code(
    chart_path: str,
    code_v1: str,
    instruction: str,
    out_path_v2: str,
) -> tuple[str, str]:
    """
    根据给定指令评审图表图像与原始代码，
    然后返回改进后的 matplotlib 代码。
    返回值：(feedback, refined_code_with_tags)。
    支持 OpenAI 与 Anthropic（Claude）。
    """
    # media_type, b64 = encode_image_b64(chart_path)

    prompt = f"""
    你是一位数据可视化专家。
    你的任务：依据给定指令评审附件中的图表与原始代码，
    并返回改进后的 matplotlib 代码。

    原始代码（用于提供上下文）：
    {code_v1}

    原始图片链接：
    {chart_path}

    输出格式（严格遵守！）：
    1) 第一行：仅包含 "feedback" 字段的有效 JSON 对象。
    示例：{{"feedback": "图例不清晰，且坐标轴标签存在重叠。"}}

    2) 换行后，仅输出用如下标签包裹的改进版 Python 代码：
    <execute_python>
    ...
    </execute_python>

    3) 在代码中导入所有必要的库。不要依赖原始代码中的 import。

    强约束：
    - 除上述两部分外，不要包含 Markdown、反引号或任何额外说明文字。
    - 仅使用 pandas/matplotlib（不使用 seaborn）。
    - 假设 df 已存在；不要从文件读取。
    - 保存到 '{out_path_v2}'，dpi=300。
    - 结尾始终调用 plt.close()（不要使用 plt.show()）。
    - 包含所有必要的 import 语句。

    架构（df 中可用的列）：
    - date (M/D/YY)
    - time (HH:MM)
    - cash_type (card 或 cash)
    - card (string)
    - price (number)
    - coffee_name (string)
    - quarter (1-4)
    - month (1-12)
    - year (YYYY)

    指令：
    {instruction}
    """
    resp = get_llm_response(prompt)
    return resp


def parse_and_execute(resp, df):
    # 提取 <execute_python> 标签中的代码
    match = re.search(r"<execute_python>([\s\S]*?)</execute_python>", resp)
    if match:
        initial_code = match.group(1).strip()
        exec_globals = {"df": df}
        exec(initial_code, exec_globals)
        return initial_code


def parse_and_improve(resp):
    # --- 仅解析第一行 JSON（feedback） ---
    lines = resp.strip().splitlines()
    json_line = lines[0].strip() if lines else ""

    try:
        obj = json.loads(json_line)
    except Exception as e:
        # 回退：尝试在完整内容中捕获第一个 {...}
        m_json = re.search(r"\{.*?\}", resp, flags=re.DOTALL)
        if m_json:
            try:
                obj = json.loads(m_json.group(0))
            except Exception as e2:
                obj = {"feedback": f"Failed to parse JSON: {e2}", "refined_code": ""}
        else:
            obj = {"feedback": f"Failed to find JSON: {e}", "refined_code": ""}
    feedback = str(obj.get("feedback", "")).strip()

    # --- 从 <execute_python>...</execute_python> 中提取改进代码 ---
    m_code = re.search(r"<execute_python>([\s\S]*?)</execute_python>", resp)
    refined_code_body = m_code.group(1).strip() if m_code else ""
    refined_code = ensure_execute_python_tags(refined_code_body)
    return feedback, refined_code


def ensure_execute_python_tags(text: str) -> str:
    """Normalize code to be wrapped in <execute_python>...</execute_python>."""
    text = text.strip()
    # Strip ```python fences if present
    text = re.sub(r"^```(?:python)?\s*|\s*```$", "", text).strip()
    if "<execute_python>" not in text:
        text = f"<execute_python>\n{text}\n</execute_python>"
    return text


def example2(db_path):
    tracks = []

    schema = get_schema(db_path)
    tracks.append(output_html(schema, "数据库结构", init=True))

    # Round 1：思考
    question = "哪种颜色的产品总销售额最高？"
    sql_V1 = generate_sql(question, schema)
    tracks.append(output_html(sql_V1, "第一版SQL语句"))

    # Round 1：执行
    df_sql_V1 = execute_sql(sql_V1, db_path=db_path)
    tracks.append(output_html(df_sql_V1, "第一版执行结果"))

    # Reflection 1：思考
    feedback, sql_V2 = reflect_sql(question=question, sql_query=sql_V1, schema=schema)
    tracks.append(output_html(feedback, "反思"))
    tracks.append(output_html(sql_V2, "优化后的SQL语句"))

    # Reflection 1：执行
    df_sql_V2 = execute_sql(sql_V2, db_path=db_path)
    tracks.append(output_html(df_sql_V2, "优化后的执行结果"))

    # Reflection 2：思考
    feedback, sql_V3 = reflect_sql_external_feedback(
        question=question, sql_query=sql_V1, df_feedback=df_sql_V1, schema=schema
    )
    tracks.append(output_html(feedback, "借助外部工具反馈的反思"))
    tracks.append(output_html(sql_V3, "借助外部工具优化后的SQL语句"))

    # Reflection 1：执行
    df_sql_V3 = execute_sql(sql_V3, db_path=db_path)
    tracks.append(output_html(df_sql_V3, "借助外部工具优化后的执行结果"))

    with open("example2.html", "w", encoding="utf-8") as f:
        f.write("\n".join(tracks))


def generate_sql(question: str, schema: str) -> str:
    prompt = f"""
    你是一名 SQL 助理。根据给定的数据库架构与用户问题，编写适用于 SQLite 的 SQL 查询。

    架构：
    {schema}

    用户问题：
    {question}

    仅返回 SQL 语句。
    """
    resp = get_llm_response(prompt)
    return resp


def reflect_sql(
    question: str,
    sql_query: str,
    schema: str,
) -> tuple[str, str]:
    """
    反思查询的“展示输出”是否回答了用户问题，
    如有需要，提出改进版 SQL。
    返回 (feedback, refined_sql)。
    """
    prompt = f"""
你是一位 SQL 审查与优化专家。

用户问题：
{question}

原始 SQL：
{sql_query}

表架构：
{schema}

步骤 1：简要评估 SQL 输出是否完整回答用户问题。
步骤 2：若需要改进，请提供适用于 SQLite 的优化版 SQL 查询。
若原始 SQL 已正确，请保持不变返回。

严格返回仅包含以下两个字段的 JSON：
{{
  "feedback": "<1-3 句解释问题或确认正确性>",
  "refined_sql": "<final SQL to run>"
}}
"""
    resp = get_llm_response(prompt)
    try:
        obj = json.loads(resp)
        feedback = str(obj.get("feedback", "")).strip()
        refined_sql = str(obj.get("refined_sql", sql_query)).strip()
        if not refined_sql:
            refined_sql = sql_query
    except Exception:
        resp = ensure_execute_json_tags(resp)
        obj = json.loads(resp)
        feedback = str(obj.get("feedback", "")).strip()
        refined_sql = str(obj.get("refined_sql", sql_query)).strip()
        if not refined_sql:
            refined_sql = sql_query

    return feedback, refined_sql


def reflect_sql_external_feedback(
    question: str,
    sql_query: str,
    df_feedback: pd.DataFrame,
    schema: str,
) -> tuple[str, str]:
    """
    评估 SQL 结果是否回答用户问题；如有必要，提出改进版查询。
    返回 (feedback, refined_sql)。
    """
    prompt = f"""
    你是一位 SQL 审查与优化专家。

    用户问题：
    {question}

    原始 SQL：
    {sql_query}

    SQL 输出：
    {df_feedback.to_markdown(index=False)}

    表架构：
    {schema}

    步骤 1：简要评估该 SQL 输出是否回答了用户问题。
    步骤 2：若可改进，请提供优化后的 SQL 查询。
    若原始 SQL 已正确，请保持不变返回。

    请严格返回仅包含以下两个字段的 JSON 对象：
    - "feedback": 简短评估与建议
    - "refined_sql": 需要执行的最终 SQL
    """

    resp = get_llm_response(prompt)
    try:
        obj = json.loads(resp)
        feedback = str(obj.get("feedback", "")).strip()
        refined_sql = str(obj.get("refined_sql", sql_query)).strip()
        if not refined_sql:
            refined_sql = sql_query
    except Exception:
        # 若模型未返回有效 JSON 的回退处理：
        # 使用原始内容作为反馈并保留原始 SQL
        resp = ensure_execute_json_tags(resp)
        obj = json.loads(resp)
        feedback = str(obj.get("feedback", "")).strip()
        refined_sql = str(obj.get("refined_sql", sql_query)).strip()
        if not refined_sql:
            refined_sql = sql_query

    return feedback, refined_sql


def execute_sql(query: str, db_path: str) -> pd.DataFrame:
    """
    Execute any SELECT over the event-sourced 'transactions' table.
    """
    q = query.strip().removeprefix("```sql").removesuffix("```").strip()
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(q, conn)
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})
    finally:
        conn.close()


def ensure_execute_json_tags(text: str) -> str:
    """Normalize code to be wrapped in <execute_python>...</execute_python>."""
    text = text.strip()
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return m.group(1)


# --------------------------
# Print
# --------------------------
def output_html(
    content: Any, title: str | None = None, is_image: bool = False, init=False
):
    """
    Pretty-print inside a styled card.
    - If is_image=True and content is a string: treat as image path/URL and render <img>.
    - If content is a pandas DataFrame/Series: render as an HTML table.
    - Otherwise (strings/others): show as code/text in <pre><code>.
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
    /* 🔒 Only affects INSIDE the card */
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
    if init:
        html_obj = HTML(css + card)
    else:
        html_obj = HTML(card)

    html_str = html_obj.data
    return html_str


if __name__ == "__main__":
    file_name = r"./coffee_sales.csv"
    example1(file_name)
    db_path = r"./products.db"
    example2(db_path)
