# tools/base.py
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    get_origin,
    get_args,
    Union,
)
from abc import ABC, abstractmethod
import inspect
import re

from pydantic import BaseModel, Field, ValidationError, create_model
from pydantic import ConfigDict, Field


class ToolErrorPayload(BaseModel):
    code: str
    message: str
    recoverable: bool = True
    details: Optional[Any] = None

    model_config = ConfigDict(extra="forbid")


class ToolResult(BaseModel):
    ok: bool
    content: str
    error: Optional[ToolErrorPayload] = None

    model_config = ConfigDict(extra="forbid")

    def __repr__(self):
        return (
            f"ToolResult(ok={self.ok}, content={self.content!r}, error={self.error!r})"
        )

    @classmethod
    def success(cls, content: str) -> "ToolResult":
        return cls(ok=True, content=content, error=None)

    @classmethod
    def failure(
        cls,
        code: str,
        message: str,
        recoverable: bool = False,
        details: Optional[Any] = None,
    ) -> "ToolResult":
        return cls(
            ok=False,
            content="",
            error=ToolErrorPayload(
                code=code, message=message, recoverable=recoverable, details=details
            ),
        )


class Tool(ABC):

    ArgsModel: Optional[Type[BaseModel]] = None  # 类属性

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, **kwargs) -> Any:
        raise NotImplementedError

    def get_args_model(self) -> Type[BaseModel]:
        """获取工具参数定义"""
        if self.ArgsModel is not None:
            return self.ArgsModel, []
        return self.infer_args_model()

    def _signature_target(self) -> Callable[..., Any]:
        return self.run

    def infer_args_model(self) -> Type[BaseModel]:
        run_fn: Callable[..., Any] = self._signature_target()
        model_name: str = f"{self.__class__.__name__}Args"
        signature = inspect.signature(run_fn)
        fields = {}
        untyped_fields: list[str] = []

        def _parse_args_section(doc: str) -> Dict[str, str]:
            """
            Parse:
                Args:
                    a: xxx
                    b: yyy
                Return { "a": "xxx", "b": "yyy" }
            """
            if not doc:
                return {}
            m = re.search(r"Args:\s*\n(.*?)(?:\n\s*\n|Returns:|$)", doc, re.DOTALL)
            if not m:
                return {}
            block = m.group(1)

            out: Dict[str, str] = {}
            # match "name: desc..."
            pattern = r"^\s*(\w+)\s*:\s*(.+?)(?=^\s*\w+\s*:|$)"
            for mm in re.finditer(pattern, block, re.MULTILINE | re.DOTALL):
                out[mm.group(1)] = re.sub(r"\s+", " ", mm.group(2).strip())
            return out

        # 获取docstring(函数和参数)
        docstring = inspect.getdoc(run_fn) or ""
        param_descriptions = _parse_args_section(docstring)

        # 从签名中获取参数
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            # type: Any兜底
            if param.annotation == inspect._empty:
                param_type = Any
                untyped_fields.append(param_name)
            else:
                param_type = param.annotation

            # 参数描述：从docstring中正则获取
            description = param_descriptions.get(param_name, "")

            # default，决定 required / optional
            if param.default == inspect._empty:
                fields[param_name] = (param_type, Field(..., description=description))
            else:
                fields[param_name] = (
                    param_type,
                    Field(default=param.default, description=description),
                )

        # 动态生成 参数 Pydantic 模型
        param_model = create_model(f"{model_name}Params", **fields)
        return param_model, untyped_fields


    def execute(self, args: Dict[str, Any]) -> ToolResult:
        """统一执行入口：捕获异常，返回 ToolResult"""
        ArgsModel, untyped_fields = self.get_args_model()
        try:
            validated = ArgsModel.model_validate(args)
        except ValidationError as e:
            return ToolResult.failure(
                code="INVALID_ARGUMENTS",
                message=f"f{str(e)}:{str(type(e))}",
                recoverable=False,
                details={"errors": e.errors(), "untyped_fields": untyped_fields},
            )
        try:
            result = self.run(**validated.model_dump())
            return ToolResult.success(f"result: {result}")
        except Exception as e:
            return ToolResult.failure(
                code="TOOL_RUNTIME_ERROR",
                message=f"f{str(e)}:{str(type(e))}",
                recoverable=False,
                details={"untyped_fields": untyped_fields},
            )

    def schema(self) -> Dict[str, Any]:
        ArgsModel, _ = self.get_args_model()
        return ArgsModel.model_json_schema()
