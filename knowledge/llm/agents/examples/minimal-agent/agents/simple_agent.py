"""简单Agent实现 - 基于OpenAI原生API"""
from typing import Optional, Iterator, TYPE_CHECKING, Dict, Any
import json
import re
from .base import Agent
from ..core import OpenAICompatibleLLM
from ..core import Message
from ..tools import ToolRegistry



class SimpleAgent(Agent):
    """简单的对话Agent，支持可选的工具调用"""
    
    def __init__(
        self,
        name: str,
        llm: OpenAICompatibleLLM,
        system_prompt: Optional[str] = None,
        registry: ToolRegistry = None,
    ):
        """
        初始化SimpleAgent
        
        Args:
            name: Agent名称
            llm: LLM实例
            system_prompt: 系统提示词
        """
        super().__init__(name, llm, system_prompt)
        self.enable_tool_calling = True
        self.registry = registry
        print(f"✅ {name} 初始化完成，工具调用: {'启用' if self.enable_tool_calling else '禁用'}")


    def run(self, user_goal: str, max_steps: int = 8, **kwargs) -> str:
        """
        运行SimpleAgent，支持可选的工具调用
        
        Args:
            user_goal: 用户输入
            max_steps: 最大工具调用迭代次数（仅在启用工具时有效）
            **kwargs: 其他参数
            
        Returns:
            Agent响应
        """
        print(f"🤖 {self.name} 正在处理: {user_goal}")

        # 构建消息列表
        messages = []
        
        # 添加系统消息
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})
        
        # 添加历史消息
        for msg in self._history:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_goal})
        self._history.append({"role": 'user', "content": user_goal})

        # 如果没有启用工具调用，使用原有逻辑
        if self.enable_tool_calling:
            for step in range(1, max_steps + 1):
                assistant_text = self.llm.invoke(messages, **kwargs) or ""
                messages.append({"role": "assistant", "content": assistant_text})

                cmd = self.extract_json(assistant_text)
                action = cmd.get("action")
                print(f'\t {step}步的 {str(cmd)}。')

                if action == "final":
                    final_resp = cmd.get("final", "")
                    break

                if action == "tool":
                    tool_name = cmd.get("tool_name")
                    tool_input = cmd.get("tool_input", "")
                    tool_result = self.registry.call(tool_name, tool_input)

                    # 把工具结果作为“观察”写回去
                    messages.append({
                        "role": "user",
                        "content": f"Tool result ({tool_name}): {tool_result}"
                    })

        else:
            final_resp = self.llm.invoke(messages, **kwargs)
        
        # 保存到历史记录
        self._history.append({"role": 'assistant', "content": final_resp})

        return final_resp
    

    def _get_enhanced_system_prompt(self) -> str:
        tool_list = self.registry.list_tools_description()
        """构建增强的系统提示词，包含工具信息"""
        SYSTEM_PROMPT = f"""
You are a minimal goal-driven agent.

You MUST respond with a single-line JSON object, no extra text.
Schema:
- {{"action": "tool", "tool_name": "...", "tool_input": "..."}}
- {{"action": "final", "final": "..."}}

Available tools:
{tool_list}

Rules:
- If you need a tool result, use action="tool".
- If you have the final answer, use action="final".

特别强调：
- 你必须且只能输出一个 JSON 对象。
- 不要输出解释文字，不要输出第二个 JSON。
"""
        return SYSTEM_PROMPT
    
    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """
        尽量从模型输出中提取 JSON（有些模型会多输出解释文字）。
        """
        # text = text.strip()
        # # 1) 直接就是 JSON
        # if text.startswith("{") and text.endswith("}"):
        #     return json.loads(text)

        # # 2) 尝试抓取第一段 {...}
        # m = re.search(r"\{.*\}", text, flags=re.S)
        # if m:
        #     return json.loads(m.group(0))        
        # raise ValueError(f"Model output is not valid JSON: {text}")
    

        """
        从模型输出中提取最后一个完整 JSON 对象。
        兼容：前后有解释文字、多个 JSON 换行拼接等情况。
        """
        decoder = json.JSONDecoder()
        s = text.strip()
        first_obj = None
        last_obj = None
        idx = 0
        while idx < len(s):
            # 找到下一个 '{'
            start = s.find("{", idx)
            if start == -1:
                break
            try:
                obj, end = decoder.raw_decode(s, start)
                last_obj = obj
                if first_obj is None:
                    first_obj = obj
                idx = end
            except json.JSONDecodeError:
                # 这个 '{' 不是合法 JSON 起点，跳过继续找
                idx = start + 1

        if last_obj is None:
            raise ValueError(f"未在输出中找到可解析的JSON：{text[:200]}")

        return first_obj # last_obj