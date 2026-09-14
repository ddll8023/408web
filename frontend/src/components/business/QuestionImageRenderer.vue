<template>
  <div
    v-if="question"
    ref="captureRoot"
    class="question-image-renderer"
    aria-hidden="true"
  >
    <header class="question-image-renderer__header">
      <h1 class="question-image-renderer__title">{{ questionTitle }}</h1>
      <div class="question-image-renderer__meta">
        <span>{{ questionTypeLabel }}</span>
        <span v-for="category in categories" :key="`category-${category}`">· {{ category }}</span>
        <span v-if="difficultyLabel">· {{ difficultyLabel }}</span>
      </div>
    </header>

    <section v-if="includeQuestion && hasQuestion" class="question-image-renderer__section">
      <h2>题目</h2>
      <MarkdownViewer
        :content="question.content"
        variant="plain"
        :interactive="false"
        @rendered="handleMarkdownRendered"
      />
    </section>

    <section v-if="includeOptions && hasOptions" class="question-image-renderer__section">
      <h2>选项</h2>
      <div class="question-image-renderer__options">
        <div
          v-for="([key, value]) in optionEntries"
          :key="key"
          class="question-image-renderer__option"
        >
          <span class="question-image-renderer__option-key">{{ key }}.</span>
          <MarkdownViewer
            :content="value"
            variant="plain"
            content-role="option"
            :interactive="false"
            @rendered="handleMarkdownRendered"
          />
        </div>
      </div>
    </section>

    <section v-if="includeAnswer && hasAnswer" class="question-image-renderer__section">
      <h2>答案</h2>
      <MarkdownViewer
        :content="question.answer || ''"
        variant="plain"
        :interactive="false"
        @rendered="handleMarkdownRendered"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { toBlob } from 'html-to-image'
import type { ExamQuestion, MockQuestion } from '@/types'
import { parseQuestionOptions } from '@/utils/questionOptions'
import { getDifficultyLabel } from '@/constants/exam'
import {
  getWordClipboardImageSize,
  WORD_CLIPBOARD_IMAGE_HEIGHT_CM,
  WORD_CLIPBOARD_IMAGE_HEIGHT_PX,
} from '@/utils/markdownMedia'
import type { QuestionContentScope, RichCopyContent } from '@/utils/questionCopy'
import MarkdownViewer from '@/components/basic/MarkdownViewer.vue'

type Question = ExamQuestion | MockQuestion

interface Props {
  question: Question
  scope: QuestionContentScope
}

const props = defineProps<Props>()
const captureRoot = ref<HTMLElement | null>(null)
const renderedCount = ref(0)

const questionTitle = computed(() => {
  const current = props.question
  const questionNumber = current.questionNumber == null ? '' : `第${current.questionNumber}题`

  if ('source' in current) {
    return [current.title || current.source || '', questionNumber]
      .filter(Boolean)
      .join(' · ') || '模拟题'
  }

  return [current.year != null ? `${current.year}年真题` : '真题', questionNumber]
    .filter(Boolean)
    .join(' ')
})

const questionTypeLabel = computed(() => {
  return props.question.questionType === 'CHOICE' ? '选择题' : '主观题'
})

const categories = computed(() => {
  return Array.isArray(props.question.category)
    ? props.question.category.filter(category => category.trim())
    : []
})

const difficultyLabel = computed(() => getDifficultyLabel(props.question.difficulty))
const hasQuestion = computed(() => Boolean(props.question.content?.trim()))
const hasAnswer = computed(() => Boolean(props.question.answer?.trim()))

const parsedOptions = computed(() => {
  if (props.question.questionType !== 'CHOICE') return null
  return parseQuestionOptions(props.question.options)
})

const optionEntries = computed(() => Object.entries(parsedOptions.value || {}))
const hasOptions = computed(() => optionEntries.value.length > 0)

const includeQuestion = computed(() => {
  return props.scope === 'question' || props.scope === 'question-options' || props.scope === 'all'
})
const includeOptions = computed(() => {
  return props.scope === 'options' || props.scope === 'question-options' || props.scope === 'all'
})
const includeAnswer = computed(() => props.scope === 'answer' || props.scope === 'all')
const hasRenderableContent = computed(() => {
  return (includeQuestion.value && hasQuestion.value) ||
    (includeOptions.value && hasOptions.value) ||
    (includeAnswer.value && hasAnswer.value)
})

