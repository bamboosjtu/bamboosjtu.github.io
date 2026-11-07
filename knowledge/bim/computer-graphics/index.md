# 计算机图形

从 Three.js 的对象和参数，回到它们要解决的图形学问题。

这一栏以 GAMES101 的原理为骨架，把 Three.js Journey 中遇到的概念放回渲染流程，再用立方体、球体与平面的简单实验检验理解。目标先是理解图像如何生成，再逐步提高画面质量。

## 先读这三篇

1. [Three.js 为什么这样拆：从 Geometry 到屏幕像素](knowledge/bim/computer-graphics/threejs-rendering-basics.md)：把 Scene、Mesh、Geometry、Material、Texture、Camera 和 Renderer 放进同一张职责图，解释有了纹理为什么还需要材质。
2. [材质课为什么又讲贴图：数据、规则与表面细节](knowledge/bim/computer-graphics/materials-and-textures.md)：区分颜色、法线、凹凸、位移、AO 与环境贴图，理解 UV、纹素和 mipmap，形成初学者的选择顺序。
3. [有光为什么还要阴影：从可见性到 Shadow Map](knowledge/bim/computer-graphics/light-and-shadow.md)：解释 shadow 为什么属于 light、物体如何参与阴影，以及透明平面模拟阴影与烘焙的区别。

## 这次学习的关键转折

容易卡住的地方，是同时在三个层级上记名字：图形学原理、Three.js 的接口、具体场景的需求。先问“这一层要解决什么问题”，再问“对应哪个类”，比从 API 列表开始更容易建立联系。

- **描述对象**：形状、表面属性、位置和组成关系。
- **生成图像**：变换、投影、光栅化、着色、可见性与采样。
- **观察结果**：形状、表面、遮挡关系，以及不同算法的画面与成本。

同一个形状可以有不同表面，同一种表面也可以应用到不同形状。把这些变化分开，才能看清每个概念的作用。

## 学习时如何使用

每学一个原理，都做一个只改变单一变量的小实验：保持形状不变换材质；保持材质不变关灯；保持相机不变关阴影；保持模型不变降低分辨率。先预测，再观察，最后解释差异。

课程只作为资料入口，不按课时建立目录。后续笔记继续按问题归档。

[返回 BIM 相关](knowledge/bim/index.md)
