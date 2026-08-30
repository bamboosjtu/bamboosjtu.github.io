# tools/actions.py
from typing import Any, Callable, List, Optional
import inspect
from tools.base import Tool


def tool_action(name: Optional[str] = None, description: Optional[str] = None):
    """
    Pure metadata decorator.
    Does NOT imply Expandable by itself.
    """

    def decorator(func: Callable[..., Any]):
        func._is_tool_action = True
        func._tool_name = name
        func._tool_description = description
        return func

    return decorator


def export_actions(obj: Any, prefix: Optional[str] = None) -> List[Tool]:
    """
    Scan obj methods with @tool_action metadata and export them as Tools.
    This function is NOT tied to Expandable; it's just one exporter strategy.
    """
    tools: List[Tool] = []
    for _, method in inspect.getmembers(obj, predicate=inspect.ismethod):
        if getattr(method, "_is_tool_action", False):
            tools.append(_MethodTool(obj, method, prefix=prefix))
    return tools


class _MethodTool(Tool):
    def __init__(
        self, parent: Any, method: Callable[..., Any], prefix: Optional[str] = None
    ):
        self._parent = parent
        self._method = method

        mname = method.__name__.lstrip("_")
        name = getattr(method, "_tool_name", None) or (
            f"{prefix}_{mname}" if prefix else mname
        )

        desc = getattr(method, "_tool_description", None)
        if not desc:
            desc = (
                _first_meaningful_line(inspect.getdoc(method) or "")
                or f"Execute {name}"
            )

        super().__init__(name=name, description=desc)

    def _signature_target(self):
        # 用 method 的真实签名推断 schema
        return self._method

    def run(self, **kwargs):
        return self._method(**kwargs)


def _first_meaningful_line(doc: str) -> Optional[str]:
    for line in doc.splitlines():
        s = line.strip()
        if s and not s.startswith("Args:") and not s.startswith("Returns:"):
            return s
    return None
