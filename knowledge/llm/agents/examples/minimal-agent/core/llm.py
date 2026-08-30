"""OpenAI 兼容的统一 LLM 接口 - 基于OpenAI原生API"""

import json
from typing import Any, Dict, List, Literal, Optional, Iterator
import os
from openai import OpenAI

        
class OpenAICompatibleLLM:
    """显式参数 > 自动检测 > LLM_PROVIDER（环境变量）"""

    @staticmethod
    def _auto_detect_provider() -> Optional[str]:
        """
        自动检测LLM提供商
        """
        # 1. 检查特定提供商的环境变量 (最高优先级)
        if os.getenv("MODELSCOPE_API_KEY"): 
            return "modelscope"
        if os.getenv("GEMINI_API_KEY"): 
            return "gemini"
        if os.getenv("OPENAI_API_KEY"): 
            return "any-openai-compatible"
        else:
            return None

    @staticmethod
    def resolve_provider(provider: Optional[str]) :
        PROVIDERS = {"modelscope","gemini","ollama","any-openai-compatible"}
        if provider is None:
            _provider = OpenAICompatibleLLM._auto_detect_provider() or os.getenv("LLM_PROVIDER")   
            if _provider is None or _provider == '':
                raise Exception(f"No Provider is provided or detected.")  
        else:
            _provider = provider

        if isinstance(_provider, str) and _provider.lower() in PROVIDERS:
            return _provider.lower()
        else:
            raise Exception(f"不支持的provider: {_provider}") 

    @staticmethod
    def resolve_model_id(
        provider: Optional[str],
        model: Optional[str]
    ) -> str:
        if model is None:
            if provider == "modelscope": 
                return os.getenv("LLM_MODEL_ID") or "Qwen/Qwen3-32B"
            elif provider == "gemini": 
                return os.getenv("LLM_MODEL_ID") or "gemini-2.5-flash"
            elif provider == "ollama": 
                return os.getenv("LLM_MODEL_ID") or "llama3:8b"
            elif provider == "any-openai-compatible" and os.getenv("LLM_MODEL_ID"): 
                return os.getenv("LLM_MODEL_ID")
            else:
                raise Exception("LLM_MODEL_ID has not been set.")
        else:
            return model

    @staticmethod
    def resolve_base_url(
        provider: Optional[str],
        base_url: Optional[str],
    ) -> str:
        if base_url is None:
            if provider == "modelscope": 
                return os.getenv("LLM_BASE_URL") or "https://api-inference.modelscope.cn/v1/"
            elif provider == "gemini": 
                return os.getenv("LLM_BASE_URL") or "https://generativelanguage.googleapis.com/v1beta/openai/"
            elif provider == "ollama": 
                return os.getenv("LLM_BASE_URL") or "http://localhost:11434/v1"
            elif provider == "any-openai-compatible" and os.getenv("LLM_BASE_URL"): 
                return os.getenv("LLM_BASE_URL")
            else:
                raise Exception("LLM_BASE_URL has not been set.")
        else:
            return base_url

    @staticmethod
    def resolve_api_key(
        provider: Optional[str],
        api_key: Optional[str],
    ) -> str:
        if api_key is None:
            if provider == "modelscope" and os.getenv("MODELSCOPE_API_KEY"): 
                return os.getenv("MODELSCOPE_API_KEY")
            if provider == "ollama":
                return ""
            elif provider == 'gemini' and os.getenv("GEMINI_API_KEY"):
                return os.getenv("GEMINI_API_KEY")
            elif provider == "any-openai-compatible" and os.getenv("OPENAI_API_KEY"):
                return os.getenv("OPENAI_API_KEY")
            else:
                raise Exception("XXX_API_KEY have not  not set.")
        else:
            return api_key

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
        **kwargs
    ):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        支持自动检测provider或使用统一的LLM_*环境变量配置。

        Args:
            provider：模型提供商(约定优于配置 + 显式覆盖点)
            model: 模型名称，如果未提供则从环境变量MODEL_ID读取
            api_key: API密钥，如果未提供则从环境变量OPENAI_API_KEY读取
            base_url: 服务地址，如果未提供则从环境变量LLM_BASE_URL读取
            temperature: 温度参数
            max_tokens: 最大token数
            timeout: 超时时间，从环境变量LLM_TIMEOUT读取，默认60秒
        """
        # 优先使用传入参数，如果未提供，则从环境变量加载
        
        self.provider = self.resolve_provider(provider)
        self.model = self.resolve_model_id(self.provider, model)
        print(f"🧠{self.provider} {self.model} starts.")

        self.api_key = self.resolve_api_key(self.provider, api_key)
        self.base_url = self.resolve_base_url(self.provider, base_url)

        self.temperature = temperature or 0.2
        self.max_tokens = max_tokens or 512
        self.timeout = timeout or 60
        self.kwargs = kwargs

        # 创建OpenAI客户端
        self._client = self._create_client()


    def _create_client(self) -> OpenAI:
        """创建OpenAI客户端"""
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    

    def invoke(self, messages: list[dict[str, str]], **kwargs) -> str:
        """
        非流式调用LLM，返回完整响应。
        适用于不需要流式输出的场景。
        messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=False,
                extra_body={
                "enable_thinking": False
                },
                **{k: v for k, v in kwargs.items() if k not in ['temperature', 'max_tokens']}
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
        


class FakeLLM:
    """
    Very small deterministic LLM for testing agent loop.
    Behavior:
      - If last user asks something like "1+2", it emits a tool_call to "add".
      - If last message is a tool result, it emits a final assistant answer.
    """

    def chat(self, *, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        last = messages[-1]

        # If we just got a tool result, produce final answer.
        if last.get("role") == "tool":
            return {
                "role": "assistant",
                "content": f"结果是：{last.get('content')}",
            }

        # Otherwise, look for a simple pattern in last user message
        if last.get("role") == "user":
            text = (last.get("content") or "").strip()
            if text == "1+2":
                return {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_fake_001",
                            "type": "function",
                            "function": {
                                "name": "add",
                                "arguments": json.dumps({"a": 1, "b": 2}),
                            },
                        }
                    ],
                }

        # Default: no tool call, just respond
        return {"role": "assistant", "content": "我不知道。"}