<template>
  <div class="markdown-editor-split" :style="{ height: height }">
    <!-- 左侧：编辑区（纯编辑模式） -->
    <div class="editor-pane">
      <v-md-editor
        ref="editorRef"
        :model-value="modelValue"
        :height="height"
        :placeholder="placeholder"
        :left-toolbar="leftToolbar"
        :toolbar="customToolbar"
        mode="edit"
        @update:model-value="handleUpdate"
        @save="handleSave"
      ></v-md-editor>
    </div>
    
    <!-- 右侧：预览区（使用 MarkdownViewer，已验证正常） -->
    <div class="preview-pane">
      <div class="preview-header">
        <span>预览</span>
      </div>
      <div class="preview-content">
        <MarkdownViewer
          :content="localContent"
          variant="plain"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Markdown编辑器组件
 * 用于编辑Markdown内容，支持实时预览和数学公式渲染
 * 遵循KISS原则：功能简单清晰
 * 
 * Source: @kangc/v-md-editor 官方文档
 * KaTeX配置：markdown-it-katex 插件
 */
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { uploadImage, getImageUrl } from '@/api/upload'
import VMdEditor from '@kangc/v-md-editor'
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

// 注意：不再使用内置 KaTeX 插件，因为预览区改用 MarkdownViewer
// MarkdownViewer 已经包含正确的公式渲染逻辑

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
  }
})

/**
 * Emits定义
 */
const emit = defineEmits(['update:modelValue', 'save'])

/**
 * 编辑器引用
 */
const editorRef = ref(null)

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
        action(editor) {
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
        action(editor) {
          selectImageFile(editor)
        }
      }
    ]
  },
  formula: {
    title: '数学公式',
    icon: 'v-md-icon-formula',
    text: '公式',
    action(editor) {
      insertFormula(editor)
    }
  }
}

/**
 * 插入公式包裹
 * 智能判断：选中文本包含换行则使用块级公式，否则使用行内公式
 * @param {Object} editor - 编辑器实例
 */
