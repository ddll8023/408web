/** 编辑预览、阅读和 PNG 复制共用的正文/选项排版语义。 */
export type MarkdownContentRole = 'body' | 'option'

/** Word/WPS 富文本复制中独立图片的默认显示高度，单位为厘米。 */
export const WORD_CLIPBOARD_IMAGE_HEIGHT_CM = 3

const CSS_PIXELS_PER_INCH = 96
const CENTIMETERS_PER_INCH = 2.54

/** 3 厘米按浏览器 96 DPI 换算出的 HTML 高度属性。 */
export const WORD_CLIPBOARD_IMAGE_HEIGHT_PX = Math.round(
  WORD_CLIPBOARD_IMAGE_HEIGHT_CM / CENTIMETERS_PER_INCH * CSS_PIXELS_PER_INCH,
)

export interface WordClipboardImageSize {
  widthCm: number
  heightCm: number
  widthPx: number
  heightPx: number
  ratio: number
}

/** 按原图比例计算 Word 图片尺寸，同时提供厘米和 HTML 像素属性，供 Word/WPS 锁定初始比例。 */
export const getWordClipboardImageSize = (ratio: number): WordClipboardImageSize | null => {
  if (!Number.isFinite(ratio) || ratio <= 0) return null

  const heightCm = WORD_CLIPBOARD_IMAGE_HEIGHT_CM
  const widthCm = Math.max(0.01, Number((heightCm * ratio).toFixed(2)))
  return {
    widthCm,
    heightCm,
    widthPx: Math.max(1, Math.round(widthCm / CENTIMETERS_PER_INCH * CSS_PIXELS_PER_INCH)),
    heightPx: WORD_CLIPBOARD_IMAGE_HEIGHT_PX,
    ratio,
  }
}

interface SvgViewport {
  width: number
  height: number
  viewBox: string
}

/** 只接受明确的正数像素尺寸；不把百分比或 em 猜成 SVG 用户坐标。 */
const pixelLength = (value: string | null): number | null => {
  if (!value || !/^\d+(?:\.\d+)?(?:px)?$/i.test(value.trim())) return null
  const number = Number.parseFloat(value)
  return Number.isFinite(number) && number > 0 ? number : null
}

/** 校验单图显示宽度，兼容 HTML width 和现有内联样式，不接受任意 CSS 表达式。 */
export const parseMediaWidth = (value: string | null): string | null => {
  if (!value) return null
  const match = /^(\d+(?:\.\d+)?)(px|em|rem|%)?$/i.exec(value.trim())
  if (!match || !Number.isFinite(Number(match[1])) || Number(match[1]) <= 0) return null
  return `${Number(match[1])}${(match[2] || 'px').toLowerCase()}`
}

/** 保留已有坐标系；只有明确的固定宽高才允许为渲染副本补 viewBox。 */
export const resolveSvgViewport = (
  width: string | null,
  height: string | null,
  viewBox: string | null,
): SvgViewport | null => {
  const fixedWidth = pixelLength(width)
  const fixedHeight = pixelLength(height)

  if (!viewBox?.trim()) {
    if (!fixedWidth || !fixedHeight || !Number.isFinite(fixedWidth / fixedHeight) || fixedWidth / fixedHeight <= 0) return null
    return { width: fixedWidth, height: fixedHeight, viewBox: `0 0 ${fixedWidth} ${fixedHeight}` }
  }

  const values = viewBox.trim().split(/[\s,]+/).map(Number)
  if (values.length !== 4 || !values.every(Number.isFinite) || values[2] <= 0 || values[3] <= 0) {
    return null
  }

  const ratio = values[2] / values[3]
  const resolvedWidth = fixedWidth || (fixedHeight ? fixedHeight * ratio : values[2])
  const resolvedHeight = fixedHeight || (fixedWidth ? fixedWidth / ratio : values[3])
  if (![ratio, resolvedWidth, resolvedHeight, resolvedWidth / resolvedHeight].every(value => Number.isFinite(value) && value > 0)) {
    return null
  }
  return { width: resolvedWidth, height: resolvedHeight, viewBox }
}

/** 根据真实图片比例设置布局变量，源文件尺寸不作为默认显示尺寸。加载后可重复调用。 */
export const prepareMarkdownImage = (image: HTMLImageElement): void => {
  if (!image.naturalWidth || !image.naturalHeight) return
  image.style.setProperty('--media-intrinsic-width', `${image.naturalWidth}px`)
  image.style.setProperty('--media-ratio', String(image.naturalWidth / image.naturalHeight))
}

/** 识别独占段落的插图；混排内容不强制换行，多个并排图片也不拆成多行。 */
const isStandaloneMedia = (media: Element): boolean => {
  const node = media.parentElement?.tagName === 'A' ? media.parentElement : media
  const parent = node.parentElement
  if (!parent || !['P', 'DIV', 'FIGURE'].includes(parent.tagName)) return false
  return Array.from(parent.childNodes).every(child =>
    child === node || (child.nodeType === 3 && !child.textContent?.trim()),
  )
}

/** 只规范化已清洗 DOM 中的内容插图，跳过公式及嵌套 SVG，不修改 Markdown 原文。 */
export const prepareMarkdownMedia = (root: HTMLElement): Array<HTMLImageElement | SVGSVGElement> => {
  const prepared: Array<HTMLImageElement | SVGSVGElement> = []

  for (const media of root.querySelectorAll<HTMLImageElement | SVGSVGElement>('img, svg')) {
    if (media.closest('.katex, math') || media.parentElement?.closest('svg')) continue

    const preferredWidth = parseMediaWidth(media.style.getPropertyValue('--media-preferred-width')) ||
      parseMediaWidth(media.style.width) || parseMediaWidth(media.getAttribute('width'))
    if (preferredWidth) media.style.setProperty('--media-preferred-width', preferredWidth)

    if (media instanceof SVGSVGElement) {
      const viewport = resolveSvgViewport(
        media.getAttribute('width'), media.getAttribute('height'), media.getAttribute('viewBox'),
      )
      // 坐标信息不足时保留原样，避免猜测 viewBox 后裁掉图形或标注。
      if (!viewport) continue
      media.setAttribute('viewBox', viewport.viewBox)
      media.setAttribute('width', String(viewport.width))
      media.setAttribute('height', String(viewport.height))
      media.style.setProperty('--media-intrinsic-width', `${viewport.width}px`)
      media.style.setProperty('--media-ratio', String(viewport.width / viewport.height))
    } else {
      prepareMarkdownImage(media)
    }

    // 保存显示宽度后清理源样式的尺寸覆盖（含 !important），防止绕过统一约束。
    for (const property of ['width', 'height', 'min-width', 'min-height', 'max-width', 'max-height', 'aspect-ratio']) {
      media.style.removeProperty(property)
    }
    media.classList.add('markdown-media')
    media.classList.toggle('markdown-media-block', isStandaloneMedia(media))
    prepared.push(media)
  }

  return prepared
}
