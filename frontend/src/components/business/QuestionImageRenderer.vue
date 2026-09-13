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

const applyInlineStyles = (
  root: HTMLElement,
  selector: string,
  styles: Record<string, string>,
) => {
  root.querySelectorAll<HTMLElement>(selector).forEach(element => {
    Object.entries(styles).forEach(([property, value]) => {
      const cssProperty = property.replace(/[A-Z]/g, match => `-${match.toLowerCase()}`)
      element.style.setProperty(cssProperty, value)
    })
  })
}

const getFormulaText = (formula: Element) => {
  return formula.querySelector('annotation')?.textContent?.trim() ||
    formula.textContent?.trim() ||
    '公式'
}

const superscriptMap: Record<string, string> = {
  '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
  '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾', 'n': 'ⁿ', 'i': 'ⁱ',
}

const subscriptMap: Record<string, string> = {
  '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
  '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎', 'i': 'ᵢ', 'n': 'ₙ',
}

const toUnicodeScript = (value: string, map: Record<string, string>) => {
  return Array.from(value).map(character => map[character] || character).join('')
}

/** 将常见 LaTeX 公式转为 Word/WPS 稳定显示的数学文本，避免数据 URI 图片被目标应用丢弃。 */
const latexToWordText = (value: string) => {
  let result = value
    .replace(/\\(?:left|right)\s*/g, '')
    .replace(/\\(?:text|mathrm|mathbf|mathit|operatorname)\{([^{}]*)\}/g, '$1')
    .replace(/\\frac\{([^{}]*)\}\{([^{}]*)\}/g, '($1)/($2)')
    .replace(/\\sqrt\{([^{}]*)\}/g, '√($1)')
    .replace(/\\sum/g, '∑')
    .replace(/\\prod/g, '∏')
    .replace(/\\infty/g, '∞')
    .replace(/\\(?:Theta|theta)/g, 'Θ')
    .replace(/\\(?:Lambda|lambda)/g, 'λ')
    .replace(/\\(?:alpha|Alpha)/g, 'α')
    .replace(/\\(?:beta|Beta)/g, 'β')
    .replace(/\\(?:gamma|Gamma)/g, 'γ')
    .replace(/\\(?:delta|Delta)/g, 'δ')
    .replace(/\\(log|ln|sin|cos|tan)\b/g, ' $1')
    .replace(/\\(?:cdot|cdotp)/g, '·')
    .replace(/\\times/g, '×')
    .replace(/\\(?:leq|le)/g, '≤')
    .replace(/\\(?:geq|ge)/g, '≥')
    .replace(/\\ne/g, '≠')
    .replace(/\\pm/g, '±')
    .replace(/\\to/g, '→')
    .replace(/\\in/g, '∈')
    .replace(/\\[,;!:]/g, '')
    .replace(/\^\{([^{}]*)\}/g, (_match, content: string) => toUnicodeScript(content, superscriptMap))
    .replace(/_\{([^{}]*)\}/g, (_match, content: string) => toUnicodeScript(content, subscriptMap))
    .replace(/\^([A-Za-z0-9])/g, (_match, content: string) => toUnicodeScript(content, superscriptMap))
    .replace(/_([A-Za-z0-9])/g, (_match, content: string) => toUnicodeScript(content, subscriptMap))
    .replace(/[{}]/g, '')
    .replace(/\\([A-Za-z]+)/g, '$1')
    .replace(/\s+/g, ' ')
    .trim()

  return result || '公式'
}

