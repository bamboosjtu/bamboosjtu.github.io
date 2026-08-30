import base64
import json
import os
import random
import re
from datetime import datetime
from io import BytesIO
import pandas as pd
import requests
from openai import OpenAI
from zai import ZhipuAiClient
from tavily import TavilyClient
from PIL import Image
from dotenv import load_dotenv
from IPython.display import Markdown, display
from tools import Tools


load_dotenv()
MODELSCOPE_API_KEY = os.getenv("MODELSCOPE_API_KEY")
ZAI_API_KEY = os.getenv("ZAI_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_ID = os.getenv("MODEL_ID")
openai_client = OpenAI(api_key=MODELSCOPE_API_KEY, base_url=BASE_URL)
zhipu_client = ZhipuAiClient(api_key=ZAI_API_KEY)

# --------------------------
# tools
# --------------------------

# Session setup (optional)
session = requests.Session()
session.headers.update(
    {"User-Agent": "LF-ADP-Agent/1.0 (mailto:your.email@example.com)"}
)


def tavily_search_tool(
    query: str, max_results: int = 5, include_images: bool = False
) -> list[dict[str, str]]:

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


def product_catalog_tool(max_items: int = 10) -> list[dict[str, str]]:
    inventory_df = create_inventory_dataframe()
    return inventory_df.head(max_items).to_dict(orient="records")


def create_inventory_dataframe():
    """
    Create an initial pandas DataFrame containing sunglasses inventory.

    Returns:
        pd.DataFrame: A DataFrame with columns for name, item_id, description,
                     quantity_in_stock, and price for 5 different sunglasses styles.
    """
    # Set seed for reproducible results
    random.seed(42)

    # Create the sunglasses inventory data
    sunglasses_data = {
        "name": ["Aviator", "Wayfarer", "Mystique", "Sport", "Round"],
        "item_id": ["SG001", "SG002", "SG003", "SG004", "SG005"],
        "description": [
            "Originally designed for pilots, these teardrop-shaped lenses with thin metal frames offer timeless appeal. The large lenses provide excellent coverage while the lightweight construction ensures comfort during long wear.",
            "Featuring thick, angular frames that make a statement, these sunglasses combine retro charm with modern edge. The rectangular lenses and sturdy acetate construction create a confident look.",
            "Inspired by 1950s glamour, these frames sweep upward at the outer corners to create an elegant, feminine silhouette. The subtle curves and often embellished temples add sophistication to any outfit.",
            "Designed for active lifestyles, these wraparound sunglasses feature a single curved lens that provides maximum coverage and wind protection. The lightweight, flexible frames include rubber grips.",
            "Circular lenses set in minimalist frames create a thoughtful, artistic appearance. These sunglasses evoke a scholarly or creative vibe while remaining effortlessly stylish.",
        ],
        "quantity_in_stock": [random.randint(3, 25) for _ in range(5)],
        "price": [random.randint(75, 150) for _ in range(5)],
    }

    return pd.DataFrame(sunglasses_data)


# --------------------------
# 1.市场调研智能体
# --------------------------
def market_research_agent(tools: Tools, return_messages: bool = False):

    print("【市场调研智能体🕵️‍♂️】登场")

    prompt_ = f"""
你是一名时尚市场调研代理，负责为夏季太阳镜活动准备趋势分析。

目标：
1. 使用网页搜索探索与太阳镜相关的当前时尚趋势。
2. 查看内部产品目录，识别与这些趋势相契合的商品。
3. 从目录中推荐一个或多个最符合新兴趋势的产品。
4. 如需注明，今天的日期是 {datetime.now().strftime("%Y-%m-%d")}。

可调用以下工具：
- tavily_search_tool：发现外部网络趋势。
- product_catalog_tool：检查内部太阳镜目录。

完成分析后，请总结：
- 你发现的 2–3 个主要趋势。
- 与这些趋势匹配的目录产品。
- 为何它们适合夏季活动的理由说明。
"""
    messages = [{"role": "user", "content": prompt_}]
    tools_registry = tools.tools()

    while True:
        response = openai_client.chat.completions.create(
            model=MODEL_ID, messages=messages, tools=tools_registry, tool_choice="auto"
        )

        msg = response.choices[0].message

        if msg.content:
            print(f">🕵️‍♂️:{msg.content}")
            return (msg.content, messages) if return_messages else msg.content

        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                print(
                    f">🧰调用：{tool_call.function.name}({tool_call.function.arguments})"
                )
                result = tools.execute_tool(tool_call)
                print(f">🧰结果：{result}")

                messages.append(msg)
                messages.append(tools.create_tool_response_message(tool_call, result))
        else:
            print(">⚠️ Unexpected.")
            return (
                ("[⚠️ Unexpected: No tool_calls or content returned]", messages)
                if return_messages
                else "[⚠️ Unexpected: No tool_calls or content returned]"
            )


# --------------------------
# 2.平面设计智能体
# --------------------------
def graphic_designer_agent(
    trend_insights: str, caption_style: str = "short punchy", size: str = "1024x1024"
) -> dict:
    """
    使用 modelscope 生成营销提示/文案，并直接使用 zhipu 生成图像。

    参数：
        trend_insights (str)：来自调研智能体的趋势摘要。
        caption_style (str)：文案的可选风格提示。
        size (str)：图像分辨率（例如 '1024x1024'）。

    返回：
        dict：包含 prompt 与 caption 的字典。
    """

    print("【平面设计智能体🎨】登场")

    # 步骤 1: 使用 MODEL 生成提示和文案
    system_message = (
        "你是一名视觉营销助理。根据输入的趋势洞见，"
        "为 AI 图像生成模型编写一个有创意的视觉提示，并生成一段简短文案。"
    )

    user_prompt = f"""
趋势洞见：
{trend_insights}

请输出：
1. 一段生动、具描述性的提示，用于引导图像生成。
2. 一句营销文案，风格：{caption_style}。

按如下格式回应：
{{"prompt": "...", "caption": "..."}}
"""

    chat_response = openai_client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = chat_response.choices[0].message.content.strip()
    match = re.search(r"\{.*\}", content, re.DOTALL)
    parsed = (
        json.loads(match.group(0))
        if match
        else {"error": "No JSON returned", "raw": content}
    )

    prompt = parsed["prompt"]
    caption = parsed["caption"]
    print(f"🎨作图：【{caption}】-t{prompt}。")

    # 步骤 2: 直接使用 zhipu-python 生成图像

    resp = zhipu_client.images.generations(
        model="glm-image", prompt=prompt, size="1024x1024"
    )
    image_url = resp.data[0].url

    img_bytes = requests.get(image_url).content
    img = Image.open(BytesIO(img_bytes))
    filename = os.path.basename(image_url.split("?")[0])
    image_path = filename
    img.save(image_path)

    # 使用本地图像记录摘要
    print(
        f"""
        <h3>已生成图像与文案</h3>

        <p><strong>图像路径：</strong> <code>{image_path}</code></p>

        <p><strong>生成的图像：</strong></p>
        <img src="{image_path}" alt="Generated Image" style="max-width: 100%; height: auto; border: 1px solid #ccc; border-radius: 8px; margin-top: 10px; margin-bottom: 10px;">

        <p><strong>提示：</strong> {prompt}</p>
    """
    )

    return {
        "image_url": image_url,
        "prompt": prompt,
        "caption": caption,
        "image_path": image_path,
    }


# --------------------------
# 3.文案智能体
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


def copywriter_agent(image_path: str, trend_summary: str) -> dict:
    """
    使用 aisuite（仅 OpenAI）发送图像与趋势摘要并返回活动短句。

    参数：
        image_path (str)：待分析图像的路径。
        trend_summary (str)：来自调研智能体的文本。

    返回：
        dict: {
            "quote": "...",
            "justification": "...",
            "image_path": "..."
        }
    """

    print("【文案智能体✍️】登场")

    # 步骤 1: 加载本地图像并编码为 base64
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    b64_img = base64.b64encode(img_bytes).decode("utf-8")

    image_url = upload_image(image_path)

    # 步骤 2: 构建兼容 OpenAI 的多模态消息
    messages = [
        {
            "role": "system",
            "content": "你是一名文案撰写者，基于图像与市场趋势摘要创作优雅的活动短句。",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{b64_img}",
                        # "url": image_url,
                        "detail": "auto",
                    },
                },
                {
                    "type": "text",
                    "text": f"""
以下为一个视觉营销图像与趋势分析：

趋势摘要：
\"\"\"{trend_summary}\"\"\"

请返回如下 JSON 对象：
{{
  "quote": "简短、优雅的活动短句（最多 12 个词）",
  "justification": "为何该短句契合该图像与趋势"
}}""",
                },
            ],
        },
    ]

    # 步骤 3: 通过 aisuite 发送请求
    response = openai_client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
    )

    # 步骤 4: 解析 JSON 响应
    content = response.choices[0].message.content.strip()

    print(f"✍️：{content}")

    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        parsed = (
            json.loads(match.group(0)) if match else {"error": "No valid JSON returned"}
        )
    except Exception as e:
        parsed = {"error": f"Failed to parse: {e}", "raw": content}

    parsed["image_path"] = image_path
    return parsed


