# Web 基础知识

逆向工程的目标不是破解，而是理解：页面如何组织数据、请求如何获得合法性、采集如何稳定运行。本篇覆盖四块基础知识——请求模型、浏览器控制、会话维持与采集工作流。

## 一、请求-响应模型

```text
用户操作（点击/滚动）
        ↓
页面 JS 执行
        ↓
生成参数（token / sign / cursor）
        ↓
发起请求（fetch / xhr）
        ↓
服务器返回数据
        ↓
页面渲染 DOM
```

**request 的关键**是请求怎么构造、带了什么材料：URL、Method、Headers、Query、Body，以及 `cursor`（基于位置的稳定翻页，可能含 lastID/时间戳/签名）与 `page`（不稳定，会乱序重复丢失）的区别。

**response 的关键**是响应值不值得利用：状态码、JSON 结构中的业务字段、`has_more` 与 `next_cursor`。

**渲染**是前端把 response 数据放进 DOM（如 `response.comments[0].content` 插入评论节点）。三种取数方式各有取舍：

| 方式 | 优点 | 缺点 |
| --- | --- | --- |
| DOM | 直观 | 易受页面结构变化影响 |
| response | 干净、结构化 | 需要会筛接口 |
| request 复现 | 可脱离浏览器 | 成本高、易失效 |

### 处理加密请求的决策树

```text
Step1 看 response：明文 JSON → 直接监听，不需要解密
Step2 看依赖：强依赖 JS/sign → 浏览器方案；弱依赖 → HTTP 可行
Step3 看目标：快速拿数据 → 监听；大规模系统 → 才考虑复现
```

三种典型情况：

1. **响应明文**（即使请求带 sign）：直接监听 response 拿数据；
2. **参数加密但响应可读**：不要逆向参数，用浏览器发请求 + 监听结果；
3. **响应本身加密**：找解密逻辑，或用 evaluate 调用页面解密函数。

```python
def handle_response(response):
    if "api" in response.url:
        try:
            print(response.url, response.json())
        except Exception:
            pass

page.on("response", handle_response)
```

### 观察页面的四个层次

| 层次 | 内容 | 常用手段 |
| --- | --- | --- |
| DOM 层 | 用户看得到的渲染结果 | locator、text_content、get_attribute |
| JS 层 | 运行时内部状态（window 变量、storage、token/sign、函数返回值） | page.evaluate() |
| Network 层 | fetch/xhr 请求与响应、分页 cursor | 监听 request/response |
| Environment 层 | 让请求"合法"的环境（cookie、上下文、登录态、指纹、时机） | browser/context/page、真实流程复用 |

### 接口分类

筛选目标接口的三步：URL 粗筛 → JSON 精筛 → 行为筛选（只在点击后/滚动后监听）。按性质分三类：**结果接口**（response 直含业务数据，优先监听）、**过程接口**（上报/心跳/埋点，忽略）、**资源接口**（图片/CSS/JS，忽略）。

### 前端反爬三件套

| 手段 | 本质 |
| --- | --- |
| JS 混淆 | 看不懂——变量名打乱、逻辑变形，抬高分析成本 |
| WASM | 更看不懂——接近编译代码，常用于加密签名 |
| 环境强绑定 | 离不开浏览器——算法内部读取 UA、窗口属性、canvas/WebGL 指纹、时间差，脱离真实环境即失效 |

## 二、浏览器自动化

> 浏览器自动化 = 控制三件事：环境（登录态/context）、请求（什么时候发/怎么发）、数据（response/DOM）。

### 对象三件套

- **browser**：浏览器程序（Chrome 实例）；
- **context**：一次独立会话——它同时是账号隔离、状态隔离和降低风控串味；
- **page**：一个标签页。

### 存储三类

| 类型 | 类比 | 本质区别 |
| --- | --- | --- |
| cookie | 身份证（每次过安检出示） | 服务器要看的，自动随请求发送；~4KB；身份认证主力 |
| localStorage | 家里的保险柜 | 前端长期缓存，不自动发送；~5MB |
| sessionStorage | 手里的草稿纸 | 当前 tab 临时状态，关闭即失 |

