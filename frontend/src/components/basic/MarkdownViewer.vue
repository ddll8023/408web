<template>
  <div
    ref="rootRef"
    class="markdown-viewer"
    :class="{ 'is-plain': variant === 'plain', 'is-option': contentRole === 'option' }"
    @load.capture="handleMediaLoad"
    @click.capture="handleMediaPreview"
    @keydown.capture="handleMediaPreview"
  >
    <!-- 使用 key 强制 v-md-preview 在内容变化时重新渲染 -->
    <v-md-preview
      :key="previewKey"
      :text="safeContent"
    ></v-md-preview>
  </div>

  <Dialog
    v-if="interactive && previewUrl"
    :visible="true"
    title="插图原尺寸预览（可滚动查看）"
    :close-on-click-modal="true"
    @close="closeMediaPreview"
  >
    <div class="media-preview-content">
      <img :src="previewUrl" :alt="previewAlt" />
    </div>
  </Dialog>
</template>

<script setup lang="ts">
/**
 * Markdown查看器组件
 * 用于渲染Markdown内容，支持数学公式渲染
 * 遵循KISS原则：功能简单清晰
 * 
 * Source: @kangc/v-md-editor 官方文档
 * KaTeX 通过组件内预处理完成公式渲染
 */
import { ref, watch, nextTick, onBeforeUnmount, type PropType } from 'vue'
import VMdPreview from '@kangc/v-md-editor/lib/preview'
import '@kangc/v-md-editor/lib/style/preview.css'
// GitHub主题
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js'
import '@kangc/v-md-editor/lib/theme/style/github.css'
// 代码高亮
import hljs from 'highlight.js'
// 数学公式支持（KaTeX）- 使用预处理保护方案
import katex from 'katex'
import 'katex/dist/katex.min.css'
// 共享的 XSS 白名单配置
import { getViewerWhitelist, configureSvgFence } from './config/xssWhitelist'
import { normalizeImageUrls } from '@/api/upload'
import { prepareMarkdownImage, prepareMarkdownMedia, type MarkdownContentRole } from '@/utils/markdownMedia'
import Dialog from './Dialog.vue'

// 使用共享的 XSS 白名单配置
VMdPreview?.xss?.extend?.({
  whiteList: getViewerWhitelist(),
})

// 使用GitHub主题
VMdPreview.use(githubTheme, {
  Hljs: hljs,
  extend(md) {
    md.set({ html: true })
    // 使用共享的 SVG 代码块渲染配置
    configureSvgFence(md)
  },
})

/**
 * Props定义
 */
