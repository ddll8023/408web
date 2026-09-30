<!-- 公共 Markdown 编辑器：统一编辑、双栏与预览模式，选项使用紧凑布局，保留独立预览渲染。 -->
<template>
  <Teleport to="body" :disabled="!isFullscreen">
    <div
      ref="rootRef"
      v-bind="$attrs"
      :id="undefined"
      class="markdown-editor"
      :class="{ 'is-compact': contentRole === 'option', 'is-fullscreen': isFullscreen }"
      :style="isFullscreen ? undefined : { height }"
      :role="isFullscreen ? 'dialog' : 'group'"
      :aria-modal="isFullscreen || undefined"
      :aria-label="`${ariaLabel || 'Markdown'}编辑器`"
      @keydown="handleFullscreenKeydown"
    >
      <div class="editor-header">
        <span class="editor-heading">{{ ariaLabel || 'Markdown' }}<span v-if="ariaLabel" class="editor-format">Markdown</span></span>
        <div class="editor-view-controls" role="group" aria-label="编辑器视图">
          <button type="button" :aria-pressed="displayMode === 'edit'" @click="selectedMode = 'edit'">编辑</button>
          <button v-if="!isCompactViewport" type="button" :aria-pressed="displayMode === 'split'" @click="selectedMode = 'split'">双栏</button>
          <button type="button" :aria-pressed="displayMode === 'preview'" @click="selectedMode = 'preview'">预览</button>
          <button
            ref="fullscreenButtonRef"
            type="button"
            class="editor-fullscreen-button"
            :aria-label="isFullscreen ? '退出全屏' : '全屏编辑'"
            :title="isFullscreen ? '退出全屏（Esc）' : '全屏编辑'"
            :aria-pressed="isFullscreen"
            @click="isFullscreen = !isFullscreen"
          >
            <font-awesome-icon :icon="['fas', isFullscreen ? 'compress' : 'expand']" aria-hidden="true" />
          </button>
        </div>
      </div>
      <div class="editor-workspace" :class="`is-${displayMode}`" :style="{ '--editor-input-min-height': `${editorInputMinHeight}px` }">
        <!-- 使用 v-show 保留编辑实例，切换视图时不丢失撤销历史或光标状态。 -->
        <v-md-editor
          v-show="displayMode !== 'preview'"
          ref="editorRef"
          :model-value="modelValue"
          height="100%"
          :placeholder="placeholder"
          :left-toolbar="leftToolbar"
          right-toolbar="toc sync-scroll"
          :toolbar="customToolbar"
          mode="edit"
          @update:model-value="handleUpdate"
          @save="handleSave"
        />
        <div
          v-show="displayMode !== 'edit'"
          class="preview-pane"
          :style="{ top: displayMode === 'split' ? `${toolbarHeight}px` : '0', width: displayMode === 'split' ? `${previewWidth}px` : '100%' }"
          role="region"
          :aria-label="`${ariaLabel || '内容'}预览`"
          tabindex="0"
        >
          <div class="preview-content">
            <MarkdownViewer v-if="localContent.trim()" :content="localContent" variant="plain" :content-role="contentRole" />
            <p v-else class="preview-empty">输入内容后在这里查看排版、公式和图片。</p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * Markdown编辑器组件
 * 用于编辑Markdown内容，支持实时预览和数学公式渲染
 * 遵循KISS原则：功能简单清晰
 * 
 * Source: @kangc/v-md-editor 官方文档
 * KaTeX 由右侧 MarkdownViewer 统一预处理
 */
import { ref, computed, watch, nextTick, onMounted, onUpdated, onUnmounted, useAttrs, type PropType } from 'vue'
import { MEDIA_QUERIES } from '@/shared/responsive/breakpoints'
import { useMediaQuery } from '@/shared/responsive/useViewport'
import '@/styles/edit-form.css'

import type { MarkdownContentRole } from '@/utils/markdownMedia'
import { uploadImage } from '@/api/upload'
import VMdEditor, { type EditorInstance } from '@kangc/v-md-editor'
import '@kangc/v-md-editor/lib/style/base-editor.css'
// GitHub主题
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js'
import '@kangc/v-md-editor/lib/theme/style/github.css'
// 代码高亮
import hljs from 'highlight.js'
// 导入 MarkdownViewer（用于右侧预览）
import MarkdownViewer from './MarkdownViewer.vue'
// 共享的 XSS 白名单配置
import { getEditorWhitelist, configureSvgFence } from './config/xssWhitelist'

