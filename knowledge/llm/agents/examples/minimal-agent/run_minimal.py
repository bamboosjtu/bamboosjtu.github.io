# tests/run_minimal.py

from tools.base import Tool

class EchoTool(Tool):
    def __init__(self):
        super().__init__("echo", "Echo back the input")

    def run(self, args):
        return args["text"]

tool = EchoTool()
print(tool.name, "-", tool.description)
print("result:", tool.run({"text": "hello"}))
