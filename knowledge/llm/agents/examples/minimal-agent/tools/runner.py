# tools/runner.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from tools.registry import ToolRegistry
from tools.adapter.openai_adapter import parse_openai_tool_calls, tool_result_to_openai_message


@dataclass
class ToolRunConfig:
    """
    Tool runner execution config (MVP).
    """
    # 当工具失败时，tool message content 里是返回结构化 error 还是只返回 message
    return_structured_error: bool = True


class ToolRunner:
    """
    ToolRunner: OpenAI tool_calls -> execute -> OpenAI tool messages.

    It does NOT call the LLM. It only runs tools and returns messages.
    """

    def __init__(self, registry: ToolRegistry, *, config: Optional[ToolRunConfig] = None):
        self.registry = registry
        self.config = config or ToolRunConfig()

    def run_openai_tool_calls(
        self,
        assistant_message: Dict[str, Any],
        *,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Input: OpenAI assistant message dict (may contain tool_calls)
        Output: list of OpenAI tool messages with tool_call_id aligned
        """
        calls = parse_openai_tool_calls(assistant_message)

        # no tool calls => return empty list
        if not calls:
            return []

        trace_id = trace_id or self.registry.telemetry.new_trace_id()

        tool_messages: List[Dict[str, Any]] = []
        for c in calls:
            result = self.registry.call(
                c.name,
                c.args,
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                tool_call_id=c.tool_call_id,
            )

            if result.ok:
                content = result.content
            else:
                if self.config.return_structured_error:
                    content = result.error.model_dump_json(ensure_ascii=False)
                else:
                    content = (result.error or {}).get("message", "tool error")

            tool_messages.append(tool_result_to_openai_message(c.tool_call_id, content))

        return tool_messages
