# tools/adapter/openai_adapter.py

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tools.registry import ToolRegistry


@dataclass
class OpenAIToolCall:
    """
    Provider-agnostic representation of one OpenAI tool call.
    """

    tool_call_id: str
    name: str
    args: Dict[str, Any]


def to_openai_tools(registry: ToolRegistry) -> List[Dict[str, Any]]:
    """
    Convert our registry tool descriptions into OpenAI function calling 'tools' format.
    """
    tools = []
    for t in registry.list():  # we'll add list_tools() in registry below
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.schema(),  # JSON Schema from pydantic
                },
            }
        )
    return tools


def parse_openai_tool_calls(assistant_message: Dict[str, Any]) -> List[OpenAIToolCall]:
    """
    Parse OpenAI assistant message dict and extract tool_calls.
    Expected shape:
      {"role":"assistant","tool_calls":[{"id":"...","type":"function",
        "function":{"name":"calc","arguments":"{\"a\":1}"}}]}
    """
    tool_calls = assistant_message.get("tool_calls") or []
    out: List[OpenAIToolCall] = []
    for tc in tool_calls:
        tc_id = tc.get("id") or ""
        fn = tc.get("function") or {}
        name = fn.get("name") or ""
        arg_str = fn.get("arguments") or "{}"
        try:
            args = json.loads(arg_str) if isinstance(arg_str, str) else dict(arg_str)
        except Exception:
            # if arguments is invalid JSON, pass raw string so tool validation can fail gracefully
            args = {"_raw_arguments": arg_str}
        out.append(OpenAIToolCall(tool_call_id=tc_id, name=name, args=args))
    return out


def tool_result_to_openai_message(tool_call_id: str, content: str) -> Dict[str, Any]:
    """
    Convert tool execution result to OpenAI 'tool' role message with tool_call_id alignment.
    """
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }
