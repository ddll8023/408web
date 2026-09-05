<template>
  <teleport to="body">
    <transition name="dialog-fade">
      <dialog
        ref="dialogRef"
        v-if="visible"
        class="fixed inset-0 z-50 flex items-start justify-center w-full h-full m-0 p-0 border-0 bg-transparent"
        :open="visible"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="title || $slots.title ? titleId : undefined"
        :aria-label="!title && !$slots.title ? ariaLabel : undefined"
        @click.self="handleBackdropClick"
        @keydown="handleKeydown"
      >
        <!-- 遮罩层 -->
        <div
          class="fixed inset-0 bg-black/50 transition-opacity"
          @click="handleBackdropClick"
        />

        <!-- 弹窗主体 -->
        <div
          class="relative z-10 bg-white rounded-lg shadow-xl overflow-hidden"
          :class="containerClass"
          :style="containerStyle"
        >
          <!-- 头部 -->
          <div v-if="title || $slots.title" :id="titleId" class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <slot name="title">
              <h2 class="text-lg font-semibold text-gray-900">{{ title }}</h2>
            </slot>
            <button
              type="button"
              class="p-1 text-gray-400 hover:text-gray-600 transition-colors rounded hover:bg-gray-100"
              @click="handleClose"
              aria-label="关闭"
            >
                            <font-awesome-icon :icon="['fas', 'times']" class="text-lg" />
            </button>
          </div>

          <!-- 内容区 -->
          <div class="overflow-y-auto px-6 py-4" :style="contentStyle" :aria-busy="loading">
            <div v-if="loading" class="flex items-center justify-center p-8" role="status" aria-live="polite">
              <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-2xl text-primary-600" />
              <span class="ml-3 text-gray-500">加载中...</span>
            </div>
            <slot v-else />
          </div>

          <!-- 底部 -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <slot name="footer" />
          </div>
        </div>
      </dialog>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'

let nextDialogId = 0

const focusableSelector = [
  'a[href]',
  'area[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  'iframe',
  'object',
  'embed',
  '[contenteditable]',
  '[tabindex]:not([tabindex="-1"])'
].join(', ')

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  ariaLabel: {
    type: String,
    default: '对话框'
  },
  width: {
    type: String,
    default: '86%'
  },
  maxWidth: {
    type: String,
    default: '1200px'
  },
  top: {
    type: String,
    default: 'calc(60px + 24px)'  // 导航栏60px + 额外边距24px
  },
  loading: {
    type: Boolean,
    default: false
  },
  closeOnClickModal: {
    type: Boolean,
    default: false
  },
  closeOnPressEscape: {
    type: Boolean,
    default: true
  },
  destroyOnClose: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits<{ 'update:visible': [value: boolean]; close: [] }>()

const dialogRef = ref<HTMLDialogElement | null>(null)
const titleId = `dialog-title-${++nextDialogId}`
let previouslyFocused: HTMLElement | null = null
let previousBodyOverflow = ''

// 容器样式
const containerClass = computed(() => {
  return {
    'w-full': true
  }
})

const containerStyle = computed(() => ({
  width: props.width,
  maxWidth: props.maxWidth,
  marginTop: props.top
}))

const contentStyle = computed(() => ({
  maxHeight: `calc(100vh - ${props.top} - 140px)`
}))

// 关闭弹窗
const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

// 点击遮罩层关闭
const handleBackdropClick = () => {
  if (props.closeOnClickModal) {
    handleClose()
  }
}

const focusableElements = () => {
  const dialog = dialogRef.value
  if (!dialog || typeof dialog.querySelectorAll !== 'function') return []

  return Array.from(dialog.querySelectorAll<HTMLElement>(focusableSelector))
    .filter(element => element.offsetParent !== null || element === document.activeElement)
}

const focusInitialElement = () => {
  const dialog = dialogRef.value
  if (!dialog) return

  const target = focusableElements()[0] || dialog
  if (target === dialog) dialog.setAttribute('tabindex', '-1')
  target.focus()
}

const restoreFocus = () => {
  const target = previouslyFocused
  previouslyFocused = null
  if (target?.isConnected) target.focus()
}

// 键盘事件：支持 Escape 关闭，并将 Tab 焦点限制在当前弹窗内
const handleKeydown = (e: KeyboardEvent) => {
  if (!props.visible) return

  if (e.key === 'Escape' && props.closeOnPressEscape) {
    e.preventDefault()
    handleClose()
    return
  }

  if (e.key !== 'Tab') return

  const elements = focusableElements()
  if (elements.length === 0) {
    e.preventDefault()
    dialogRef.value?.focus()
    return
  }

  const first = elements[0]
  const last = elements[elements.length - 1]
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}

// 监听 visible 变化，处理 body 滚动锁、初始焦点和关闭后的焦点恢复
const syncVisibility = async (val: boolean) => {
  if (typeof document === 'undefined') return
  const body = document.body

  if (!body?.style) {
    if (!val) restoreFocus()
    return
  }

  if (val) {
    previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null
    previousBodyOverflow = body.style.overflow
    body.style.overflow = 'hidden'
    await nextTick()
    focusInitialElement()
  } else {
    body.style.overflow = previousBodyOverflow
    previousBodyOverflow = ''
    restoreFocus()
  }
}

watch(() => props.visible, (val) => {
  void syncVisibility(val)
}, { immediate: true })

onUnmounted(() => {
  if (typeof document !== 'undefined' && document.body?.style) {
    document.body.style.overflow = previousBodyOverflow
  }
  restoreFocus()
})
</script>

<style scoped>
dialog[open] {
  display: flex;
}

/* 过渡动画 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-active .bg-white,
.dialog-fade-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.dialog-fade-enter-from .bg-white,
.dialog-fade-leave-to .bg-white {
  transform: scale(0.95);
}
</style>
