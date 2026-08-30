"""
1. 把这些函数包装成 LLM tools JSON 规范
    - Tools.__init__
    - _add_tools
        - _convert_to_tool_spec(辅助函数:_unwrap_optiona)
        - _infer_from_signature(辅助函数:_extract_param_descriptions)
2. 发送给模型
    - tools
        - _convert_to_openai_format
3. 自动多轮
    - client.toolrunner 闭环调用函数, 检查 tool_calls
4. 解析参数并调用你的函数
    - execute_tool
5. 把返回结果插入对话消息，再发回模型
6. 多轮循环直到模型不再请求工具或达到 max_turns
"""

import inspect
import json
from typing import Any, Callable, Dict, Optional, Type, Union, get_args, get_origin
from pydantic import Field, ValidationError, create_model, BaseModel
from docstring_parser import parse


class Tools:
    """
    把“普通函数”变成 LLM 能理解的 tool
    """

    def __init__(self, tools: list[Callable] = None):
        """
        传入一个 list[Callable]（普通 Python 函数）
        Tools 会对每个函数调用 _add_tool，
        """
        self._tools = {}
        if tools:
            for tool in tools:
                self._add_tools(tool)

    def _add_tools(self, tool: Callable, param_model: Optional[Type[BaseModel]] = None):
        """
        建立内部注册表
        - 如果显式给了 Pydantic 模型，走_convert_to_tool_spec
        - (×)如果是 MCP 工具，用原始 schema
        - 否则，走 __infer_from_signature，从函数签名里自动推断参数模型
        """
        if param_model:
            tool_spec = self._convert_to_tool_spec(tool, param_model)
        else:
            tool_spec, param_model = self._infer_from_signature(tool)

        self._tools[tool.__name__] = {
            "function": tool,
            "param_model": param_model,
            "spec": tool_spec,
        }

    def _convert_to_tool_spec(
        self, tool: Callable, param_model: Type[BaseModel]
    ) -> Dict[str, Any]:
        """
        把 Pydantic 模型转成 OpenAI 兼容的工具描述
        """
        type_mapping = {str: "string", int: "integer", float: "number", bool: "boolean"}

        properties = {}
        for field_name, field in param_model.model_fields.items():
            field_type = field.annotation

            # 处理Optional
            field_type, is_optional = self._unwrap_optional(field_type)

            # 处理enum
            if hasattr(field_type, "__members__"):
                enum_values = [
                    member.value if hasattr(member, "value") else member.name
                    for member in field_type
                ]
                properties[field_name] = {
                    "type": "string",
                    "enum": enum_values,
                    "description": field.description or "",
                }
                # enum的default
                if str(field.default) != "PydanticUndefined":
                    properties[field_name]["default"] = (
                        field.default.value
                        if hasattr(field.default, "value")
                        else field.default
                    )
            else:
                properties[field_name] = {
                    "type": type_mapping.get(field_type, str(field_type)),
                    "description": field.description or "",
                }
                # 参数的default
                if str(field.default) != "PydanticUndefined":
                    properties[field_name]["default"] = field.default

        return {
            "name": tool.__name__,
            "description": tool.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": [
                    name
                    for name, field in param_model.model_fields.items()
                    if field.is_required and str(field.default) == "PydanticUndefined"
                ],
            },
        }

    def _unwrap_optional(self, field_type: Type):
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            # Optional[T] is Union[T, None]
            if type(None) in args:
                # Get the non-None type
                non_none_types = [arg for arg in args if arg is not type(None)]
                if len(non_none_types) == 1:
                    return non_none_types[0], True
        return field_type, False

    def _infer_from_signature(
        self, tool: Callable
    ) -> tuple[Dict[str, Any], Type[BaseModel]]:
        """
        从函数签名里自动推断参数模型, 生成OpenAI 兼容的工具描述 + 参数 Pydantic 模型
        """
        signature = inspect.signature(tool)
        fields = {}
        required_fields = []

        # 获取docstring(函数和参数)
        docstring = inspect.getdoc(tool) or ""
        param_descriptions = self._extract_param_descriptions(tool)

        # 解析docstring
        parsed_docstring = parse(docstring)
        function_description = parsed_docstring.short_description or ""
        if parsed_docstring.long_description:
            function_description += "\n\n" + parsed_docstring.long_description

        # 从签名中获取参数
        for param_name, param in signature.parameters.items():
            # Check if a type annotation is missing
            if param.annotation == inspect._empty:
                raise TypeError(
                    f"Parameter '{param_name}' in function '{tool.__name__}' must have a type annotation."
                )

            # 参数类型与optional
            param_type = param.annotation
            description = param_descriptions.get(param_name, "")

            if param.default == inspect._empty:
                fields[param_name] = (param_type, Field(..., description=description))
                required_fields.append(param_name)
            else:
                fields[param_name] = (
                    param_type,
                    Field(default=param.default, description=description),
                )

        # 动态生成 参数 Pydantic 模型
        param_model = create_model(f"{tool.__name__.capitalize()}Params", **fields)

        # 生成OpenAI 兼容的工具描述
        tool_spec = self._convert_to_tool_spec(tool, param_model)
        tool_spec["description"] = function_description

        return tool_spec, param_model

    def _extract_param_descriptions(self, tool: Callable):
        docstring = inspect.getdoc(tool) or ""
        parsed_docstring = parse(docstring)

        param_descriptions = {}
        for param in parsed_docstring.params:
            param_descriptions[param.arg_name] = param.description or ""

        return param_descriptions

    def tools(self, format="openai") -> list:
        """
        输出给模型用的 tools 列表
        """
        if format == "openai":
            return self._convert_to_openai_format()

    def _convert_to_openai_format(self) -> list:
        return [
            {"type": "function", "function": tool["spec"]}
            for tool in self._tools.values()
        ]

    """
    Step 2: 实际调用函数,并返回结果
    """

    def execute_tool(self, tool_calls) -> tuple[list, list]:
        """
        调用函数
        """
        results = []
        messages = []

        # 1. 支持单个或列表
        if not isinstance(tool_calls, list):
            tool_calls = [tool_calls]

        for tool_call in tool_calls:
            # 2. 统一解析工具名和参数
            if isinstance(tool_call, dict):
                tool_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]
                tool_call_id = tool_call["id"]
            else:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments
                tool_call_id = tool_call.id

            # 3. arguments 可能是 JSON 字符串，转成 dict
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            if tool_name not in self._tools:
                raise ValueError(f"Tool '{tool_name}' not registered.")

            # 4. 找到已注册的函数
            tool = self._tools[tool_name]
            tool_func = tool["function"]
            param_model = tool["param_model"]

            # 5. 用 Pydantic 校验 + 解析参数
            try:
                validated_args = param_model(**arguments)
                result = tool_func(**validated_args.model_dump())

                # 6. 结果 + 构造回给 LLM 的 tool 消息
                results.append(result)
                messages.append(
                    {
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result),
                        "tool_call_id": tool_call_id,
                    }
                )
            except ValidationError as e:
                raise ValueError(f"Error in tool '{tool_name}' parameters: {e}")

        return results, messages
    
    def create_tool_response_message(self, tool_call, tool_result):
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.function.name,
            "content": json.dumps(tool_result)
        }
