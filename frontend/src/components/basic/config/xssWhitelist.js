/**
 * Markdown 编辑器/查看器共享的 XSS 白名单配置
 * 遵循 SOLID 原则：单一职责，集中管理安全配置
 * 
 * 包含：SVG 元素、KaTeX 数学公式元素、foreignObject 内部 HTML 元素
 */

// SVG 相关白名单
const svgWhitelist = {
  // SVG 基础元素
  svg: ['width', 'height', 'viewBox', 'xmlns', 'class', 'style', 'xmlns:xlink', 'content'],
  g: ['class', 'transform', 'id', 'style'],
  
  // SVG 形状元素
  line: ['x1', 'y1', 'x2', 'y2', 'stroke', 'stroke-width', 'class', 'style'],
  circle: ['cx', 'cy', 'r', 'stroke', 'stroke-width', 'fill', 'class', 'style'],
  ellipse: ['cx', 'cy', 'rx', 'ry', 'stroke', 'stroke-width', 'fill', 'class', 'style'],
  rect: ['x', 'y', 'width', 'height', 'rx', 'ry', 'fill', 'stroke', 'stroke-width', 'class', 'style'],
  path: ['d', 'fill', 'stroke', 'stroke-width', 'class', 'style'],
  polygon: ['points', 'fill', 'stroke', 'stroke-width', 'class', 'style'],
  polyline: ['points', 'fill', 'stroke', 'stroke-width', 'class', 'style'],
  
  // SVG 文本元素
  text: ['x', 'y', 'dx', 'dy', 'text-anchor', 'font-size', 'font-family', 'font-weight', 'fill', 'class', 'style'],
  tspan: ['x', 'y', 'dx', 'dy', 'class', 'style'],
  textPath: ['href', 'xlink:href', 'class', 'style'],
  
  // SVG 容器和引用元素
  defs: [],
  use: ['href', 'xlink:href', 'x', 'y', 'width', 'height', 'class'],
  symbol: ['id', 'viewBox', 'class'],
  switch: ['class', 'style'],
  
  // SVG 图片元素
  image: ['x', 'y', 'width', 'height', 'href', 'xlink:href', 'class', 'style', 'preserveAspectRatio'],
  
  // SVG 裁剪和遮罩
  clipPath: ['id', 'class'],
  mask: ['id', 'x', 'y', 'width', 'height', 'class'],
  
  // SVG 渐变
  linearGradient: ['id', 'x1', 'y1', 'x2', 'y2', 'gradientUnits', 'class'],
  radialGradient: ['id', 'cx', 'cy', 'r', 'fx', 'fy', 'gradientUnits', 'class'],
  stop: ['offset', 'stop-color', 'stop-opacity', 'class', 'style'],
  
  // SVG 滤镜（基础支持）
  filter: ['id', 'x', 'y', 'width', 'height', 'class'],
  feGaussianBlur: ['in', 'stdDeviation'],
  feOffset: ['dx', 'dy'],
  feBlend: ['mode', 'in', 'in2'],
  
  // SVG 其他元素
  a: ['href', 'xlink:href', 'target', 'class'],
  title: [],
  desc: [],
  metadata: [],
  marker: ['id', 'viewBox', 'refX', 'refY', 'markerWidth', 'markerHeight', 'orient', 'class'],
  pattern: ['id', 'x', 'y', 'width', 'height', 'patternUnits', 'patternTransform', 'class'],
}


// KaTeX 数学公式元素白名单（仅 Editor 需要）
const katexWhitelist = {
  annotation: ['encoding'],
  math: ['xmlns'],
  menclose: ['notation'],
  merror: [],
  mfrac: ['linethickness'],
  mi: ['mathvariant'],
  mmultiscripts: [],
  mn: [],
  mo: ['fence', 'separator', 'stretchy', 'symmetric', 'largeop', 'movablelimits'],
  mover: [],
  mpadded: [],
  mphantom: [],
  mprescripts: [],
  mroot: [],
  mrow: [],
  ms: [],
  mspace: ['width', 'height', 'depth'],
  msqrt: [],
  mstyle: ['scriptlevel', 'displaystyle'],
  msub: [],
  msubsup: [],
  msup: [],
  mtable: ['columnalign', 'rowspacing', 'columnspacing'],
  mtd: ['columnalign'],
  mtext: [],
  mtr: [],
  munder: [],
  munderover: [],
  semantics: [],
}

// foreignObject 内部 HTML 元素白名单
const htmlWhitelist = {
  foreignObject: ['x', 'y', 'width', 'height', 'class'],
  div: ['xmlns', 'class', 'style'],
  span: ['class', 'style', 'aria-hidden'],
  p: ['class', 'style'],
  strong: ['class', 'style'],
  em: ['class', 'style'],
  b: ['class', 'style'],
  i: ['class', 'style'],
  br: [],
  table: ['class', 'style'],
  tr: ['class', 'style'],
  td: ['class', 'style', 'colspan', 'rowspan'],
  th: ['class', 'style', 'colspan', 'rowspan'],
  img: ['src', 'alt', 'title', 'width', 'height', 'class', 'style'],
}

/**
 * 获取 Viewer 组件的 XSS 白名单（不含 KaTeX）
 */
export const getViewerWhitelist = () => ({
  ...svgWhitelist,
  ...htmlWhitelist,
})

/**
 * 获取 Editor 组件的 XSS 白名单（含 KaTeX）
 */
export const getEditorWhitelist = () => ({
  ...katexWhitelist,
  ...svgWhitelist,
  ...htmlWhitelist,
})

/**
 * 配置 markdown-it 的 SVG 代码块渲染
 * @param {Object} md - markdown-it 实例
 */
export const configureSvgFence = (md) => {
  const defaultFenceRender = md.renderer.rules.fence
  md.renderer.rules.fence = (tokens, idx, options, env, self) => {
    const token = tokens[idx]
    const info = token.info.trim()
    
    // 如果是 svg 代码块，直接渲染 SVG 内容
    if (info === 'svg') {
      return `<div class="custom-svg-block">${token.content}</div>`
    }
    
    // 其他代码块使用默认渲染
    return defaultFenceRender(tokens, idx, options, env, self)
  }
}
