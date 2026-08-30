# Transformer 架构

> 如果把当前的大模型（LLM）生态比作一个现代化的工业体系，那么 **Transformers** 框架就是那个生产发动机的“核心标准工厂”。---

## 一、AI 界的“标准库”

[transformers](https://huggingface.co/docs/transformers/index) 是由 **Hugging Face** 公司开发和维护的开源库。它最初只是为了让人们能更方便地在 PyTorch 中使用 BERT 模型，但现在它已经成为了几乎所有主流模型（从文本到图像、音频、视频）的“官方接口”。

与 AutoGen, OpenAI, LangChain 等的关系：

| 层次            | 角色                  | 代表工具                  | 它们在干什么？                                            |
| --------------- | --------------------- | ------------------------- | --------------------------------------------------------- |
| **应用/代理层** | **CEO (指挥官)**      | **AutoGen, CrewAI**       | 负责“指挥”。决定让哪个 Agent 去干活，如何分工。           |
| **逻辑/架构层** | **架构师 (中层管理)** | **LangChain, LlamaIndex** | 负责“连接”。把模型、数据库（RAG）、搜索工具串联成工作流。 |
| **模型引擎层**  | **发动机 (动力源)**   | **Transformers, OpenAI**  | 负责“计算”。输入信息，输出预测。                          |

- **vs OpenAI**: OpenAI 是**闭源的云端服务**（你通过 API 买电）；Transformers 是**开源的引擎库**（你自己建发电站）。
- **vs LangChain / LlamaIndex**:
  - Transformers 关注的是**单个模型**如何运行。
  - LangChain 关注的是**多个组件**（模型 + 数据库 + 记忆）如何组合。你可以在 LangChain 里调用一个通过 Transformers 加载的本地模型。
- **vs AutoGen / CrewAI**:
  - 这两个是**多智能体（Multi-Agent）框架**。
  - 它们是站在最高层的。例如，CrewAI 可能会雇佣一个“作家 Agent”（底层用的是 OpenAI）和一个“研究员 Agent”（底层用的是通过 Transformers 跑在本地的 Llama 4）。

### 1. 发展历程

从单打独斗到万物统一

- 2018 - 起步期：发布 `pytorch-pretrained-bert`，最初只是为了复现 Google 的 BERT。
- 2019-2020 - 扩张期：更名为 `transformers`。引入了 **Pipeline** 概念，让小白也能三行代码跑 AI。支持了 TensorFlow 2.0，实现了框架的大一统。
- 2021-2024 - 爆发期：不仅是 NLP，模型开始覆盖计算机视觉（ViT）和音频（Whisper）。Hugging Face Hub 成为 AI 界的 GitHub。
- 2025-2026 - 工业化期 (v5版本)：重点转向了**推理性能**（如集成 PagedAttention）、**多模态深度集成**和**边缘端部署**（Transformers.js v4 允许模型在浏览器飞速运行）。

### 2. 设计思想

Transformers 的设计极其优雅，其核心哲学是“每一个模型由三个基本组件构成”：

1. Configuration (配置类)：模型的“基因图谱”，定义层数、头数、隐藏层维度等超参数。
2. Tokenizer/Processor (处理类)：模型的“翻译官”，负责把文字、图片或声音变成模型能看懂的数字（Tensor）。
3. Model (模型类)：模型的“大脑”，负责执行复杂的数学运算并输出预测结果。

## 二、包组成

基于 2026 年 v5 标准，现在的 `transformers` 库比以前更模块化，主要由以下部分组成：

- `models`: 核心仓库，包含数百种模型架构（Llama 4, Qwen 3, BERT等）的参考实现。
- `pipelines`: 高级抽象 API。你不需要懂模型结构，只需告诉它任务类型（如 `task="visual-qa"`），它自动帮你搞定一切。
- `trainer`: 工业级训练/微调接口。原生支持了混合精度、FlashAttention 和分布式训练。
- `generation`: 专门负责“生成”文本的逻辑。集成了最新的采样策略（如分层采样、推测性采样）。
- `transformers serve` (新)：v5 引入的新特性，让开发者可以一键启动一个兼容 OpenAI 标准的本地推理服务器。

## 三、核心类

### 1. 模型类

AutoModel vs AutoModelForCausalLM 的核心区别在于**“有没有最后那一层（Head）”**。

- **拿表示做别的事**（embedding/自定义任务）→ `AutoModel`
- **按上下文往后生成 token**→ `AutoModelForCausalLM`

形象理解：AutoModel 是一个充满智慧但沉默的哲学家（只能感受语义）；而 AutoModelForCausalLM 是给他装上了麦克风，让他能够开口说话（生成文本）。

#### 1) AutoModel

- 输出内容：输出的是 Hidden States（隐藏状态，即一堆稠密的向量）。
- 本质：它是模型的“身体”，没有具体的“嘴巴”。它把输入的 Token 转化为高维语义表示，但不负责预测具体的下一个字。
- 用途：主要用于特征提取、计算句子相似度（Embedding），或者作为自定义下游任务（如分类、回归）的特征输入。

#### 3) AutoModelForCausalLM

- 输出内容：输出的是 Logits（词表上的概率分布）。
- 本质：在 AutoModel 的基础上加了一个 Language Modeling Head（通常是一个线性层，把隐藏向量映射到词表大小）。
- 用途：用于文本生成、对话、续写。它会根据前面的词，预测下一个词出现的概率。这是 GPT、Llama、Qwen 等生成式模型最常用的类。

## 四、代码示例

[transformers.py](./examples/model-apis/transformers.py ":include :type=code python")