defineOptions({ inheritAttrs: false })

// 使用共享的 XSS 白名单配置（含 KaTeX 元素）
VMdEditor?.xss?.extend?.({
  whiteList: getEditorWhitelist(),
})

// 使用GitHub主题，并开启 markdown-it 的 HTML 支持
VMdEditor.use(githubTheme, {
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
   * Markdown文本内容（支持v-model）
   */
  modelValue: {
    type: String,
    default: ''
  },
  /**
   * 编辑器高度
   */
  height: {
    type: String,
    default: '600px'
  },
  /**
   * 占位符文本
   */
  placeholder: {
    type: String,
    default: '请输入内容...'
  },
  /** 选项编辑使用与阅读、复制相同的紧凑预览规则。 */
  contentRole: {
    type: String as PropType<MarkdownContentRole>,
    default: 'body'
  },
  // 编辑器的可访问名称
  ariaLabel: {
    type: String,
    default: ''
  }
})

/**
 * Emits定义
 */
const emit = defineEmits<{ 'update:modelValue': [value: string]; save: [content: {text: string; html: string}] }>()

/**
 * 编辑器引用
 */
const attrs = useAttrs()
const editorRef = ref<EditorInstance | null>(null)
const rootRef = ref<HTMLElement | null>(null)
const fullscreenButtonRef = ref<HTMLButtonElement | null>(null)
const isCompactViewport = useMediaQuery(MEDIA_QUERIES.compact)
const selectedMode = ref<'edit' | 'split' | 'preview' | null>(null)
const displayMode = computed(() => {
  const mode = selectedMode.value ?? (props.contentRole === 'option' || isCompactViewport.value ? 'edit' : 'split')
  return isCompactViewport.value && mode === 'split' ? 'edit' : mode
})
const isFullscreen = ref(false)
const toolbarHeight = ref(0)
const previewWidth = ref(0)
const editorInputMinHeight = ref(0)
let layoutObserver: ResizeObserver | null = null
let previousBodyOverflow = ''

// 全屏使用 Teleport 移出弹窗，避免被弹窗的裁剪和移动端变换限制。
watch(isFullscreen, async fullscreen => {
  if (fullscreen) {
    previousBodyOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = previousBodyOverflow
  }
  await nextTick()
  fullscreenButtonRef.value?.focus()
})

/** 全屏时独立处理退出和焦点循环，不触发父弹窗的关闭快捷键。 */
const handleFullscreenKeydown = (event: KeyboardEvent) => {
  if (!isFullscreen.value) return
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    isFullscreen.value = false
    return
  }
  if (event.key !== 'Tab') return
  const elements = Array.from(rootRef.value?.querySelectorAll<HTMLElement>(
    'button:not([disabled]), textarea, a[href], [tabindex="0"]'
  ) ?? []).filter(element => element.getClientRects().length > 0)
  const first = elements[0]
  const last = elements[elements.length - 1]
  if (!first || !last) return
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

/** 库不透传普通属性，因此把业务可访问名称设置到实际输入控件。 */
const syncInputLabel = () => {
  const input = editorRef.value?.$el.querySelector('textarea')
  if (!input) return
  input.setAttribute('aria-label', props.ariaLabel || 'Markdown 内容')
  // 外部 FormLabel 必须指向 textarea，不能把业务 ID 留在包装 div 上。
  if (typeof attrs.id === 'string') input.id = attrs.id
  else input.removeAttribute('id')
}
onUpdated(syncInputLabel)

/**
 * 本地内容状态
 * 用于实时同步到预览区，避免依赖 props 往返更新
 */
const localContent = ref(props.modelValue || '')

// 监听 props 变化，同步到本地状态（处理外部更新，如JSON导入）
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal !== localContent.value) {
      localContent.value = newVal || ''
    }
  },
  { immediate: true }
)

/**
 * 左侧工具栏配置
 * 移除默认image，使用自定义my-image按钮（包含下拉菜单）
 */
// 内置预览与全屏按钮只作用于库自身，由顶部模式栏统一接管外置预览。
const leftToolbar = 'undo redo clear | h bold italic strikethrough quote | ul ol table hr | link my-image code formula | save'

