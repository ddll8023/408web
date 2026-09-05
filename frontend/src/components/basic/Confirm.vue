<template>
  <Dialog
    v-model:visible="visible"
    :title="state.title"
    aria-label="操作确认"
    width="420px"
    max-width="90vw"
    close-on-click-modal
    @close="handleCancel"
  >
    <div class="flex items-start gap-4">
      <div class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center" :class="iconBgClass">
        <font-awesome-icon :icon="icon" class="text-xl" :class="iconClass" aria-hidden="true" />
      </div>
      <p class="flex-1 m-0 text-gray-600 text-base whitespace-pre-wrap break-words">{{ state.message }}</p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-3">
        <button
          v-if="state.mode === 'confirm'"
          type="button"
          class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 focus-visible:ring-offset-2"
          @click="handleCancel"
        >
          {{ state.cancelText }}
        </button>
        <button
          type="button"
          class="px-4 py-2 text-white rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
          :class="confirmBtnClass"
          @click="handleConfirm"
        >
          {{ state.confirmText }}
        </button>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
/**
 * Confirm 确认/提示对话框组件
 * 通过 utils/confirm.ts 提供命令式调用，同时复用通用 Dialog 的可访问性和焦点管理。
 */
import { computed, reactive, ref } from 'vue'
import Dialog from './Dialog.vue'

export type ConfirmType = 'success' | 'warning' | 'danger' | 'info'
export type ConfirmMode = 'confirm' | 'alert'

export interface ConfirmOptions {
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  type?: ConfirmType
  mode?: ConfirmMode
}

const state = reactive<Required<ConfirmOptions>>({
  title: '提示',
  message: '确定要执行此操作吗？',
  confirmText: '确定',
  cancelText: '取消',
  type: 'warning',
  mode: 'confirm'
})

const visible = ref(false)

let onConfirmCallback: (() => void) | null = null
let onCancelCallback: (() => void) | null = null

const icon = computed(() => {
  const icons: Record<ConfirmType, string[]> = {
    success: ['fas', 'check'],
    warning: ['fas', 'exclamation-triangle'],
    danger: ['fas', 'trash'],
    info: ['fas', 'info']
  }
  return icons[state.type]
})

const iconBgClass = computed(() => {
  const classes: Record<ConfirmType, string> = {
    success: 'bg-green-100',
    warning: 'bg-yellow-100',
    danger: 'bg-red-100',
    info: 'bg-blue-100'
  }
  return classes[state.type]
})

const iconClass = computed(() => {
  const classes: Record<ConfirmType, string> = {
    success: 'text-green-600',
    warning: 'text-yellow-600',
    danger: 'text-red-600',
    info: 'text-blue-600'
  }
  return classes[state.type]
})

const confirmBtnClass = computed(() => {
  const classes: Record<ConfirmType, string> = {
    success: 'bg-green-600 hover:bg-green-700 focus-visible:ring-green-500',
    warning: 'bg-yellow-600 hover:bg-yellow-700 focus-visible:ring-yellow-500',
    danger: 'bg-red-600 hover:bg-red-700 focus-visible:ring-red-500',
    info: 'bg-blue-600 hover:bg-blue-700 focus-visible:ring-blue-500'
  }
  return classes[state.type]
})

const clearCallbacks = () => {
  onConfirmCallback = null
  onCancelCallback = null
}

const handleConfirm = () => {
  const callback = onConfirmCallback
  visible.value = false
  clearCallbacks()
  callback?.()
}

const handleCancel = () => {
  const callback = onCancelCallback
  visible.value = false
  clearCallbacks()
  callback?.()
}

const show = (
  options: ConfirmOptions = {},
  onConfirm: (() => void) | null = null,
  onCancel: (() => void) | null = null
) => {
  state.title = options.title ?? '提示'
  state.message = options.message ?? '确定要执行此操作吗？'
  state.confirmText = options.confirmText ?? '确定'
  state.cancelText = options.cancelText ?? '取消'
  state.type = options.type ?? 'warning'
  state.mode = options.mode ?? 'confirm'
  onConfirmCallback = onConfirm
  onCancelCallback = onCancel
  visible.value = true
}

defineExpose({ show })
</script>