const handleMarkdownRendered = () => {
  renderedCount.value += 1
}

const wait = (milliseconds: number) => {
  return new Promise<void>(resolve => window.setTimeout(resolve, milliseconds))
}

const waitForNextFrame = () => {
  return new Promise<void>(resolve => {
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(() => resolve())
    } else {
      window.setTimeout(resolve, 0)
    }
  })
}

const waitForMarkdown = async (root: HTMLElement) => {
  const expectedCount = root.querySelectorAll('.markdown-viewer').length
  if (expectedCount === 0) return

  const deadline = Date.now() + 2500
  while (renderedCount.value < expectedCount && Date.now() < deadline) {
    await wait(16)
  }

  if (renderedCount.value < expectedCount) {
    throw new Error('MARKDOWN_RENDER_TIMEOUT')
  }
}

const waitForImages = async (root: HTMLElement) => {
  const images = Array.from(root.querySelectorAll('img'))

  await Promise.all(images.map(async image => {
    // 截图节点位于视口外，避免 lazy 图片一直等待浏览器调度。
    image.loading = 'eager'

    if (!image.complete) {
      await new Promise<void>(resolve => {
        const timeout = window.setTimeout(resolve, 5000)
        const finish = () => {
          window.clearTimeout(timeout)
          image.removeEventListener('load', finish)
          image.removeEventListener('error', finish)
          resolve()
        }
        image.addEventListener('load', finish, { once: true })
        image.addEventListener('error', finish, { once: true })
      })
    }

    if (image.naturalWidth === 0) {
      throw new Error('IMAGE_LOAD_FAILED')
    }

    if (typeof image.decode === 'function') {
      try {
        await image.decode()
      } catch {
        // 已经有可用 naturalWidth 时，忽略浏览器解码 API 的偶发拒绝。
      }
    }
  }))
}

const waitForReadyContent = async (root: HTMLElement) => {
  await nextTick()
  await waitForMarkdown(root)
  if (document.fonts) {
    await document.fonts.ready
  }
  await waitForImages(root)
  await waitForNextFrame()
}

const setInlineStyles = (element: HTMLElement, styles: Record<string, string>) => {
  Object.entries(styles).forEach(([property, value]) => {
    const cssProperty = property.replace(/[A-Z]/g, match => `-${match.toLowerCase()}`)
    element.style.setProperty(cssProperty, value)
  })
}

const applyInlineStyles = (
  root: HTMLElement,
  selector: string,
  styles: Record<string, string>,
) => {
  root.querySelectorAll<HTMLElement>(selector).forEach(element => {
    setInlineStyles(element, styles)
  })
}

// Word/WPS 使用 mso 字体属性区分西文和中文字体，普通 CSS 作为其他富文本应用的回退。
const wordBodyFontStyles = {
  fontFamily: '"Times New Roman", "宋体", SimSun, serif',
  msoAsciiFontFamily: '"Times New Roman"',
  msoHansiFontFamily: '"Times New Roman"',
  msoFareastFontFamily: '宋体',
  msoBidiFontFamily: '"Times New Roman"',
}
const wordCodeFontStyles = {
  fontFamily: 'Consolas, monospace',
  msoAsciiFontFamily: 'Consolas',
  msoHansiFontFamily: 'Consolas',
  msoFareastFontFamily: 'Consolas',
  msoBidiFontFamily: 'Consolas',
}
const wordLineHeight = '1'
const wordCodeLineHeight = '10pt'

const getFormulaLatex = (formula: Element) => {
  return formula.querySelector('annotation[encoding="application/x-tex"]')?.textContent?.trim() ||
    formula.querySelector('annotation')?.textContent?.trim() ||
    formula.textContent?.trim() ||
    '公式'
}

