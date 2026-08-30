import base64
from datetime import datetime
import json
import re
from typing import Any
import pandas as pd
import requests
import urllib
import wikipedia
from tools import Tools
from dotenv import load_dotenv
from pprint import pprint
import os
from openai import OpenAI
from tavily import TavilyClient
import xml.etree.ElementTree as ET
from IPython.display import HTML

load_dotenv()
API_KEY = os.getenv("MODELSCOPE_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_ID = os.getenv("MODEL_ID")
openai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# --------------------------
# tool
# --------------------------
def arxiv_search_tool(query: str, max_results: int = 5) -> list[dict]:
    """
    Searches arXiv for research papers matching the given query.
    Args:
        query (str): The search query.
        max_results (int): Number of results to return (default 5).
    Returns:
        list[dict]: A list of dictionaries with keys like 'title', 'authors', 'published'， ‘url', 'summary', and 'link_pdf'.
    """
    url = f"https://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
    session = requests.Session()
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return [{"error": str(e)}]

    try:
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        results = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip()
            authors = [
                author.find("atom:name", ns).text
                for author in entry.findall("atom:author", ns)
            ]
            published = entry.find("atom:published", ns).text[:10]
            url_abstract = entry.find("atom:id", ns).text
            summary = entry.find("atom:summary", ns).text.strip()

            link_pdf = None
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title") == "pdf":
                    link_pdf = link.attrib.get("href")
                    break

            results.append(
                {
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "url": url_abstract,
                    "summary": summary,
                    "link_pdf": link_pdf,
                }
            )

        return results
    except Exception as e:
        return [{"error": f"Parsing failed: {str(e)}"}]


arxiv_tool_def = {
    "type": "function",
    "function": {
        "name": "arxiv_search_tool",
        "description": "Searches for research papers on arXiv by query string.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords for research papers.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


def tavily_search_tool(
    query: str, max_results: int = 5, include_images: bool = False
) -> list[dict]:
    """
    Perform a search using the Tavily API.
    Args:
        query (str): The search query.
        max_results (int): Number of results to return (default 5).
        include_images (bool): Whether to include image results.
    Returns:
        list[dict]: A list of dictionaries with keys like 'title', 'content', and 'url'.
    """
    params = {}
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables.")
    params["api_key"] = api_key

    client = TavilyClient(api_key)

    try:
        response = client.search(
            query=query, max_results=max_results, include_images=include_images
        )

        results = []
        for r in response.get("results", []):
            results.append(
                {
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", ""),
                }
            )

        if include_images:
            for img_url in response.get("images", []):
                results.append({"image_url": img_url})

        return results

    except Exception as e:
        return [{"error": str(e)}]


tavily_tool_def = {
    "type": "function",
    "function": {
        "name": "tavily_search_tool",
        "description": "Performs a general-purpose web search using the Tavily API.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords for retrieving information from the web.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 5,
                },
                "include_images": {
                    "type": "boolean",
                    "description": "Whether to include image results.",
                    "default": False,
                },
            },
            "required": ["query"],
        },
    },
}


def wikipedia_search_tool(query: str, sentences: int = 5) -> list[dict]:
    """
    Searches Wikipedia for a summary of the given query.
    Args:
        query (str): Search query for Wikipedia.
        sentences (int): Number of sentences to include in the summary.
    Returns:
        list[dict]: A list with a single dictionary containing title, summary, and URL.
    """
    try:
        page_title = wikipedia.search(query)[0]
        page = wikipedia.page(page_title)
        summary = wikipedia.summary(page_title, sentences=sentences)

        return [{"title": page.title, "summary": summary, "url": page.url}]
    except Exception as e:
        return [{"error": str(e)}]