/**
 * 自定义工具栏按钮配置
 */
const customToolbar = {
  // 自定义image按钮（包含下拉菜单）
  'my-image': {
    title: '图片',
    icon: 'v-md-icon-img',
    menus: [
      {
        name: 'link-image',
        text: '链接图片',
        action(editor: EditorInstance) {
          // 插入图片链接模板
          editor.insert(() => ({
            text: '![图片描述](图片链接)',
            selected: '图片描述'
          }))
        }
      },
      {
        name: 'upload-image',
        text: '上传图片',
        action(editor: EditorInstance) {
          selectImageFile(editor)
        }
      }
    ]
  },
  formula: {
    title: '数学公式',
    icon: 'v-md-icon-formula',
    text: '公式',
    action(editor: EditorInstance) {
      insertFormula(editor)
    }
  }
}

/**
 * 插入公式包裹
 * 智能判断：选中文本包含换行则使用块级公式，否则使用行内公式
 * @param {Object} editor - 编辑器实例
 */
const insertFormula = (editor: EditorInstance) => {
  // 获取当前选中的文本
  const selectedText = editor.getCurrentSelectedStr() || ''
  
  // 获取编辑器引擎
  const editorEngine = editor.$refs.editorEgine
  if (!editorEngine) return

  // 获取当前光标位置
  const { start, end } = editorEngine.getRange()

  // 智能判断：如果选中文本包含换行符，使用块级公式；否则使用行内公式
  const isBlockFormula = selectedText.includes('\n')
  const wrapper = isBlockFormula ? '$$' : '$'
  
  // 如果选中文本已经包含公式包裹，则移除；否则添加
  let newText
  const trimmed = selectedText.trim()
  if (trimmed.startsWith('$') && trimmed.endsWith('$') && !trimmed.startsWith('$$')) {
    // 移除行内公式包裹
    newText = trimmed.slice(1, -1)
  } else if (trimmed.startsWith('$$') && trimmed.endsWith('$$')) {
    // 移除块级公式包裹
    newText = trimmed.slice(2, -2)
  } else {
    // 添加公式包裹
    newText = selectedText ? `${wrapper}${selectedText}${wrapper}` : `${wrapper} ${wrapper}`
  }

  // 使用编辑器的 replaceSelectionText 方法替换选中文本
  editor.replaceSelectionText(newText)

  // 调整光标位置
  if (selectedText) {
    // 如果有选中文本，光标放在公式包裹后
    const newStart = start + newText.length
    editorEngine.setRange({ start: newStart, end: newStart })
  } else {
    // 如果没有选中文本，光标放在公式包裹中间
    const newStart = start + wrapper.length + 1
    editorEngine.setRange({ start: newStart, end: newStart })
  }
}

/**
 * 处理内容更新
 * 同时更新本地状态（实时预览）和向父组件发出事件
 */
const handleUpdate = (value: string) => {
  localContent.value = value
  emit('update:modelValue', value)
}

/**
 * 处理保存（Ctrl+S快捷键触发）
 */
const handleSave = (text: string, html: string) => {
  emit('save', { text, html })
}


/**
 * 上传图片文件（核心上传逻辑，供按钮上传和粘贴上传共用）
 * 使用项目统一的 upload API，遵循 SOLID 原则
 * @param {File} file - 图片文件对象
 * @param {Object} editor - 编辑器实例
 * @returns {Promise<boolean>} 上传是否成功
 */
const uploadImageFile = async (file: File, editor: EditorInstance) => {
  // 验证文件大小（100MB）
  if (file.size > 100 * 1024 * 1024) {
    alert('图片大小不能超过100MB')
    return false
  }

  try {
    // 调用统一的上传API（自动处理：Token、baseURL、错误拦截）
    const relativePath = await uploadImage(file)
    
    // 保存后端返回的相对路径，避免把当前环境的域名和端口写入题目内容
    const imageSyntax = `![${file.name}](${relativePath})`
    editor.insert(() => ({
      text: imageSyntax,
      selected: imageSyntax
    }))
    
    return true
  } catch (error) {
    // 错误已由 request.ts 的拦截器统一处理（显示自定义 Toast）
    console.error('图片上传失败:', error)
    return false
  }
}

