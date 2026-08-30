# OpenAI 兼容 API

> 几乎所有模型提供商——Anthropic、Google、DeepSeek、Kimi、Qwen、本地 Ollama/vLLM 等——都提供 **OpenAI 兼容接口（OpenAI-compatible API）**：只要把 `base_url` 和 `api_key` 换成对应服务商的值，同一份 OpenAI SDK 代码就能直接调用不同模型。这带来两个直接好处：一是学习成本只有一套，二是智能体应用在模型之间迁移几乎零成本。本文以 OpenAI 官方接口为主线，这些知识适用于所有兼容端点。

## 一、核心API接口

> Completions（legacy） → Chat Completions（messages 结构） → Responses（统一新原语）

- **Chat Completions API (`POST /chat/completions`)**：以“**对话消息 messages**”为中心的旧一代接口，输入/输出主要围绕 `messages[]` 与 `choices[]`。
- **Responses API (`POST /responses`)**：新一代“**统一响应原语（primitive）**”，把文本生成、多模态、工具调用、以及多轮状态串联在一个接口里，定位为 Chat Completions 的演进版/继任方向。
- 官方仍支持`Chat Completions API`，但新项目更推荐 `Responses API`。在维护旧项目、只做**简单对话生成**、且不想改动现有 messages/choices 结构，可以继续用 **Chat Completions** ；要做**Agent / tool calling / 多模态 / 需要跨轮保留推理与工具上下文**，优先 **Responses**。

### 1. Completions API

- 端点：POST /completions
- 输入：prompt（字符串或数组），偏“写一段提示 → 续写/补全”
- 输出：choices[]，每个 choice 里是生成的文本（与流式/非流式形状一致是它的特点之一）
- 定位：官方文档仍保留该接口，但在一些文档/镜像说明里会标注 Legacy，并提示多数开发者应使用 Chat Completions（以及更进一步的 Responses）。

### 2. Chat Completions API

- 输入：以 `messages[]` 为中心（`{role, content, ...}`）。
- 输出：以 `choices[]` 为中心，核心内容在 `choices[i].message`（流式返回 chunk）。
- 多轮对话：接口本身是**无状态**的；通常需要你把历史消息都放进 `messages[]` 一起传。
- 多候选：支持 `n` 生成多个候选。

### 3. Responses API

- 输入：以 `input` 为中心（可直接给字符串或结构化输入）；常配合 `instructions` 承载系统/开发者指令。
- 输出：返回一个类型化 `response` 对象；输出组织为一组 **items/output**（可包含 message、tool 调用与 tool 输出等）。
- 多轮/状态化：支持用 `previous_response_id` 把前一次响应串起来（形成链/分叉），可减少你手动拼历史的负担。
- 多候选：迁移指南明确 **不再支持 `n`**（按一次响应轨迹组织）。
- 把“生成 + 工具 + 状态 + 多模态”统一成一个原语，减少你自己维护对话历史、工具循环、不同端点拼装的复杂度。
- 输出从“一个 message”升级为“可组合的 items”：工具调用、工具输出、消息内容拆分更清晰，方便做 Agent。
- 面向未来模型：官方明确“新项目推荐 Responses”。

## 二、基础接口

