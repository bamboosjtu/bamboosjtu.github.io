"""
最小参数校验：required 参数检查

现在错误太粗糙（KeyError），我们先加一个最简单的校验：
缺少必须参数就返回 INVALID_ARGUMENTS，不进入 run。
"""

import json
from pprint import pprint
from tools.base import Tool
from tools.registry import ToolRegistry


class AddTool(Tool):
    def __init__(self):
        super().__init__("add", "Add two integers")

    def run(self, a: int, b: int) -> int:
        """Add two numbers.
        Args:
            a: first integer
            b: second integer
        """
        return a + b


r = ToolRegistry()
tool = AddTool()
r.register(tool)

print("1) OK:", r.call("add", {"a": 1, "b": 2}))
print("2) missing b:", r.call("add", {"a": 1}))
print("3) wrong type:", r.call("add", {"a": "x", "b": 2}))

print(json.dumps(tool.schema(), ensure_ascii=False, indent=2))
