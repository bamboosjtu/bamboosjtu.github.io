# That Open 新手入门

That Open Company 是一家创建**免费开源 BIM 技术**的公司，前身即知名开源项目 **IFC.js** 的团队，目标是"降低开发开放式 BIM 应用的门槛"，让任何人都可以使用、修改、甚至出售基于其技术的软件。

## 一、. That Open 是什么

That Open 把自己的生态称为 **AECOsystem**，由两部分组成：

| 组成部分 | 说明 |
|---|---|
| **That Open Platform** | 技术平台，包含 That Open Libraries（一组 100% 免费开源的 JavaScript 库）、That Open Docs（持续更新的官方文档与示例）等。 |
| **That Open People** | 开发者社区（people.thatopen.com），"openers" 在这里交流、学习、合作开发。 |

公司由 Antonio González Viegas 领导，其公开演讲的主题即是"自由软件与开放技术应用于 AECO 行业"。

### 1. 项目特点

- **免费 + 开源（MIT 协议）**：核心库全部 MIT 授权，可以商用、可以卖钱，限制少。
- **Web 优先**：所有库基于 JavaScript/TypeScript 与 Three.js（全球最流行的网页 3D 库），构建的 BIM 应用可直接跑在浏览器里。
- **一份代码，多端运行**：网页（原生或 React/Vue/Angular）、服务器（Node.js）、桌面（Electron）、移动端（React Native 或 iframe 嵌入 Flutter）。
- **功能覆盖完整**：IFC 的导入、显示、导航、编辑、导出；其他 3D 格式导入；3D+2D 建模与编辑（进行中）；模型存储与分发；测量、剖切、标注；与 PowerBI、Sharepoint、Cesium、Mapbox 等数据/GIS 系统集成。

---

### 2. 生态全景：核心库一览

That Open 的技术统称 **That Open Engine**——官方称之为"AECO 软件引擎"，100% 开源免费，构建于 Three.js 之上。 GitHub 组织 **ThatOpen** 共有 15 个公开仓库，其中与新手直接相关的是下面这些（数据截至 2026-10-24）。