wikipedia_tool_def = {
    "type": "function",
    "function": {
        "name": "wikipedia_search_tool",
        "description": "Searches for a Wikipedia article summary by query string.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords for the Wikipedia article.",
                },
                "sentences": {
                    "type": "integer",
                    "description": "Number of sentences in the summary.",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


# --------------------------
# Print
# --------------------------
def pretty_print_chat_completion_html(response):
    def format_json(data):
        try:
            return json.dumps(data, indent=2)
        except:
            return str(data)

    steps_html = ""
    tool_sequence = []
    choice = response.choices[0]
    intermediate_messages = getattr(choice, "intermediate_messages", [])

    step_ = 0
    for step in intermediate_messages:
        if hasattr(step, "tool_calls") and step.tool_calls:
            for call in step.tool_calls:
                step_ += 1
                tool_name = call.function.name
                tool_sequence.append(tool_name)
                args = json.loads(call.function.arguments)
                steps_html += f"""
                <div style="border-left: 4px solid #444; margin: 10px 0; padding: 10px; background: #f0f0f0;">
                    <strong style="color:#222;">🧠 LLM Action [{step_}]:</strong> <code>调用函数{tool_name}</code>
                    <pre style="color:#000; font-size:13px;">参数：{format_json(args)}</pre>
                </div>
                """
        elif isinstance(step, dict) and step.get("role") == "tool":
            tool_name = step.get("name")
            tool_output = step.get("content")
            try:
                parsed_output = json.loads(tool_output)
            except:
                parsed_output = tool_output
            steps_html += f"""
            <div style="border-left: 4px solid #007bff; margin: 10px 0; padding: 10px; background: #eef6ff;">
                <strong style="color:#222;">🔧 Tool Response [{step_}]:</strong> <code>函数{tool_name}执行</code>
                <pre style="color:#000; font-size:13px;">结果：{format_json(parsed_output)}</pre>
            </div>
            """

    final_msg = choice.message.content
    steps_html += f"""
    <div style="border-left: 4px solid #28a745; margin: 20px 0; padding: 10px; background: #eafbe7;">
        <strong style="color:#222;">✅ Final Assistant Message:</strong>
        <p style="color:#000;">最终结果：{final_msg}</p>
    </div>
    """

    if tool_sequence:
        arrow_sequence = " → ".join(tool_sequence)
        steps_html += f"""
        <div style="border-left: 4px solid #666; margin: 20px 0; padding: 10px; background: #f8f9fa;">
            <strong style="color:#222;">🧭 Tool Sequence:</strong>
            <p style="color:#000;">{arrow_sequence}</p>
        </div>
        """

    html_obj = HTML(steps_html)
    with open("research_inter.html", "w", encoding="utf-8") as f:
        f.write(html_obj.data)


def print_html(
    content: Any,
    title: str | None = None,
    is_image: bool = False,
    output_file: str = "research.html",
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
    html_obj = HTML(css + card)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_obj.data)


# --------------------------
# agent
# --------------------------


def get_llm_response(messages, tools):
    resp = openai_client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        tools=tools,
        temperature=0.2,
        tool_choice="auto",
        stream=False,
        extra_body={"enable_thinking": False},
    )
    return resp


def find_references_with_intermediate(task: str, tools: list[Any]):
    """使用外部工具（arxiv、tavily、wikipedia）执行研究任务。"""

    prompt = f"""
    你是一个研究学者，可以访问：
    - arxiv_tool：学术论文
    - tavily_tool：通用网页搜索（需要时返回 JSON）
    - wikipedia_tool：百科式摘要

    任务：
    {task}

    今天是 {datetime.now().strftime('%Y-%m-%d')}。

    特别强调：
    - 要从多种渠道搜索
    - 选出其中最可信的内容
    - 输出要包含来源url
    """.strip()

    messages = [{"role": "user", "content": prompt}]

    tools_instance = Tools(tools)
    tool_regsitry = tools_instance.tools()

    turns = 0
    intermediate_responses = []
    intermediate_messages = []

    while turns < 10:
        # 2. 调 LLM
        response = get_llm_response(messages, tools=tool_regsitry)
        response = extract_thinking_content(response)

        # 在response中加入intermediate_responses
        intermediate_responses.append(response)
        tool_calls = (
            getattr(response.choices[0].message, "tool_calls", None)
            if hasattr(response, "choices")
            else None
        )
        intermediate_messages.append(response.choices[0].message)

        if not tool_calls:
            # 3. 没有 tool_calls，说明对话结束，返回最终结果
            response.intermediate_responses = intermediate_responses[:-1]
            response.choices[0].intermediate_messages = intermediate_messages
            return response

        # 4. 有 tool_calls，就用 Tools 去执行你的普通函数
        results, tool_messages = tools_instance.execute_tool(tool_calls)

        # 5. 把工具结果消息追加进 messages，继续下一轮
        intermediate_messages.extend(tool_messages)
        messages.extend([response.choices[0].message, *tool_messages])

        turns += 1

    response.intermediate_responses = intermediate_responses[:-1]
    response.choices[0].intermediate_messages = intermediate_messages
    return response


def extract_thinking_content(response):
    """
    解析llm的返回，提取think标签内容。
    """
    if hasattr(response, "choices") and response.choices:
        message = response.choices[0].message
        if hasattr(message, "content") and message.content:
            content = message.content.strip()
            if content.startswith("<think>") and "</think>" in content:
                start_idx = len("<think>")
                end_idx = content.find("</think>")
                thinking_content = content[start_idx:end_idx].strip()
                message.reasoning_content = thinking_content
                message.content = content[end_idx + len("</think>") :].strip()
    return response


def clean_json_block(raw: str) -> str:
    """
    从一段字符串中去掉包裹 JSON 的 Markdown 代码块标记（或json），
    返回：
        干净的 JSON 文本。
    """
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return raw.strip()


# --------------------------
# evaluation
# --------------------------
_URL_RE = re.compile(r"https?://[^\s\)\]\}<>\"']+", re.IGNORECASE)


def _extract_hostname(url: str) -> str:
    """
    从一个 URL 字符串中提取“主机名（hostname）”，并去掉前缀 www.，
    返回：
        一个干净的域名；如果解析失败则返回空字符串
    """
    try:
        host = urllib.parse.urlparse(url).hostname or ""
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def extract_urls(text: str) -> list[dict[str, Any]]:
    """
    从一段任意文本中尽量提取出所有 URL，
    返回把每个 URL 规范化成一个统一结构的字典列表，其中：
        - url：原始 URL
        - source：URL 的主机名（去掉 www.），作为来源
        - title：占位字段，目前始终为 None
    """
    if not isinstance(text, str):
        text = str(text)
    urls = _URL_RE.findall(text)
    items = []
    for u in urls:
        host = _extract_hostname(u)
        items.append({"title": None, "url": u, "source": host or None})
    return items


def evaluate_anytext_against_domains(
    TOP_DOMAINS: set[str], payload: Any, min_ratio: float = 0.4
):
    """
    输入：
      - raw list[dict] (Tavily-like), or
      - raw string (free text with links), or
      - dict with 'results' list
    规则：
        判断一段内容里的链接，有多少比例来自指定的可信域名（TOP_DOMAINS）集合，
        如果达到最小比例（默认 40%），就判定通过。
    返回：
        - ok：一个“是否合规”的布尔结果
        - report_dict：一份详细评估报告
    """
    items = []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        items = payload["results"]
    elif isinstance(payload, str):
        s = payload.strip()
        if s.startswith("```"):
            s = re.sub(r"^```(?:json|text|markdown)?\s*", "", s)
            s = re.sub(r"\s*```$", "", s)
        try:
            maybe = json.loads(s)
            if isinstance(maybe, list):
                items = maybe
            else:
                items = extract_urls(payload)
        except Exception:
            items = extract_urls(payload)
    else:
        items = extract_urls(str(payload))

    total = len(items)
    if total == 0:
        return False, {
            "total": 0,
            "approved": 0,
            "ratio": 0.0,
            "details": [],
            "note": "No items/links parsed",
        }

    details = []
    approved = 0
    for it in items:
        url = (it or {}).get("url")
        host = _extract_hostname(url or "")
        ok = any(host.endswith(dom) for dom in TOP_DOMAINS) if host else False
        if ok:
            approved += 1
        details.append(
            {
                "title": (it or {}).get("title"),
                "url": url,
                "host": host,
                "approved": ok,
            }
        )

    ratio = approved / max(total, 1)
    ok = ratio >= min_ratio
    return ok, {
        "total": total,
        "approved": approved,
        "ratio": ratio,
        "details": details,
        "min_ratio": min_ratio,
    }


def evaluate_references(
    history: list[tuple[str, str, str]], TOP_DOMAINS: set[str], min_ratio: float = 0.4
) -> str:
    """
    在一段多步骤对话/执行历史中，自动找到“研究来源输出”，
    评估其中链接的可信域名占比是否达标，并生成一段可直接展示的 Markdown 格式“通过 / 失败”评估报告。
    """
    # 1) 从 history 里找最近一次 research_agent 的输出（或兜底文本）
    payload = None
    for step, agent, output in reversed(history):
        if agent == "research_agent":
            payload = output
            break
    if payload is None:
        for _, _, output in reversed(history):
            if isinstance(output, str) and (
                ("http://" in output)
                or ("https://" in output)
                or ("[" in output and "]" in output)
            ):
                payload = output
                break

    # 2) 提取其中的链接，检查这些链接是否主要来自 TOP_DOMAINS，
    #    如果比例 ≥ min_ratio，就 PASS，否则 FAIL，并输出一段 Markdown 评估表。
    if payload is None:
        ok, report = False, {
            "total": 0,
            "approved": 0,
            "ratio": 0.0,
            "details": [],
            "min_ratio": min_ratio,
        }
    else:
        ok, report = evaluate_anytext_against_domains(
            TOP_DOMAINS, payload, min_ratio=min_ratio
        )

    status = "✅ PASS" if ok else "⚠️ FAIL"
    header = f"### Evaluation — Tavily Top Domains ({status})"
    summary = (
        f"- Total: {report['total']}\n"
        f"- Approved: {report['approved']}\n"
        f"- Ratio: {report['ratio']:.0%} (min {int(min_ratio*100)}%)\n"
    )

    rows = (report.get("details") or [])[:10]
    lines = ["| Host | Approved | Title |", "|---|:---:|---|"]
    for r in rows:
        lines.append(
            f"| {r.get('host') or '-'} | {'✔' if r.get('approved') else '—'} | {r.get('title') or r.get('url') or '-'} |"
        )

    note = "*Note: Evaluation compares extracted link domains to a fixed allow-list (`TOP_DOMAINS`) and does not re-query tools.*"
    return "\n".join([header, summary, *lines, note])


def evaluate_tavily_results(TOP_DOMAINS, raw, min_ratio=0.4):
    """
    把 Tavily 的搜索结果（JSON 或列表）拿来，统计其中 URL 属于可信域名的比例；
    如果比例 ≥ min_ratio（默认 40%），就判定 PASS，并输出一段 Markdown 报告。
    """
    results = []
    if isinstance(raw, str):
        try:
            results = json.loads(raw)
        except Exception:
            return False, f"⚠️ Could not parse Tavily output:\n```\n{raw}\n```"
    elif isinstance(raw, list):
        results = raw
    else:
        return False, f"⚠️ Unexpected input type: {type(raw)}"

    total = len(results)
    trusted_count = 0
    details = []

    for r in results:
        url = r.get("url", "")
        domain = url.split("/")[2] if "://" in url else url
        trusted = any(td in domain for td in TOP_DOMAINS)
        if trusted:
            trusted_count += 1
        details.append(f"- {url} → {'✅ TRUSTED' if trusted else '❌ NOT TRUSTED'}")

    ratio = trusted_count / total if total > 0 else 0
    flag = ratio >= min_ratio

    report = f"""
### Evaluation — Tavily Top Domains
- Total results: {total}
- Trusted results: {trusted_count}
- Ratio: {ratio:.2%}
- Threshold: {min_ratio:.0%}
- Status: {"✅ PASS" if flag else "❌ FAIL"}

**Details:**
{chr(10).join(details)}
"""
    return flag, report


if __name__ == "__main__":

    TOP_DOMAINS = {
        # 通用参考 / 机构 / 出版方
        "wikipedia.org",
        "nature.com",
        "science.org",
        "sciencemag.org",
        "cell.com",
        "mit.edu",
        "stanford.edu",
        "harvard.edu",
        "nasa.gov",
        "noaa.gov",
        "europa.eu",
        # 计算机科学 / 人工智能领域会议与索引
        "arxiv.org",
        "acm.org",
        "ieee.org",
        "neurips.cc",
        "icml.cc",
        "openreview.net",
        # 其他权威出版源
        "elifesciences.org",
        "pnas.org",
        "jmlr.org",
        "springer.com",
        "sciencedirect.com",
        # 额外域名（针对特定情况）
        "pbs.org",
        "nova.edu",
        "nvcc.edu",
        "cccco.edu",
        # 知名编程网站
        "codecademy.com",
        "datacamp.com",
    }

    tools = [
        tavily_search_tool,
        arxiv_search_tool,
        wikipedia_search_tool,
    ]

    tools_instance = Tools(tools)
    tool_regsitry = tools_instance.tools()
    print(tool_regsitry)

    research_task = "黑洞科学的最新进展"
    research_result = find_references_with_intermediate(research_task, tools)
    pretty_print_chat_completion_html(research_result)
    
    final_result = research_result.choices[0].message.content
    print_html(final_result, title="研究函数输出", output_file="final.html")
    print_html(
        evaluate_anytext_against_domains(TOP_DOMAINS, final_result),
        output_file="eval.html",
    )