/**
 * 选择并上传图片（通过文件选择器）
 * 打开文件选择对话框,上传到服务器后插入Markdown语法
 * @param {Object} editor - 编辑器实例
 */
const selectImageFile = (editor: EditorInstance) => {
  // 创建文件输入元素
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/jpeg,image/jpg,image/png,image/gif,image/webp'
  
  input.onchange = async (e) => {
    const file = input.files?.[0]
    if (!file) return
    
    // 调用通用上传逻辑
    await uploadImageFile(file, editor)
  }

  // 触发文件选择
  input.click()
}

/**
 * 处理粘贴事件（支持粘贴图片上传）
 * @param {ClipboardEvent} event - 粘贴事件对象
 */
const handlePaste = async (event: ClipboardEvent) => {
  // 获取剪贴板数据
  const items = event.clipboardData?.items
  if (!items) return

  // 查找图片类型
  for (let item of items) {
    if (item.type.startsWith('image/')) {
      // 阻止默认粘贴行为（避免粘贴base64图片）
      event.preventDefault()
      
      // 获取图片文件
      const file = item.getAsFile()
      if (file && editorRef.value) {
        // 上传图片
        await uploadImageFile(file, editorRef.value)
      }
      break
    }
  }
}

/**
 * 组件挂载时添加粘贴事件监听
 */
onMounted(() => {
  const editorElement = editorRef.value?.$el
  if (!editorElement) return
  editorElement.addEventListener('paste', handlePaste)
  syncInputLabel()
  const toolbar = editorElement.querySelector<HTMLElement>('.v-md-editor__toolbar')
  const inputWrapper = editorElement.querySelector<HTMLElement>('.v-md-editor__editor-wrapper')
  const rightArea = editorElement.querySelector<HTMLElement>('.v-md-editor__right-area')
  if (toolbar && inputWrapper && rightArea) {
    // 同时观察工具栏与输入视口：换行、全屏和模式切换都可能改变可编辑高度。
    const syncLayout = () => {
      toolbarHeight.value = toolbar.offsetHeight
      editorInputMinHeight.value = inputWrapper.clientHeight
      // 大纲打开后右侧工作区会变窄，预览按真实工作区宽度定位。
      previewWidth.value = rightArea.clientWidth / 2
    }
    syncLayout()
    layoutObserver = new ResizeObserver(syncLayout)
    layoutObserver.observe(toolbar)
    layoutObserver.observe(inputWrapper)
  }
})

/** 卸载时清理监听器，并恢复全屏前的页面滚动状态。 */
onUnmounted(() => {
  editorRef.value?.$el.removeEventListener('paste', handlePaste)
  layoutObserver?.disconnect()
  if (isFullscreen.value) document.body.style.overflow = previousBodyOverflow
})
</script>

<style scoped>
.markdown-editor {
  display: flex;
  width: 100%;
  min-height: 140px;
  min-width: 0;
  flex-direction: column;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
}

.markdown-editor:focus-within {
  border-color: var(--brand-accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand-accent) 10%, transparent);
}

.markdown-editor.is-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 1400;
  height: 100dvh;
  border: 0;
  border-radius: 0;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
}

.editor-header {
  display: flex;
  min-height: 38px;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 8px 8px 0 0;
  background: #f9fafb;
  padding: 4px 10px;
}