| 仓库 / npm 包 | 作用 | Stars | 活跃度 |
|---|---|---|---|
| [engine_web-ifc](https://github.com/ThatOpen/engine_web-ifc)（npm: `web-ifc`） | 用 JavaScript **读写 IFC 文件**的底层引擎，"以原生速度"解析 IFC | ≈1100 | 持续维护 |
| [engine_components](https://github.com/ThatOpen/engine_components)（npm: `@thatopen/components` + `@thatopen/components-front`） | **最核心的上层库**：基于 Three.js 的一整套 BIM 组件（后处理、尺寸标注、平面图导航、DXF 导出等），MIT 授权 | ≈717 | 非常活跃 |
| [engine_fragment](https://github.com/ThatOpen/engine_fragment)（npm: `@thatopen/fragments`） | 开源几何格式 Fragments：**高效存储、显示、导航、编辑海量 BIM 数据**，任意设备可流畅加载 | ≈222 | 持续维护 |
| [engine_ui-components](https://github.com/ThatOpen/engine_ui-components)（npm: `@thatopen/ui`） | 面向 BIM 应用的 Web UI 组件集合 | ≈59 | 维护中 |
| [engine_templates](https://github.com/ThatOpen/engine_templates)（npm: `create-bim-app`） | 脚手架 CLI：一条命令生成基于 That Open Engine + Vite 的 BIM 应用模板（TypeScript） | ≈60 | 维护中 |
| web-ifc-three（npm: `web-ifc-three`） | web-ifc 的 Three.js 封装，曾是 **Three.js 官方 IFCLoader**；现已被新的组件体系取代 | ≈594 | 最后更新 2024-04 |
| [engine_docs](https://github.com/ThatOpen/engine_docs) | 官方文档仓库，文档站 docs.thatopen.com 的代码与示例部署 | ≈23 | 持续更新 |
| [ifcjs-crash-course](https://github.com/ThatOpen/ifcjs-crash-course) | 历史 Crash Course 的练习代码（见第 7 节） | 123 | 停更             |

**入门只需要记住三个包的关系**：

```
web-ifc（底层：解析 IFC 文件）
   ↑
@thatopen/fragments（中层：高性能 BIM 数据格式）
   ↑
@thatopen/components（上层：开箱即用的 BIM 功能组件）
   +
three（Three.js 渲染引擎，一切的基础）
```

四个包**版本必须互相匹配**（官方文档特别强调 peer dependencies 要与库所用版本一致）。

`fragments` 是 That Open 自研的开放几何格式，把 IFC 转成它之后，大模型在手机上也能流畅加载。

---

## 二、第一个 3D 应用

### 1. 方式 A：脚手架一键开始（推荐）

官方提供了 `create-bim-app` 脚手架，基于 That Open Engine + Vite 生成 TypeScript 模板，启动一个现成的 IFC 浏览器。

```bash
# 在任意位置新建项目文件夹并进入后执行：
npm create bim-app@latest
# 按提示选择模板（目前提供 Vanilla 模板），完成后：
npm install
npm run dev
```

### 2. 方式 B：手动安装理解每个包

```bash
npm i @thatopen/components
npm i three
npm i @thatopen/fragments
npm i web-ifc
```

注意：`fragments` 与 `web-ifc` 是 peer dependencies，**版本需与 `@thatopen/components` 所用的保持一致**。

### 3. 官方权威示例

以下代码直接来自 [ThatOpen/engine_components 官方 README](https://github.com/ThatOpen/engine_components)，创建一个可用鼠标/触摸导航的 3D 立方体场景，完整版见官方 `Worlds` 示例：[cite:8]

```js
import * as THREE from "three";
import * as OBC from "@thatopen/components";

const container = document.getElementById("container")!;

const components = new OBC.Components();

const worlds = components.get(OBC.Worlds);
const world = worlds.create<
  OBC.SimpleScene,
  OBC.SimpleCamera,
  OBC.SimpleRenderer
>();
world.scene = new OBC.SimpleScene(components);
world.renderer = new OBC.SimpleRenderer(components, container);
world.camera = new OBC.SimpleCamera(components);

components.init();

const material = new THREE.MeshLambertMaterial({ color: "#6528D7" });
const geometry = new THREE.BoxGeometry();
const cube = new THREE.Mesh(geometry, material);
world.scene.three.add(cube);

world.scene.setup();
world.camera.controls.setLookAt(3, 3, 3, 0, 0, 0);
```

这段不到 30 行的代码浓缩了 That Open 的两个设计思想——**组件模式**与**World（世界）抽象**：

1. **`new OBC.Components()`**：一切从"组件管理器"开始。组件（Component）是这些库的基本积木，有两大特点：全局可访问（应用各处解耦地取用逻辑）+ 生命周期管理（3D 应用每帧都要更新，还要防止内存泄漏）。[cite:3]
2. **`components.get(OBC.Worlds)`**：想用某个功能就"取"对应组件——这是全局访问模式的体现。
3. **`worlds.create<...>()`**：创建一个"世界"。世界 = 场景（Scene）+ 相机（Camera）+ 渲染器（Renderer）三件套，正是 Three.js 的核心三角。[cite:8]
4. **`components.init()`**：初始化并启动每帧更新循环。
5. **`new THREE.Mesh(...)` + `world.scene.three.add(cube)`**：从这里开始就是**纯 Three.js 语法**——That Open 不重造轮子，`world.scene.three` 直接暴露原生 Three.js 场景，任何 Three.js 教程学到的知识都能用。[cite:8]

跑起来之后你就拥有了一个可旋转、缩放、平移的 3D 视口——所有 BIM 应用的起点。

---

## 三、模型与官方学习路径

### 1. 官方文档三大板块

[docs.thatopen.com](https://docs.thatopen.com) 分为三部分：

- **🧩 Components**：组件的入门与自定义组件开发，含教程路径；
- **📋 API**：全部类/属性/方法的自动生成文档（与 IDE 提示一致）；
- **👩🏻‍🏫 Tutorials**：分步教程，每个教程都带一个**可实时操作的在线示例应用**（示例由仓库最新代码自动部署，文档即测试）。

### 2. 官方教程路径

官方把几十篇教程组织成了三段式路线：

| 阶段 | 主题 | 代表教程 |
|---|---|---|
| 第一阶段：库的第一步 | 核心组件基础 | 创建你的第一个 3D 应用、设置网格（Grid）、与场景交互、创建剖切面（Clipping planes） |
| 第二阶段：进阶 3D 应用 | 专业级体验 | 高级相机、可扩展 3D 场景、精美渲染、小地图、阴影、剖切边线、距离测量、快速创建 UI |
| 第三阶段：BIM 数据 | 加载与编辑 | 加载 IFC 文件、认识 Fragments、查看已加载模型、读取模型属性、理解模型关系（墙属于哪层等）、几何过滤 |

### 3. 加载 IFC 的典型流程

理解流程即可，具体 API 以官方 IfcLoader / FragmentsManager 教程为准（API 迭代较快）：

1. 用 `IfcLoader` 组件加载 `.ifc` 文件（浏览器 `input[type=file]` 或 URL）；
2. 底层由 `web-ifc` 解析、转换为 **Fragments** 格式并缓存；
3. `FragmentsManager` 负责把 Fragment 加载进世界、供相机导航；
4. 后续可用 `Classifier`/`ItemsFinder` 按类别过滤、`Highlighter` 高亮、`LengthMeasurement` 测量——全是取组件、设参数的组合。[cite:11]

---

## 四、推荐学习路线

综合调研结果，给新手一条"免费 + 最新 + 少走弯路"的路线：以 [docs.thatopen.com 官方教程路径](https://docs.thatopen.com/components/tutorial-paths)为主线，用旧 IFC.js Crash Course 补前端基础，用 [Tutorials 组件目录](https://docs.thatopen.com/Tutorials/Components/)按需查阅，完成一个可开源的个人项目。

**官方教程页的通用技巧**：每个教程页面顶部都有 "Source" 链接，直达 GitHub 上的完整源码（例如 [IfcLoader 教程](https://docs.thatopen.com/Tutorials/Components/Core/IfcLoader)的源码在 [packages/core/src/fragments/IfcLoader/example.ts](https://github.com/ThatOpen/engine_components/blob/main/packages/core/src/fragments/IfcLoader/example.ts)），页面右侧还有可实时操作的在线示例——看不懂文字时直接抄源码即可。

### Section1：打地基

**Chapter01 —— Web 基础修补**

- 学什么：HTML 结构、CSS（重点 Flexbox）、DOM 操作、JavaScript 模块化（`import/export`）；
- 资料：[MDN Web 文档](https://developer.mozilla.org/zh-CN/)；旧 [ThatOpen/ifcjs-crash-course](https://github.com/ThatOpen/ifcjs-crash-course) 的 `exercises/` 目录（HTML、CSS/Flexbox 等练习与技术版本无关，永不过时）；
- 产出：能手写一个带按钮、表单和样式的静态页面。

**Chapter02 —— Three.js 三件套**

- 学什么：Scene / Camera / Renderer / OrbitControls，以及 Mesh、Geometry、Material 的概念；
- 资料：[three.js 官方手册](https://threejs.org/manual/)（"Creating a scene" 等入门章节）；
- 产出：**不用 That Open**，纯 Three.js 实现一个可鼠标旋转的立方体——这一步是检验地基是否牢固的关键。

**Chapter03 —— 正式进入 That Open**

- 学什么：[Getting Started](https://docs.thatopen.com/components/getting-started)（组件理念、四个包及版本对齐）+ [Worlds 教程](https://docs.thatopen.com/Tutorials/Components/Core/Worlds)（创建第一个 3D 世界，含 UI 面板）；
- 环境：用第 5 节脚手架 [create-bim-app](https://www.npmjs.com/package/create-bim-app)[cite:16] 一键生成 TypeScript + Vite 模板；
- 产出：跑通官方 Worlds 示例，并能向别人解释 `Components → Worlds → World` 三层结构。

**Chapter04 —— 核心交互组件**

- 学什么：[Grids](https://docs.thatopen.com/Tutorials/Components/Core/Grids)（网格）、[Raycasters](https://docs.thatopen.com/Tutorials/Components/Core/Raycasters)（射线拾取/点选）、[OrthoPerspectiveCamera](https://docs.thatopen.com/Tutorials/Components/Core/OrthoPerspectiveCamera)（正交/透视双相机）；
- 产出：一个带网格、能点选物体并在控制台输出信息的视口。

### Section2：进阶 3D + BIM 数据

**Chapter05 —— 剖切与渲染质感**

- 学什么：[Clipper](https://docs.thatopen.com/Tutorials/Components/Core/Clipper)（剖切平面）、[ClipStyler](https://docs.thatopen.com/Tutorials/Components/Front/ClipStyler)（剖切边线与样式）、[PostproductionRenderer](https://docs.thatopen.com/Tutorials/Components/Front/PostproductionRenderer)（后处理：环境光遮蔽、轮廓线、抗锯齿）；
- 产出：模型可以被剖面"切开"，且画面有专业软件级质感。

**Chapter06 —— 高亮、悬停与信息展示**

- 学什么：[Highlighter](https://docs.thatopen.com/Tutorials/Components/Front/Highlighter)（点选高亮）、[Hoverer](https://docs.thatopen.com/Tutorials/Components/Front/Hoverer)（悬停反馈）、[Marker](https://docs.thatopen.com/Tutorials/Components/Front/Marker)（标记）与 [Outliner](https://docs.thatopen.com/Tutorials/Components/Front/Outliner)（大纲树）；
- 产出：点选模型构件能变色、能弹出信息标签。

**Chapter07 —— BIM 数据：加载 IFC（里程碑！）**

- 学什么：[IfcLoader](https://docs.thatopen.com/Tutorials/Components/Core/IfcLoader)[cite:22] —— 官方推荐工作流是**运行时一次性把 IFC 解析转换为 Fragments（`.frag`）文件并保存复用**，之后每次启动直接加载 Fragment，而非反复现场解析；再学 [FragmentsManager](https://docs.thatopen.com/Tutorials/Components/Core/FragmentsManager) 管理模型加载与缓存；
- 产出：把自己的一个真实 IFC 模型加载进应用并流畅导航（新手可先用社区/官方仓库里的示例 IFC）。

**Chapter08—— 属性、过滤与测量**

- 学什么：[Classifier](https://docs.thatopen.com/Tutorials/Components/Core/Classifier)（按类别/楼层等分组）、[ItemsFinder](https://docs.thatopen.com/Tutorials/Components/Core/ItemsFinder)（按规则查找构件）、[Hider](https://docs.thatopen.com/Tutorials/Components/Core/Hider)（显示/隐藏）、[LengthMeasurement](https://docs.thatopen.com/Tutorials/Components/Front/LengthMeasurement)（测距）；
- 产出："半成品查看器"：能按楼层隐藏、点选看属性、测距离。

### Section3：实战项目 + 进阶选学

**Chapter09 —— 毕业项目：BIM 模型查看器**

- MVP 功能清单：
  1. 加载 `.frag` 模型 + 网格 + 相机导航；
  2. 楼层/类别树过滤（Classifier + Hider）；
  3. 点选高亮 + 属性面板（Highlighter + 模型属性 API）；
  4. 距离测量（LengthMeasurement）；
  5. 剖切（Clipper）；
  6. 后处理美化（PostproductionRenderer）。

**Chapter10 —— 进阶选学（按兴趣挑 1-2 个）**

- [Viewpoints](https://docs.thatopen.com/Tutorials/Components/Core/Viewpoints)（视点保存与截图）、[BCFTopics](https://docs.thatopen.com/Tutorials/Components/Core/BCFTopics)（BIM 协同问题单）、[TechnicalDrawings](https://docs.thatopen.com/Tutorials/Components/Core/TechnicalDrawings)（2D 图纸）、[PointCloudLoader](https://docs.thatopen.com/Tutorials/Components/Front/PointCloudLoader)（点云加载）、[CivilNavigators](https://docs.thatopen.com/Tutorials/Components/Front/CivilNavigators)（土木线性工程导航）。

**Chapter11 —— 收尾与发布**

- 项目整理后开源到 GitHub，写清 README 与运行步骤；
- 遇到问题：到 [engine_components 的 issues](https://github.com/ThatOpen/engine_components/issues) 提问（官方文档指定的官方求助入口），或到社区 [people.thatopen.com](https://people.thatopen.com/) 交流；
- 想继续系统深入（含 AI for BIM Developers 等专题）：[That Open University — Master BIM Software Developer](https://thatopen.com/university/master-bim/)（付费，可选）。

## 五、官方组件速查表

以下链接均位于 `docs.thatopen.com/Tutorials/Components/` 下，分为 **Core**（核心，`@thatopen/components`）与 **Front**（浏览器专属，`@thatopen/components-front`）两组。

| Core 组件教程 | Front 组件教程 |
|---|---|
| [Worlds](https://docs.thatopen.com/Tutorials/Components/Core/Worlds)（世界） | [Highlighter](https://docs.thatopen.com/Tutorials/Components/Front/Highlighter)（高亮） |
| [Grids](https://docs.thatopen.com/Tutorials/Components/Core/Grids)（网格） | [Hoverer](https://docs.thatopen.com/Tutorials/Components/Front/Hoverer)（悬停） |
| [OrthoPerspectiveCamera](https://docs.thatopen.com/Tutorials/Components/Core/OrthoPerspectiveCamera)（相机） | [PostproductionRenderer](https://docs.thatopen.com/Tutorials/Components/Front/PostproductionRenderer)（后处理渲染） |
| [Raycasters](https://docs.thatopen.com/Tutorials/Components/Core/Raycasters)（射线拾取） | [LengthMeasurement](https://docs.thatopen.com/Tutorials/Components/Front/LengthMeasurement)（长度测量） |
| [Clipper](https://docs.thatopen.com/Tutorials/Components/Core/Clipper)（剖切） | [AngleMeasurement](https://docs.thatopen.com/Tutorials/Components/Front/AngleMeasurement)（角度测量） |
| [FragmentsManager](https://docs.thatopen.com/Tutorials/Components/Core/FragmentsManager)（Fragments 管理） | [AreaMeasurement](https://docs.thatopen.com/Tutorials/Components/Front/AreaMeasurement)（面积测量） |
| [IfcLoader](https://docs.thatopen.com/Tutorials/Components/Core/IfcLoader)（IFC 加载） | [VolumeMeasurement](https://docs.thatopen.com/Tutorials/Components/Front/VolumeMeasurement)（体积测量） |
| [Classifier](https://docs.thatopen.com/Tutorials/Components/Core/Classifier)（分类器） | [Marker](https://docs.thatopen.com/Tutorials/Components/Front/Marker)（标记） |
| [ItemsFinder](https://docs.thatopen.com/Tutorials/Components/Core/ItemsFinder)（构件查找） | [Outliner](https://docs.thatopen.com/Tutorials/Components/Front/Outliner)（大纲树） |
| [Hider](https://docs.thatopen.com/Tutorials/Components/Core/Hider)（显隐控制） | [ClipStyler](https://docs.thatopen.com/Tutorials/Components/Front/ClipStyler)（剖切样式） |
| [BoundingBoxer](https://docs.thatopen.com/Tutorials/Components/Core/BoundingBoxer)（包围盒） | [PointCloudLoader](https://docs.thatopen.com/Tutorials/Components/Front/PointCloudLoader)（点云） |
| [EdgeProjector](https://docs.thatopen.com/Tutorials/Components/Core/EdgeProjector)（边线投影） | [SplatLoader](https://docs.thatopen.com/Tutorials/Components/Front/SplatLoader)（高斯泼溅） |
| [ShadowedScene](https://docs.thatopen.com/Tutorials/Components/Core/ShadowedScene)（阴影场景） | [DrawingEditor](https://docs.thatopen.com/Tutorials/Components/Front/DrawingEditor)（图纸编辑） |
| [Viewpoints](https://docs.thatopen.com/Tutorials/Components/Core/Viewpoints)（视点） | [CivilNavigators](https://docs.thatopen.com/Tutorials/Components/Front/CivilNavigators)（土木导航） |
| [Views](https://docs.thatopen.com/Tutorials/Components/Core/Views)（视图） | — |
| [BCFTopics](https://docs.thatopen.com/Tutorials/Components/Core/BCFTopics)（BFC 问题单） | — |
| [IDSSpecifications](https://docs.thatopen.com/Tutorials/Components/Core/IDSSpecifications)（IDS 规范） | — |
| [TechnicalDrawings](https://docs.thatopen.com/Tutorials/Components/Core/TechnicalDrawings)（技术图纸） | — |

---

## 六、新手常见坑与 FAQ

**Q1：npm 装完 `@thatopen/components` 一运行就报错？**
大概率是 peer dependency 版本不匹配。官方明确要求 `three`、`@thatopen/fragments`、`web-ifc` 与 components 库所用版本一致，装最新版即可对齐。

**Q2：为什么加载 IFC 前要先转 Fragments？**
IFC 是文本交换格式，直接渲染很慢；Fragments 是官方设计的开源几何格式，专门为"海量 BIM 数据在任何设备上高效加载"而生。[cite:9]

**Q3：跟着旧博客/视频敲代码，发现 API 对不上？**
That Open 迭代很快，2023 年前的资料（IFC.js / web-ifc-three / Components v1）API 已变。认准 docs.thatopen.com 与官方仓库 README，教程页面里的在线示例由仓库最新代码自动部署，是最可信的参考。

**Q4：`.wasm` 文件是什么？**
`web-ifc` 用 WebAssembly 实现"原生速度"的 IFC 解析，部署时需要把 `.wasm` 文件一起发给浏览器（脚手架模板已配置好）。

**Q5：能不能用 React / Vue？**
可以。组件体系与框架无关，官方文档说明其库兼容 vanilla、React、Vue、Angular、Svelte，甚至 Node.js 后端、Electron 桌面与 React Native 移动端。[cite:3]

**Q6：完全零编程基础能直接学吗？**
官方文档的诚实回答：这些文档假设你已具备 Web 开发基础概念（前端/后端/库/调试）；零基础者建议先学一轮 Web 编程再回来，That Open University 也提供从零开始、面向 BIM 方向的编程课程。

**Q7：商用要付费吗？**
核心库 MIT 授权，自由使用、修改、商用乃至出售成品软件；公司提供商业服务与 Accelerator 加速计划，但不构成使用限制。

---

## Sources

1. [That Open Company 官网首页（AECOsystem、That Open Platform / People）](https://thatopen.com/)
2. [That Open Docs — Introduction（能力清单、预备知识、文档结构）](https://docs.thatopen.com/)
3. [That Open Docs — Components: Getting Started（安装、peer deps、组件理念、兼容性）](https://docs.thatopen.com/components/getting-started)
4. [That Open Docs — Tutorial Paths（三阶段官方学习路径）](https://docs.thatopen.com/components/tutorial-paths)
5. [That Open Engine 官方介绍页（100% 开源、基于 Three.js、Web 优先）](https://thatopen.com/bim-software-open-source/engine/)
6. [web-ifc 官方文档（"以原生速度读写 IFC"）](https://thatopen.github.io/engine_web-ifc/docs/)
7. [GitHub 组织 ThatOpen（15 个公开仓库、星数、活跃度）](https://github.com/ThatOpen)
8. [ThatOpen/engine_components README（Open BIM Components、双包结构、官方示例代码）](https://github.com/ThatOpen/engine_components)
9. [npm: @thatopen/fragments（Fragments 格式官方描述）](https://www.npmjs.com/package/@thatopen/fragments)
10. [BIM Tools Hub — That Open Components（MIT 授权、功能定位）](https://bimtoolshub.com/that-open-components)
11. [GitHub API — ThatOpen/ifcjs-crash-course（123★、58 fork、2023-04 停更、目录结构）](https://github.com/ThatOpen/ifcjs-crash-course)
12. [YouTube — BIMvoice《IFC.js Crash Course》播放列表](https://www.youtube.com/playlist?list=PLUIgjxgKOw-o1hwrA5A01o2V0r-4pTX6S)
13. [Open Collective — IFC.js Crash Course（项目已归档）](https://opencollective.com/ifcjs-crash-course)
14. [GitHub API — myoualid/ifc-101-course（110★、IFC + BlenderBIM 视频系列）](https://github.com/myoualid/ifc-101-course)
15. [That Open University — Master BIM Software Developer（6 模块课程体系）](https://thatopen.com/university/master-bim/)
16. [ThatOpen/engine_templates README（create-bim-app 脚手架用法）](https://github.com/ThatOpen/engine_templates)
17. [ThatOpen/engine_docs 仓库目录树（各组件教程页面清单）](https://github.com/ThatOpen/engine_docs)
18. [npm — web-ifc-three（Three.js 官方 IFCLoader 的历史定位）](https://www.npmjs.com/~ansoni)
19. [Dezign Ark — Antonio González Viegas（That Open Company 负责人）公开演讲报道](https://dezignark.com/blog/el-futuro-del-openbim-y-la-ia/)
20. [Ecosyste.ms — ifcjs-crash-course 的 fork 与依赖记录](https://repos.ecosyste.ms/hosts/GitHub/repositories/ehtick/ifcjs-crash-course)
21. [官方教程 — Worlds（第一个 3D 世界，实测可访问，含完整源码链接）](https://docs.thatopen.com/Tutorials/Components/Core/Worlds)
22. [官方教程 — IfcLoader（IFC→Fragments 转换工作流，实测可访问）](https://docs.thatopen.com/Tutorials/Components/Core/IfcLoader)
23. [官方教程目录 — Tutorials/Components（全部 32 篇组件教程入口）](https://docs.thatopen.com/Tutorials/Components/)
