# Tool runner checks
"""
- 注册一个工具
- mock assistant message（带 2 个 tool_calls：成功+失败）
- ToolRunner 跑完输出 tool messages
- 你会同时在 stdout 看到 span 日志（tool.start/tool.end）并包含 tool_call_id
"""
import json
from typing import Optional

from tools.base import Tool
from tools.registry import ToolRegistry
from tools.telemetry import Telemetry
from tools.runner import ToolRunner, ToolRunConfig


class AddTool(Tool):
    def __init__(self):
        super().__init__("add", "Add two integers")

    def run(self, a: int, b: int = 1, note: Optional[str] = None) -> int:
        """Add.
        Args:
            a: first integer
            b: second integer, default 1
            note: optional note (nullable)
        """
        return a + b


telemetry = Telemetry(service_name="demo-toolrunner")
registry = ToolRegistry(telemetry=telemetry)
registry.register(AddTool())

runner = ToolRunner(registry, config=ToolRunConfig(return_structured_error=True))

assistant_message = {
    "role": "assistant",
    "tool_calls": [
        {
            "id": "call_ok",
            "type": "function",
            "function": {"name": "add", "arguments": json.dumps({"a": 1, "b": 2})},
        },
        {
            "id": "call_bad",
            "type": "function",
            "function": {"name": "add", "arguments": json.dumps({"a": "x"})},
        },
    ],
}

trace_id = telemetry.new_trace_id()

tool_messages = runner.run_openai_tool_calls(assistant_message, trace_id=trace_id)

print("\n=== tool messages ===")
print(json.dumps(tool_messages, ensure_ascii=False, indent=2))