/** 用原始 LaTeX 替换 KaTeX DOM；WPS 公式编辑器不需要 Markdown 的 `$` 分隔符。 */
const replaceFormulaWithLatex = (sourceRoot: HTMLElement, targetRoot: HTMLElement) => {
  const sourceFormulas = Array.from(sourceRoot.querySelectorAll<HTMLElement>('.katex'))
  const targetFormulas = Array.from(targetRoot.querySelectorAll<HTMLElement>('.katex'))

  sourceFormulas.forEach((sourceFormula, index) => {
    const targetFormula = targetFormulas[index]
    if (!targetFormula) return

    const text = document.createElement('span')
    text.className = 'word-formula'
    text.textContent = getFormulaLatex(sourceFormula)
    const isDisplay = Boolean(sourceFormula.closest('.katex-display-wrapper'))
    text.style.display = isDisplay ? 'block' : 'inline-block'
    text.style.fontFamily = '"Times New Roman", serif'
    text.style.fontSize = isDisplay ? '10.5pt' : 'inherit'
    text.style.lineHeight = wordLineHeight
    text.style.textAlign = isDisplay ? 'center' : 'left'
    text.style.whiteSpace = isDisplay ? 'normal' : 'nowrap'
    text.style.verticalAlign = 'middle'
    if (isDisplay) text.style.margin = '0.2em 0'
    targetFormula.replaceWith(text)
  })
}

const wordChineseCharacterPattern = /[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u3000-\u303F\uFF00-\uFFEF]/
const wordTextPartPattern = /[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u3000-\u303F\uFF00-\uFFEF]+|[^\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u3000-\u303F\uFF00-\uFFEF]+/g
const wordChineseFontStyles = {
  fontFamily: '"宋体", SimSun, serif',
  msoAsciiFontFamily: '宋体',
  msoHansiFontFamily: '宋体',
  msoFareastFontFamily: '宋体',
  msoBidiFontFamily: '宋体',
}
const wordEnglishFontStyles = {
  fontFamily: '"Times New Roman", serif',
  msoAsciiFontFamily: '"Times New Roman"',
  msoHansiFontFamily: '"Times New Roman"',
  msoFareastFontFamily: '"Times New Roman"',
  msoBidiFontFamily: '"Times New Roman"',
}

/** 为 Word 文本运行显式指定中西文字体，避免 Word 使用当前文档的默认字体。 */
const applyWordCharacterFonts = (root: HTMLElement) => {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  const textNodes: Text[] = []
  let currentNode = walker.nextNode()

  while (currentNode) {
    if (currentNode instanceof Text) {
      const parent = currentNode.parentElement
      if (parent && !parent.closest('.clipboard-code, .word-formula') && currentNode.nodeValue?.trim()) {
        textNodes.push(currentNode)
      }
    }
    currentNode = walker.nextNode()
  }

  textNodes.forEach(textNode => {
    const value = textNode.nodeValue
    if (!value) return

    const parts = value.match(wordTextPartPattern)
    if (!parts) return

    const fragment = document.createDocumentFragment()
    parts.forEach(part => {
      const span = document.createElement('span')
      setInlineStyles(
        span,
        wordChineseCharacterPattern.test(part)
          ? wordChineseFontStyles
          : wordEnglishFontStyles,
      )
      span.textContent = part
      fragment.appendChild(span)
    })
    textNode.replaceWith(fragment)
  })
}

const sanitizeClipboardDom = (root: HTMLElement) => {
  root.querySelectorAll('script, iframe, object, embed, form, style').forEach(element => element.remove())

  root.querySelectorAll<HTMLElement>('*').forEach(element => {
    Array.from(element.attributes).forEach(attribute => {
      const name = attribute.name.toLowerCase()
      if (name.startsWith('on') ||
        (['href', 'src'].includes(name) && /^\s*javascript:/i.test(attribute.value))) {
        element.removeAttribute(attribute.name)
      }
    })
  })
}

