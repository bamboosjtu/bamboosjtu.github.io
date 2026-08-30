# 开源BIM技术生态





| 项目                                  | 主要用途                                                     | 适合关注原因                                                 |
| ------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| **IfcOpenShell / Bonsai**             | IFC 解析、转换、几何引擎、BIM 自动化、Blender 原生 IFC 建模  | OpenBIM 生态里非常核心的项目。IfcOpenShell 提供 C++/Python API、IfcConvert、BCF、IDS、Bonsai 等工具；Bonsai 是基于 Blender 的原生 IFC BIM 创作平台。([GitHub](https://github.com/IfcOpenShell/IfcOpenShell?utm_source=chatgpt.com)) |
| **ThatOpen / web-ifc / components**   | Web 端读取、写入、可视化 IFC；构建浏览器 BIM 应用            | JavaScript / Three.js 方向最值得看的 IFC 工具链之一。`web-ifc` 面向高速读写 IFC，`components` 提供尺寸、楼层导航、DXF 导出等浏览器 BIM 应用组件。([GitHub](https://github.com/ThatOpen/engine_web-ifc?utm_source=chatgpt.com)) |
| **xeokit-sdk**                        | Web 端高性能 BIM / IFC / 工程模型查看器                      | 适合做“轻量化 BIM 平台”“网页模型浏览器”“数字孪生前端”。其定位是浏览器中查看高细节、高精度 3D 工程和 BIM 模型。([GitHub](https://github.com/xeokit/xeokit-sdk?utm_source=chatgpt.com)) |
| **BIMserver**                         | BIM 模型服务器、IFC 数据管理、协同平台后端                   | 经典 OpenBIM 后端项目，可存储和管理建筑项目 BIM 信息，数据基于 IFC 开放标准。([GitHub](https://github.com/opensourceBIM/BIMserver?utm_source=chatgpt.com)) |
| **BIMsurfer**                         | WebGL BIM / IFC 模型查看器                                   | 属于 opensourceBIM 生态，常与 BIMserver 搭配，用于网页端 IFC 可视化。opensourceBIM 组织还维护多个 BIMserver 插件和相关工具。([GitHub](https://github.com/opensourceBIM?utm_source=chatgpt.com)) |
| **xBIM Toolkit / XbimEssentials**     | .NET / C# 处理 IFC、COBie、几何和可视化                      | 如果你做的是 C#、.NET、Windows 企业应用，xBIM 比 JavaScript 生态更合适。官方定位是支持 buildingSMART IFC 数据模型的开源 BIM 开发工具包。([GitHub](https://github.com/xBimTeam?utm_source=chatgpt.com)) |
| **Speckle / speckle-server**          | AEC 数据协同、版本化、连接 Revit/Rhino/Grasshopper/Blender 等工具 | 更偏“建筑工程数据协同平台”，不是单纯 IFC 解析器。适合研究 BIM 数据平台、模型版本管理、跨软件数据流转。([GitHub](https://github.com/specklesystems?utm_source=chatgpt.com)) |
| **FreeCAD BIM Workbench / NativeIFC** | 开源参数化建模、BIM 工作流、IFC 导入导出                     | 适合学习“开源 Revit/ArchiCAD 替代路径”。FreeCAD BIM Workbench 提供墙、梁、屋顶、窗、楼梯、管道等参数化 BIM 对象，并支持 IFC。([GitHub](https://github.com/yorikvanhavre/BIM_Workbench?utm_source=chatgpt.com)) |
| **Ladybug Tools / Honeybee**          | 建筑性能分析、日照、能耗、Radiance、EnergyPlus、OpenStudio   | 严格说它不是 BIM 核心库，但在建筑设计与 BIM 工作流中很常见，适合做绿色建筑、能耗分析、设计性能评估。([GitHub](https://github.com/ladybug-tools/honeybee-energy?utm_source=chatgpt.com)) |
| **Cloud2BIM**                         | 点云转 IFC / Scan-to-BIM                                     | 新一些的研究型项目，面向激光扫描/点云自动生成 IFC 模型。论文称其支持墙、板、洞口、房间分区等自动化流程。([arXiv](https://arxiv.org/abs/2503.11498?utm_source=chatgpt.com)) |
| **MCP4IFC / IfcLLM 等 AI+BIM 项目**   | 用大模型查询、生成、修改 IFC/BIM 模型                        | 这是近两年快速出现的方向，适合研究“AI 助手 + BIM 模型操作”。MCP4IFC 提供基于 MCP 的 IFC 查询和编辑工具；IfcLLM 研究自然语言查询 IFC 模型。([arXiv](https://arxiv.org/abs/2511.05533?utm_source=chatgpt.com)) |

| 项目                                        | 定位                                      | 适合场景                                        | 评价                                                         |
| ------------------------------------------- | ----------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------ |
| **That Open Engine / That Open Components** | 基于 Three.js 的 Web BIM 开发组件库       | 自研 BIM 浏览器、IFC 查看器、模型审查工具       | 当前比较活跃，组件化程度高。官方说明它提供浏览器端 BIM 应用能力，如尺寸、楼层平面导航、DXF 导出、后处理等；其文档也说明相关库可用于快速创建 3D BIM 软件。([GitHub](https://github.com/ThatOpen/engine_components?utm_source=chatgpt.com)) |
| **web-ifc**                                 | IFC 解析/读写核心库，WebAssembly 加速     | 浏览器端解析 IFC、查询 IFC 属性、生成几何       | 它本身不是完整浏览器 UI，而是 IFC 底层引擎。官方描述为 JavaScript 库，可高速读取和写入 IFC 文件，是 That Open 生态的一部分。([GitHub](https://github.com/ThatOpen/engine_web-ifc?utm_source=chatgpt.com)) |
| **xeokit SDK**                              | 高性能 Web BIM / AEC 可视化 SDK           | 大模型查看器、工程模型平台、IFC/点云/CAD 可视化 | 偏专业工程可视化。支持浏览器端 BIM Viewer 开发，常用 XKT 轻量化格式，也可加载 glTF、CityJSON、LAZ、OBJ 等格式。需要注意许可证：xeokit SDK 是 AGPLv3，闭源商用一般要看商业授权。([GitHub](https://github.com/xeokit/xeokit-sdk?utm_source=chatgpt.com)) |
| **xeokit-bim-viewer**                       | 基于 xeokit SDK 的现成 2D/3D BIM Viewer   | 快速搭一个浏览器 BIM 查看器                     | 比 xeokit SDK 更偏“开箱即用”。官方说明它是开源 2D/3D BIM Viewer，可在浏览器中加载本地模型文件，并已集成于 OpenProject BIM。([Xeokit](https://xeokit.github.io/xeokit-bim-viewer/?utm_source=chatgpt.com)) |
| **Speckle Viewer**                          | Speckle 生态里的 Web 3D 模型查看器        | AEC 数据协同、模型流转、跨软件数据平台          | 更偏“BIM 数据协作平台 + Viewer”，不是纯 IFC 浏览器。官方文档称 Speckle Viewer 是开源 3D 模型查看器，可在 Web 浏览器中渲染大型模型；`@speckle/viewer` 可作为 npm 包嵌入 Web 应用。([Speckle Docs](https://docs.speckle.systems/developers/viewer/introduction?utm_source=chatgpt.com)) |
| **BIMsurfer**                               | WebGL IFC Viewer，常与 BIMserver 生态配合 | OpenBIM 后端 + Web 查看器研究                   | 老牌开源 BIM Web Viewer。当前 v3 版本是 WebGL 2.0，面向高性能，并引入 3D Tiles；但官方也说明 v3 尚无正式 release，生产使用要谨慎评估。([GitHub](https://github.com/opensourceBIM/BIMsurfer?utm_source=chatgpt.com)) |
| **iTwin.js**                                | 基础设施数字孪生 Web 开发框架             | 桥梁、道路、轨道、市政、工业设施数字孪生        | Bentley 生态相关，但核心是开源的。官方称 iTwin.js 是开源项目，并用于构建 iTwin 应用；iTwin Viewer 可在浏览器中查看和交互 iModels。([iTwin.js](https://www.itwinjs.org/?utm_source=chatgpt.com)) |
| **CesiumJS**                                | WebGIS / 3D Tiles 大场景引擎              | BIM + GIS、城市级数字孪生、园区/线路/电网场景   | 不是纯 BIM 引擎，但适合 BIM/GIS 融合。CesiumJS 是开源 JavaScript 库，支持 WebGL、3D Tiles 和大规模地理空间数据；3D Tiles 规范本身也覆盖 BIM/CAD、3D 建筑、点云等内容。([GitHub](https://github.com/CesiumGS/cesium?utm_source=chatgpt.com)) |

## OpenBIM



**OpenBIM 不是一个单一开源组织，也不是某个软件框架。**

更准确地说，**OpenBIM 是一种基于开放标准的 BIM 协作理念、方法体系和工作流**。它强调不同软件、不同参与方之间，能够通过开放、中立、非专有的数据标准交换 BIM 信息，而不是被某一家软件厂商的私有格式绑定。

官方定义里，buildingSMART 认为 openBIM 的核心是 **vendor neutral collaborative process**，也就是“厂商中立的协作流程”。它的目标是提升建筑资产行业中数字数据的可访问性、可用性、管理能力和可持续性。([buildingSMART International](https://www.buildingsmart.org/about/openbim-old/openbim-definition/?utm_source=chatgpt.com))

可以这样理解：

| 概念                            | 它是什么                                       | 类比                                  |
| ------------------------------- | ---------------------------------------------- | ------------------------------------- |
| **OpenBIM**                     | 开放 BIM 协作理念 / 标准体系 / 工作流          | 类似“Web 开放标准生态”                |
| **buildingSMART**               | 推动 OpenBIM 标准的国际组织                    | 类似 W3C 之于 Web 标准                |
| **IFC**                         | OpenBIM 最核心的数据交换标准                   | 类似 HTML / JSON / XML 的行业数据格式 |
| **BCF**                         | BIM 问题沟通、批注、协同标准                   | 类似 issue / comment / markup         |
| **IDS**                         | 信息交付要求标准，用于定义模型必须包含什么信息 | 类似可机器读取的交付检查规则          |
| **IfcOpenShell、xBIM、web-ifc** | 基于 OpenBIM / IFC 的开源软件库或工具          | 类似实现标准的开源 SDK                |

所以，**OpenBIM 和开源不是一回事**。

OpenBIM 里的 “open” 主要指：

1. **开放标准**：比如 IFC、BCF、IDS、bSDD 等；
2. **厂商中立**：Revit、Tekla、Archicad、Bentley、FreeCAD、Blender Bonsai 等理论上都可以通过 IFC/BCF 等标准协作；
3. **数据可交换**：模型信息不应该只锁死在某个软件的私有格式里；
4. **流程可验证**：通过 IDS、MVD、IDM 等方式定义交付要求、检查模型质量。

但 OpenBIM **不等于所有软件都必须开源**。Autodesk Revit、Graphisoft Archicad、Tekla、Bentley 等商业软件也可以支持 OpenBIM，只要它们支持相关开放标准。buildingSMART 中国也把 IFC、BCF、IDM、MVD、IDS、bSDD 等归为共同构成 openBIM 方法体系的核心标准。([buildingSMART China](https://19650.org/standards?utm_source=chatgpt.com))

更具体一点：

**buildingSMART 是组织。**
它是推动 OpenBIM 标准的主要国际组织，维护或推动 IFC、BCF、IDS、bSDD 等标准。OpenBIM KnowledgeBase 也把 buildingSMART 称为 openBIM 的“home”，即主要推动方。([openbim-knowledgebase.org](https://openbim-knowledgebase.org/en/docs/bimcert-manual-2024/chapter-1-introduction-openbim-and-buildingsmart/chapter-1-1-buildingsmart-as-the-home-of-openbim/?utm_source=chatgpt.com))

**IFC 是标准 / 数据模型。**
IFC，全称 Industry Foundation Classes，是 BIM 模型在不同软件之间交换信息的开放标准。你可以把它理解成 BIM 领域最重要的开放数据格式。

**IfcOpenShell、xBIM、web-ifc 是框架 / SDK / 工具库。**
它们不是 OpenBIM 本身，而是实现或使用 OpenBIM 标准的技术项目。

一句话总结：

> **OpenBIM 是“开放标准驱动的 BIM 协作体系”；buildingSMART 是主要推动这个体系的组织；IFC/BCF/IDS 是这个体系里的标准；IfcOpenShell、xBIM、web-ifc 等是实现这些标准的开源工具。**

如果你是做工程建设 + 企业数字化转型，理解 OpenBIM 的重点不是“它是不是开源”，而是：**它能不能让模型数据从设计、施工、运维系统中解耦出来，变成企业可长期管理、可集成、可审计的数据资产。**







## 附录：系统架构

游戏引擎适合做 BIM/GIM 的交互式可视化、培训仿真、漫游展示和轻量数字孪生前端；IFC/GIM 解析、模型轻量化、属性管理、版本管理和协同审查，应交给外部 BIM 工具链或后端模型服务。

### BIM 浏览器

```
BIM / GIM / IFC / Revit 模型
        ↓
模型转换与轻量化
        ↓
几何数据 + 构件属性 + 层级结构
        ↓
Web / 桌面 BIM 浏览器
        ↓
属性查询、剖切、测量、协同、运维、进度、审查
```

### 游戏引擎

```
3D 资产 / 场景 / 角色 / 动画
        ↓
材质、光照、物理、脚本、交互逻辑
        ↓
实时渲染引擎
        ↓
沉浸式体验、仿真、训练、展示、交互应用
```

游戏引擎适合做**高表现力的 BIM 应用外壳**，但不是开箱即用的 BIM 数据平台。

1. **模型轻量化**
    BIM 模型原始数据通常很重，不能直接全部塞进游戏引擎。
2. **构件 ID 保留**
    转成 FBX/glTF 后，很多 BIM 构件属性容易丢失。
3. **属性数据库关联**
    需要把构件几何和属性表、设备台账、文档、传感器数据关联起来。
4. **专业层级维护**
    比如项目、单体、楼层、系统、专业、构件分类。
5. **工程坐标处理**
    BIM/GIM 常用大地坐标或工程坐标，游戏引擎更习惯局部坐标。
6. **模型增量更新**
    设计模型变更后，如何只更新变更部分，而不是重新导入整个场景。
7. **审查与协同功能**
    比如剖切、测量、批注、碰撞、问题单、版本对比等。

