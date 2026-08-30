"""
ToolResult 的统一成功与失败语义

目前如果传错参数，会直接 KeyError，agent 会崩。
目标： 工具不管成功失败都返回统一结构，agent 才能稳定循环。
"""

from tools.base import Tool
from tools.registry import ToolRegistry


class AddTool(Tool):
    def __init__(self):
        super().__init__("add", "Add two numbers")

    def run(self, a, b: int) -> int:
        """Add two numbers.
        Args:
            a: first integer
            b: second integer
        """
        return a + b


r = ToolRegistry()
r.register(AddTool())

print(r.call("add", {"a": 1, "b": 2}))
print(r.call("add", {"a": 1, "b": None}))
print(r.call("add", {"a": None, "b": 2}))
