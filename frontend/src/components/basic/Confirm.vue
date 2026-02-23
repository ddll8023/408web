<template>
  <teleport to="body">
    <transition name="modal">
      <div
        v-if="visible"
        class="fixed inset-0 z-[9999] flex items-center justify-center"
      >
        <!-- 遮罩 -->
        <div class="absolute inset-0 bg-black/50" @click="handleCancel" />

        <!-- 对话框 -->
        <div class="relative bg-white rounded-lg shadow-xl w-[400px] max-w-[90%] p-6">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center" :class="iconBgClass">
              <font-awesome-icon :icon="icon" class="text-xl" :class="iconClass" />
            </div>
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ title }}</h3>
              <p class="text-gray-600 text-base">{{ message }}</p>
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6">
            <button
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              @click="handleCancel"
            >
              {{ cancelText }}
            </button>
            <button
              class="px-4 py-2 text-white rounded-lg transition-colors"
              :class="confirmBtnClass"
              @click="handleConfirm"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
/**
 * Confirm 确认对话框组件
 */
import { ref, computed, reactive } from 'vue'

const props = reactive({
  title: '提示',
  message: '确定要执行此操作吗？',
  confirmText: '确定',
  cancelText: '取消',
  type: 'warning'
})

const visible = ref(false)

// 回调函数
let onConfirmCallback = null
let onCancelCallback = null

const icon = computed(() => {
  const icons = {
    success: ['fas', 'check'],
    warning: ['fas', 'exclamation-triangle'],
    danger: ['fas', 'trash'],
    info: ['fas', 'info']
  }
  return icons[props.type] || icons.info
})

const iconBgClass = computed(() => {
  const classes = {
    success: 'bg-green-100',
    warning: 'bg-yellow-100',
    danger: 'bg-red-100',
    info: 'bg-blue-100'
  }
  return classes[props.type] || classes.info
})

const iconClass = computed(() => {
  const classes = {
    success: 'text-green-600',
    warning: 'text-yellow-600',
    danger: 'text-red-600',
    info: 'text-blue-600'
  }
  return classes[props.type] || classes.info
})

const confirmBtnClass = computed(() => {
  const classes = {
    success: 'bg-green-600 hover:bg-green-700',
    warning: 'bg-yellow-600 hover:bg-yellow-700',
    danger: 'bg-red-600 hover:bg-red-700',
    info: 'bg-blue-600 hover:bg-blue-700'
  }
  return classes[props.type] || classes.info
})

const show = (options = {}, onConfirm, onCancel) => {
  props.title = options.title || '提示'
  props.message = options.message || '确定要执行此操作吗？'
  props.confirmText = options.confirmText || '确定'
  props.cancelText = options.cancelText || '取消'
  props.type = options.type || 'warning'

  onConfirmCallback = onConfirm
  onCancelCallback = onCancel

  visible.value = true
}

const handleConfirm = () => {
  visible.value = false
  if (onConfirmCallback) {
    onConfirmCallback()
    onConfirmCallback = null
    onCancelCallback = null
  }
}

const handleCancel = () => {
  visible.value = false
  if (onCancelCallback) {
    onCancelCallback()
    onConfirmCallback = null
    onCancelCallback = null
  }
}

defineExpose({ show })
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.95);
}
</style>
