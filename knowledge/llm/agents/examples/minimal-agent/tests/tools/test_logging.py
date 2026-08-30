# Logging checks
import json
from tools.base import Tool
from tools.registry import ToolRegistry
from tools.telemetry import Telemetry
from tools.adapter.openai_adapter import to_openai_tools, parse_openai_tool_calls, tool_result_to_openai_message

class AddTool(Tool):
    def __init__(self):
        super().__init__("add", "Add two integers")

    def run(self, a: int, b: int = 1) -> int:
        return a + b

r = ToolRegistry(telemetry=Telemetry(service_name="demo"))
r.register(AddTool())

print("1+2：Tracing+Span")
# 同一个 trace_id 表示同一轮 agent 过程
trace_id = r.telemetry.new_trace_id()

print("result1:", r.call("add", {"a": 1, "b": 2}, trace_id=trace_id, tool_call_id="call_1"))
print('-'*60)
print("result2:", r.call("add", {"a": "x"}, trace_id=trace_id, tool_call_id="call_2"))  # 类型错误
print('-'*60)
print("result3:", r.call("missing", {"x": 1}, trace_id=trace_id, tool_call_id="call_3"))


print("\n\n3（把 OpenAI tool_call_id 全链路贯穿）\n")
# --------- setup ----------
telemetry = Telemetry(service_name="demo-openai-align")
registry = ToolRegistry(telemetry=telemetry)
registry.register(AddTool())

# --------- 1) show OpenAI tools schema ----------
print("=== OpenAI tools schema ===")
print(json.dumps(to_openai_tools(registry), ensure_ascii=False, indent=2))

# --------- 2) mock OpenAI assistant tool_calls ----------
assistant_message = {
    "role": "assistant",
    "tool_calls": [
        {
            "id": "call_ok_001",
            "type": "function",
            "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3, "note": None})},
        },
        {
            "id": "call_bad_002",
            "type": "function",
            "function": {"name": "add", "arguments": json.dumps({"a": "x"})},  # wrong type
        },
        {
            "id": "call_nf_003",
            "type": "function",
            "function": {"name": "missing_tool", "arguments": json.dumps({"x": 1})},
        },
    ],
}



calls = parse_openai_tool_calls(assistant_message)

# --------- 3) execute with same trace_id (one agent turn) ----------
trace_id = telemetry.new_trace_id()

tool_messages = []
for c in calls:
    result = registry.call(
        c.name,
        c.args,
        trace_id=trace_id,
        tool_call_id=c.tool_call_id,   # 👈 对齐点：会进入 span attributes
    )

    # OpenAI tool message expects content string; for errors we stringify structured error
    content = result.content if result.ok else result.error.model_dump_json()
    tool_messages.append(tool_result_to_openai_message(c.tool_call_id, content))

print("\n=== Tool messages to feed back to OpenAI ===")
print(json.dumps(tool_messages, ensure_ascii=False, indent=2))

print("\nNOTE: In stdout logs you should see tool.start/tool.end events, each containing tool_call_id.")


