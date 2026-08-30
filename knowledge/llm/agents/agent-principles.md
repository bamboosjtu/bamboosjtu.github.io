# 智能体的原理

## 一、智能体在模拟大脑的思维方式

把 LLM 放进一个循环里，它就开始像一个小脑瓜那样工作：接收目标、想一想、动手试、看看结果、再想一想。智能体（Agent）不是某种新模型，而是**围绕语言模型组织起来的一套思维方式**——模型负责"想"，外围系统负责"记、看、做"。

这个类比可以拆得更细：

| 大脑 | 智能体中的对应物 |
| --- | --- |
| 皮层推理能力 | LLM 本身：理解、规划、生成 |
| 思维方式（直觉/深思/反省） | 行为范式：ReAct、Plan-and-Solve、Reflection |
| 分工与协作 | Multi-Agent：角色化子任务 |
| 记忆 | 上下文窗口 + 外部存储（见`智能体的记忆](knowledge/llm/agents/agent-memory)） |
| 手脚与感官 | 工具调用：读文件、跑代码、操作浏览器（见`智能体的执行](knowledge/llm/agents/agent-execution)） |

其中有一个关键概念值得单独命名：**Harness（执行框架）**。

> **Harness 是介于模型与真实世界之间的那层系统**：它把模型输出的"意图"翻译成对工具的真实调用，把环境的反馈结构化后送回模型，并管理状态、权限、错误与停止条件。

模型只产出 token；harness 决定这些 token 能不能安全、可靠地作用于世界。同一个大脑，配不同的 harness，表现天差地别——这正是后文`智能体的执行]与`智能体的演进]要展开的主题。本篇先讲"思维方式"本身：四种经典范式。

## 二、ReAct：边想边做

ReAct (Reasoning and Acting) 将"思考"和"行动"紧密结合：思考指导行动，行动结果又反过来修正思考。它通过提示工程让模型每一步输出遵循固定轨迹：

1. **Thought (思考)**：内心独白——分析现状、分解任务、制定计划或反思上一步。
2. **Action (行动)**：决定采取的具体动作，通常是调用外部工具。
3. **Observation (观察)**：工具返回的结果，作为下一步思考的输入。

这是最接近"直觉"的模式：不预设完整路线，走一步看一步，适合探索型任务。

### 提示词模板

```python
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一:
- `{{tool_name}}`{{tool_input}}]`:调用一个可用工具。
- `Finish`最终答案]`:当你认为已经获得最终答案时。

现在，请开始解决以下问题:
Question: {question}
History: {history}
"""
```

模板的四个关键部件：

- **角色定义**：设定 LLM 的角色；
- **工具清单** (`{tools}`)：告知 LLM 它有哪些可用的"手脚"；
- **格式规约** (Thought/Action)：强制输出结构化，使 harness 能精确解析意图——这一步正是 harness 的职责边界；
- **动态上下文** (`{question}`/`{history}`)：注入原始问题和累积交互历史。

实践代码：[`examples/patterns/tools.py`](./examples/patterns/tools.py ":include")、[`examples/patterns/tool_use.py`](./examples/patterns/tool_use.py ":include")。

## 三、Plan-and-Solve：三思而后行

先生成完整行动计划，再严格执行。对应人类解题时"先列提纲再动笔"的慢思考。

1. **规划阶段**：接收完整问题，不直接求解，而是将问题分解为清晰、分步骤的行动计划。计划本身是一次 LLM 调用的产物。
2. **执行阶段**：严格按计划逐步执行。每一步可能是一次独立 LLM 调用，直到所有步骤完成得出答案。

### 规划器角色

