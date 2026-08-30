# Agent-loop checks with a fake model
"""
- 注册 add 工具
- 初始化 messages
- 跑 AgentLoop
- 输出 final 与 messages
- 你还能看到工具 tracing 日志（因为 registry.call 打 span）
"""
import json
from typing import Any, Dict, List, Optional

from tools.base import Tool
from tools.registry import ToolRegistry
from tools.telemetry import Telemetry

from core.agent_loop import AgentLoop, AgentLoopConfig
from core.llm import FakeLLM


class AddTool(Tool):
    def __init__(self):
        super().__init__("add", "Add two integers")

    def run(self, a: int, b: int = 1, note: Optional[str] = None) -> int:
        return a + b


telemetry = Telemetry(service_name="demo-agent-loop")
registry = ToolRegistry(telemetry=telemetry)
registry.register(AddTool())

llm = FakeLLM()
loop = AgentLoop(llm, registry)

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Use tools when needed.",
    },
    {"role": "user", "content": "1+2"},
]

final, all_messages = loop.run(messages)

print("\n=== FINAL ===")
print(final)

print("\n=== MESSAGES ===")
print(json.dumps(all_messages, ensure_ascii=False, indent=2))




class SpamToolCallsLLM:
    def chat(self, *, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        # always emit 10 tool calls
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": f"call_{i}", "type": "function", "function": {"name": "add", "arguments": json.dumps({"a": i, "b": 1})}}
                for i in range(10)
            ],
        }


telemetry = Telemetry(service_name="t91")
registry = ToolRegistry(telemetry=telemetry)
registry.register(AddTool())

cfg = AgentLoopConfig(max_steps=1, max_tool_calls_per_step=4, on_excess_tool_calls="truncate")
loop = AgentLoop(SpamToolCallsLLM(), registry, config=cfg)

final, msgs = loop.run([{"role": "user", "content": "hi"}])
assistant = msgs[-1]  # last appended assistant
print("tool_calls_len:", len(assistant.get("tool_calls", [])))  # expect 4
