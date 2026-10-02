<!-- AI 回答渲染：自建 Markdown 与 XSS 策略，不复用题目区共享白名单。 -->
<template>
  <div ref="rootRef" class="ai-answer-viewer"></div>
</template>

<script setup lang="ts">
/**
 * AI 回答渲染组件。
 * 与题目区 MarkdownViewer 的关键差异：回答文本不可信，因此本组件
 * ① 使用独立 MarkdownIt 实例并关闭原始 HTML；② 使用独立 FilterXSS 白名单，
 * 不允许 svg / img / iframe / style 与内联样式；③ 不引用 v-md-editor 的全局
 * 单例清洗器，题目区白名单与其渲染结果均不受影响。
 * 公式由 KaTeX 在清洗之后注入，属于本组件生成的受信任标记。
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { FilterXSS } from 'xss'

const props = defineProps<{ content: string }>()

/** 独立白名单：不含 svg、img、iframe、script、style 与任何 style 属性。 */
const AI_ANSWER_WHITE_LIST: Record<string, string[]> = {
  p: [], br: [], hr: [], blockquote: [],
  strong: [], b: [], em: [], i: [], del: [], s: [], u: [], sub: [], sup: [],
  h1: [], h2: [], h3: [], h4: [], h5: [], h6: [],
  ul: [], ol: ['start'], li: [],
  table: [], thead: [], tbody: [], tr: [], th: ['align'], td: ['align'],
  pre: [], code: ['class'], span: ['class'],
  a: ['href', 'title'],
}

/** 回答清洗器：白名单之外直接去标签保留文字，脚本与样式连同内容一起丢弃。 */
const answerSanitizer = new FilterXSS({
  whiteList: AI_ANSWER_WHITE_LIST,
  stripIgnoreTag: true,
  stripIgnoreTagBody: ['script', 'style'],
  // 链接只放行 http(s)：javascript:、data: 与站内相对跳转一律移除 href。
  onTagAttr(tag: string, name: string, value: string, isWhiteAttr: boolean) {
    if (isWhiteAttr && tag === 'a' && name === 'href' && !/^https?:\/\//i.test(value.trim())) return ''
    return undefined
  },
})

/** 回答只做展示，公式渲染不开启 KaTeX 的 HTML/链接信任开关。 */
const markdown = new MarkdownIt({
  html: false,
  linkify: false,
  breaks: true,
  highlight(code: string, language: string): string {
    if (language && hljs.getLanguage(language)) {
      try {
        return hljs.highlight(code, { language, ignoreIllegals: true }).value
      } catch {
        // 高亮失败时交给 MarkdownIt 默认转义，不放弃整段回答。
        return ''
      }
    }
    return ''
  },
})

interface Formula { placeholder: string; content: string; display: boolean }
/** 公式匹配按优先级排列：块级公式先于行内公式，避免 `$$` 被行内规则截断。 */
const FORMULA_PATTERNS = [
  { regex: /\$\$([\s\S]+?)\$\$/g, display: true },
  { regex: /\\\[([\s\S]+?)\\\]/g, display: true },
  { regex: /\$([^$\n]+?)\$/g, display: false },
  { regex: /\\\(([\s\S]+?)\\\)/g, display: false },
]

const ESCAPE_MAP: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

/** 公式渲染失败时只回显原文，不把异常内容拼进 DOM。 */
function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, char => ESCAPE_MAP[char] ?? char)
}

/** 每次渲染使用随机占位符前缀，回答文本无法伪造占位符换取公式标记注入。 */
function createPlaceholderPrefix(): string {
  return `KATEXTOKEN${Math.random().toString(36).slice(2, 10).toUpperCase()}`
}

/** 把公式替换为普通文本占位符，保证 Markdown 解析与清洗都不会破坏公式原文。 */
function extractFormulas(content: string, prefix: string): { text: string; formulas: Formula[] } {
  const formulas: Formula[] = []
  let text = content
  for (const { regex, display } of FORMULA_PATTERNS) {
    text = text.replace(regex, (_match: string, body: string) => {
      const placeholder = `${prefix}${display ? 'B' : 'I'}${formulas.length}`
      formulas.push({ placeholder, content: body, display })
      return placeholder
    })
  }
  return { text, formulas }
}

