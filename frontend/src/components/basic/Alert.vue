<template>
  <div
    v-if="visible"
    class="p-4 rounded-lg border"
    :class="alertClass"
    :role="type === 'error' ? 'alert' : 'status'"
    aria-live="polite"
  >
    <div class="flex items-start">
      <font-awesome-icon
        v-if="showIcon"
        :icon="icon"
        class="mt-0.5 mr-3"
        :class="iconClass"
        aria-hidden="true"
      />
      <div class="flex-1">
        <div v-if="title" class="font-medium mb-1" :class="titleClass">{{ title }}</div>
        <div :class="contentClass">
          <slot />
        </div>
      </div>
      <button
        v-if="closable"
        type="button"
        class="ml-3 text-gray-400 hover:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 rounded"
        aria-label="关闭提示"
        @click="handleClose"
      >
        <font-awesome-icon :icon="['fas', 'times']" aria-hidden="true" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'info',
    validator: (val: string) => ['success', 'warning', 'error', 'info'].includes(val)
  },
  title: {
    type: String,
    default: ''
  },
  closable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits<{ close: [] }>()
const visible = ref(true)

const alertClass = computed(() => {
  const base = 'border-l-4'
  switch (props.type) {
    case 'success':
      return `${base} bg-green-50 border-green-400`
    case 'warning':
      return `${base} bg-yellow-50 border-yellow-400`
    case 'error':
      return `${base} bg-red-50 border-red-400`
    case 'info':
    default:
      return `${base} bg-blue-50 border-blue-400`
  }
})

const iconClass = computed(() => {
  switch (props.type) {
    case 'success':
      return 'text-green-500'
    case 'warning':
      return 'text-yellow-500'
    case 'error':
      return 'text-red-500'
    case 'info':
    default:
      return 'text-blue-500'
  }
})

const icon = computed(() => {
  const icons: Record<string, string[]> = {
    success: ['fas', 'check-circle'],
    warning: ['fas', 'exclamation-triangle'],
    error: ['fas', 'times-circle'],
    info: ['fas', 'info-circle']
  }
  return icons[props.type] || icons.info
})

const titleClass = computed(() => {
  switch (props.type) {
    case 'success':
      return 'text-green-800'
    case 'warning':
      return 'text-yellow-800'
    case 'error':
      return 'text-red-800'
    case 'info':
    default:
      return 'text-blue-800'
  }
})

const contentClass = computed(() => {
  switch (props.type) {
    case 'success':
      return 'text-green-700'
    case 'warning':
      return 'text-yellow-700'
    case 'error':
      return 'text-red-700'
    case 'info':
    default:
      return 'text-blue-700'
  }
})

const showIcon = computed(() => props.type !== 'info')

const handleClose = () => {
  visible.value = false
  emit('close')
}
</script>
