# 开源 BIM 技术生态

**开源世界存在不少可以直接拿来研究甚至 Fork 的 BIM 浏览器，但没有一个项目像 Chromium 一样垄断整个技术栈。**

原因不在于 BIM 开源生态不成熟，恰恰相反——是因为 BIM 的技术边界太宽。它同时涉及：**标准、数据库、几何内核、三维引擎、运行时格式、大模型渲染、工程语义和协同平台。**

| 目标                              | 项目                                           |
| --------------------------------- | ---------------------------------------------- |
| 直接 Fork 一个完整 Web BIM Viewer | **xeokit-bim-viewer**                          |
| 研究现代 Web BIM 技术栈           | **That Open Components + Fragments + web-ifc** |
| 研究 IFC Kernel                   | **IfcOpenShell**                               |
| 研究 Model Server                 | **BIMserver**                                  |
| 研究经典 Server + Viewer          | **BIMserver + BIMsurfer**                      |
| Windows / .NET BIM                | **xBIM + XbimXplorer**                         |
| 研究 AEC 数据平台                 | **Speckle**                                    |
| 研究基础设施数字孪生              | **iTwin.js**                                   |
| 研究 BIM + GIS / 超大空间模型     | **CesiumJS + 3D Tiles**                        |

------

## 一、技术概览

### 1. BIM 浏览器≠ 3D Viewer

普通 Web 三维查看器的核心链路相对简单：

```text
3D文件
   ↓
Geometry / Material
   ↓
Scene Graph
   ↓
GPU Rendering
```

典型技术是：

```text
glTF / GLB
    ↓
Three.js
    ↓
WebGL / WebGPU
```

BIM 浏览器的问题复杂得多。对于一个 IFC 构件，三维几何只是信息的一部分：

```text
IfcElement
   │
   ├── GlobalId
   ├── Type
   ├── Name
   ├── Classification
   ├── PropertySet
   ├── Quantity
   │
   ├── Spatial Relationship
   ├── Type Relationship
   ├── System Relationship
   │
   └── Representation
            ↓
         Geometry
```

也就是说：**BIM 浏览器真正处理的是“工程对象”，而不是 Mesh。**Mesh 是工程对象的一种三维表达。这决定了 BIM 浏览器天然至少包含：

```text
标准解析
+
对象模型
+
几何计算
+
模型运行时
+
大模型渲染
+
工程交互
+
属性与关系查询
```

------

### 2. 开源全景图

目前可以把主流开源 BIM 技术放进下面这张地图。

```text
┌──────────────────────────────────────────────────────────────┐
│                       OpenBIM 标准层                         │
│                                                              │
│       IFC          IDS          BCF          bSDD            │
│                     buildingSMART                            │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    BIM / IFC Kernel 层                       │
│                                                              │
│         IfcOpenShell        web-ifc        xBIM              │
│                                                              │
│      IFC解析 / Schema / Geometry / Property / Relationship   │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    BIM Runtime / Format                      │
│                                                              │
│          Fragments           XKT / GLB 等                    │
│                                                              │
│    几何组织 / Metadata / Worker / Streaming / Spatial Index │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                       Viewer SDK 层                          │
│                                                              │
│       That Open Components          xeokit SDK               │
│                                                              │
│ Selection / Clipping / Measurement / Tree / Properties      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                        Viewer 产品层                         │
│                                                              │
│      xeokit-bim-viewer      BIMsurfer      XbimXplorer       │
│                                                              │
│               完整 UI + BIM 浏览交互                        │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                   BIM 数据与协同平台层                       │
│                                                              │
│                BIMserver          Speckle                    │
│                                                              │
│       Object / Query / Version / Project / Collaboration     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              Infrastructure / Digital Twin 层                │
│                                                              │
│           iTwin.js                CesiumJS / 3D Tiles        │
│                                                              │
│ BIM + GIS + Reality + PointCloud + IoT + Large Scale        │
└──────────────────────────────────────────────────────────────┘
```

不应该把不同层级的项目相互比较，例如 IfcOpenShell 是 IFC 内核和几何引擎；xeokit 是面向 AEC 大模型的 Viewer Engine，其实两者根本不是一个层次。

------

### 3. 主要技术路线

#### 浏览器原生 IFC

> **浏览器自己理解 IFC。**不需要预先把 IFC 转换成另外一种服务器格式。

典型路线：

```text
IFC
 ↓
WebAssembly
 ↓
IFC Objects / Geometry
 ↓
Three.js
 ↓
BIM Components
```

代表：`web-ifc + That Open Components`

优点：技术链短、部署简单、IFC 原生能力强。

