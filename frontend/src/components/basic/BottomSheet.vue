<!-- 通用底部抽屉：移动端导航与筛选面板共用的弹层，负责遮罩、滚动锁、焦点和底部安全区。 -->
<template>
  <teleport to="body">
    <transition name="bottom-sheet">
      <div
        v-if="visible"
        class="bottom-sheet"
        role="presentation"
        @click.self="handleBackdropClick"
      >
        <section
          ref="panelRef"
          class="bottom-sheet__panel"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="title ? titleId : undefined"
          :aria-label="title ? undefined : ariaLabel"
          :style="{ maxHeight }"
          tabindex="-1"
          @keydown="handleKeydown"
        >
          <span class="bottom-sheet__handle" aria-hidden="true" />

          <header class="bottom-sheet__header">
            <slot name="header">
              <h2 :id="titleId" class="bottom-sheet__title">{{ title }}</h2>
            </slot>
            <button type="button" class="bottom-sheet__close" aria-label="关闭" @click="handleClose">
              <font-awesome-icon :icon="['fas', 'times']" aria-hidden="true" />
            </button>
          </header>

          <div class="bottom-sheet__body scrollbar-stable">
            <slot />
          </div>

          <div v-if="$slots.footer" class="bottom-sheet__footer">
            <slot name="footer" />
          </div>
        </section>
      </div>
    </transition>
  </teleport>
</template>

<script setup lang="ts">
/**
 * 底部抽屉组件
 * 关闭时不挂载插槽内容，避免被隐藏的导航列表继续占用渲染开销；
 * 遮罩层与全局导航的层级关系固定为低于 Dialog（1100），高于全站导航（1000）
 */
import { nextTick, onUnmounted, ref, watch } from 'vue'

const focusableSelector = [
  'button:not([disabled])',
  'a[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])'
].join(', ')

let nextSheetId = 0

const props = defineProps({
  // 是否显示抽屉
  visible: {
    type: Boolean,
    default: false
  },
  // 抽屉标题，同时作为可访问名称
  title: {
    type: String,
    default: ''
  },
  // 无标题时使用的可访问名称
  ariaLabel: {
    type: String,
    default: '底部面板'
  },
  // 面板最大高度，默认不超过视口七成并兼容动态视口单位
  maxHeight: {
    type: String,
    default: 'min(70dvh, 640px)'
  },
  // 是否允许点击遮罩关闭
  closeOnBackdrop: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits<{ 'update:visible': [value: boolean]; close: [] }>()

const panelRef = ref<HTMLElement | null>(null)
const titleId = `bottom-sheet-title-${++nextSheetId}`
let previouslyFocused: HTMLElement | null = null
let previousBodyOverflow = ''

const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

const handleBackdropClick = () => {
  if (props.closeOnBackdrop) handleClose()
}

const focusableElements = () => {
  const elements = panelRef.value?.querySelectorAll<HTMLElement>(focusableSelector)
  return elements ? Array.from(elements) : []
}

// 键盘事件：Escape 关闭，Tab 焦点限制在面板内部
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    event.preventDefault()
    handleClose()
    return
  }

  if (event.key !== 'Tab') return

  const elements = focusableElements()
  if (elements.length === 0) {
    event.preventDefault()
    panelRef.value?.focus()
    return
  }

  const first = elements[0]
  const last = elements[elements.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

const restoreFocus = () => {
  const target = previouslyFocused
  previouslyFocused = null
  if (target?.isConnected) target.focus()
}

// 打开期间锁定页面滚动并转移焦点，关闭后恢复原焦点
const syncVisibility = async (visible: boolean) => {
  if (typeof document === 'undefined') return
  const body = document.body

  if (!body?.style) {
    if (!visible) restoreFocus()
    return
  }

  if (visible) {
    previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null
    previousBodyOverflow = body.style.overflow
    body.style.overflow = 'hidden'
    await nextTick()
    panelRef.value?.focus()
  } else {
    body.style.overflow = previousBodyOverflow
    previousBodyOverflow = ''
    restoreFocus()
  }
}

watch(() => props.visible, (visible) => {
  void syncVisibility(visible)
}, { immediate: true })

onUnmounted(() => {
  if (typeof document !== 'undefined' && document.body?.style) {
    document.body.style.overflow = previousBodyOverflow
  }
})
</script>

<style scoped>
.bottom-sheet {
  position: fixed;
  inset: 0;
  z-index: 1050;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  background: rgba(27, 35, 35, 0.42);
}

.bottom-sheet__panel {
  display: flex;
  max-height: 70vh;
  flex-direction: column;
  overflow: hidden;
  border-radius: 16px 16px 0 0;
  outline: none;
  background: #fffdf8;
  box-shadow: 0 -18px 48px rgba(30, 42, 39, 0.18);
  padding-bottom: env(safe-area-inset-bottom);
}

.bottom-sheet__handle {
  width: 36px;
  height: 4px;
  flex: 0 0 auto;
  align-self: center;
  margin-top: 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--brand-accent) 25%, transparent);
}

.bottom-sheet__header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid #ece5db;
}

.bottom-sheet__title {
  margin: 0;
  min-width: 0;
  overflow: hidden;
  color: var(--brand-ink);
  font-size: 15px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bottom-sheet__close {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 10px;
  background: color-mix(in srgb, var(--brand-accent) 8%, transparent);
  color: #8b6f47;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.bottom-sheet__close:hover,
.bottom-sheet__close:focus-visible {
  background: color-mix(in srgb, var(--brand-accent) 16%, transparent);
  outline: none;
}

.bottom-sheet__body {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 12px 16px 16px;
}

.bottom-sheet__footer {
  flex: 0 0 auto;
  border-top: 1px solid #ece5db;
  padding: 10px 16px;
}

.bottom-sheet-enter-active,
.bottom-sheet-leave-active {
  transition: background-color 0.24s ease;
}

.bottom-sheet-enter-active .bottom-sheet__panel,
.bottom-sheet-leave-active .bottom-sheet__panel {
  transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.bottom-sheet-enter-from,
.bottom-sheet-leave-to {
  background: rgba(27, 35, 35, 0);
}

.bottom-sheet-enter-from .bottom-sheet__panel,
.bottom-sheet-leave-to .bottom-sheet__panel {
  transform: translateY(100%);
}

@media (prefers-reduced-motion: reduce) {
  .bottom-sheet-enter-active,
  .bottom-sheet-leave-active,
  .bottom-sheet-enter-active .bottom-sheet__panel,
  .bottom-sheet-leave-active .bottom-sheet__panel {
    transition: none;
  }
}
</style>
