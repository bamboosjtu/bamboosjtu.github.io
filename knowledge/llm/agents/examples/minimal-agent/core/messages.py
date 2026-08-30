# core/messages.py
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, Field, ConfigDict


# ---------- Role ----------

class Role(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


# ---------- Base Message ----------
"""
对话历史中的一条记录（事实）
        ┌─────────────┐
        │   Message   │   ← 对话历史（state）
        └─────────────┘
                ▲
                │
    ┌─────────┴─────────┐
    │                   │
user / assistant      tool result
"""

class Message(BaseModel):
    role: Role
    content: str
    name: Optional[str] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = ConfigDict(extra="ignore")

    def to_dict(self):
        data = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name:
            data["name"] = self.name
        return data



# ---------- Model Output Protocol (Pure JSON) ----------
"""
ParsedOutput = 模型这一步“打算做什么”（意图）
    ┌────────────────────┐
    │    ParsedOutput     │  ← 模型决策（control）
    └────────────────────┘
                ▲
    ┌─────────┼─────────┐
    │         │         │
ToolCall   Final    ModelError

"""

class ToolCall(BaseModel):
    type: Literal["tool_call"]
    name: str = Field(min_length=1)
    args: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class Final(BaseModel):
    type: Literal["final"]
    content: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class ModelError(BaseModel):
    type: Literal["error"]
    message: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


ParsedOutput = Union[ToolCall, Final, ModelError]


# ---------- helpers ----------

def tool_message(
    tool_name: str,
    result: Union[str, Dict[str, Any]],
) -> Message:
    """
    Normalize tool execution result into a tool message.
    Keep content short and text-based.
    """
    if isinstance(result, str):
        content = result
    else:
        content = str(result)

    return Message(
        role=Role.tool,
        name=tool_name,
        content=content,
    )