/** 用表格承载选项，避免 Word/WPS 对 flex、gap 和 calc 宽度支持不一致。 */
const compactClipboardOptions = (root: HTMLElement) => {
  root.querySelectorAll<HTMLElement>('.question-image-renderer__options').forEach(container => {
    const options = Array.from(container.children).filter(element =>
      element.classList.contains('question-image-renderer__option'),
    )
    if (options.length === 0) return

    const table = document.createElement('table')
    table.style.width = '100%'
    table.style.margin = '0'
    table.style.borderCollapse = 'collapse'
    table.style.tableLayout = 'fixed'
    setInlineStyles(table, {
      ...wordBodyFontStyles,
      fontSize: '9.5pt',
      lineHeight: wordLineHeight,
    })

    const body = document.createElement('tbody')
    options.forEach(option => {
      const row = document.createElement('tr')
      const keyCell = document.createElement('td')
      const contentCell = document.createElement('td')
      const key = option.querySelector<HTMLElement>('.question-image-renderer__option-key')
      const content = option.querySelector<HTMLElement>('.markdown-viewer')

      keyCell.textContent = key?.textContent?.trim() || ''
      keyCell.style.width = '28px'
      keyCell.style.padding = '2px 6px 2px 0'
      keyCell.style.border = '0'
      setInlineStyles(keyCell, {
        ...wordBodyFontStyles,
        color: '#8b6f47',
        fontSize: '9.5pt',
        fontWeight: '700',
        lineHeight: wordLineHeight,
        verticalAlign: 'top',
      })
      setInlineStyles(contentCell, {
        ...wordBodyFontStyles,
        padding: '2px 0',
        border: '0',
        fontSize: '9pt',
        lineHeight: wordLineHeight,
        verticalAlign: 'top',
      })

      if (content) {
        content.style.display = 'block'
        content.style.width = '100%'
        content.style.minWidth = '0'
        contentCell.appendChild(content)
      }

      row.append(keyCell, contentCell)
      body.appendChild(row)
    })
    table.appendChild(body)
    container.replaceChildren(table)
  })
}

/** 将代码块改为紧凑段落，并用 br 明确保留换行，规避 Word/WPS 折叠 pre 的空白字符。 */
const compactClipboardCode = (root: HTMLElement) => {
  root.querySelectorAll<HTMLElement>('pre').forEach(pre => {
    const code = pre.querySelector<HTMLElement>('code') || pre
    const codeClone = code.cloneNode(true) as HTMLElement
    codeClone.querySelectorAll('br').forEach(br => br.replaceWith('\n'))
    const codeText = (codeClone.textContent || '')
      .replace(/\r\n?/g, '\n')
      .replace(/^[ \t]*\n/, '')
      .replace(/\n[ \t]*\n+/g, '\n')
      .replace(/\n[ \t]*$/, '')
    const replacement = document.createElement('p')

    replacement.className = 'clipboard-code'
    codeText.split('\n').forEach((line, index, lines) => {
      // 使用不换行空格保留代码缩进，避免目标应用再次折叠普通空格。
      replacement.appendChild(document.createTextNode(line.replace(/\t/g, '    ').replace(/ /g, '\u00a0')))
      if (index < lines.length - 1) replacement.appendChild(document.createElement('br'))
    })
    setInlineStyles(replacement, {
      ...wordCodeFontStyles,
      boxSizing: 'border-box',
      display: 'block',
      width: '100%',
      margin: '4px 0',
      padding: '4px 6px',
      background: '#f6f8fa',
      border: '1px solid #e5e7eb',
      borderRadius: '3px',
      fontSize: '8pt',
      lineHeight: wordCodeLineHeight,
      msoLineHeightRule: 'exactly',
      msoLineHeightAlt: wordCodeLineHeight,
      whiteSpace: 'normal',
      overflowWrap: 'anywhere',
    })
    // CSSOM 可能丢弃 mso-* 属性，直接补入 style 属性确保 Word 识别为“固定值”。
    const codeStyle = replacement.getAttribute('style') || ''
    replacement.setAttribute(
      'style',
      `${codeStyle};line-height:${wordCodeLineHeight};mso-line-height-rule:exactly;mso-line-height-alt:${wordCodeLineHeight};`,
    )
    pre.replaceWith(replacement)
  })
}

const clipboardMediaScale = 2
const parseClipboardDimension = (value: string | null) => {
  if (!value) return null
  const match = /^\s*(\d+(?:\.\d+)?)(?:px)?\s*$/i.exec(value)
  const dimension = match ? Number(match[1]) : NaN
  return Number.isFinite(dimension) && dimension > 0 ? dimension : null
}

const getSvgDimensions = (svg: SVGSVGElement) => {
  const viewBox = (svg.getAttribute('viewBox') || '').trim().split(/[\\s,]+/).map(Number)
  const hasViewBox = viewBox.length === 4 && viewBox[2] > 0 && viewBox[3] > 0
  const rect = svg.getBoundingClientRect()
  const width = parseClipboardDimension(svg.getAttribute('width')) ||
    (hasViewBox ? viewBox[2] : null) || rect.width || 300
  const height = parseClipboardDimension(svg.getAttribute('height')) ||
    (hasViewBox ? viewBox[3] : null) || rect.height || width

  return {
    width: width || height,
    height: height || width,
  }
}