问题：大 IFC 文件意味着浏览器要承担STEP 解析、IFC Schema 处理、几何求值、三角化、属性解析、内存组织，这些工作都比较重。`web-ifc` 通过 `C++ → WebAssembly` 来解决性能问题，并同时提供浏览器和 Node.js 使用方式。

------

#### 模型预处理 + 高性能 Runtime

> **IFC 负责交换，Fragments 负责运行。**IFC 是交换格式，不应该直接作为浏览器运行格式。

典型路线：

```text
IFC
 ↓
Offline / Server Conversion
 ↓
Optimized Runtime Format
 ↓
Web Viewer
```

代表：`xeokit`、`That Open Fragments`。

例如 That Open 已经把 Fragments 独立成一个 BIM visualization / persistence layer，其当前设计包括：`.frag + FlatBuffers + Worker + Model Data + Streaming + Rendering Runtime`。官方说明中，Fragments 的 Worker 持有模型数据，再向主线程流送需要渲染的数据。2026 年发布的 3.4.0 又加入了 CRS、IFC splitter、extractor、LOD highlight 等能力。

------

#### Model Server + Thin Viewer

> BIM 根本不应该以“文件”为系统中心。

典型路线：

```text
IFC
 ↓
Object Database
 ↓
Query / Filter / Merge / Version
 ↓
Viewer
```

代表：`BIMserver + BIMsurfer`

BIMserver 官方明确强调自己**不是 file server**，而采用 model-driven architecture，将 IFC 保存为对象，因此可以查询、合并、过滤、版本管理，再动态生成 IFC。

------

#### AEC Data Platform / Digital Twin

扩大系统边界：

```text
BIM
+
其他工程模型
+
GIS
+
Reality
+
IoT
+
Version
+
Collaboration
```

代表：`Speckle`、`iTwin.js`、`Cesium / 3D Tiles`

Speckle 的 Server 仓库已经同时包含：Server、Frontend、3D Viewer、Object Loader、Preview Service、Webhook Service。其 Viewer 只是整个 AEC Data Hub 的一个组件。

iTwin.js 则直接定位为：创建、查询、修改和显示 Infrastructure Digital Twins 的开源库，并明确支持聚合 Engineering Models、Reality Data、GIS 和 IoT。

------

### 4. BIM 浏览器难点

#### IFC ≠ Browser Runtime

> OpenBIM 标准解决的是交换问题，而 BIM Viewer 还需要解决运行问题。

IFC 为长期、厂商中立的数据交换设计，非常丰富且复杂。

```text
IfcProduct
IfcTypeObject
IfcPropertySet
IfcRelDefinesByType
IfcRelContainedInSpatialStructure
IfcRepresentation
IfcMappedItem
IfcBooleanClippingResult
...
```

浏览器真正需要的却是：`GPU-friendly Geometry + Spatial Index + Object ID + Runtime Properties`，因此几乎所有高性能系统最后都会增加自己的 Runtime Layer。于是出现：

```text
xeokit        → XKT / optimized models
That Open     → Fragments
Speckle       → Speckle Objects
Bentley       → iModel
Cesium        → 3D Tiles
```

------

#### BIM 语义空间复杂

网页的 `<button>` 基本到处都是 `<button>`，而 BIM 里的对象高度领域化。

建筑：Wall、Door、Slab、Space

铁路：Alignment、Track、Signal

道路：Road、Pavement、Alignment

工业设施：Equipment、Pipe、Valve、System

因此很难定义一个所有行业都满意的统一 Runtime Object Model。

------

#### 几何本身不统一

普通 Web Viewer 通常处理三角网格，IFC 却可能包含：

```text
SweptSolid
BRep
CSG
MappedRepresentation
Boolean
TriangulatedFaceSet
Curve
Surface
```

于是 BIM Viewer 前面往往必须存在真正的：**Geometry Kernel**。这也是 IfcOpenShell 和 xBIM 这种项目存在的重要原因，IfcOpenShell 既负责 IFC parsing，也拥有 IFC geometry engine；目前对 IFC2x3、IFC4 以及 IFC4.3 等 Schema 提供解析支持。

------

#### 项目规模增长

一个几十 MB 的模型和数 GB 工程模型是两种完全不同的问题。真正进入工程应用之后，很快会遇到：

```text
几十万构件
数百万 Mesh
重复设备
大量 Property
大地坐标
多模型联合
点云
动态加载
```

所以 BIM Viewer 的竞争重点不仅仅是打开 `.ifc` 或者 `.gim` 文件，而是**谁能把几十万甚至更多工程对象流畅地组织起来？**这也是 Fragments、XKT、3D Tiles 等运行格式不断出现的主要原因。

------

#### 功能边界扩张

从三位模型展示，到多参建方协作，到GIS、物联网、VR、仿真等，BIM与数字孪生的技术边界越来越模糊。因此这个市场最终自然分裂成：