const props = defineProps({
  /**
   * Markdown文本内容
   */
  content: {
    type: String,
    default: ''
  },
  /**
   * 展示变体：
   * - card：默认，带背景与内边距
   * - plain：无背景与内边距，用于嵌入到卡片/列表行内部
   */
  variant: {
    type: String,
    default: 'card'
  },
  /** 内容角色决定统一字号和插图上限，阅读、预览和复制使用相同规则。 */
  contentRole: {
    type: String as PropType<MarkdownContentRole>,
    default: 'body'
  },
  /** 隐藏的图片复制节点不创建可交互的媒体或预览弹窗。 */
  interactive: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits<{ rendered: [] }>()
const rootRef = ref<HTMLElement | null>(null)

// 存储提取的公式
interface MathExpression { placeholder: string; content: string; display: boolean; original: string }
const mathExpressions = ref<MathExpression[]>([])

/**
 * 公式提取与保护
 * 按优先级匹配：块级公式 → 行内公式
 * 使用唯一占位符替换，防止 Markdown 解析破坏
 */
const extractMath = (text: string) => {
  const expressions: MathExpression[] = []
  let index = 0
  
  // 占位符使用反引号包裹，Markdown 渲染为 <code> 标签
  const placeholder = (i: number, isBlock: boolean) =>
    `\`KATEX${isBlock ? 'B' : 'I'}${i}PH\``
  
  // 正则模式（按优先级排序）
  const patterns = [
    { regex: /\$\$([\s\S]+?)\$\$/g, display: true },
    { regex: /\\\[([\s\S]+?)\\\]/g, display: true },
    { regex: /\$([^\$\n]+?)\$/g, display: false },
    { regex: /\\\(([\s\S]+?)\\\)/g, display: false },
  ]
  
  let result = text
  
  for (const { regex, display } of patterns) {
    result = result.replace(regex, (match, content) => {
      const ph = placeholder(index, display)
      expressions.push({
        placeholder: ph,
        content: content,
        display: display,
        original: match
      })
      index++
      return ph
    })
  }
  
  return { safeText: result, expressions }
}

/**
 * 将公式内容渲染为 HTML 字符串
 */
const renderMathToHtml = (content: string, display: boolean) => {
  try {
    // 预处理：将 KaTeX 不支持的语法转换为兼容格式
    let processed = content
      .replace(/@\{[^}]*\}/g, '')
      .replace(/\\\\?\s*\\hline\s*/g, '\\\\ \\hline ')
    
    return katex.renderToString(processed, {
      displayMode: display,
      throwOnError: false,
      strict: false,
      trust: false,
    })
  } catch (e) {
    return `<span class="katex-error">${escapeHtml(content)}</span>`
  }
}

/**
 * HTML 转义
 */
const escapeHtml = (text: string) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * 在 DOM 中恢复公式并渲染
 */
const restoreAndRenderMath = () => {
  if (!rootRef.value || mathExpressions.value.length === 0) return
  
  const container = rootRef.value.querySelector('.v-md-editor-preview') || rootRef.value
  
  let html = container.innerHTML
  
  for (const expr of mathExpressions.value) {
    const wrapperClass = expr.display ? 'katex-display-wrapper' : 'katex-inline-wrapper'
    const renderedMath = renderMathToHtml(expr.content, expr.display)
    const replacement = `<span class="${wrapperClass}">${renderedMath}</span>`
    
    const placeholderText = expr.placeholder.replace(/`/g, '')
    const codeTagPattern = new RegExp(`<code[^>]*>${placeholderText}</code>`, 'g')
    
    html = html.replace(codeTagPattern, replacement)
  }
  
  container.innerHTML = html
}

// 安全内容（公式已替换为占位符）
const safeContent = ref('')

// 用于强制 v-md-preview 重新渲染的 key
const previewKey = ref(0)

/**
 * 处理内容变化：提取公式并生成安全内容
 */
const processContent = () => {
  if (!props.content) {
    safeContent.value = ''
    mathExpressions.value = []
    return
  }
  
  const normalized = normalizeImageUrls(props.content.replace(/\\n/g, '\n'))
  const { safeText, expressions } = extractMath(normalized)
  mathExpressions.value = expressions
  
  safeContent.value = safeText

  // 递增 key 强制 v-md-preview 重新渲染
  previewKey.value++
}

const previewUrl = ref('')
const previewAlt = ref('')
let previewObjectUrl = ''

/** 关闭原图预览并释放 SVG 临时资源，避免重复查看时累积 Blob。 */
const closeMediaPreview = () => {
  previewUrl.value = ''
  if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl)
  previewObjectUrl = ''
}

/** 插图加载后更新真实宽高比；不处理 SVG 内部图片或 KaTeX 的内部节点。 */
const handleMediaLoad = (event: Event) => {
  const image = event.target
  if (image instanceof HTMLImageElement && image.classList.contains('markdown-media')) {
    prepareMarkdownImage(image)
  }
}

/** 媒体尺寸在公式恢复后统一处理，交互入口只添加到非链接插图。 */
const prepareMedia = () => {
  if (!rootRef.value) return
  for (const media of prepareMarkdownMedia(rootRef.value)) {
    if (!props.interactive || media.closest('a')) continue
    media.setAttribute('tabindex', '0')
    media.setAttribute('role', 'button')
    media.setAttribute('aria-label', `放大查看：${media.getAttribute('alt') || media.querySelector('title')?.textContent || '插图'}`)
  }
}

/** 点击或按 Enter/空格查看原尺寸；拦截冒泡，避免同时触发选项作答。 */
const handleMediaPreview = (event: MouseEvent | KeyboardEvent) => {
  if (!props.interactive || !(event.target instanceof Element)) return
  if (event instanceof KeyboardEvent && !['Enter', ' '].includes(event.key)) return
  const media = event.target.closest('.markdown-media')
  if (!media || media.closest('a')) return

  event.preventDefault()
  event.stopPropagation()
  closeMediaPreview()
  previewAlt.value = media.getAttribute('alt') || media.querySelector('title')?.textContent || '插图'

  if (media instanceof HTMLImageElement) {
    previewUrl.value = media.currentSrc || media.src
  } else if (media instanceof SVGSVGElement) {
    // 克隆已清洗的 SVG，以 img 加载，既保留独立坐标系，也不执行 SVG 内交互内容。
    const clone = media.cloneNode(true) as SVGSVGElement
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    clone.removeAttribute('class')
    clone.removeAttribute('tabindex')
    clone.removeAttribute('role')
    clone.style.width = `${media.getAttribute('width')}px`
    clone.style.height = `${media.getAttribute('height')}px`
    clone.style.maxWidth = 'none'
    clone.style.maxHeight = 'none'
    clone.style.fontFamily = getComputedStyle(media).fontFamily
    clone.style.fontSize = getComputedStyle(media).fontSize
    const serialized = new XMLSerializer().serializeToString(clone)
    previewObjectUrl = URL.createObjectURL(new Blob([serialized], { type: 'image/svg+xml' }))
    previewUrl.value = previewObjectUrl
  }
}

/**
 * 延迟执行公式恢复，等待 v-md-preview 完成渲染
 */
let renderTimer: ReturnType<typeof setTimeout> | undefined

const delayedRestore = () => {
  nextTick(() => {
    if (renderTimer) clearTimeout(renderTimer)
    // 增加延迟确保 v-md-preview 完成渲染
    renderTimer = setTimeout(() => {
      renderTimer = undefined
      restoreAndRenderMath()
      prepareMedia()
      emit('rendered')
    }, 100)
  })
}

// 监听内容变化，使用 flush: 'post' 确保在 DOM 更新后执行
watch(
  () => props.content,
  () => {
    closeMediaPreview()
    processContent()
    // 双重 nextTick 确保 v-md-preview 完成渲染
    delayedRestore()
  },
  { immediate: true, flush: 'post' }
)

onBeforeUnmount(() => {
  if (renderTimer) clearTimeout(renderTimer)
  closeMediaPreview()
})
</script>

<style scoped>
/* Markdown查看器组件样式 */

.markdown-viewer {
  --content-font-size: 16px;
  --media-max-width: calc(24 * var(--content-font-size));
  --media-max-height: calc(18 * var(--content-font-size));
  width: 100%;
  min-width: 0;
  min-height: 200px;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
  font-size: var(--content-font-size);
  line-height: 1.6;
}

.markdown-viewer.is-option {
  --content-font-size: 14px;
  --media-max-width: calc(10 * var(--content-font-size));
  --media-max-height: calc(8 * var(--content-font-size));
  line-height: 1.5;
}

.markdown-viewer :deep(.github-markdown-body) {
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
}

/* 优化Markdown渲染样式 */
:deep(.v-md-editor-preview) {
  background-color: #fff;
  padding: 16px;
  border-radius: 4px;
}

/* plain 变体：用于嵌入式场景，去除额外留白与背景 */
.markdown-viewer.is-plain {
  min-height: auto;
}

.markdown-viewer.is-plain :deep(.v-md-editor-preview) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
}

/* 只约束标记过的内容插图；以真实比例同时收缩盒子的宽高，不波及 KaTeX SVG。
   important 仅用于收敛原文内联尺寸，单图覆盖统一走 width + media-wide/media-inline。 */
.markdown-viewer :deep(.markdown-media) {
  display: inline-block;
  width: min(var(--media-intrinsic-width, 100%), var(--media-preferred-width, 100%), 100%, var(--media-max-width), calc(var(--media-max-height) * var(--media-ratio, 1))) !important;
  height: auto !important;
  max-width: 100% !important;
  max-height: var(--media-max-height) !important;
  object-fit: contain;
  vertical-align: middle;
}

.markdown-viewer :deep(.markdown-media-block) {
  display: block;
  margin: 0.75em auto;
}

.markdown-viewer.is-option :deep(.markdown-media-block) {
  margin: 0.25em 0;
}

.markdown-viewer.is-option :deep(p) {
  margin: 0.35em 0;
}

.markdown-viewer.is-option :deep(p:first-child) {
  margin-top: 0;
}

.markdown-viewer.is-option :deep(p:last-child) {
  margin-bottom: 0;
}

/* 密集图主动选择宽图时解除紧凑上限，但仍不超过容器或原图宽度。 */
.markdown-viewer :deep(.markdown-media.media-wide:not(.media-inline)) {
  width: min(var(--media-intrinsic-width, 100%), var(--media-preferred-width, 100%), 100%) !important;
  max-height: none !important;
}

.markdown-viewer :deep(.markdown-media.media-inline) {
  --media-max-width: 100%;
  --media-max-height: calc(1.4 * var(--content-font-size));
  display: inline-block;
  margin: 0 0.15em;
  vertical-align: -0.2em;
}

.markdown-viewer :deep(.markdown-media[role='button']) {
  cursor: zoom-in;
}

.markdown-viewer :deep(.markdown-media:focus-visible) {
  outline: 2px solid #8b6f47;
  outline-offset: 3px;
}

.media-preview-content {
  overflow: auto;
}

.media-preview-content img {
  display: block;
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
}
</style>
