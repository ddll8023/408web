<template>
  <button
    :class="buttonClasses"
    :disabled="loading || disabled"
    type="button"
    @click="handleClick"
  >
    <!-- Loading 图标 -->
    <span v-if="loading" class="relative inline-flex items-center justify-center">
      <span class="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full"></span>
    </span>

    <!-- 图标 (Element Plus图标组件) -->
    <component
      v-if="icon && !loading"
      :is="icon"
      class="inline-flex items-center justify-center text-inherit w-[1em] h-[1em]"
    />

    <!-- 按钮文本 -->
    <span v-if="$slots.default" class="inline-flex items-center inline-block">
      <slot></slot>
    </span>
  </button>
</template>

<script setup>
/**
 * 自定义按钮组件
 * 功能：替代Element Plus的el-button，使用自定义样式
 * 遵循KISS原则：简洁实现，只包含必需功能
 * 遵循YAGNI原则：只实现项目实际使用的props
 */
import { computed } from 'vue'

const props = defineProps({
  // 按钮类型：primary, text, default
  type: {
    type: String,
    default: 'default',
    // 支持文本按钮的语义化变体: text-primary(蓝色)、text-danger(红色)、text-warning(橙色)
    validator: (value) => ['default', 'primary', 'text', 'text-primary', 'text-danger', 'text-warning', 'success', 'danger', 'warning'].includes(value)
  },
  // 按钮尺寸：small, medium, large
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium'].includes(value)
  },
  // 是否加载中
  loading: {
    type: Boolean,
    default: false
  },
  // 图标组件（Element Plus图标）
  icon: {
    type: Object,
    default: null
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

/**
 * 计算按钮样式类名
 */
const buttonClasses = computed(() => {
  return [
    'custom-btn',
    `custom-btn--${props.type}`,
    `custom-btn--${props.size}`,
    {
      'is-loading': props.loading,
      'is-disabled': props.disabled
    }
  ]
})

/**
 * 处理点击事件
 */
const handleClick = (event) => {
  if (!props.loading && !props.disabled) {
    emit('click', event)
  }
}
</script>

<style scoped>
/**
 * 自定义按钮样式
 * 使用纯CSS样式，兼容Tailwind CSS 4
 */

/* 基础按钮样式 */
.custom-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  cursor: pointer;
  transition: all 0.15s;
  outline: none;
  white-space: nowrap;
  user-select: none;
  background-color: #fff;
  color: #333;
}

.custom-btn:hover:not(.is-disabled):not(.is-loading) {
  color: #8B6F47;
  border-color: #8B6F47;
  background-color: rgba(139, 111, 71, 0.1);
}

.custom-btn:active:not(.is-disabled):not(.is-loading) {
  opacity: 0.8;
}

/* Primary类型 */
.custom-btn--primary {
  background-color: #8B6F47;
  border-color: #8B6F47;
  color: #fff;
}

.custom-btn--primary:hover:not(.is-disabled):not(.is-loading) {
  background-color: #a88559;
  border-color: #a88559;
  color: #fff;
}

/* 文本按钮基础样式 */
.custom-btn--text,
.custom-btn--text-primary,
.custom-btn--text-danger,
.custom-btn--text-warning {
  border-color: transparent;
  background-color: transparent;
  padding-left: 8px;
  padding-right: 8px;
}

/* 文本按钮类型配置 */
.custom-btn--text {
  color: #8B6F47;
}

.custom-btn--text:hover:not(.is-disabled):not(.is-loading) {
  background-color: rgba(139, 111, 71, 0.1);
  border-color: transparent;
}

.custom-btn--text-primary {
  color: #3b82f6;
}

.custom-btn--text-primary:hover:not(.is-disabled):not(.is-loading) {
  background-color: #eff6ff;
  border-color: transparent;
}

.custom-btn--text-danger {
  color: #ef4444;
}

.custom-btn--text-danger:hover:not(.is-disabled):not(.is-loading) {
  background-color: #fef2f2;
  border-color: transparent;
}

.custom-btn--text-warning {
  color: #f97316;
}

.custom-btn--text-warning:hover:not(.is-disabled):not(.is-loading) {
  background-color: #fff7ed;
  border-color: transparent;
}

/* Success类型 */
.custom-btn--success {
  background-color: #22c55e;
  border-color: #22c55e;
  color: #fff;
}

.custom-btn--success:hover:not(.is-disabled):not(.is-loading) {
  background-color: #4ade80;
  border-color: #4ade80;
  color: #fff;
}

/* Danger类型 */
.custom-btn--danger {
  background-color: #ef4444;
  border-color: #ef4444;
  color: #fff;
}

.custom-btn--danger:hover:not(.is-disabled):not(.is-loading) {
  background-color: #f87171;
  border-color: #f87171;
  color: #fff;
}

/* Warning类型 */
.custom-btn--warning {
  background-color: #f97316;
  border-color: #f97316;
  color: #fff;
}

.custom-btn--warning:hover:not(.is-disabled):not(.is-loading) {
  background-color: #fb923c;
  border-color: #fb923c;
  color: #fff;
}

/* 尺寸变体 */
.custom-btn--small {
  padding: 6px 12px;
  font-size: 12px;
}

.custom-btn--medium {
  padding: 10px 16px;
  font-size: 14px;
}

/* 加载状态 */
.custom-btn.is-loading {
  cursor: not-allowed;
  opacity: 0.8;
}

/* 禁用状态 */
.custom-btn.is-disabled {
  cursor: not-allowed;
  opacity: 0.5;
  pointer-events: none;
}
</style>

