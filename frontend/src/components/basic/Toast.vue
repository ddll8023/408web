<template>
  <teleport to="body">
    <transition name="toast">
      <div
        v-if="visible"
        class="fixed top-4 left-1/2 transform -translate-x-1/2 z-[9999] px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium"
        :class="typeClass"
      >
        <div class="flex items-center gap-2">
          <font-awesome-icon :icon="icon" />
          <span>{{ message }}</span>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
/**
 * Toast 消息提示组件
 * 使用单例模式，确保同时只有一个 Toast 显示
 */
import { ref, computed } from 'vue'

const visible = ref(false)
const message = ref('')
const type = ref('success')

const typeClass = computed(() => {
  const classes = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    warning: 'bg-yellow-600',
    info: 'bg-blue-600'
  }
  return classes[type.value] || classes.info
})

const icon = computed(() => {
  const icons = {
    success: ['fas', 'check-circle'],
    error: ['fas', 'times-circle'],
    warning: ['fas', 'exclamation-circle'],
    info: ['fas', 'info-circle']
  }
  return icons[type.value] || icons.info
})

let timer = null

const show = (msg, msgType = 'success', duration = 3000) => {
  message.value = msg
  type.value = msgType
  visible.value = true

  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    visible.value = false
  }, duration)
}

defineExpose({ show })
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -20px);
}
</style>