const getCanvasSize = (width: number, height: number) => {
  const scale = Math.min(clipboardMediaScale, 4096 / width, 4096 / height)
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  }
}

const rasterizeLoadedImage = (
  image: HTMLImageElement,
  width = image.naturalWidth,
  height = image.naturalHeight,
) => {
  if (!width || !height) return null

  const canvas = document.createElement('canvas')
  const size = getCanvasSize(width, height)
  canvas.width = size.width
  canvas.height = size.height
  const context = canvas.getContext('2d')
  if (!context) return null

  context.drawImage(image, 0, 0, size.width, size.height)
  return canvas.toDataURL('image/png')
}

const loadClipboardImage = (source: string) => {
  return new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('CLIPBOARD_IMAGE_LOAD_FAILED'))
    image.src = source
  })
}

const serializeSvg = (svg: SVGSVGElement) => {
  const clone = svg.cloneNode(true) as SVGSVGElement
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.removeAttribute('tabindex')
  clone.removeAttribute('role')
  return new XMLSerializer().serializeToString(clone)
}

/** 将 SVG 栅格化为 PNG，Word 粘贴时使用稳定的图片格式；失败时保留 SVG 图片数据。 */
const rasterizeSvg = async (svg: SVGSVGElement) => {
  const serialized = serializeSvg(svg)
  const svgSource = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(serialized)}`
  const dimensions = getSvgDimensions(svg)

  try {
    const image = await loadClipboardImage(svgSource)
    return rasterizeLoadedImage(image, dimensions.width, dimensions.height) || svgSource
  } catch {
    return svgSource
  }
}

const rasterizeImage = async (image: HTMLImageElement) => {
  const source = image.currentSrc || image.src
  if (!source) return null

  try {
    const loadedImage = image.complete && image.naturalWidth
      ? image
      : await loadClipboardImage(source)
    return rasterizeLoadedImage(loadedImage) || source
  } catch {
    // 跨域图片可能无法绘制到 Canvas，保留原地址作为兼容回退。
    return source
  }
}

const copyMediaAttributes = (source: HTMLElement | SVGElement, target: HTMLImageElement) => {
  const className = source.getAttribute('class')
  if (className) target.setAttribute('class', `${className} clipboard-media`)
  else target.classList.add('clipboard-media')

  const alt = source.getAttribute('alt') || source.querySelector('title')?.textContent?.trim()
  if (alt) target.alt = alt

  for (const attribute of ['width', 'height']) {
    const value = source.getAttribute(attribute)
    if (value) target.setAttribute(attribute, value)
  }

  const preferredWidth = source.style.getPropertyValue('--media-preferred-width').trim()
  if (preferredWidth) target.style.width = preferredWidth
}

const getClipboardMediaRatio = (source: HTMLElement | SVGElement): number | null => {
  const styledRatio = Number(source.style.getPropertyValue('--media-ratio'))
  if (Number.isFinite(styledRatio) && styledRatio > 0) return styledRatio

  if (source instanceof SVGSVGElement) {
    const dimensions = getSvgDimensions(source)
    const ratio = dimensions.width / dimensions.height
    return Number.isFinite(ratio) && ratio > 0 ? ratio : null
  }

  const image = source instanceof HTMLImageElement ? source : null
  const rect = source.getBoundingClientRect()
  const width = image?.naturalWidth ||
    parseClipboardDimension(source.getAttribute('width')) || rect.width
  const height = image?.naturalHeight ||
    parseClipboardDimension(source.getAttribute('height')) || rect.height
  const ratio = width / height
  return Number.isFinite(ratio) && ratio > 0 ? ratio : null
}

/** 为 Word/WPS 独立图片写入 3 厘米高度，并按原图比例同步宽度。 */
const applyWordImageSize = (image: HTMLImageElement, ratio: number | null) => {
  const size = ratio ? getWordClipboardImageSize(ratio) : null
  if (size) {
    // 同时写入厘米 CSS、像素属性和 aspect-ratio，避免依赖 Word/WPS 的 VML 解析。
    image.setAttribute('width', String(size.widthPx))
    image.setAttribute('height', String(size.heightPx))
    setInlineStyles(image, {
      width: `${size.widthCm.toFixed(2)}cm`,
      height: `${size.heightCm.toFixed(2)}cm`,
      maxWidth: 'none',
      maxHeight: 'none',
      aspectRatio: String(size.ratio),
    })
    return
  }

  image.removeAttribute('width')
  image.setAttribute('height', String(WORD_CLIPBOARD_IMAGE_HEIGHT_PX))
  setInlineStyles(image, {
    width: 'auto',
    height: `${WORD_CLIPBOARD_IMAGE_HEIGHT_CM.toFixed(2)}cm`,
    maxWidth: 'none',
    maxHeight: 'none',
  })
}

const alignClipboardMedia = (
  image: HTMLImageElement,
  standalone: boolean,
  ratio: number | null,
) => {
  if (standalone) {
    if (!image.classList.contains('media-inline')) {
      applyWordImageSize(image, ratio)
    } else {
      setInlineStyles(image, {
        maxWidth: '100%',
        height: 'auto',
      })
    }
    setInlineStyles(image, {
      display: 'inline-block',
      margin: '4px 0',
      objectFit: 'contain',
    })

    const parent = image.parentElement
    if (parent) {
      setInlineStyles(parent, { textAlign: 'center' })
      if (parent.tagName === 'A') {
        setInlineStyles(parent, { display: 'inline-block', textAlign: 'center' })
        if (parent.parentElement) setInlineStyles(parent.parentElement, { textAlign: 'center' })
      }
    }
    return
  }

  setInlineStyles(image, {
    display: 'inline-block',
    maxWidth: '100%',
    height: 'auto',
    verticalAlign: 'middle',
    objectFit: 'contain',
  })
}

/** 将图片和 SVG 变为 Word 可识别的 img 图片，并为独占段落补充居中样式。 */
const prepareClipboardMedia = async (root: HTMLElement, referenceRoot = root) => {
  const getMedia = (container: HTMLElement) => Array.from(
    container.querySelectorAll<HTMLImageElement | SVGSVGElement>('img, svg'),
  )
    .filter(element => !element.closest('.katex, math, .clipboard-code'))
    .filter(element => !element.parentElement?.closest('svg'))
  const media = getMedia(root)
  const referenceMedia = getMedia(referenceRoot)

  for (const [index, source] of media.entries()) {
    const standalone = source.classList.contains('markdown-media-block')
    const ratio = getClipboardMediaRatio(referenceMedia[index] || source)
    if (source instanceof SVGSVGElement) {
      const image = document.createElement('img')
      copyMediaAttributes(source, image)
      image.src = await rasterizeSvg(source)
      source.replaceWith(image)
      alignClipboardMedia(image, standalone, ratio)
      continue
    }

    const imageSource = await rasterizeImage(source)
    if (imageSource) source.src = imageSource
    alignClipboardMedia(source, standalone, ratio)
  }
}

const prepareClipboardClone = (root: HTMLElement) => {
  const clone = root.cloneNode(true) as HTMLElement
  clone.removeAttribute('aria-hidden')
  // Word 复制只保留题目主标题，不带类型、分类和难度标签。
  clone.querySelector('.question-image-renderer__meta')?.remove()
  clone.style.position = 'static'
  clone.style.left = '0'
  clone.style.top = '0'
  clone.style.zIndex = 'auto'
  clone.style.width = '100%'
  clone.style.maxWidth = '760px'
  clone.style.padding = '0'
  clone.style.backgroundColor = '#ffffff'
  clone.style.pointerEvents = 'auto'
  setInlineStyles(clone, {
    ...wordBodyFontStyles,
    lineHeight: wordLineHeight,
  })

  applyInlineStyles(clone, '.question-image-renderer__header', {
    ...wordBodyFontStyles,
    paddingBottom: '6px',
    borderBottom: '1px solid #e5e7eb',
  })
  applyInlineStyles(clone, '.question-image-renderer__title', {
    margin: '0',
    ...wordBodyFontStyles,
    color: '#374151',
    fontSize: '13pt',
    fontWeight: '700',
    lineHeight: wordLineHeight,
  })
  applyInlineStyles(clone, '.question-image-renderer__meta', {
    display: 'block',
    ...wordBodyFontStyles,
    marginTop: '3px',
    color: '#8b6f47',
    fontSize: '8.5pt',
    lineHeight: wordLineHeight,
  })
  applyInlineStyles(clone, '.question-image-renderer__meta span', {
    display: 'inline',
    marginRight: '4px',
    padding: '0',
  })
  applyInlineStyles(clone, '.question-image-renderer__section', {
    marginTop: '6px',
  })
  applyInlineStyles(clone, '.question-image-renderer__section h2', {
    ...wordBodyFontStyles,
    margin: '0 0 2px',
    color: '#4b5563',
    fontSize: '10pt',
    fontWeight: '700',
    lineHeight: wordLineHeight,
  })
  applyInlineStyles(clone, '.question-image-renderer__options', {
    display: 'block',
    margin: '0',
  })
  applyInlineStyles(clone, '.question-image-renderer__option', {
    display: 'block',
    marginBottom: '3px',
    padding: '2px 0',
  })
  applyInlineStyles(clone, '.question-image-renderer__option-key', {
    display: 'inline-block',
    marginRight: '6px',
    ...wordBodyFontStyles,
    color: '#8b6f47',
    fontSize: '9.5pt',
    fontWeight: '700',
    lineHeight: wordLineHeight,
    verticalAlign: 'top',
  })
  applyInlineStyles(clone, '.question-image-renderer__option .markdown-viewer', {
    display: 'block',
    width: '100%',
    minWidth: '0',
    verticalAlign: 'top',
  })
  applyInlineStyles(clone, '.markdown-viewer, .v-md-editor-preview, .github-markdown-body', {
    ...wordBodyFontStyles,
    width: '100%',
    minHeight: 'auto',
    padding: '0',
    backgroundColor: 'transparent',
    fontSize: '9.5pt',
    lineHeight: wordLineHeight,
  })
  applyInlineStyles(clone, '.markdown-viewer.is-option, .markdown-viewer.is-option .github-markdown-body', {
    ...wordBodyFontStyles,
    fontSize: '9pt',
    lineHeight: wordLineHeight,
  })
  applyInlineStyles(clone, '.question-image-renderer__option .markdown-viewer', {
    display: 'block',
    width: '100%',
    minWidth: '0',
    verticalAlign: 'top',
  })
  applyInlineStyles(clone, '.markdown-viewer h1, .markdown-viewer h2, .markdown-viewer h3', {
    ...wordBodyFontStyles,
    margin: '4px 0 2px',
    fontWeight: '700',
    lineHeight: wordLineHeight,
  })
  applyInlineStyles(clone, '.markdown-viewer h1', {
    fontSize: '11.5pt',
  })
  applyInlineStyles(clone, '.markdown-viewer h2', {
    fontSize: '10.5pt',
  })
  applyInlineStyles(clone, '.markdown-viewer h3', {
    fontSize: '10pt',
  })
  applyInlineStyles(clone, 'hr', {
    margin: '4px 0',
  })
  applyInlineStyles(clone, 'p', {
    ...wordBodyFontStyles,
    margin: '0',
    padding: '0',
    lineHeight: wordLineHeight,
    msoMarginTopAlt: '0',
    msoMarginBottomAlt: '0',
  })
  applyInlineStyles(clone, 'ul, ol', {
    paddingLeft: '2em',
  })
  applyInlineStyles(clone, 'blockquote', {
    margin: '0.5em 0',
    paddingLeft: '0.75em',
    borderLeft: '3px solid #dfe2e5',
    color: '#57606a',
  })
  applyInlineStyles(clone, 'table', {
    borderCollapse: 'collapse',
    maxWidth: '100%',
  })
  applyInlineStyles(clone, 'th, td', {
    padding: '2px 6px',
    border: '1px solid #dfe2e5',
  })
  applyInlineStyles(clone, 'img', {
    maxWidth: '100%',
    height: 'auto',
  })
  applyInlineStyles(clone, '.katex-display-wrapper', {
    display: 'block',
    margin: '0.25em 0',
    textAlign: 'center',
  })
  applyInlineStyles(clone, '.katex-inline-wrapper', {
    display: 'inline',
  })
  compactClipboardOptions(clone)
  compactClipboardCode(clone)

  return clone
}

const extractClipboardText = (root: HTMLElement) => {
  const clone = root.cloneNode(true) as HTMLElement
  clone.removeAttribute('aria-hidden')
  clone.querySelector('.question-image-renderer__meta')?.remove()
  clone.style.position = 'static'
  clone.style.left = '0'
  clone.style.top = '0'
  clone.style.width = '760px'

  clone.querySelectorAll<HTMLElement>('.katex').forEach(formula => {
    formula.replaceWith(document.createTextNode(getFormulaLatex(formula)))
  })

  const holder = document.createElement('div')
  holder.style.position = 'fixed'
  holder.style.left = '-100000px'
  holder.style.top = '0'
  holder.style.width = '760px'
  holder.appendChild(clone)
  document.body.appendChild(holder)
  try {
    return (clone.innerText || clone.textContent || '')
      .replace(/\u00a0/g, ' ')
      .replace(/[ \t]+\n/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim()
  } finally {
    document.body.removeChild(holder)
  }
}

const getClipboardContent = async (): Promise<RichCopyContent> => {
  if (!hasRenderableContent.value) {
    throw new Error('NO_COPY_CONTENT')
  }

  await nextTick()
  const root = captureRoot.value
  if (!root) {
    throw new Error('IMAGE_RENDERER_NOT_READY')
  }

  await waitForReadyContent(root)
  const text = extractClipboardText(root)
  const clone = prepareClipboardClone(root)
  replaceFormulaWithLatex(root, clone)
  await prepareClipboardMedia(clone, root)
  applyWordCharacterFonts(clone)
  sanitizeClipboardDom(clone)

  const wrapper = document.createElement('div')
  setInlineStyles(wrapper, {
    ...wordBodyFontStyles,
    boxSizing: 'border-box',
    width: '100%',
    maxWidth: '760px',
    padding: '0',
    background: '#fff',
    color: '#333',
    fontSize: '9.5pt',
    lineHeight: wordLineHeight,
  })
  wrapper.innerHTML = clone.innerHTML

  return {
    html: `<!--StartFragment-->${wrapper.outerHTML}<!--EndFragment-->`,
    text,
  }
}

const capture = async (): Promise<Blob> => {
  if (!hasRenderableContent.value) {
    throw new Error('NO_COPY_CONTENT')
  }

  await nextTick()
  const root = captureRoot.value
  if (!root) {
    throw new Error('IMAGE_RENDERER_NOT_READY')
  }

  await waitForReadyContent(root)

  const blob = await toBlob(root, {
    backgroundColor: '#ffffff',
    cacheBust: true,
    pixelRatio: 2,
    // 原节点位于视口外，截图副本必须回到画布原点。
    style: {
      position: 'static',
      left: '0',
      top: '0',
      zIndex: 'auto'
    }
  })

  if (!blob) {
    throw new Error('IMAGE_BLOB_EMPTY')
  }

  return blob
}

defineExpose({ capture, getClipboardContent })
</script>

<style scoped>
.question-image-renderer {
  position: fixed;
  top: 0;
  left: -100000px;
  z-index: 0;
  box-sizing: border-box;
  width: 760px;
  padding: 32px;
  overflow: visible;
  background: #fff;
  color: #333;
  text-align: left;
  white-space: normal;
  font-family: Arial, "Microsoft YaHei", "PingFang SC", sans-serif;
  font-size: 16px;
  line-height: 1.6;
  pointer-events: none;
}

.question-image-renderer__header {
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.question-image-renderer__title {
  margin: 0;
  color: #374151;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.4;
}

.question-image-renderer__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  color: #8b6f47;
  font-size: 13px;
}

.question-image-renderer__meta span {
  padding: 2px 8px;
  border: 1px solid rgba(139, 111, 71, 0.25);
  border-radius: 999px;
  flex: 0 0 auto;
  white-space: nowrap;
}

.question-image-renderer__section {
  margin-top: 24px;
}

.question-image-renderer__section h2 {
  margin: 0 0 10px;
  color: #4b5563;
  font-size: 17px;
  font-weight: 700;
}

.question-image-renderer__options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.question-image-renderer__option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.question-image-renderer__option-key {
  flex: 0 0 auto;
  font-size: 14px;
  line-height: 1.5;
  color: #8b6f47;
  font-weight: 700;
}

.question-image-renderer__option :deep(.markdown-viewer) {
  flex: 1;
  min-width: 0;
}

.question-image-renderer :deep(.markdown-viewer) {
  width: 100%;
  min-height: auto;
}

.question-image-renderer :deep(.v-md-editor-preview),
.question-image-renderer :deep(.github-markdown-body) {
  padding: 0;
  background: transparent;
}

.question-image-renderer :deep(pre) {
  overflow: visible;
  white-space: pre-wrap;
}

.question-image-renderer :deep(table) {
  max-width: 100%;
}
</style>
