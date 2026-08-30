# OpenCLI skill

可以把 OpenCLI 理解成一种**“把现有软件系统改造成 Agent 可调用工具”的开源实现范式**。但如果只叫它“连接器”，会低估它。

OpenCLI 官方自己的定位是：

> “Convert any website into a CLI & run Browser Use on your logged-in Chrome.”

它不仅支持网站，还试图把浏览器会话、Electron 应用、本地 CLI 都统一成确定性的接口，供人或 AI Agent 调用。

我更倾向于把它定义成：

> **Agent Adapter Runtime / Connector Framework**
> 一个把 Legacy System 转换成 Agent-friendly semantic API/CLI 的框架。

------

## 1. 它解决的核心问题是什么？

传统企业系统经常是这样的：

```text
Legacy System
    ↓
Web 页面
    ↓
菜单 / 表格 / 按钮 / 表单
    ↓
人操作
```

比如一个 10 年前开发的业务系统：

```text
登录
→ 选择工程
→ 打开“安全管理”
→ 打开“日计划一本账”
→ 输入日期
→ 点击查询
→ 翻页
→ 看表格
```

对于人来说没问题。

但 Agent 希望看到的是：

```text
dailyPlanLedger(date="2026-08-30")
```

甚至：

```text
查询今天所有高风险作业
```

所以中间缺了一层：

```text
        Agent
          │
          ▼
┌──────────────────────┐
│ Semantic Tool Layer  │
│ daily-plan-list      │
│ risk-work-list       │
│ project-search       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Legacy System        │
│ Web / API / Browser  │
└──────────────────────┘
```

**OpenCLI 做的就是这一层。**

------

## 2. 它与普通“浏览器 Agent”最大的区别

比如 Playwright / Browser Use / browser-use 类型工具，本质暴露的是：

```text
open(url)
click(selector)
fill(selector, value)
getText(selector)
```

这些是**操作原语**。

Agent 要自己理解：

```text
“我要查日计划”
→ 找菜单
→ 点击
→ 找日期框
→ 输入
→ 点击查询
→ 找表格
→ 翻页
```

这很像让 Agent 每次重新操作电脑。

OpenCLI 同时提供 Browser primitives，但更重要的是鼓励把稳定工作流进一步固化成 Adapter。README 明确区分了两种使用方式：

- `opencli browser ...`：Agent 临时操作真实浏览器；
- `opencli <site> <command>`：已经封装好的确定性 adapter。

于是：

```text
第一次
Agent
 ↓
Browser primitives
 ↓
探索系统
 ↓
发现真实业务接口 / 页面逻辑
 ↓
形成 Adapter

以后
Agent
 ↓
Semantic Command
 ↓
Adapter
 ↓
业务系统
```

这是 OpenCLI 最有价值的思想。

------

## 3. 所以它不是简单 RPA

传统 RPA：

```text
点击坐标
→ 输入文字
→ 找按钮
→ 点击
→ OCR/DOM 读表格
```

OpenCLI 更倾向：

```text
                     Legacy Website
                          │
             ┌────────────┴────────────┐
             │                         │
           UI/DOM                 Network API
             │                         │
             └────────────┬────────────┘
                          │
                     OpenCLI Adapter
                          │
                   semantic command
                          │
                          ▼
                        Agent
```

如果能找到页面背后的 API，它更倾向于直接用 API。

如果 API 需要浏览器 Cookie，则复用浏览器登录态。

如果请求必须由网页 JS 生成签名，它可以在浏览器里执行或者拦截请求。

实在不行，再走 UI。

README 对 Adapter 的认证/访问路径就明确列了：

```text
PUBLIC
COOKIE
INTERCEPT
UI
LOCAL
```

而 Adapter 开发流程也是：

```text
Recon
→ Discover endpoint
→ Pick auth
→ Decode response
→ Design output
→ Verify
```

这其实已经不是普通 RPA 了，而更像：

> **对现有应用进行运行时“接口化”。**

------

## 4. Browser Bridge 是整个思想的关键

这里是 OpenCLI 特别适合 Legacy System 的地方。