````
PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划,```python与```作为前后缀是必要的:
'''python
`"步骤1", "步骤2", "步骤3", ...]
'''
"""
````

### 执行器角色

```
EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
请你专注于解决"当前步骤"，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对"当前步骤"的回答:
"""
```

### 结构化输出与安全边界

规划模式的关键是**用结构化输出保证计划可被下游代码可靠执行**——提示词需明确 JSON 结构（description 步骤描述 / tool 工具名 / arguments 参数）。

规划模式在 AI Coding 中非常成功，但赋予 agent 写代码的能力时要注意：

- 提示词要求明确：要求 LLM 编写代码解决查询，并以 Python 代码返回，用 `<code>` 等标签分隔；
- 安全问题：直接运行生成的代码有风险，需要沙箱等安全执行环境——这同样是 harness 的职责。

实践代码：[`examples/patterns/planning.py`](./examples/patterns/planning.py ":include")。

## 四、Reflection：自我修正闭环

Reflection 对应人类的元认知——不仅做事，还"审视自己做得怎么样"。它让智能体主动评估自身输出的质量，发现不足则生成改进建议并重新执行，形成"执行 → 反思 → 修正"闭环。

### 三层递进

1. **基础版：模型内审**——生成初稿后，将初稿再次输入模型，提示其检查错误并写出改进版。
2. **进阶版：思考模型组合**——用一个擅长快速生成的模型写初稿，再用一个擅长逻辑推理的"思考模型"反思改进。不同模型各有所长，组合能达到 "1+1>2"。
3. **终极版：结合外部反馈**——仅靠内省有限；引入来自模型之外的新信息（测试运行结果、搜索证据、人工评审）能带来质的飞跃。

### 反思提示的黄金法则

| 黄金法则 | 核心要点 | 说明与示例 |
| --- | --- | --- |
| **明确指示反思动作** | 不要笼统说"请改进"，要用明确动词 | 请**审查**邮件初稿 / 请**检查**逻辑漏洞 / 请**验证** HTML 是否合规 |
| **具体指定检查标准** | 明确列出评判维度，不要只说"让它更好" | 域名任务：**易发音、无负面含义**；邮件任务：**语气专业、事实准确** |

### 完整实现：三个角色的提示词

以"生成高效 Python 函数"为例，系统包含任务提出者、评审员、资深专家三个角色。

```python
INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。请根据以下要求，编写一个Python函数。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。

要求: {task}

请直接输出代码，不要包含任何额外的解释。
"""

REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
你的任务是审查以下Python代码，并专注于找出其在<strong>算法效率</strong>上的主要瓶颈。

# 原始任务:
{task}

# 待审查的代码:
'''
python
{code}
'''

请分析该代码的时间复杂度，并思考是否存在一种<strong>算法上更优</strong>的解决方案来显著提升性能。
如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
如果代码在算法层面已经达到最优，才能回答"无需改进"。

请直接输出你的反馈，不要包含任何额外的解释。
"""

REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务:
{task}

# 完整的执行与反思轨迹:
{trajectory}

评审员的反馈：
{feedback}

