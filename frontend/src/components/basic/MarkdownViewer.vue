<!-- 公共 Markdown 查看器：统一渲染公式与媒体，并在 DOM 就绪后交付带源码范围的预览快照。 -->
<template>
  <div
    ref="rootRef"
    class="markdown-viewer"
    :class="{ 'is-plain': variant === 'plain', 'is-option': contentRole === 'option' }"
    @load.capture="handleMediaLoad"
    @click.capture="handleMediaPreview"
    @keydown.capture="handleMediaPreview"
  >
    <v-md-preview
      :text="content"
      @change="handlePreviewChange"
    />
  </div>

  <ImageViewer
    :visible="interactive && Boolean(previewUrl)"
    :src="previewUrl"
    :alt="previewAlt"
    @close="closeMediaPreview"
  />
</template>

<script setup lang="ts">
/**
 * Markdown查看器组件
 * 用于渲染Markdown内容，支持数学公式渲染
 * 遵循KISS原则：功能简单清晰
 * 
 * Source: @kangc/v-md-editor 官方文档
 * 解析器保留公式原文及源码范围，安全清洗后生成公式 DOM，再发布同版本的预览快照
 */
import { ref, watch, nextTick, onBeforeUnmount, type PropType } from 'vue'
import VMdPreview from '@kangc/v-md-editor/lib/preview'
import '@kangc/v-md-editor/lib/style/preview.css'
// GitHub主题
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js'
import '@kangc/v-md-editor/lib/theme/style/github.css'
// 代码高亮
import hljs from 'highlight.js'
import 'katex/dist/katex.min.css'
import { configureMarkdownSourceMapping, renderParsedMarkdownMath, type MarkdownRenderSnapshot } from '@/utils/markdownSourceMapping'
// 共享的 XSS 白名单配置
import { getViewerWhitelist, configureSvgFence } from './config/xssWhitelist'
import { prepareMarkdownImage, prepareMarkdownMedia, type MarkdownContentRole } from '@/utils/markdownMedia'
import ImageViewer from './ImageViewer.vue'
import { useMarkdownMediaResize } from '@/composables/useMarkdownMediaResize'

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
    configureMarkdownSourceMapping(md)
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
  },
  /** 是否允许拖拽调整独立插图宽度；仅题干等题目展示场景开启。 */
  resizable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{ rendered: [snapshot: MarkdownRenderSnapshot] }>()
const rootRef = ref<HTMLElement | null>(null)
const mediaResize = useMarkdownMediaResize({ getRoot: () => rootRef.value })
let renderRevision = 0
let disposed = false

/** 清洗后的 DOM 提交后先完成公式和媒体，再通知滚动控制器测量，避免使用中间态高度。 */
const handlePreviewChange = (source: string) => {
  const revision = ++renderRevision
  nextTick(() => {
    if (disposed || revision !== renderRevision || source !== props.content) return
    const root = rootRef.value
    if (!root) return
    mediaResize.dispose()
    renderParsedMarkdownMath(root)
    prepareMedia()
    emit('rendered', { source, revision })
  })
}

const previewUrl = ref('')
const previewAlt = ref('')
let previewObjectUrl = ''

/** 关闭全屏查看并释放 SVG 临时资源，避免重复查看时累积 Blob。 */
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

/** DOM 提交后统一准备媒体，交互入口只添加到非链接插图。 */
const prepareMedia = () => {
  if (!rootRef.value) return
  for (const media of prepareMarkdownMedia(rootRef.value)) {
    if (!props.interactive || media.closest('a')) continue
    media.setAttribute('tabindex', '0')
    media.setAttribute('role', 'button')
    media.setAttribute('aria-label', `放大查看：${media.getAttribute('alt') || media.querySelector('title')?.textContent || '插图'}`)
    // 只有题目展示场景的正文独立大图可拖拽调尺寸；选项图与内联小图不挂把手
    if (props.resizable && media.classList.contains('markdown-media-block')) {
      mediaResize.attach(media)
    }
  }
}

/** 点击或按 Enter/空格打开全屏查看；拦截冒泡，避免同时触发选项作答。 */
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

// 同步作废尚未提交的通知，避免 A → B → A 的快速修改交付旧任务。
watch(() => props.content, () => {
  renderRevision += 1
  closeMediaPreview()
}, { flush: 'sync' })