现代 Agent 系统经常遇到一个现实问题：

```text
已有 Web 系统
+
复杂 SSO
+
验证码
+
Cookie
+
企业统一认证
+
反爬 / WAF
```

如果你重新写一个 HTTP Client：

```text
Agent
 ↓
独立 SDK
 ↓
重新登录
```

你需要重新解决：

```text
SSO
Cookie
Token
验证码
签名
WAF
风控
```

而 OpenCLI 的做法是：

```text
             用户已经登录的 Chrome
                     │
                     │ session owner
                     ▼
             Browser Bridge Extension
                     │
                  local daemon
                     │
                OpenCLI Runtime
                     │
               Adapter / Agent
```

官方 README 明确说明 Browser Bridge 是 Chrome 扩展 + 本地 daemon，OpenCLI 通过它连接已经登录的 Chrome。

也就是说：

> **浏览器不是一个临时自动化工具，而是 Session Owner。**

这是个很重要的架构思想。

------

## 5. 更准确地说，OpenCLI 有三层

我会把它抽象成：

```text
┌──────────────────────────────────────────────┐
│                 Agent Layer                  │
│ Claude / Cursor / Codex / other Agent        │
└──────────────────────┬───────────────────────┘
                       │
                 semantic command
                       │
┌──────────────────────▼───────────────────────┐
│              OpenCLI Adapter Layer           │
│                                              │
│ twitter.search                               │
│ bilibili.hot                                 │
│ xiaohongshu.note                             │
│ mylegacy.project.list                        │
│                                              │
│ 参数验证 / 输出归一 / command discovery      │
└──────────────────────┬───────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ Browser API  │ │ Browser UI  │ │ External CLI │
│ cookie/api   │ │ click/fill  │ │ gh/docker... │
│ intercept    │ │ DOM         │ │ local binary │
└──────┬───────┘ └─────┬───────┘ └──────┬───────┘
       └───────────────┬┴─────────────────┘
                       ▼
              Legacy / Existing System
```

它甚至允许把现有本地二进制注册成 OpenCLI command：

```text
opencli external register my-tool
```

之后：

```text
opencli my-tool ...
```

只是透传到已有 binary。

所以它实际上在构造一个：

> **Agent Tool Bus / CLI Hub**

------

## 6. 那么，它是不是“连接器”？

可以叫连接器，但有三个层次

### 最简单的 connector：

```text
Agent
 ↓
Connector
 ↓
API
```

例如：

```text
Agent → Gmail API
Agent → GitHub API
Agent → Salesforce API
```

这种连接器前提是：

> **系统本来就有一个稳定、正式、可访问的 API。**

OpenCLI 针对的很多场景恰恰不是这样。

它可以处理：

```text
没有公开 API
只有 Web UI

有内部 API
但是没有文档

API 需要浏览器 Cookie

API 需要页面 JS 计算 Token

API 只能在浏览器环境工作

最终只能点击 UI
```

因此：

### 普通 Connector

```text
Existing API
    │
    ▼
Connector
    │
    ▼
Agent
```

### OpenCLI

```text
Existing Application
    │
    ├── Internal API
    ├── Browser session
    ├── Network request
    ├── DOM
    ├── UI
    └── Local binary
             │
             ▼
       Adapter Runtime
             │
             ▼
     Semantic Interface
             │
             ▼
           Agent
```

所以更准确的叫法是：

> **Connector Builder / Adapter Framework**

甚至可以说：

> **它是“连接器的生产工具”，而不只是一个连接器。**

------

## 7. 为什么 CLI 特别适合 Agent？

这也是 OpenCLI 的一个核心设计选择。

Agent 并不特别需要 GUI。

Agent 非常擅长：

```bash
opencli project list --year 2026
```

并消费：

```json
[
  {
    "projectCode": "...",
    "name": "...",
    "voltageLevel": "500"
  }
]
```

因为 CLI 天然拥有：

```text
command
arguments
stdout
stderr
exit code
JSON
```

这其实已经非常接近 Tool Calling：

```text
Tool
  name
  parameters
  result
  error
```

