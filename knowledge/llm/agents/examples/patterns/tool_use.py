from datetime import datetime
import os
import json
from typing import Any
import requests
from dotenv import load_dotenv
from IPython.display import display, HTML
from openai import BaseModel, OpenAI
import qrcode
from qrcode.image.styledpil import StyledPilImage
from pprint import pprint
from tools import Tools

load_dotenv()
API_KEY = os.getenv("MODELSCOPE_API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_ID = os.getenv("MODEL_ID")
openai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# --------------------------
# Tool
# --------------------------
# 获取ip所在地位置
def get_ip():
    """
    通过 IP 地址获取地理坐标
    返回：
        tuple: (latitude, longitude)
    """
    lat, lon = requests.get("https://ipinfo.io/json").json()["loc"].split(",")
    return lat, lon


# 获取当天位置的气温
def get_weather_from_ip(lat: str, lon: str):
    """
    获取用户所在位置的当前、最高与最低温度（华氏制），并返回给用户。
    参数：
        lat：latitude
        log: longitude
    返回：
        str：当天气温情况
    """
    # 设置天气 API 调用的参数
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "auto",
    }

    # 获取天气数据
    weather_data = requests.get(
        "https://api.open-meteo.com/v1/forecast", params=params
    ).json()

    # 格式化并返回简洁字符串
    return (
        f"Current: {weather_data['current']['temperature_2m']}°F, "
        f"High: {weather_data['daily']['temperature_2m_max'][0]}°F, "
        f"Low: {weather_data['daily']['temperature_2m_min'][0]}°F"
    )


# 写入文本文件
def write_txt_file(file_path: str, content: str):
    """
    将字符串写入 .txt 文件（若已存在则覆盖）。
    参数：
        file_path (str)：目标路径。
        content (str)：要写入的文本。
    返回：
        str：写入文件的路径。
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


# 生成二维码
def generate_qr_code(data: str, filename: str, image_path: str):
    """
    给定数据与图片路径，生成二维码图像。
    参数：
        data：要编码的文本或 URL
        filename：输出 PNG 文件名（不含扩展名）
        image_path：用于嵌入到二维码中的图片路径
    返回：
        str：写入文件的路径。
    """
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)
    img = qr.make_image(image_factory=StyledPilImage, embedded_image_path=image_path)
    output_file = f"{filename}.png"
    img.save(output_file)

    return f"QR code saved as {output_file} containing: {data[:50]}..."


def get_current_time():
    """
    返回：
        当前时间的字符串。
    """
    return datetime.now().strftime("%H:%M:%S")


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
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(html_obj.data)


# --------------------------
# agent
# --------------------------
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


def get_llm_response(messages, tools):
    resp = openai_client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
        tools=tools,
        temperature=0.2,
        stream=False,
        extra_body={"enable_thinking": False},
    )
    return resp


def agent_with_tools(
    messages: list,
    tools: Any,
    max_turns: int,
    **kwargs,
):
    # 1. 创建 Tools 实例，并把 tools 参数转换成 LLM 需要的 JSON 规范
    if isinstance(tools, Tools):
        tools_instance = tools
        tool_regsitry = tools_instance.tools()
    else:
        # tool检查
        if not all(callable(tool) for tool in tools):
            raise ValueError("One or more tools is not callable")
        tools_instance = Tools(tools)
        tool_regsitry = tools_instance.tools()

    turns = 0
    intermediate_responses = []
    intermediate_messages = []

    while turns < max_turns:
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


if __name__ == "__main__":
    tools = [
        get_ip,
        get_weather_from_ip,
        write_txt_file,
        generate_qr_code,
        get_current_time,
    ]
    messages = [
        {"role": "system", "content": "你是一个工作助手。"},
        {
            "role": "user",
            "content": "你能帮我用图片 me.png 生成一个跳转到 www.deeplearning.com 的二维码吗？另外请写一个包含当前天气的 txt 备忘。",
        },
    ]
    registry = Tools(tools)
    pprint(registry.tools())
    pretty_print_chat_completion_html(agent_with_tools(messages, tools, 5))