请根据评审员的反馈和完整的执行轨迹，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
"""
```

### Memory 机制

Memory 类在 Reflection Agent 中承担"短期记忆"：存储执行轨迹和反思记录。

```python
class Memory:
    def __init__(self):
        self.records: List`Dict`str, Any]] = `]

    def add_record(self, record_type: str, content: str):
        record = {"type": record_type, "content": content}
        self.records.append(record)

    def get_trajectory(self) -> str:
        trajectory_parts = `]
        for record in self.records:
            if record`'type'] == 'execution':
                trajectory_parts.append(f"--- 上一轮尝试 (代码) ---\n{record`'content']}")
            elif record`'type'] == 'reflection':
                trajectory_parts.append(f"--- 评审员反馈 ---\n{record`'content']}")
        return "\n\n".join(trajectory_parts)

    def get_last_execution(self) -> Optional`str]:
        for record in reversed(self.records):
            if record`'type'] == 'execution':
                return record`'content']
        return None
```

在 Agent 主循环中的使用：

```python
# 初始执行
initial_code = self._get_llm_response(initial_prompt)
self.memory.add_record("execution", initial_code)

# 反思
last_code = self.memory.get_last_execution()
reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
feedback = self._get_llm_response(reflect_prompt)
self.memory.add_record("reflection", feedback)

# 优化
refine_prompt = REFINE_PROMPT_TEMPLATE.format(
    task=task, trajectory=self.memory.get_trajectory(), feedback=feedback
)
refined_code = self._get_llm_response(refine_prompt)
self.memory.add_record("execution", refined_code)
```

一个实现层面的教训：某教材示例中 `get_trajectory` 实际没有发挥作用，进入提示词的只有 `get_last_execution` 的结果——轨迹信息被浪费了。自己实现时应把轨迹真正注入上下文。更系统的记忆话题见`智能体的记忆](knowledge/llm/agents/agent-memory)。

实践代码：[`examples/patterns/reflection.py`](./examples/patterns/reflection.py ":include")。

## 五、Multi-Agent：分工协作

单个上下文装不下所有信息和角色，就像一个人不可能精通所有专业。Multi-Agent 把一个任务拆给多个各司其职的子智能体：

- **任务分解**：像人类团队一样，将复杂任务自然分解为拥有不同角色和技能的子任务；
- **专注性**：单个 Agent 的任务越简单，完成效果越好——一次专注构建最好的"平面设计师智能体"；
- **模块化与复用**：通用的"平面设计师智能体"可复用于营销手册和社交媒体帖子；
- **突破上下文限制**：让每个 Agent 只负责自己的部分、总结 Agent 只看各子 Agent 的结论，就能规避上下文限制；
- **节约成本**：每个 Agent 上下文更短，Token 费用更低、延迟更低，还能并行处理。

### 协作拓扑

| 模式类型 | 结构特征 | 优点 | 缺点 | 适用场景 |
| --- | --- | --- | --- | --- |
| 线性（Linear） | 顺序执行，单向通信 | 简单 | 不灵活 | 固定流程任务 |
| 双层（Hierarchical） | 中心协调 | 易控制 | 管理负担 | 多任务协调 |
| 多层（Deep Hierarchy） | 子 Agent 层次化 | 模块化 | 复杂 | 大型系统 |
| 去中心（All-to-all） | 自由对话 | 创造性强 | 不可预测 | 探索型、生成型任务 |
| 对话（Dialogue） | 双 Agent 轮流对话（执行/审查） | 可控性强、反馈明确 | 效率较低 | 高质量输出、结果审查类任务 |

注意：仅仅给同一个模型设置多个角色名，通常不会自动带来更好的结果——角色分工要有真实的信息、工具或责任差异支撑，否则只是同一颗大脑的自言自语。

实践代码：[`examples/patterns/multi_agent.py`](./examples/patterns/multi_agent.py ":include")（MODELSCOPE 文本生成 + ZHIPU 图像生成的双 Agent 示例）。

## 六、从范式到系统

范式是思维方式的抽象，落到工程上还要回答三个问题：什么任务值得用 agent、循环怎么设计、如何判断它在变好。

### 1. 适用场景

| 较易实现的任务 | 较难实现的任务 |
|---------------------------|----------------------------|
| 清晰、逐步的流程：有明确的执行步骤 | 步骤未知：需求在执行前不确定，需动态规划 |
| 标准程序：企业已有成熟的操作手册 | 边执行边解决：代理需要在过程中推理和决策 |
| 纯文本资产：输入和输出均为文本 | 多模态输入：需要处理图像、声音等非文本 |

### 2. 工作流方法论

- **从宏观到微观**：面对复杂任务不要试图一步到位，先分解为几个大步骤；
- **逐步评估**：对每一步自问"能否由 LLM 或某个工具完成？"，不能就继续细分；
- **组合构件**：最终的工作流由"模型"和"工具"两个基本构件按特定顺序组成；
- **设计原则**：从简单开始（先做 1–3 步原型）、模块化、加入检查与评审步骤避免错误累积、持续迭代。

### 3. 范式选型速查

| 模式 | 是否含反馈 | 是否支持工具 | 是否多 Agent | 典型场景 |
|------|-----------|------------|-------------|--------|
| **Reflection** | ✅（自反馈） | 可选 | ❌ | 文本优化、代码修复 |
| **ReAct** | ✅（环境反馈） | ✅ | ❌ | 工具调用、问答 |
| **Plan-and-Execute** | ✅（进度检查） | ✅ | ❌ | 复杂任务分解 |
| **Multi-Agent** | ✅（互反馈） | ✅ | ✅ | 决策、评审、创新 |
| **CoT** | ❌ | ❌ | ❌ | 简单推理 |
| **Memory-Augmented** | ✅（历史反馈） | ✅ | ❌ | 长期对话、个性化 |
| **Adaptive Controller** | ✅（元反馈） | ✅ | ✅ | 通用 Agent |

现代高级模型往往融合多种模式：

```mermaid
graph LR
    A`用户请求] --> B{任务复杂度?}
    B -->|简单| C`CoT + Direct Answer]
    B -->|中等| D`ReAct + Tool Calling]
    B -->|复杂| E`Plan-and-Execute]
    E --> F`启动 Reflection 循环]
    E --> G`调用 Multi-Agent 协作]
    F & G --> H`Memory 更新]
    H --> I`最终输出]
```

### 4. 最小运行时的组件视角

无论用哪种范式、哪个框架，一个可运行的智能体都由同样的几块组成：

```mermaid
flowchart LR
    A`Messages] --> B`Model Adapter]
    B --> C`Parser]
    C --> D{Tool call?}
    D -- Yes --> E`Registry / Runner]
    E --> A
    D -- No --> F`Final result]
```

- **消息协议**：统一用户、模型、工具和系统消息；
- **模型适配器**：隔离不同模型 API 的差异；
- **解析器**：把模型输出转换为结构化动作；
- **工具注册与执行**：验证参数、执行能力并返回标准结果；
- **Agent Loop**：维护状态、限制步数、处理错误和停止；
- **观测**：记录每一步输入、输出、耗时与异常。

这就是 harness 的最小形态。运行时不应负责具体业务规则：工具描述告诉模型"可以做什么"，业务代码决定"实际允许做什么"；任何有外部副作用的工具都需要权限检查、幂等策略和明确的失败语义。完整参考实现在 [`examples/minimal-agent/`](knowledge/llm/agents/examples/minimal-agent/README.md)。

理解了原理之后，下一站是这个循环的两个关键器官：模型如何`执行](knowledge/llm/agents/agent-execution)、如何`记忆](knowledge/llm/agents/agent-memory)，以及如何`评估](knowledge/llm/agents/agent-evaluation)它是否真的在变好。

## 附录：搜索工具集成

不同搜索 API 的定位差异：Tavily 定位是"直接给 LLM 用的答案"，Token 消耗少；SerpApi (Google Search Results) 定位是"给开发者用的原始搜索列表"，实时性更好但在国内访问不稳定；DuckDuckGo 无需 API Key 且国内基本可直连。

### 1. Tavily

```python
from tavily import TavilyClient

client = TavilyClient(api_key="your_key")
response = client.search(query="2024年奥运会举办城市", search_depth="advanced", include_answer=True)
print(response`"answer"])  # 直接得到答案
```

### 2. SerpApi

```python
# pip install google-search-results
from serpapi import GoogleSearch

params = {
    "api_key": "YOUR_API_KEY",
    "engine": "google",
    "q": "Python tutorial",
    "hl": "zh",
    "gl": "cn",
    "num": 10,
}
search = GoogleSearch(params)
results = search.get_dict()
if "organic_results" in results:
    for result in results`"organic_results"]:
        print(result`"title"], result`"link"], result.get("snippet", "N/A"))
```

### 3. DuckDuckGo

无需 API Key、无访问限制，对应的库是 `ddgs`。

```python
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = ddgs.text("2024奥运会举办地", max_results=3)
    for r in results:
        print(r`"title"], r`"href"], r`"body"])
```

### 4. requests + Bing 国内版

兜底方案：直接解析国内可访问的 Bing 搜索页。

```python
import requests
from bs4 import BeautifulSoup

url = "https://cn.bing.com/search?q=2024奥运会"
headers = {"User-Agent": "Mozilla/5.0"}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")
```