/** 公式由 KaTeX 生成，渲染失败时降级为原文文本。 */
function renderFormula(formula: Formula): string {
  try {
    return katex.renderToString(formula.content, {
      displayMode: formula.display,
      throwOnError: false,
      strict: false,
      trust: false,
    })
  } catch {
    return escapeHtml(formula.content)
  }
}

/** 渲染顺序固定：Markdown → 独立清洗 → 注入公式，清洗只作用于不可信部分。 */
function renderAnswer(content: string): string {
  if (!content) return ''
  const prefix = createPlaceholderPrefix()
  const { text, formulas } = extractFormulas(content, prefix)
  let html = answerSanitizer.process(markdown.render(text))
  for (const formula of formulas) {
    html = html.split(formula.placeholder).join(renderFormula(formula))
  }
  return html
}

const rootRef = ref<HTMLElement | null>(null)
/** 每帧最多渲染一次：流式增量密集到达时避免同一帧内重复解析整段回答。 */
let frameHandle = 0

function scheduleRender(): void {
  if (frameHandle) return
  frameHandle = window.requestAnimationFrame(() => {
    frameHandle = 0
    if (rootRef.value) rootRef.value.innerHTML = renderAnswer(props.content)
  })
}

onMounted(scheduleRender)
watch(() => props.content, scheduleRender)
onBeforeUnmount(() => {
  if (frameHandle) window.cancelAnimationFrame(frameHandle)
  frameHandle = 0
})
</script>

<style scoped>
/*
 * 回答排版样式。
 * 注入的 HTML 不携带 scoped 属性，因此统一通过 :deep() 命中。
 */
.ai-answer-viewer {
  font-size: 0.875rem;
  line-height: 1.7;
  color: var(--brand-ink, #333);
  overflow-wrap: anywhere;
}

.ai-answer-viewer :deep(> :first-child) {
  margin-top: 0;
}

.ai-answer-viewer :deep(> :last-child) {
  margin-bottom: 0;
}

.ai-answer-viewer :deep(p) {
  margin: 0.5rem 0;
}

.ai-answer-viewer :deep(h1),
.ai-answer-viewer :deep(h2),
.ai-answer-viewer :deep(h3),
.ai-answer-viewer :deep(h4),
.ai-answer-viewer :deep(h5),
.ai-answer-viewer :deep(h6) {
  margin: 0.75rem 0 0.375rem;
  font-weight: 600;
  line-height: 1.4;
}

.ai-answer-viewer :deep(h1) { font-size: 1.125rem; }
.ai-answer-viewer :deep(h2) { font-size: 1.0625rem; }
.ai-answer-viewer :deep(h3),
.ai-answer-viewer :deep(h4),
.ai-answer-viewer :deep(h5),
.ai-answer-viewer :deep(h6) { font-size: 1rem; }

.ai-answer-viewer :deep(ul),
.ai-answer-viewer :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}

.ai-answer-viewer :deep(ul) { list-style: disc; }
.ai-answer-viewer :deep(ol) { list-style: decimal; }
.ai-answer-viewer :deep(li) { margin: 0.25rem 0; }

.ai-answer-viewer :deep(blockquote) {
  margin: 0.5rem 0;
  padding: 0.25rem 0.75rem;
  border-left: 3px solid var(--brand-line, #e8dcc8);
  color: var(--brand-ink-soft, #666);
}

.ai-answer-viewer :deep(code) {
  padding: 0.1rem 0.3rem;
  border-radius: 0.25rem;
  background: #f3f4f6;
  font-size: 0.8125rem;
}

.ai-answer-viewer :deep(pre) {
  margin: 0.5rem 0;
  padding: 0.625rem 0.75rem;
  border-radius: 0.5rem;
  background: #f6f8fa;
  overflow-x: auto;
}

.ai-answer-viewer :deep(pre code) {
  padding: 0;
  background: transparent;
  font-size: 0.8125rem;
}

.ai-answer-viewer :deep(table) {
  margin: 0.5rem 0;
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.ai-answer-viewer :deep(th),
.ai-answer-viewer :deep(td) {
  padding: 0.375rem 0.5rem;
  border: 1px solid var(--brand-line, #e8dcc8);
  text-align: left;
}

.ai-answer-viewer :deep(a) {
  color: var(--brand-accent);
  text-decoration: underline;
}

/* 长公式不能撑破面板，横向滚动只作用于公式本身。 */
.ai-answer-viewer :deep(.katex-display) {
  margin: 0.5rem 0;
  overflow-x: auto;
  overflow-y: hidden;
}
</style>
