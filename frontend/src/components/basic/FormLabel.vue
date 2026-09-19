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

    <!-- 信息图标：仅鼠标悬停时显示；触屏没有 hover，改为直接展开说明文字 -->
    <span
      v-if="tooltip"
      class="form-label__tooltip ml-0.5 text-gray-400"
      :title="tooltip"
    >
      <span class="form-label__tooltip-text font-normal">（{{ tooltip }}）</span>
      <font-awesome-icon
        :icon="['fas', 'circle-question']"
        class="form-label__tooltip-icon text-xs transition-opacity duration-200 opacity-0 group-hover:opacity-100"
        aria-hidden="true"
      />
    </span>
  </label>
</template>

<script setup lang="ts">
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
    validator: (value: string) => ['default', 'primary', 'success', 'warning', 'danger'].includes(value)
  },
  // 尺寸
  size: {
    type: String,
    default: 'md',
    validator: (value: string) => ['sm', 'md', 'lg'].includes(value)
  }
})

// 标签颜色映射
const labelColor = computed(() => {
  const colors: Record<string, string> = {
    default: 'text-[#333]',
    primary: 'text-[#8B6F47]',
    success: 'text-green-600',
    warning: 'text-orange-500',
    danger: 'text-red-500'
  }

  const sizeClasses: Record<string, string> = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  }

  return `${colors[props.color]} ${sizeClasses[props.size]}`
})
</script>

<style scoped>
/* 说明文字默认隐藏，只保留需要悬停才能看到的信息图标。 */
.form-label__tooltip-text {
  display: none;
  font-size: 12px;
}

/* 触屏设备没有稳定的 hover，隐藏图标并直接展示说明文字，避免提示不可见。 */
@media (pointer: coarse) {
  .form-label__tooltip-text {
    display: inline;
  }

  .form-label__tooltip-icon {
    display: none;
  }
}
</style>