# --------------------------
# 4.工作流
# --------------------------


def packaging_agent(
    trend_summary: str,
    image_url: str,
    quote: str,
    justification: str,
    output_path: str = "campaign_summary.md",
) -> str:
    """
    将活动资产打包为精美的 Markdown 报告，供高管审阅。

    Args:
        trend_summary (str)：市场趋势摘要。
        image_url (str)：活动图像的 URL。
        quote (str)：需叠加的营销短句。
        justification (str)：短句的理由说明。
        output_path (str)：保存 Markdown 报告的路径。

    Returns:
        str：已保存的 Markdown 文件路径。
    """

    print("打包智能体", "📦")

    # 我们在 <img> 的 src 中使用此路径
    styled_image_html = f"""
![打开生成的文件查看]({image_url})
    """

    beautified_summary = (
        openai_client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": "你是一名市场传播专家，为高管撰写优雅的活动总结。",
                },
                {
                    "role": "user",
                    "content": f"""
请将以下趋势摘要改写为清晰、专业且适合 CEO 受众的表达：

\"\"\"{trend_summary.strip()}\"\"\"
""",
                },
            ],
        )
        .choices[0]
        .message.content.strip()
    )

    # 将所有部分合并为 markdown
    markdown_content = f"""# 🕶️ 夏季太阳镜活动 – 高管摘要

## 📊 精炼的趋势洞见
{beautified_summary}

## 🎯 活动视觉
{styled_image_html}

## ✍️ 活动短句
{quote.strip()}

## ✅ 原因说明
{justification.strip()}

---

*报告生成日期 {datetime.now().strftime('%Y-%m-%d')}*
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return output_path


if __name__ == "__main__":
    tools = Tools([tavily_search_tool, product_catalog_tool])
    print(tools.tools())
    # print(tavily_search_tool('trends in sunglasses fashion'))
    # print(product_catalog_tool())
    market_research_result = market_research_agent(tools)
    print(f"STEP1：{market_research_result}")
    # ✅ 市场调研完成
    graphic_designer_agent_result = graphic_designer_agent(
        trend_insights=market_research_result
    )
    print(f"STEP2：{graphic_designer_agent_result}")
    # 🖼️ 图像已生成
    copywriter_agent_result = copywriter_agent(
        image_path=graphic_designer_agent_result["image_path"],
        trend_summary=market_research_result,
    )
    print(f"STEP3：{copywriter_agent_result}")
    # 💬 短句已生成
    md_path = packaging_agent_result = packaging_agent(
        trend_summary=market_research_result,
        image_url=graphic_designer_agent_result["image_path"],
        quote=copywriter_agent_result["quote"],
        justification=copywriter_agent_result["justification"],
        output_path=f"campaign_summary_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md",
    )
    print(f"📦 报告已生成：{md_path}")
