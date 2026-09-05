<template>
  <span
    :class="[
      'inline-flex items-center rounded font-medium transition-colors',
      sizeClasses[props.size] || sizeClasses.md,
      typeClasses[props.variant || props.type] || typeClasses.default
    ]"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
/**
 * 标签组件
 * 功能描述：用于显示分类、状态等标签信息
 * 依赖：无
 */

const props = defineProps({
  type: {
    type: String,
    default: 'default',
    validator: (value: string) => ['default', 'success', 'primary', 'info', 'warning', 'danger'].includes(value)
  },
  // variant 是历史调用方使用的别名，统一映射到 type，避免旧页面退回默认样式
  variant: {
    type: String,
    default: '',
    validator: (value: string) => !value || ['default', 'success', 'primary', 'info', 'warning', 'danger'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value: string) => ['sm', 'md', 'lg', 'small'].includes(value)
  }
})

const sizeClasses: Record<string, string> = {
  sm: 'px-1.5 py-0.5 text-xs',
  small: 'px-1.5 py-0.5 text-xs',
  md: 'px-2 py-0.5 text-xs',
  lg: 'px-2.5 py-1 text-sm'
}

const typeClasses: Record<string, string> = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  primary: 'bg-blue-100 text-blue-800',
  info: 'bg-cyan-100 text-cyan-800',
  warning: 'bg-yellow-100 text-yellow-800',
  danger: 'bg-red-100 text-red-800'
}
</script>
