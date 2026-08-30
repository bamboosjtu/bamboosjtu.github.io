"""
Step5：适配OpenAI Schema：OpenAI function calling 格式 + tool_call_id 对齐

1）支持 OpenAI function calling 格式

```json
[
    {
        "type": "function",
        "function": {
            "name": "...",
            "description": "...",
            "parameters": { ...JSON Schema... }
        }
    }
]

```

2）对齐 tool_call_id：执行完工具后，必须把结果回给模型时附上同一个 tool_call_id。

```json
{ "role": "tool", "tool_call_id": "call_abc", "content": "..." }
```
"""

# Model adapter and function-calling checks
import json
from typing import Optional

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

    def run(self, a: int, b: int = 1, note: Optional[str] = None) -> int:
        """Add.
        Args:
            a: first integer
            b: second integer, default 1
            note: optional note (nullable)
        """
        return a + b


# 1) registry + tool schema
r = ToolRegistry()
r.register(AddTool())

openai_tools = to_openai_tools(r)
print("=== OpenAI tools schema ===")
print(json.dumps(openai_tools, ensure_ascii=False, indent=2))

# 2) mock an OpenAI assistant message that triggers tool call
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

# 3) execute tool(s)
for c in calls:
    result = r.call(c.name, c.args)
    print("\n=== ToolResult ===")
    print(result)

    # 4) align tool result back to OpenAI tool message with tool_call_id
    tool_msg = tool_result_to_openai_message(
        c.tool_call_id, result.content if result.ok else json.dumps(result.error)
    )
    print("\n=== Tool message to feed back ===")
    print(json.dumps(tool_msg, ensure_ascii=False, indent=2))
