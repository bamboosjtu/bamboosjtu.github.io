# core/parser.py
from __future__ import annotations

from typing import Callable, Optional

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from .messages import ParsedOutput


# ---------- exceptions ----------

class ParseError(Exception):
    """
    Raised when model output cannot be parsed into ParsedOutput.
    """
    pass


# ---------- config (pydantic) ----------

class ParserConfig(BaseModel):
    max_repair_attempts: int = Field(default=1, ge=0)
    strict_single_object: bool = True  # 保留扩展位：当前实现要求顶层是 JSON object

    model_config = ConfigDict(extra="forbid")


# ---------- parser ----------

class OutputParser:
    """
    Parse model output into ParsedOutput (ToolCall | Final | ModelError)
    using pydantic validation.

    - Tries to extract one JSON object from raw text.
    - Validates it against ParsedOutput union.
    - Optional one-step repair via repair_fn(prompt)->new_raw_text.
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()
        self._adapter = TypeAdapter(ParsedOutput)

    def parse(
        self,
        raw_text: str,
        repair_fn: Optional[Callable[[str], str]] = None,
    ) -> ParsedOutput:
        try:
            return self._parse_once(raw_text)
        except ParseError as e:
            if repair_fn is None or self.config.max_repair_attempts <= 0:
                raise

            repair_prompt = self._build_repair_prompt(raw_text, str(e))
            repaired_text = repair_fn(repair_prompt)

            # 只修复一次：第二次失败就抛出
            return self._parse_once(repaired_text)

    # ---------- internal ----------

    def _parse_once(self, raw_text: str) -> ParsedOutput:
        json_str = self._extract_json_object(raw_text)

        try:
            # 1) JSON parse
            # 2) Union 分发到 ToolCall/Final/ModelError
            # 3) extra="forbid" 等规则校验
            return self._adapter.validate_json(json_str)
        except ValidationError as e:
            # e.errors() 也可以用于更结构化的错误输出
            raise ParseError(f"Schema validation failed: {e}") from e
        except Exception as e:
            raise ParseError(f"Invalid JSON or parse failure: {e}") from e

    def _extract_json_object(self, raw_text: str) -> str:
        """
        Pure JSON protocol expects raw_text is JSON only.
        But models may add extra text. We extract the first {...} block as fallback.
        """
        s = raw_text.strip()

        if s.startswith("{") and s.endswith("}"):
            return s

        start = s.find("{")
        end = s.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ParseError("No JSON object found in model output.")
        return s[start : end + 1]

    def _build_repair_prompt(self, raw_text: str, error: str) -> str:
        return (
            "Your previous output was invalid.\n"
            f"Error: {error}\n"
            "You MUST output ONLY ONE valid JSON object, no extra text.\n"
            "Schema:\n"
            '1) {"type":"final","content":"..."}\n'
            '2) {"type":"tool_call","name":"tool_name","args":{...}}\n'
            '3) {"type":"error","message":"..."}\n'
            "Previous output:\n"
            f"{raw_text}"
        )