### 认证的本质

为什么补上 localStorage 里的 token 还是 401？因为 token 只是"身份材料"之一，不一定是完整通行证——很多站点还校验签名（防伪造）、时间戳（限重放）、nonce（防重复）、设备环境字段（证可信上下文）和行为链路（证明请求来自正常页面流程）。

同样面对 401/403，背后是两类问题：认证材料不全，或材料对了但生成环境不对。**把请求抄下来是复制表面形式，把请求跑成功是复现生成条件**——请求不是一个静态文本，而是一个动态产物。

### 心智模型三层

- 表层：页面操作（点击/输入/滚动）；
- 中层：请求构造（header/cookie/token/参数）；
- 底层：环境生成能力（JS 执行上下文、storage、指纹、时序、页面生命周期、登录态演化）。

排查思路沿底层向上走：页面操作 → 请求出现 → 合法性依赖什么 → 哪些依赖来自环境 → 该选纯 HTTP、半自动化还是浏览器上下文。

### 函数选择

- `page.text_content("h1")`：从已渲染的 DOM 里取文本——用户眼睛能看到的结果；
- `page.evaluate("() => document.title")`：进入页面自己的 JS 环境执行代码——访问 JS 世界里的变量、storage、动态计算的 token/sign。

## 三、会话与登录态

登录态的生命周期：

```text
登录动作 → 服务器下发凭证 → 浏览器保存 → 后续请求携带 → 持续校验 → 某一时刻可能失效
```

### 失效的四类原因

1. **凭证过期**：session cookie 过期、token 过期、refresh 机制失效；
2. **服务端主动失效**：单点登录踢下线、异地登录、风控清 session；
3. **本地状态丢失**：换了 context、cookie/storage 未保存、新会话未复用；
4. **依赖链断裂**：表面"已登录"，但后续请求还依赖 header token、页面初始化变量、特定进入路径或刷新后的上下文状态——表现也像"登录态没了"。

### 分析三问

- 状态从哪里来：cookie / localStorage / sessionStorage / header token？
- 状态怎么延续：context 复用、storage_state、页面内刷新后的新 token？
- 失效后怎么恢复：重新登录、重新初始化页面、重建上下文、更新 token？

## 四、采集与测试工作流

拿到一个站点，先做全站架构分析再动手：

1. **页面建档**：菜单、路由、页面分类、入口关系；
2. **接口采集**：页面触发请求、筛选器请求、初始化请求、主数据请求；
3. **关系映射**：页面—接口、字段—展示、菜单—权限、字段—字典；
4. **假设验证**：驱动关系、权限关系、字典关系、聚合关系；
5. **自动化策略**：requests 优先还是浏览器兜底；
6. **脚本生成**：DrissionPage / requests / OpenAPI 草案 / 监控接入。

采集主循环：

```text
触发 → 拿 response → 提取数据 → 提取 cursor（处理分页）→ 判断继续/停止 → 去重 → 异常兜底
```

各环节要点：

- **触发机制**：滚动？点击？自动加载？
- **提取机制**：JSON 结构解析、字段抽取、去重；
- **翻页与停止**：cursor 怎么传、has_more 怎么判、什么时候停。

### 故障四象限

| 类别 | 典型现象 | 关键词 |
| --- | --- | --- |
| 时间问题 | 元素没出来、请求未返回、DOM 未渲染完 | wait / timeout / ready |
| 状态问题 | 有时有数据有时空、cursor 失效、token 过期 | cookie / token / cursor / session |
| 环境问题 | 必须从某页面点进去才有数据、换 context 就不行 | context / 来源页 / JS 环境 / 风控上下文 |
| 网络问题 | 超时、5xx、连接失败、中断 | timeout / retry / backoff |

遇到失败先归入象限，再对症处理——这比盲目重试有效得多。

进阶案例见[瑞数6初探](knowledge/web-automation/ruishu6-notes)：当站点使用动态防护时，上述常规手段如何升级为系统化的逆向工程。
