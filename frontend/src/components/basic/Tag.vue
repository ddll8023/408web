<template>
  <span
    :class="[
      'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium transition-colors',
      typeClasses[variant]
    ]"
  >
    <slot />
  </span>
</template>

<script setup>
/**
 * 标签组件
 * 功能描述：用于显示分类、状态等标签信息
 * 依赖：无
 */

defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'success', 'primary', 'info', 'warning', 'danger'].includes(value)
  }
})

const typeClasses = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  primary: 'bg-blue-100 text-blue-800',
  info: 'bg-gray-100 text-gray-600',
  warning: 'bg-yellow-100 text-yellow-800',
  danger: 'bg-red-100 text-red-800'
}
</script>
