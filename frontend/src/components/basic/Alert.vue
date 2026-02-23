<template>
  <div
    class="p-4 rounded-lg border"
    :class="alertClass"
  >
    <div class="flex items-start">
      <i v-if="showIcon" class="mt-0.5 mr-3" :class="iconClass"></i>
      <div class="flex-1">
        <div v-if="title" class="font-medium mb-1" :class="titleClass">{{ title }}</div>
        <div :class="contentClass">
          <slot />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'info',
    validator: (val) => ['success', 'warning', 'error', 'info'].includes(val)
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
      return 'fa fa-check-circle text-green-500'
    case 'warning':
      return 'fa fa-exclamation-triangle text-yellow-500'
    case 'error':
      return 'fa fa-times-circle text-red-500'
    case 'info':
    default:
      return 'fa fa-info-circle text-blue-500'
  }
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
</script>