const insertFormula = (editor) => {
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
const handleUpdate = (value) => {
  // DEBUG: 追踪更新
  console.log('[MarkdownEditor] handleUpdate:', {
    placeholder: props.placeholder?.substring(0, 20),
    valueLength: value?.length,
    localContentBefore: localContent.value?.length
  })
  localContent.value = value
  emit('update:modelValue', value)
}

/**
 * 处理保存（Ctrl+S快捷键触发）
 */
const handleSave = (text, html) => {
  emit('save', { text, html })
}


/**
 * 上传图片文件（核心上传逻辑，供按钮上传和粘贴上传共用）
 * 使用项目统一的 upload API，遵循 SOLID 原则
 * @param {File} file - 图片文件对象
 * @param {Object} editor - 编辑器实例
 * @returns {Promise<boolean>} 上传是否成功
 */
const uploadImageFile = async (file, editor) => {
  // 验证文件大小（100MB）
  if (file.size > 100 * 1024 * 1024) {
    alert('图片大小不能超过100MB')
    return false
  }

  try {
    // 调用统一的上传API（自动处理：Token、baseURL、错误拦截）
    const relativePath = await uploadImage(file)
    
    // 构建完整图片URL（使用环境变量配置的baseURL）
    const imageUrl = getImageUrl(relativePath)
    
    // 插入Markdown图片语法
    const imageSyntax = `![${file.name}](${imageUrl})`
    editor.insert(() => ({
      text: imageSyntax,
      selected: imageSyntax
    }))
    
    return true
  } catch (error) {
    // 错误已由 request.js 的拦截器统一处理（显示 ElMessage）
    console.error('图片上传失败:', error)
    return false
  }
}

/**
 * 选择并上传图片（通过文件选择器）
 * 打开文件选择对话框,上传到服务器后插入Markdown语法
 * @param {Object} editor - 编辑器实例
 */
const selectImageFile = (editor) => {
  // 创建文件输入元素
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/jpeg,image/jpg,image/png,image/gif,image/webp'
  
  input.onchange = async (e) => {
    const file = e.target.files[0]
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
const handlePaste = async (event) => {
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
  if (editorRef.value && editorRef.value.$el) {
    const editorElement = editorRef.value.$el
    editorElement.addEventListener('paste', handlePaste)
  }
})

/**
 * 组件卸载时移除粘贴事件监听
 */
onUnmounted(() => {
  if (editorRef.value && editorRef.value.$el) {
    const editorElement = editorRef.value.$el
    editorElement.removeEventListener('paste', handlePaste)
  }
})
</script>

<style scoped>
/**
 * Markdown编辑器组件样式（左右分栏布局）
 * 左侧：编辑区  右侧：预览区（使用 MarkdownViewer）
 * 已迁移至纯CSS，保留共享样式
 */

.markdown-editor-split {
  display: flex;
  width: 100%;
  gap: 0;
  border: 1px solid #dfe2e5;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.editor-pane {
  flex: 1;
  min-width: 0;
  height: 100%;
  border-right: 1px solid #dfe2e5;
}

.editor-pane :deep(.v-md-editor) {
  height: 100% !important;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.preview-pane {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #fff;
}

.preview-header {
  height: 40px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  background-color: #fff;
  border-bottom: 1px solid #dfe2e5;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.preview-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px;
}

/* 自定义滚动条样式 */
.preview-content::-webkit-scrollbar {
  width: 8px;
}

.preview-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.preview-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.preview-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 优化编辑器样式 */
:deep(.v-md-editor) {
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

/* 优化工具栏样式 */
:deep(.v-md-editor__toolbar) {
  background-color: #fff;
  border-bottom: 1px solid #dfe2e5;
}

/* 公式按钮图标样式 */
:deep(.v-md-icon-formula)::before {
  content: '∑';
  font-size: 18px;
  font-weight: bold;
}

/* 优化编辑区样式 */
:deep(.v-md-editor__left-area) {
  background-color: #fff;
}

/* 优化预览区样式 */
:deep(.v-md-editor__preview) {
  background-color: #fff;
}

/* 共享 Markdown 内容样式 */
:deep(.v-md-editor__preview) pre {
  border-radius: 4px;
  background-color: #efefef;
}

:deep(.v-md-editor__preview) table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

:deep(.v-md-editor__preview) table th,
:deep(.v-md-editor__preview) table td {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
}

:deep(.v-md-editor__preview) .katex {
  font-size: 1.1em;
}

:deep(.v-md-editor__preview) .katex-display {
  margin: 16px 0;
  overflow-x: auto;
  overflow-y: hidden;
}

:deep(.v-md-editor__preview) .katex-mathml {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: 0;
  padding: 0;
  overflow: hidden;
  clip: rect(1px, 1px, 1px, 1px);
  white-space: nowrap;
}

:deep(.v-md-editor__preview) svg {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 16px auto;
}

:deep(.v-md-editor__preview) .custom-svg-block {
  max-width: 100%;
  overflow: hidden;
  display: flex;
  justify-content: center;
  margin: 16px 0;
}

:deep(.v-md-editor__preview) .custom-svg-block svg {
  max-width: 100% !important;
  width: 100% !important;
  height: auto !important;
  display: block;
}

/* 滚动条样式 */
:deep(.v-md-editor__left-area-title),
:deep(.v-md-editor__preview-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}

:deep(.v-md-editor__left-area-title)::-webkit-scrollbar,
:deep(.v-md-editor__preview-wrapper)::-webkit-scrollbar {
  width: 8px;
}

:deep(.v-md-editor__left-area-title)::-webkit-scrollbar-track,
:deep(.v-md-editor__preview-wrapper)::-webkit-scrollbar-track {
  background: #f1f1f1;
}

:deep(.v-md-editor__left-area-title)::-webkit-scrollbar-thumb,
:deep(.v-md-editor__preview-wrapper)::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}
</style>

