<template>
  <div
    ref="rootRef"
    class="markdown-viewer"
    :class="{ 'is-plain': variant === 'plain' }"
  >
    <!-- 使用 key 强制 v-md-preview 在内容变化时重新渲染 -->
    <v-md-preview 
      :key="previewKey"
      :text="safeContent" 
      @image-click="handleImageClick"
    ></v-md-preview>

    <!-- 图片预览组件 -->
    <el-image-viewer
      v-if="showImageViewer"
      :url-list="previewImages"
      :initial-index="initialIndex"
      @close="closeImageViewer"
    />
  </div>
  
</template>

<script setup>
/**
 * Markdown查看器组件
 * 用于渲染Markdown内容，支持数学公式渲染
 * 遵循KISS原则：功能简单清晰
 * 
 * Source: @kangc/v-md-editor 官方文档
 * KaTeX配置：markdown-it-katex 插件
 */
import { ref, watch, onMounted, nextTick, computed } from 'vue'
import { ElImageViewer } from 'element-plus'
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
  /**
   * 图片最大高度
   * 默认 400px，传入空字符串则不限制
   */
  maxImageHeight: {
    type: String,
    default: '400px'
  },
  /**
   * 是否启用图片点击预览
   */
  enableImagePreview: {
    type: Boolean,
    default: true
  }
})

const rootRef = ref(null)

// 图片预览状态
const showImageViewer = ref(false)
const previewImages = ref([])
const initialIndex = ref(0)

// 存储提取的公式
const mathExpressions = ref([])

/**
 * 公式提取与保护
 * 按优先级匹配：块级公式 → 行内公式
 * 使用唯一占位符替换，防止 Markdown 解析破坏
 */
const extractMath = (text) => {
  const expressions = []
  let index = 0
  
  // 占位符使用反引号包裹，Markdown 渲染为 <code> 标签
  const placeholder = (i, isBlock) => 
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
const renderMathToHtml = (content, display) => {
  try {
    // 预处理：将 KaTeX 不支持的语法转换为兼容格式
    let processed = content
      .replace(/@\{[^}]*\}/g, '')
      .replace(/\\\\?\s*\\hline\s*/g, '\\\\ \\hline ')
    
    return katex.renderToString(processed, {
      displayMode: display,
      throwOnError: false,
      strict: false,
      trust: true,
    })
  } catch (e) {
    return `<span class="katex-error">${escapeHtml(content)}</span>`
  }
}

/**
 * HTML 转义
 */
const escapeHtml = (text) => {
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
    console.log('[MarkdownViewer] processContent: empty content')
    return
  }
  
  const normalized = props.content.replace(/\\n/g, '\n')
  const { safeText, expressions } = extractMath(normalized)
  mathExpressions.value = expressions
  
  // DEBUG: 追踪 safeContent 更新
  console.log('[MarkdownViewer] processContent:', {
    propsContentLength: props.content?.length,
    safeTextLength: safeText?.length,
    safeContentBefore: safeContent.value?.length
  })
  
  safeContent.value = safeText
  
  // 递增 key 强制 v-md-preview 重新渲染
  previewKey.value++
  
  console.log('[MarkdownViewer] safeContent updated:', safeContent.value?.length, 'key:', previewKey.value)
}

/**
 * 处理图片点击事件
 * @param {Array} images 图片URL数组
 * @param {Number} index 当前点击的图片索引
 */
const handleImageClick = (images, index) => {
  if (!props.enableImagePreview || !images || images.length === 0) return
  
  previewImages.value = images
  initialIndex.value = index
  showImageViewer.value = true
}

const closeImageViewer = () => {
  showImageViewer.value = false
}

/**
 * 延迟执行公式恢复，等待 v-md-preview 完成渲染
 */
const delayedRestore = () => {
  nextTick(() => {
    // 增加延迟确保 v-md-preview 完成渲染
    setTimeout(restoreAndRenderMath, 100)
  })
}

// 监听内容变化，使用 flush: 'post' 确保在 DOM 更新后执行
watch(
  () => props.content,
  (newVal) => {
    // DEBUG: 追踪内容更新
    console.log('[MarkdownViewer] content changed:', {
      contentLength: newVal?.length,
      variant: props.variant
    })
    processContent()
    // 双重 nextTick 确保 v-md-preview 完成渲染
    nextTick(() => {
      nextTick(() => {
        setTimeout(restoreAndRenderMath, 100)
      })
    })
  },
  { immediate: true, flush: 'post' }
)
</script>

<style lang="scss" scoped>
/* 使用共享的 Markdown 样式 - @use 必须在最前面 */
@use './styles/markdown-shared' as md;

/**
 * Markdown查看器组件样式
 * 使用Sass变量统一管理主题
 * 注：变量和mixins已通过Vite全局注入，无需手动导入
 */

.markdown-viewer {
  width: 100%;
  min-height: 200px;
}

/* 优化Markdown渲染样式 */
:deep(.v-md-editor-preview) {
  background-color: $color-bg-white;
  padding: $spacing-sm;
  border-radius: $border-radius-base;
  
  // 图片样式优化
  img {
    max-width: 100%;
    height: auto;
    border-radius: $border-radius-small;
    
    // 限制最大高度，防止大图撑开
    @if (v-bind(maxImageHeight)) {
      max-height: v-bind(maxImageHeight);
      object-fit: contain; // 保持比例
    }
    
    // 启用预览时的鼠标样式
    &[src] {
      cursor: v-bind("enableImagePreview ? 'zoom-in' : 'default'");
      transition: transform 0.2s;
      
      &:hover {
        opacity: 0.95;
      }
    }
  }
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

/* 应用共享的 Markdown 样式 */
@include md.markdown-viewer-styles(':deep(.v-md-editor-preview)');
</style>