因此：

```text
CLI ≈ 本地 Tool Protocol
```

而且它比 MCP 更简单。

------

## 8. OpenCLI 和 MCP 的关系

这两个不要混在一起。

MCP 解决：

> **Agent 怎么发现和调用 Tool。**

OpenCLI 解决：

> **一个原本不是 Tool 的网站，怎么变成 Tool。**

所以可以组合：

```text
Legacy System
      │
      ▼
OpenCLI Adapter
      │
      ▼
Semantic CLI
      │
      ▼
MCP Server
      │
      ▼
Agent
```

或者直接：

```text
Agent
 ↓ shell
OpenCLI
 ↓
Legacy System
```

因此 OpenCLI 与 MCP 更多是**互补**，不是竞争关系。

------

## 9. 对 Legacy System 来说，这种方法为什么很有价值

传统企业系统 Agent 化通常有三条路。

| 方法     | 做法                           | 成本         |
| -------- | ------------------------------ | ------------ |
| 重构系统 | 给旧系统重新建设正式 API       | 极高         |
| RPA      | Agent 操作页面                 | 低，但不稳定 |
| Adapter  | 复用现有系统行为，形成语义 API | 中           |

OpenCLI 属于第三条。

它相当于：

```text
不改 Legacy System

而是在外面增加：

Legacy System
      │
      ▼
Compatibility Layer
      │
      ▼
Agent-native Interface
```

这跟很多历史上的计算机兼容层非常类似。

比如：

```text
旧数据库 → ODBC
旧系统 → REST Gateway
设备协议 → OPC UA Gateway
Legacy Web → Agent Adapter
```

我认为这是理解 OpenCLI 最合适的方式。

------

## 10. 一个具体例子

假设某企业有一个 2015 年建设的工程管理系统。

页面：

```text
工程管理
  └─ 安全管理
       └─ 风险作业
```

Agent 最初只能：

```text
browser.open
browser.click
browser.click
browser.fill
browser.click
browser.extract
```

OpenCLI 的开发过程是：

```text
① Agent 用 Browser Bridge 打开系统

② 观察 Network
   POST /api/risk/queryPage

③ 发现登录态来自浏览器 Cookie

④ 分析 payload
   {
      date: "...",
      projectCode: "...",
      page: {...}
   }

⑤ 写 Adapter

⑥ 暴露

legacy risk list
    --date
    --project

⑦ Agent 从此直接调用
```

最终：

```text
Agent:
“帮我看今天有哪些高风险作业”

↓ planning

legacy risk list --date 2026-08-30

↓ Adapter

Browser Session API

↓ Legacy system

JSON result

↓ Agent reasoning

生成分析
```

**UI 在 Agent 的正常工作路径里已经消失了。**

但登录仍然可以继续依赖 UI/浏览器。

这就是这个架构最漂亮的地方。

------

## 11. 所以我会怎样给 OpenCLI 定性

不是：

> 浏览器自动化工具。

也不仅是：

> CLI 工具。

更不是单纯：

> MCP connector。

我认为更准确的是：

> **OpenCLI 是一种 Agent Compatibility Layer：通过 Browser Bridge、接口逆向、Adapter 和 CLI Contract，把原本面向人的 Web/桌面/本地软件转化成 Agent 可发现、可调用、可验证的语义工具。**

如果专门讨论企业 Legacy System，那么可以进一步概括成：

> **Legacy System → Agent Tool 的开源参考实现。**

而且它最重要的创新不一定是某段浏览器技术，而是这个设计原则：

```text
Browser 负责：
登录、会话、环境、复杂交互

Adapter 负责：
业务语义、参数、稳定接口

Agent 负责：
意图理解、规划、组合工具

Legacy System：
尽量不修改
```

这正是很多企业现有系统 Agent 化比较现实的一条路径。

如果继续往下学 OpenCLI，我建议下一步不要再看“它有哪些命令”，而是直接拆 **Adapter 的四种实现路径：PUBLIC → COOKIE → INTERCEPT → UI**。理解这四层之后，OpenCLI 的架构基本就看透了。