- [OpenAI Model Spec](https://cdn.openai.com/spec/model-spec-2024-05-08.html#definitions)
- [OpenAI开发者手册](https://developers.openai.com/api/docs/quickstart)

| 模块                             | 基本概念                                                                         |
| -------------------------------- | -------------------------------------------------------------------------------- |
| 基础调用与提示词                 | API 请求结构（model/messages）、System/User 角色、提示词清晰性、温度等参数的作用 |
| 流式输出与会话状态               | 流式返回（chunk/delta）、choices 可能为空、finish_reason、多轮上下文累积         |
| 多模态输入                       | 文本+图片输入格式、视觉理解任务、输入内容组织方式                                |
| 结构化输出                       | JSON Schema、Pydantic、结构化解析思路、让输出可程序化消费                        |
| Function Calling / Tools（重点） | 工具定义（name/params）、模型决定何时调工具、工具结果回传、Agent 执行闭环        |
| 文件输入与推理                   | 文件作为上下文、复杂任务分步推理、长上下文处理思路                               |
| Web Search                       | 联网检索、检索增强回答、事实新鲜度与可追溯性                                     |
| File Search / RAG 基础           | 向量检索、基于私有知识回答、RAG 基本流程（索引→检索→生成）                       |

## 三、Chat Completions 实践要点

### 1. Client 配置

```python
from openai import OpenAI, AsyncOpenAI

client = OpenAI(
    api_key="sk-xxx",                      # 更安全的做法是用环境变量 OPENAI_API_KEY
    base_url="https://api.openai.com/v1",  # 支持自定义端点（如网关、Azure）
    timeout=30.0,
    max_retries=2
)
```

- 高并发场景使用 **异步客户端** `AsyncOpenAI`；
- 需要代理/证书配置时，可通过 `http_client` 参数注入 `httpx.Client`；
- Azure 兼容模式通过 `api_version` 和 `azure_endpoint` 参数切换。

### 2. 请求参数与常见陷阱

| 参数 | 说明 | 陷阱 |
|---|---|--|
| `temperature` | 随机性 0~2 | 越高越发散 |
| `max_completion_tokens` | 生成上限 | 新标准，替代 `max_tokens` |
| `seed` | 确定性采样 | 仅部分模型支持 |
| `logprobs=True` | 返回 token 概率（调试） | 额外计费 |
| `parallel_tool_calls` | 单次调用多个工具 | 默认关闭 |
| `presence_penalty` / `frequency_penalty` | 减少重复话题 | 二者互补 |
| `response_format={"type":"json_object"}` | 强制 JSON 输出 | 需在提示词中提及 JSON |

生产环境建议永远指定精确模型版本（带日期后缀）避免意外变更。

### 3. 消息结构要点

```python
{
    "role": "system" | "user" | "assistant" | "tool",
    "content": str | null,   # 工具调用时可能为 null，JSON 序列化需显式设置
    "name": str,             # 可选：工具/函数名称
    "tool_call_id": str      # tool 角色消息必须携带
}
```

- `system` 设置行为准则，但对较新模型的权重有所弱化，关键约束应同时在 user 消息中强调；
- `tool` 消息的 `tool_call_id` 必须与 assistant 发起的调用一一匹配；
- 多模态输入时 `content` 为数组：`[{"type": "text", ...}, {"type": "image_url", ...}]`。

### 4. 响应解析与错误层级

响应核心是 `choices[i].message` 与 `finish_reason`：

- `"stop"` 正常结束 / `"length"` 达到 token 上限 / `"tool_calls"` 模型请求调用工具；
- 流式模式下返回 chunk 迭代器，每个 chunk 取 `choices[0].delta.content`，**必须以 `finish_reason` 判断结束**；
- 工具调用结果以 `role: "tool"` 消息追加回历史后重新请求。

错误类型层级：`APIError` 下分 `RateLimitError`、`AuthenticationError`、`Timeout` 等，重试策略应区别对待（限流退避重试、认证错误直接失败）。

## 四、模型类别

按 OpenAI 官方文档，常见可以分这几类（截至 2026-03-03）：

1. Reasoning models（推理模型）
   - 例如 o3、o3-mini，以及新一代里可配置推理强度的 GPT-5 系列。适合复杂多步任务。
   - 参考：https://platform.openai.com/docs/guides/reasoning/how-reasoning-works%3B.ejs
   - 参考：https://platform.openai.com/docs/guides/reasoning-best-practices

2. GPT models（非推理通用模型）
   - 例如 gpt-4.1（文档写的是 “Smartest non-reasoning model”）。适合通用生成和工具调用。
   - 参考：https://platform.openai.com/docs/models/gpt-4.1

3. Omni / 多模态 GPT 模型
   - 例如 gpt-4o、gpt-4o-mini，支持文本+图像等多模态输入（以具体模型页为准）。
   - 参考：https://platform.openai.com/docs/models/gpt-4o-mini

4. Frontier models（前沿旗舰系列）
   - 官方模型总览中的高性能主力（当前以 GPT-5.x 家族为主）。
   - 参考：https://platform.openai.com/docs/models

5. Open-weight models（开权重模型）
   - 例如 gpt-oss-120b、gpt-oss-20b，可下载部署（Apache 2.0 许可）。
   - 参考：https://platform.openai.com/docs/models/gpt-oss
   - 参考：https://platform.openai.com/docs/models

## 五、OpenAI Agents SDK

[官方文档](https://openai.github.io/openai-agents-python/ref/agent/)

OpenAI Agents SDK 是一个用于构建 agent 工作流的 Python SDK。官方把它定位为：**轻量、易用、抽象极少**，并且是此前实验性项目 Swarm 的生产化升级版。
它的设计重点不是堆很多“框架魔法”，而是提供一组很小的基本原语，让你用普通 Python 就能表达 agent、工具调用、委派、状态和调试。

### 1. 核心概念

> **用 `Agent` 定义角色，用 `Runner` 驱动循环，用 `tools` 赋予行动能力，用 `handoffs` 做委派，用 `context/sessions` 管状态，用 `guardrails` 做约束，用 `tracing` 做调试。**

#### 1) Agent

`Agent` 是最核心的对象。可以把它理解成：

> **一个带有 instructions、模型、工具和可选委派能力的 LLM 单元。**

官方文档列出的常见属性包括 `name`、`instructions`、`model`、`tools`、`handoffs`、`output_type`、`input_guardrails`、`output_guardrails` 等。最小定义通常长这样：

```python
from agents import Agent

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant."
)
```

- `name`：给人看的 agent 名称
- `instructions`：系统级行为说明，决定这个 agent 的角色和风格。

#### 2) Runner

`Runner` 负责真正执行 agent。可以把它理解成：

> **Agent 是“配置”，Runner 是“执行引擎”。**

官方说明中，`Runner.run(...)` 会处理：

- 模型调用
- 工具调用
- 工具结果回传
- handoff
- 直到运行完成为止的整个 agent loop。

典型调用形式是：

```python
result = await Runner.run(agent, "用户输入")
```

最终结果常见地从 `result.final_output` 读取。

#### 3) Tools

Tools 是给 agent 增加“行动能力”的方式。官方文档指出，你可以把任意 Python 函数转成 tool，并自动生成 schema 与参数验证。

常见写法是用 `@function_tool`：

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    return f"{city} is sunny."
```

然后挂到 agent 上：

```python
agent = Agent(
    name="Weather Agent",
    instructions="Help users with weather questions.",
    tools=[get_weather],
)
```

#### 4) Handoffs

`handoffs` 是多 agent 协作的核心机制之一。它表示：

> 当前 agent 可以把任务转交给另一个更合适的 agent。

官方 quickstart 用的是一个 triage agent，把问题路由给不同专家 agent。`handoff_description` 用来告诉路由 agent：这个被委派的 agent 擅长什么。

这是 **“任务转移”** 风格。官方还提到另一种风格是 **“agents as tools”**，即 orchestrator 自己保持控制，把其他 agent 当工具来调用。

#### 5) Guardrails

Guardrails 是输入和输出检查机制。官方把它描述为与 agent 执行并行运行的验证与安全检查，如果不通过，可以快速失败。

作用可以概括为两类：

- **输入 guardrails**：限制用户输入类型或风险内容
- **输出 guardrails**：限制模型输出格式或安全边界。

#### 6) Context / Sessions

官方文档里，`context` 是一个依赖注入与运行期状态容器。你可以把任意 Python 对象传给 `Runner.run()`，它会在 agent、tools、handoffs 之间共享。

这意味着它不只是“聊天历史”，更像：

> **一次运行里共享的状态和依赖集合。**

官方还把 `sessions` 列为独立能力，用来在 agent loop 中维护持久化上下文。

#### 7) Tracing

Tracing 是官方明确强调的内建能力。它用于可视化、调试和监控 agent workflow，官方 quickstart 还提到可以在控制台的 Trace viewer 查看运行轨迹。([OpenAI][4])

这点很重要，因为 agent 系统一旦涉及工具和多 agent，没有 trace 很难排障。

### 2. 核心原语

最简化地看，OpenAI Agents SDK 的运行逻辑是：

```text
Agent = 角色定义
Runner = 执行循环
Tool = 外部能力
Handoff = 委派给别的 agent
Guardrail = 输入/输出约束
Context/Session = 状态
Tracing = 调试与观察
```

### 3. 最小可运行版本

#### 1) 单agent

最小版本：**一个 agent，零工具，单轮运行。**

```python
# pip install openai-agents

import asyncio
from agents import Agent, Runner

agent = Agent(
    name="Assistant",
    instructions="You are a concise assistant."
)

async def main():
    result = await Runner.run(
        agent,
        "用一句话解释什么是 Transformer。"
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

这个 demo 体现了最核心的两件事：

- 用 `Agent(...)` 定义角色
- 用 `Runner.run(...)` 执行并拿到 `final_output`。([OpenAI][4])

---

#### 2) 单agent带一个工具

```python
import asyncio
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """Returns simple weather info for a city."""
    return f"{city}：晴，25摄氏度。"

agent = Agent(
    name="Weather Assistant",
    instructions="You help with weather questions. Use tools when useful.",
    tools=[get_weather],
)

async def main():
    result = await Runner.run(
        agent,
        "北京今天天气怎么样？"
    )
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

这个 demo 体现的是：

- `function_tool` 把普通 Python 函数暴露给模型
- `Runner` 会自动处理工具调用与结果回传。

---

#### 3) 多 agent 路由

一个分诊 agent，把问题交给不同专家。

```python
import asyncio
from agents import Agent, Runner

history_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist for history questions",
    instructions="Answer history questions clearly and concisely."
)

math_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist for math questions",
    instructions="Explain math step by step."
)

triage_agent = Agent(
    name="Triage Agent",
    instructions="Route each question to the right specialist.",
    handoffs=[history_agent, math_agent],
)

async def main():
    result = await Runner.run(
        triage_agent,
        "谁是美国第一任总统？"
    )
    print(result.final_output)
    print(result.last_agent.name)

if __name__ == "__main__":
    asyncio.run(main())
```

这里最关键的是：

- `handoffs=[...]` 定义可委派目标
- `handoff_description` 帮助路由判断
- `result.last_agent.name` 可以看到最后是谁回答的。

### 4. 常见误区

#### 1) Agent 不是“自动体”

它首先是一个 **配置对象**，不是自己跑起来的线程或服务。真正执行它的是 `Runner`。这点官方 quickstart 的示例结构很清楚。

#### 2) Tools 是第一优先级能力扩展

很多 agent 的“能力”本质不来自 prompt，而来自它能调用的函数、MCP 服务或其他工具。官方文档也把 tools 列为核心组件。

#### 3) 多 agent 不一定要“群聊”

OpenAI Agents SDK 支持多 agent，但默认最直观的模式通常是 **handoff** 或 **agents as tools**，而不是让多个 agent 自由对话。

#### 4) Trace 很重要

只要有 tools 或 handoffs，就建议看 tracing。否则你很难判断：是 prompt 问题、工具 schema 问题，还是路由判断问题。官方明确提供了 Trace viewer。