/** 用稳定的数学文本替换 KaTeX DOM，避免 Word/WPS 不支持页面外部 CSS 或 data URI 图片。 */
const replaceFormulaWithWordText = (sourceRoot: HTMLElement, targetRoot: HTMLElement) => {
  const sourceFormulas = Array.from(sourceRoot.querySelectorAll<HTMLElement>('.katex'))
  const targetFormulas = Array.from(targetRoot.querySelectorAll<HTMLElement>('.katex'))

  sourceFormulas.forEach((sourceFormula, index) => {
    const targetFormula = targetFormulas[index]
    if (!targetFormula) return

    const text = document.createElement('span')
    text.textContent = latexToWordText(getFormulaText(sourceFormula))
    const isDisplay = Boolean(sourceFormula.closest('.katex-display-wrapper'))
    text.style.display = isDisplay ? 'block' : 'inline-block'
    text.style.fontFamily = 'Cambria Math, STIX Two Math, Times New Roman, serif'
    text.style.fontSize = isDisplay ? '10.5pt' : 'inherit'
    text.style.lineHeight = '1.2'
    text.style.textAlign = isDisplay ? 'center' : 'left'
    text.style.whiteSpace = isDisplay ? 'normal' : 'nowrap'
    text.style.verticalAlign = 'middle'
    if (isDisplay) text.style.margin = '0.2em 0'
    targetFormula.replaceWith(text)
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
    table.style.fontSize = '9.5pt'
    table.style.lineHeight = '1.25'

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
      keyCell.style.color = '#8b6f47'
      keyCell.style.fontSize = '9.5pt'
      keyCell.style.fontWeight = '700'
      keyCell.style.lineHeight = '1.25'
      keyCell.style.verticalAlign = 'top'
      contentCell.style.padding = '2px 0'
      contentCell.style.border = '0'
      contentCell.style.fontSize = '9pt'
      contentCell.style.lineHeight = '1.2'
      contentCell.style.verticalAlign = 'top'

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

/** 将代码块改为紧凑 div，并用 br 明确保留换行，规避 Word/WPS 折叠 pre 的空白字符。 */
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
    const replacement = document.createElement('div')

    replacement.className = 'clipboard-code'
    codeText.split('\n').forEach((line, index, lines) => {
      // 使用不换行空格保留代码缩进，避免目标应用再次折叠普通空格。
      replacement.appendChild(document.createTextNode(line.replace(/\t/g, '    ').replace(/ /g, '\u00a0')))
      if (index < lines.length - 1) replacement.appendChild(document.createElement('br'))
    })
    replacement.setAttribute(
      'style',
      'box-sizing:border-box;display:block;width:100%;margin:4px 0;padding:4px 6px;' +
        'background:#f6f8fa;border:1px solid #e5e7eb;border-radius:3px;' +
        'font-family:Menlo,Monaco,Consolas,monospace;font-size:8pt;' +
        'line-height:9pt;mso-line-height-rule:exactly;white-space:normal;' +
        'overflow-wrap:anywhere;',
    )
    pre.replaceWith(replacement)
  })
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

  applyInlineStyles(clone, '.question-image-renderer__header', {
    paddingBottom: '6px',
    borderBottom: '1px solid #e5e7eb',
  })
  applyInlineStyles(clone, '.question-image-renderer__title', {
    margin: '0',
    color: '#374151',
    fontSize: '13pt',
    fontWeight: '700',
    lineHeight: '1.25',
  })
  applyInlineStyles(clone, '.question-image-renderer__meta', {
    display: 'block',
    marginTop: '3px',
    color: '#8b6f47',
    fontSize: '8.5pt',
    lineHeight: '1.2',
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
    margin: '0 0 2px',
    color: '#4b5563',
    fontSize: '10pt',
    fontWeight: '700',
    lineHeight: '1.2',
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
    color: '#8b6f47',
    fontSize: '9.5pt',
    fontWeight: '700',
    lineHeight: '1.25',
    verticalAlign: 'top',
  })
  applyInlineStyles(clone, '.question-image-renderer__option .markdown-viewer', {
    display: 'block',
    width: '100%',
    minWidth: '0',
    verticalAlign: 'top',
  })
  applyInlineStyles(clone, '.markdown-viewer, .v-md-editor-preview, .github-markdown-body', {
    width: '100%',
    minHeight: 'auto',
    padding: '0',
    backgroundColor: 'transparent',
    fontFamily: 'Arial, "Microsoft YaHei", "PingFang SC", sans-serif',
    fontSize: '9.5pt',
    lineHeight: '1.2',
  })
  applyInlineStyles(clone, '.markdown-viewer.is-option, .markdown-viewer.is-option .github-markdown-body', {
    fontSize: '9pt',
    lineHeight: '1.2',
  })
  applyInlineStyles(clone, '.question-image-renderer__option .markdown-viewer', {
    display: 'block',
    width: '100%',
    minWidth: '0',
    verticalAlign: 'top',
  })
  applyInlineStyles(clone, '.markdown-viewer h1, .markdown-viewer h2, .markdown-viewer h3', {
    margin: '4px 0 2px',
    fontWeight: '700',
    lineHeight: '1.2',
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
    margin: '0',
    padding: '0',
    lineHeight: '1.2',
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
    formula.replaceWith(document.createTextNode(latexToWordText(getFormulaText(formula))))
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
  replaceFormulaWithWordText(root, clone)
  sanitizeClipboardDom(clone)

  const wrapper = document.createElement('div')
  wrapper.setAttribute(
    'style',
    'box-sizing:border-box;width:100%;max-width:760px;padding:0;background:#fff;color:#333;' +
      'font-family:Arial,"Microsoft YaHei","PingFang SC",sans-serif;font-size:9.5pt;line-height:1.2;',
  )
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