.editor-heading {
  display: flex;
  min-width: 0;
  align-items: baseline;
  gap: 8px;
  overflow: hidden;
  color: var(--brand-ink);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.editor-format {
  color: var(--brand-ink-soft);
  font-size: 10px;
  font-weight: 400;
}

.editor-view-controls {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 2px;
}

.editor-view-controls button {
  border: 0;
  border-radius: 4px;
  background: transparent;
  padding: 4px 8px;
  color: var(--brand-ink-soft);
  font-size: 12px;
  line-height: 20px;
  cursor: pointer;
}

.editor-view-controls button:hover {
  background: #e5e7eb;
  color: var(--brand-ink);
}

.editor-view-controls button[aria-pressed='true'] {
  background: color-mix(in srgb, var(--brand-accent) 12%, #fff);
  color: var(--brand-accent-deep);
  font-weight: 600;
}

.editor-view-controls button:focus-visible,
.preview-pane:focus-visible {
  outline: 2px solid var(--brand-accent);
  outline-offset: -2px;
}

.editor-workspace {
  position: relative;
  flex: 1;
  min-height: 0;
  min-width: 0;
}

.editor-workspace :deep(.v-md-editor) {
  height: 100%;
  border: 0;
  border-radius: 0 0 8px 8px;
  box-shadow: none;
}

.editor-workspace :deep(.v-md-editor__right-area) {
  min-width: 0;
  min-height: 0;
}

.editor-workspace.is-split :deep(.v-md-editor__editor-wrapper) {
  flex: 0 0 50%;
  width: 50%;
}

/* 工具栏占满整行；允许换行，不用横向滚动容器裁剪下拉菜单。 */
.editor-workspace :deep(.v-md-editor__toolbar) {
  flex-shrink: 0;
  border-bottom: 1px solid #e5e7eb;
  background: #fff;
  padding: 4px 6px;
}

.editor-workspace :deep(.v-md-editor__toolbar-left-wrapper) {
  min-width: 0;
}

.editor-workspace :deep(.v-md-editor__toolbar-item) {
  border-radius: 4px;
  color: var(--brand-ink-soft);
}

.editor-workspace :deep(.v-md-editor__toolbar-item:hover),
.editor-workspace :deep(.v-md-editor__toolbar-item--active) {
  background: color-mix(in srgb, var(--brand-accent) 9%, #fff);
  color: var(--brand-accent-deep);
}

.editor-workspace :deep(.v-md-editor__toolbar-divider) {
  margin-right: 7px;
  margin-left: 7px;
}

.editor-workspace :deep(.v-md-icon-formula)::before {
  content: '∑';
  font-size: 16px;
  font-weight: 600;
}

/* 库只在 height 属性变化时更新镜像最小高度；全屏与工具栏换行改用真实输入视口高度。 */
.editor-workspace :deep(.v-md-textarea-editor pre) {
  min-height: var(--editor-input-min-height) !important;
}

/* 镜像 pre 与 textarea 必须共享字体和间距，否则光标与滚动高度会错位。 */
.editor-workspace :deep(.v-md-textarea-editor pre),
.editor-workspace :deep(.v-md-textarea-editor textarea) {
  padding: 14px 16px;
  color: var(--brand-ink);
  font-family: ui-monospace, SFMono-Regular, Consolas, 'Microsoft YaHei', monospace;
  font-size: 14px;
  line-height: 1.7;
}

.preview-pane {
  position: absolute;
  right: 0;
  bottom: 0;
  display: flex;
  width: 100%;
  min-height: 0;
  flex-direction: column;
  border-radius: 0 0 8px 8px;
  background: #fff;
}

.is-split .preview-pane {
  width: 50%;
  border-left: 1px solid #e5e7eb;
  border-bottom-left-radius: 0;
}

.preview-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: #c5c8cc #f9fafb;
  padding: 12px 16px;
}

.preview-empty {
  margin: 0;
  color: var(--brand-ink-soft);
  font-size: 12px;
  line-height: 1.7;
}

.is-compact .editor-header {
  min-height: 30px;
  padding: 2px 8px;
}

.is-compact .editor-view-controls button {
  padding: 2px 6px;
}

.is-compact .editor-format {
  display: none;
}

.is-compact .editor-workspace :deep(.v-md-editor__toolbar) {
  padding: 2px 4px;
}

.is-compact .editor-workspace :deep(.v-md-editor__toolbar-item) {
  height: 24px;
  margin-left: 2px;
  padding: 0 4px;
  font-size: 13px;
  line-height: 24px;
}

.is-compact .editor-workspace :deep(.v-md-editor__toolbar-divider) {
  height: 24px;
  margin-right: 4px;
  margin-left: 4px;
}

.is-compact .editor-workspace :deep(.v-md-textarea-editor pre),
.is-compact .editor-workspace :deep(.v-md-textarea-editor textarea),
.is-compact .preview-content {
  padding: 8px 10px;
}

@media (max-width: 767px) {
  /* 手机工具栏换行时保证至少一行正文可见，不强行挤进桌面端的 140px。 */
  .markdown-editor.is-compact {
    min-height: 180px;
  }

  .editor-format {
    display: none;
  }

  .editor-workspace :deep(.v-md-textarea-editor pre),
  .editor-workspace :deep(.v-md-textarea-editor textarea) {
    font-size: 16px;
  }
}
</style>
