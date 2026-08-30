# core/agent_loop.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple

from tools.registry import ToolRegistry
from tools.adapter.openai_adapter import to_openai_tools
from tools.runner import ToolRunner


class ChatModel(Protocol):
    """
    Minimal LLM interface for OpenAI-like chat:
    returns an assistant message dict, maybe containing tool_calls.
    """

    def chat(
        self, *, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]: ...


@dataclass
class AgentLoopConfig:
    max_steps: int = 8

    # 限制每步最大工具调用数（max_tool_calls_per_step）
    max_tool_calls_per_step: int = 4
    on_excess_tool_calls: str = "truncate"  # "truncate" | "error"


class AgentLoop:
    """
    Complete loop:
      messages -> llm.chat() -> assistant_message
      if tool_calls -> ToolRunner -> tool_messages -> append -> continue
      else -> final -> stop
    """

    def __init__(
        self,
        llm: ChatModel,
        registry: ToolRegistry,
        *,
        config: Optional[AgentLoopConfig] = None,
    ):
        self.llm = llm
        self.registry = registry
        self.runner = ToolRunner(registry)
        self.config = config or AgentLoopConfig()

    def _enforce_tool_call_limit(self, assistant_msg: Dict[str, Any]) -> Optional[str]:
        tool_calls = assistant_msg.get("tool_calls")
        if not tool_calls:
            return None

        if len(tool_calls) <= self.config.max_tool_calls_per_step:
            return None

        if self.config.on_excess_tool_calls == "truncate":
            assistant_msg["tool_calls"] = tool_calls[
                : self.config.max_tool_calls_per_step
            ]
            return None

        # error mode
        assistant_msg.pop("tool_calls", None)
        assistant_msg["content"] = (
            (assistant_msg.get("content") or "")
            + f"\n[ERROR] Too many tool calls: {len(tool_calls)} > {self.config.max_tool_calls_per_step}"
        )
        return "TOO_MANY_TOOL_CALLS"

    def run(
        self, messages: List[Dict[str, Any]], *, trace_id: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        trace_id = trace_id or self.registry.telemetry.new_trace_id()
        tools_schema = to_openai_tools(self.registry)

        for _step in range(self.config.max_steps):
            assistant_msg = self.llm.chat(messages=messages, tools=tools_schema)

            # Step9.1: enforce per-step tool call limit before appending/executing
            self._enforce_tool_call_limit(assistant_msg)

            messages.append(assistant_msg)

            tool_msgs = self.runner.run_openai_tool_calls(
                assistant_msg, trace_id=trace_id, parent_span_id=None
            )
            if tool_msgs:
                messages.extend(tool_msgs)
                continue

            return (assistant_msg.get("content") or ""), messages

        return "[ERROR] Reached max_steps without final answer.", messages
