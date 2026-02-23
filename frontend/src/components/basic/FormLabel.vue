<template>
  <label
    v-if="label"
    :for="forId"
    class="flex items-center gap-1.5 text-sm font-medium select-none group"
    :class="[
      labelColor,
      { 'cursor-pointer': forId }
    ]"
  >
    <!-- 标签文本 -->
    <span class="transition-colors duration-200">{{ label }}</span>

    <!-- 必填标记 -->
    <span
      v-if="required"
      class="text-red-500 font-bold"
      title="必填"
    >*</span>

    <!-- 提示信息 -->
    <span
      v-if="hint"
      class="ml-1 text-xs text-gray-400 font-normal"
    >({{ hint }})</span>

    <!-- 信息图标 -->
    <span
      v-if="tooltip"
      class="ml-0.5 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity duration-200 cursor-help"
      :title="tooltip"
    >
      <font-awesome-icon :icon="['fas', 'circle-question']" class="text-xs" />
    </span>
  </label>
</template>

<script setup>
/**
 * FormLabel 表单标签组件
 * 功能：统一表单标签样式，支持必填标记、提示文字、工具提示
 * 遵循KISS原则：仅实现必需功能
 * 遵循YAGNI原则：按需启用各项属性
 */
import { computed } from 'vue'

const props = defineProps({
  // 标签文本
  label: {
    type: String,
    default: ''
  },
  // 关联的表单元素ID
  forId: {
    type: String,
    default: ''
  },
  // 是否必填
  required: {
    type: Boolean,
    default: false
  },
  // 提示文字（显示在括号中）
  hint: {
    type: String,
    default: ''
  },
  // 工具提示（鼠标悬停显示）
  tooltip: {
    type: String,
    default: ''
  },
  // 标签颜色变体
  color: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'primary', 'success', 'warning', 'danger'].includes(value)
  },
  // 尺寸
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  }
})

// 标签颜色映射
const labelColor = computed(() => {
  const colors = {
    default: 'text-[#333]',
    primary: 'text-[#8B6F47]',
    success: 'text-green-600',
    warning: 'text-orange-500',
    danger: 'text-red-500'
  }

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  }

  return `${colors[props.color]} ${sizeClasses[props.size]}`
})
</script>
