# tools/registry.py

import time
from typing import Dict, Any, List, Optional

from pydantic import BaseModel
from tools.base import Tool, ToolResult
from tools.expandable import Expandable
from tools.actions import export_actions
from tools.telemetry import Telemetry


class ToolRegistry:
    def __init__(self, telemetry: Optional[Telemetry] = None):
        self._tools: Dict[str, Tool] = {}
        self.telemetry = telemetry or Telemetry()

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def register_expandable(
        self, obj: Any, *, use_actions: bool = False, prefix: str | None = None
    ):
        """
        Option A: obj implements Expandable -> obj.expand()
        Option B: use_actions=True -> export_actions(obj)
        They are not strongly coupled.
        """
        if isinstance(obj, Expandable):
            for t in obj.expand():
                self.register(t)
            return

        if use_actions:
            for t in export_actions(obj, prefix=prefix):
                self.register(t)
            return

        raise TypeError("Object is not Expandable and use_actions=False")

    def get(self, name: str) -> Tool:
        return self._tools.get(name)

    def call(
        self,
        name: str,
        args: Dict[str, Any],
        *,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> ToolResult:
        """执行工具"""
        trace_id = trace_id or self.telemetry.new_trace_id()
        span = self.telemetry.start_span(
            "tool",
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            attributes={
                "tool_call_id": tool_call_id,
                "args_keys": sorted(list(args.keys())),
                "args_size": len(args),
            },
        )

        tool = self.get(name)
        if not tool:
            span.end(ok=False, error_code="TOOL_NOT_FOUND")
            self.telemetry.emit(
                "tool.call",
                {
                    "trace_id": trace_id,
                    "tool_call_id": tool_call_id,
                    "tool": name,
                    "ok": False,
                    "error_code": "TOOL_NOT_FOUND",
                    "latency_ms": 0,
                    "args_keys": sorted(list(args.keys())),
                    "args_size": len(args),
                },
            )

            return ToolResult.failure(
                code="TOOL_NOT_FOUND",
                message=f"Tool {name} not found.",
                recoverable=False,
            )

        result = tool.execute(args)

        if result.ok:
            span.end(ok=True)
        else:
            err = result.error
            if isinstance(err, BaseModel):
                err = err.model_dump(mode="json")
            code = (err or {}).get("code", "TOOL_ERROR") if not result.ok else None
            span.end(ok=False, error_code=code)
        return result

    def list(self) -> Dict[str, Tool]:
        """列出所有注册的工具"""
        return self._tools.values()

    def describe_for_llm(self) -> List[Dict[str, Any]]:
        """
        给 LLM 用的“工具说明”：包含 JSON Schema。
        """
        out = []
        for t in self._tools.values():
            out.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "args_schema": t.schema(),
                }
            )
        return out