```text
IFC Kernel
BIM Viewer SDK
Model Server
AEC Platform
Digital Twin Platform
```

而不是收敛成一个单体应用。

------

## 二、技术路线发展

从开源项目演进历史看，BIM Viewer 可以大致划分成五个阶段。

------

### Desktop IFC Kernel

早期最核心的问题是

> **IFC 究竟应该怎样被软件理解？**

代表项目：

```text
IfcOpenShell
xBIM
BIMserver
```

核心工作包括：

```text
STEP Parser
EXPRESS Schema
Entity
Relationship
Property
Geometry Kernel
```

------

### IFC → Mesh → Web Viewer

WebGL 和 Three.js 成熟后，问题变成：

> 怎样把 IFC 显示在浏览器？

典型链路：

```text
IFC
 ↓
Parser
 ↓
Triangles
 ↓
Three.js Mesh
 ↓
WebGL
```

代表项目：

```text
IFC.js
web-ifc-three
web-ifc-viewer
```

这一时期最大的突破是：**BIM 第一次可以不依赖重型桌面 CAD/BIM 软件，在浏览器里运行。**

但问题也逐渐暴露出来，Mesh ≠ BIM Object，如果只是把 IFC 转成 Three.js Mesh，最终很容易出现`mesh.userData.properties`大量工程语义被挂在渲染对象上。对于小Demo 没问题，对大型工程软件却很难长期维护。旧的 `web-ifc-viewer` 和 `web-ifc-three` 目前已经被官方标记为 deprecated，That Open 推荐转向 Components。

------

### 浏览器原生 BIM Component

随后出现一个明显变化：Viewer 不再作为一个完整黑盒，而开始组件化。技术思想从"Use this Viewer"转向"Build your BIM Application"。

代表项目：

```text
That Open Components
```

它提供的不是一个固定 Viewer，而是：

```text
World
Camera
Renderer
Highlighter
Raycaster
Classifier
Clipping
Measurement
Property Viewer
...
```

每一个能力都是 Component。官方目前将其定义为基于 Three.js 的 BIM 工具集合，用于创建 Browser-based 3D BIM applications；核心包和前端包也被明确分开。

------

### IFC 与 Runtime 分离

大型工程模型存在很明细的性能问题，大家逐渐意识到**IFC 不适合作为最终运行时。**

典型链路变为：

```text
IFC
     ↓
Preprocessing
     ↓
Runtime Format
     ↓
Viewer
```

这时候出现的核心技术不再只是 Renderer，而是：

```text
Binary Format
Worker
LOD
Batching
Instancing
Spatial Index
Streaming
Metadata
```

That Open 的 Fragments 就是一个典型例子。其内部现在直接包含：`BIM persistence + BIM visualization + IFC importer + Worker runtime + query + edit`。

而 `IfcLoader` 本身只是：`web-ifc → Fragments`的桥接组件。

------

### Scene Graph 与 Data Graph 分离

> **BIM Viewer 正逐渐从“支持工程属性的 3D Engine”，演化成“带三维表达能力的 Engineering Data Runtime”。**

传统 3D Engine，Scene Graph承担一切：

```text
Node
 ├─ Mesh
 ├─ Transform
 └─ userData
```

新的 BIM Runtime 越来越强调：Data Graph ≠ Scene Graph，而是：

```text
Engineering Object
    │
    ├── Type
    ├── Property
    ├── Relationship
    │
    └── Representation
             │
             ▼
         Scene Object
```

Speckle、BIMserver、iTwin 都可以看成这一趋势向更大系统边界的继续发展。

------

## 三、核心项目介绍

### 1. IfcOpenShell

IfcOpenShell 是 OpenBIM 世界最重要的基础设施之一，提供**BIM 世界的基础数据库内核 + Geometry Kernel**， LGPL 开源。

当前项目包括：

- C++ IFC library；
- Python API；
- IfcConvert；
- geometry engine；
- Bonsai；
- IDS tooling；
- BCF tooling；
- IFC query / patch 等大量工具。

最值得研究的是两件事：

**第一，IFC Schema 如何映射成程序对象。**

**第二，复杂 IFC Representation 如何变成真正可渲染几何。**

------

### 2. web-ifc

web-ifc 提供 Browser IFC Kernel ，是现代 Web OpenBIM 技术栈非常重要的一块地基，MPL-2.0许可。

如果说 IfcOpenShell 是传统原生 IFC Engine，那么 web-ifc 最大的创新就是：`C++  → WebAssembly  → Browser`，它让 JavaScript 可以直接操作 ifc 文件。

```text
Open IFC
Read Entity
Read Property
Generate Geometry
Write IFC
```

官方同时提供：

- Browser WASM；
- multithread WASM；
- Node WASM；
- TypeScript definitions。

