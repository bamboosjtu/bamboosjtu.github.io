"""
Tool 协议的最小骨架

目标： 先定义“工具”是什么：有名字、有描述、能执行。
先不管参数、注册表、异常、schema。
"""

from tools.base import Tool


class EchoTool(Tool):
    def __init__(self):
        super().__init__("echo", "Echo back the input")

    def run(self, args):
        return args["text"]


tool = EchoTool()
print(tool.name, "-", tool.description)
print("result:", tool.run({"text": "hello"}))