onBeforeUnmount(() => {
  disposed = true
  renderRevision += 1
  mediaResize.dispose()
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

/* 以下为拖拽调尺寸相关样式，顺序需保持在 media-wide/media-inline 之后，
   才能用手动尺寸覆盖紧凑上限。 */
.markdown-viewer :deep(.markdown-media-frame) {
  position: relative;
  display: block;
  width: fit-content;
  max-width: 100%;
  margin: 0.75em auto;
  line-height: 0;
  border-radius: 4px;
}

/* 拖拽框架内的插图改用固定长度：min() 里一旦残留百分比，在 fit-content 中就是循环尺寸，
   外层会被原图宽度撑开，把手无法贴住图片右下角。容器约束改由 max-width 承担。 */
.markdown-viewer :deep(.markdown-media-frame > .markdown-media:not(.media-inline)) {
  width: min(
    var(--media-intrinsic-width, 9999px),
    var(--media-preferred-width, 9999px),
    var(--media-max-width, 9999px),
    calc(var(--media-max-height, 9999px) * var(--media-ratio, 1))
  ) !important;
  max-width: 100% !important;
  max-height: none !important;
  margin: 0 !important;
}

/* 手动调整过的图片解除紧凑上限，宽度只受容器约束（框架宽度由脚本同步设定） */
.markdown-viewer :deep(.markdown-media-frame > .markdown-media.media-manual:not(.media-inline)) {
  width: min(var(--media-preferred-width, 100%), 100%) !important;
  max-height: none !important;
}

.markdown-viewer :deep(.markdown-media-frame:hover),
.markdown-viewer :deep(.markdown-media-frame:focus-within) {
  outline: 1px dashed color-mix(in srgb, var(--brand-accent) 45%, transparent);
  outline-offset: 2px;
}

.markdown-viewer :deep(.markdown-media-frame.is-resizing) {
  outline-style: solid;
  outline-color: color-mix(in srgb, var(--brand-accent) 80%, transparent);
}

.markdown-viewer :deep(.markdown-media-size-tip) {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 6px);
  z-index: 1;
  padding: 2px 8px;
  border-radius: 4px;
  background-color: rgb(0 0 0 / 0.8);
  color: #fff;
  font-size: 12px;
  line-height: 1.5;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  opacity: 0;
  transform: translateX(-50%);
  transition: opacity 0.15s ease;
  pointer-events: none;
}

.markdown-viewer :deep(.markdown-media-size-tip.is-visible) {
  opacity: 1;
}

.markdown-viewer :deep(.markdown-media-handle),
.markdown-viewer :deep(.markdown-media-reset) {
  position: absolute;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  opacity: 0;
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.markdown-viewer :deep(.markdown-media-handle) {
  right: 3px;
  bottom: 3px;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  background-color: #8b6f47;
  color: #fff;
  cursor: nwse-resize;
  touch-action: none;
}

.markdown-viewer :deep(.markdown-media-handle svg) {
  width: 8px;
  height: 8px;
  fill: currentColor;
}

.markdown-viewer :deep(.markdown-media-reset) {
  /* 默认不可见且不可聚焦，避免空白按钮进入 Tab 顺序 */
  right: 21px;
  bottom: 3px;
  width: 20px;
  height: 20px;
  border: 1px solid color-mix(in srgb, var(--brand-accent) 35%, transparent);
  border-radius: 9999px;
  background-color: rgb(255 255 255 / 0.92);
  color: #8b6f47;
  cursor: pointer;
  visibility: hidden;
  pointer-events: none;
}

.markdown-viewer :deep(.markdown-media-reset svg) {
  width: 11px;
  height: 11px;
  fill: currentColor;
}

.markdown-viewer :deep(.markdown-media-frame:hover .markdown-media-handle),
.markdown-viewer :deep(.markdown-media-frame:focus-within .markdown-media-handle),
.markdown-viewer :deep(.markdown-media-frame.is-resizing .markdown-media-handle) {
  opacity: 1;
}

.markdown-viewer :deep(.markdown-media-frame.is-resizing .markdown-media-handle) {
  transform: scale(1.1);
}

.markdown-viewer :deep(.markdown-media-frame.is-customized:hover .markdown-media-reset),
.markdown-viewer :deep(.markdown-media-frame.is-customized:focus-within .markdown-media-reset) {
  visibility: visible;
  opacity: 1;
  pointer-events: auto;
}

.markdown-viewer :deep(.markdown-media-handle:hover),
.markdown-viewer :deep(.markdown-media-handle:focus-visible) {
  opacity: 1;
  outline: 2px solid #fff;
  outline-offset: 2px;
}

.markdown-viewer :deep(.markdown-media-reset:focus-visible) {
  opacity: 1;
  outline: 2px solid #8b6f47;
  outline-offset: 2px;
}

/* 到达宽度上下限时把手变淡，提示已到边界；置于悬停规则之后覆盖其不透明度 */
.markdown-viewer :deep(.markdown-media-frame.is-limit .markdown-media-handle) {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 触屏没有悬停状态，直接常显入口 */
@media (pointer: coarse) {
  .markdown-viewer :deep(.markdown-media-frame) {
    outline: 1px dashed color-mix(in srgb, var(--brand-accent) 30%, transparent);
    outline-offset: 2px;
  }

  .markdown-viewer :deep(.markdown-media-handle) {
    opacity: 0.85;
  }
}
</style>