------

### 3. That Open Components + Fragments

That Open 最大特点不是“有一个很好看的 Viewer”，而是形成完整的 Web BIM SDK + Runtime 技术栈，采用 MIT 许可。官方将其定义为用于高效保存、显示、导航和编辑大规模 BIM 数据的开源库。

```text
             web-ifc
                │
                ▼
            IFC Loader
                │
                ▼
            Fragments
                │
                ▼
      That Open Components
                │
                ▼
             Three.js
```

Components负责：

```text
Scene
Camera
Renderer
Selection
Highlight
Clipping
Measurement
Classification
Properties
Floorplan
...
```

Fragments负责：

```text
BIM Runtime
+
Binary Format
+
Model Persistence
+
Worker
+
Streaming
```

------

### 4. xeokit SDK + xeokit-bim-viewer

官方定义：open source 2D/3D BIM viewer that runs in the browser，采用AGPL-3.0许可。

典型链路：

```text
Fork repository
 ↓
Convert IFC
 ↓
放入 data
 ↓
Serve
```

核心功能：

```text
Project
Model
Object
Tree
Storey
IFC Type
Property
BCF Viewpoint
Viewer State
```

------

### 5. BIMserver + BIMsurfer

BIMserver 最大的思想不是 Viewer，而是**IFC Database。**

```text
IFC
 ↓
BIMserver
 ↓
BIMsurfer
```

BIMserver将 IFC 保存为对象，而不是文件，可以：

```text
Query
Merge
Filter
Version
Project
Model Checking
```

BIMsurfer 则负责 WebGL Viewer。目前 BIMsurfer v3 已经完全重写为 WebGL2，并引入 3D Tiles、section plane、measurement 等方向，但官方仍明确标记v3 beta，尚无正式 release。 

------

### 6. xBIM + XbimXplorer

这是 `.NET / C#` 世界非常完整的一条 BIM 技术路线。整个 xBIM 生态到 2026 年仍然非常活跃，包括 Geometry、WindowsUI、IDS Validator 等项目都仍有更新。许可证采用 CDDL，官方特别说明可以用于 Larger Work，包括闭源商业软件，但修改覆盖文件仍需遵循许可证义务。

```text
XbimEssentials
       │
XbimGeometry
       │
XbimWindowsUI
       │
XbimXplorer
```

XbimEssentials 可以：

- read IFC；
- write IFC；
- validate；
- query；
- 处理 IFC2x3 / IFC4。

XbimXplorer 则是一个完整 WPF BIM Viewer，可以展示三维 IFC 和 semantic data。

------

### 7. Speckle

Speckle 从 BIM Viewer走向 AEC Data Platform，其主仓库直接包含 Server、Frontend、Viewer、ObjectLoader、Preview Service 等，**把工程数据从 File Exchange 转向 Object Exchange。**

其架构更像：

```text
AEC Applications
       ↓
Connectors
       ↓
Speckle Objects
       ↓
Server
       ↓
Version / Project / API
       ↓
Web Viewer
```

------

### 8. iTwin.js：

iTwin.js 进一步迈向数字孪生基础设施（Infrastructure Digital Twin），核心代码采用 MIT License。技术完整度很高，但学习成本也明显更高，因为必须理解 Bentley 自己的 iModel/BIS 数据体系。

```text
Engineering Models
Reality Data
GIS
IoT
```

------

### 9. CesiumJS + 3D Tiles

CesiumJS 是**3D Geospatial Engine。**真正和 BIM 技术产生交集的是 3D Tiles，很多大型数字孪生项目最终都会同时出现 BIM Engine 和 Cesium。

```
建筑内部 → BIM

城市/线路/区域 → GIS / 3D Tiles
```

3D Tiles 明确面向：

- Photogrammetry；
- BIM/CAD；
- 3D Building；
- Instanced Feature；
- Point Cloud；

并设计了空间层级、流式加载、LOD 和 Feature Metadata。([GitHub](https://github.com/CesiumGS/3d-tiles?utm_source=chatgpt.com))

------

## 四、总结

**BIM 浏览器不是“支持 IFC 的 Three.js Viewer”，而是一套将工程信息模型转换为可实时运行、可查询、可交互三维工程对象的 Runtime System。**

```text
                    BIM Browser
                         │
        ┌────────────────┼────────────────┐
        │                │                │
      Data             Runtime         Interaction
        │                │                │
        ▼                ▼                ▼
 IFC Parser        Binary Format       Picking
 Geometry Kernel   Streaming           Section
 Semantic Model    LOD                 Measure
 Relationship      Spatial Index       Tree
 Property          Worker              Property
 Classification    GPU Optimization    BCF
        │                │                │
        └────────────────┼────────────────┘
                         │
                    3D Rendering
```

