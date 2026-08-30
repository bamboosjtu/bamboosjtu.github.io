"""
Registry 的工具注册与查找

目标： 多个工具放一起，按 name 找到并调用。
这就是注册表的意义。
"""

# Registry contract checks
import json
from tools.base import Tool
from tools.registry import ToolRegistry
from tools.adapter.openai_adapter import (
    to_openai_tools,
    parse_openai_tool_calls,
    tool_result_to_openai_message,
)


class AddTool(Tool):
    def __init__(self):
        super().__init__("add", "Add two numbers")

    def run(self, a: int, b: int) -> int:
        """Add two numbers.
        Args:
            a: first integer
            b: second integer
        """
        return a + b


# 注册工具
registry = ToolRegistry()
registry.register(AddTool())

# 测试工具执行
result = registry.call("add", {"a": 1, "b": 2})
print(result.ok)
print(result.content)

print(AddTool().schema())
print("=== args schema ===")
print(json.dumps(registry.describe_for_llm(), ensure_ascii=False, indent=2))

openai_tools = to_openai_tools(registry)
print("=== OpenAI tools schema ===")
print(json.dumps(openai_tools, ensure_ascii=False, indent=2))

assistant_message = {
    "role": "assistant",
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "add",
                "arguments": json.dumps({"a": 2, "b": 3, "note": None}),
            },
        }
    ],
}

calls = parse_openai_tool_calls(assistant_message)
print("\n=== Parsed tool calls ===")
print(calls)

for c in calls:
    result = registry.call(c.name, c.args)
    print("\n=== ToolResult ===")
    print(result)

    tool_msg = tool_result_to_openai_message(
        c.tool_call_id, result.content if result.ok else json.dumps(result.error)
    )
    print("\n=== Tool message to feed back ===")
    print(json.dumps(tool_msg, ensure_ascii=False, indent=2))
