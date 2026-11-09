<div class="blog-hero blog-hero--compact llm-hero">
  <p class="eyebrow">COMPUTER GRAPHICS / RENDERING PIPELINE</p>
  <h1>计算机<em>图形学</em></h1>
  <p class="hero-title">三维世界如何变成一张图。</p>
  <p class="hero-copy">
    先读开篇，划清 BIM 与图形学的边界；再沿渲染管线理解变换、光栅化、几何、着色与可见性。用对照实验区分"看起来变了"与"计算变了"。
  </p>
</div>

<section class="home-section" style="margin-top: 0;">
  <div class="section-kicker">01 · START HERE</div>
  <div class="section-heading">
    <h2>先读开篇</h2>
    <p>BIM 不等于 CAD + 仿真，数字孪生也不是 BIM 的升级版。</p>
  </div>
  <div class="doc-grid">
    <a class="doc-item" href="#/knowledge/computer-graphics/01-BIMer需要的图形学">
      <span class="doc-num">01</span>
      <h4>BIMer需要的图形学</h4>
      <p>先划清 CAD、仿真、数字孪生与图形学各管哪一段，再反推该重点学什么</p>
    </a>
  </div>
</section>

<section class="home-section">
  <div class="section-kicker">02 · RENDERING PIPELINE</div>
  <div class="section-heading">
    <h2>渲染管线</h2>
    <p>按 02 → 03 → 04 → 05 → 06 推进：变换、光栅化、几何、着色、可见性。</p>
  </div>
  <div class="doc-grid">
    <a class="doc-item" href="#/knowledge/computer-graphics/02-变换与投影">
      <span class="doc-num">02</span>
      <h4>变换与投影</h4>
      <p>模型、观察与投影矩阵；从裁剪空间到屏幕坐标的完整链路</p>
    </a>
    <a class="doc-item" href="#/knowledge/computer-graphics/03-光栅化与抗锯齿">
      <span class="doc-num">03</span>
      <h4>光栅化与抗锯齿</h4>
      <p>三角形覆盖、重心坐标、深度缓冲；锯齿为什么是采样问题</p>
    </a>
    <a class="doc-item" href="#/knowledge/computer-graphics/04-几何表示与曲面">
      <span class="doc-num">04</span>
      <h4>几何表示与曲面</h4>
      <p>隐式与显式表示、三角网格、Bézier 曲线、细分与简化</p>
    </a>
    <a class="doc-item" href="#/knowledge/computer-graphics/05-着色与纹理">
      <span class="doc-num">05</span>
      <h4>着色与纹理</h4>
      <p>局部光照、着色频率、UV 采样、Mipmap 与环境映射</p>
    </a>
    <a class="doc-item" href="#/knowledge/computer-graphics/06-可见性与阴影">
      <span class="doc-num">06</span>
      <h4>可见性与阴影</h4>
      <p>阴影映射的两次观察、分辨率与偏移伪影、软阴影与全局光照边界</p>
    </a>
  </div>
</section>

<section class="home-section">
  <div class="section-kicker">03 · HOW TO READ</div>
  <div class="section-heading">
    <h2>阅读方式</h2>
    <p>开篇定方向，其余五篇各自独立，按编号顺序读最省力。</p>
  </div>
  <div class="home-intro">
    <p>每篇聚焦管线中的一个阶段：先问这一阶段在解决什么问题，再看它引入哪些近似与代价。文末的对照实验用来验证理解——改动一个参数，预期哪一种现象会变、哪一种不会变。章节内容参考 GAMES101 的课程范围，正文为独立讲解，不是官方讲义；顺序按 BIM 场景的需要重新编排。</p>
  </div>
</section>
