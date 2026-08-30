# Tool-chain checks
from tools.base import Tool
import json
from typing import Optional
from tools.expandable import Expandable
from tools.actions import tool_action, export_actions
from tools.registry import ToolRegistry
from tools.adapter.openai_adapter import (
    to_openai_tools,
    tool_result_to_openai_message,
    parse_openai_tool_calls,
)


print("1：先引入 Expandable（不使用 decorator）")


class AddTool(Tool):
    def __init__(self):
        super().__init__("add", "Add two ints")

    def run(self, a: int, b: int) -> int:
        return a + b


class CalcTool(Tool):
    def __init__(self):
        super().__init__("calc", "Calc expression")

    def run(self, expression: str) -> str:
        return str(eval(expression))


class MathKit(Expandable):
    def expand(self):
        # 手动列出子工具（最直观）
        return [AddTool(), CalcTool()]


kit = MathKit()
tools = kit.expand()
print([t.name for t in tools])
print(tools[0].schema()["required"])  # 看 required


print("2：再引入 @tool_action（作为“生成子工具的方式之一")


class Memory:
    def __init__(self):
        self._data = []

    @tool_action(name="memory_add", description="Add a memory item")
    def add(self, content: str, importance: float = 0.5) -> str:
        """Add memory.
        Args:
            content: memory text
            importance: score 0~1
        """
        self._data.append((content, importance))
        return "ok"

    @tool_action(name="memory_search", description="Search memory")
    def search(self, query: str, top_k: int = 3, tag: Optional[str] = None) -> list:
        """Search memory.
        Args:
            query: query string
            top_k: number of results
            tag: optional tag (nullable)
        """
        return self._data[:top_k]


mem = Memory()
tools = export_actions(mem, prefix="mem")

print([t.name for t in tools])
print("schema(memory_search).required:", tools[1].schema().get("required"))
print(json.dumps(tools[1].schema(), ensure_ascii=False, indent=2))


print("3：把 Expandable + decorator 接到 Registry，并让 OpenAI schema 输出子工具")

r = ToolRegistry()
# 关键：不要求 mem 实现 Expandable，直接用 actions exporter
r.register_expandable(mem, use_actions=True, prefix=None)

print("=== registry tools ===")
print([t.name for t in r.list()])

print("\n=== OpenAI tools schema (should include memory_add/memory_search) ===")
print(json.dumps(to_openai_tools(r), ensure_ascii=False, indent=2))

# 模拟一次 OpenAI tool call
assistant_message = {
    "role": "assistant",
    "tool_calls": [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "memory_add",
                "arguments": json.dumps({"content": "hi", "importance": 0.2}),
            },
        },
        {
            "id": "call_2",
            "type": "function",
            "function": {
                "name": "memory_search",
                "arguments": json.dumps({"query": "h", "top_k": 2, "tag": None}),
            },
        },
    ],
}

calls = parse_openai_tool_calls(assistant_message)
for c in calls:
    res = r.call(c.name, c.args)
    msg = tool_result_to_openai_message(
        c.tool_call_id, res.content if res.ok else res.error.model_dump_json()
    )
    print("\n=== tool result message ===")
    print(json.dumps(msg, ensure_ascii=False, indent=2))
