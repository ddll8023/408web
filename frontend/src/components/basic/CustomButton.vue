<template>
  <button
    :class="buttonClasses"
    :disabled="loading || disabled"
    type="button"
    @click="handleClick"
  >
    <!-- Loading 图标 -->
    <span v-if="loading" class="btn-loading">
      <span class="loading-spinner"></span>
    </span>
    
    <!-- 图标 (Element Plus图标组件) -->
    <component 
      v-if="icon && !loading" 
      :is="icon" 
      class="btn-icon"
    />
    
    <!-- 按钮文本 -->
    <span v-if="$slots.default" class="btn-text">
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

<style lang="scss" scoped>
/**
 * 自定义按钮样式
 * 基于项目的Sass变量系统
 * 注：变量已通过Vite全局注入，无需手动导入
 */

// 导入 Sass color 模块，用于颜色调整函数
@use 'sass:color';

/* 基础按钮样式 */
.custom-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: $spacing-xs - 2px; // 6px
  padding: $spacing-xs + 2px $spacing-sm; // 10px 16px
  border: 1px solid $color-border;
  border-radius: $border-radius-base;
  font-size: $font-size-base;
  font-weight: $font-weight-medium;
  line-height: 1.5;
  cursor: pointer;
  transition: $transition-fast;
  outline: none;
  white-space: nowrap;
  user-select: none;
  
  /* 默认样式 */
  background-color: $color-bg-white;
  color: $color-text-primary;
  border-color: rgba(0, 0, 0, 0.15); // 浅色主题使用深色边框
  
  &:hover:not(.is-disabled):not(.is-loading) {
    color: $color-accent;
    border-color: $color-accent;
    background-color: $color-accent-light;
  }
  
  &:active:not(.is-disabled):not(.is-loading) {
    opacity: 0.8;
  }
}

/* Primary类型 */
.custom-btn--primary {
  background-color: $color-accent; // 使用深色强调色
  border-color: $color-accent;
  color: $color-text-white;
  
  &:hover:not(.is-disabled):not(.is-loading) {
    // 使用 color.adjust 调整亮度，变亮10%
    background-color: color.adjust($color-accent, $lightness: 10%);
    border-color: color.adjust($color-accent, $lightness: 10%);
    color: $color-text-white;
  }
}

/* 文本按钮基础样式 mixin */
@mixin text-btn-base {
  border-color: transparent;
  background-color: transparent;
  padding-left: $spacing-xs;
  padding-right: $spacing-xs;
}

/* 文本按钮类型配置 */
$text-btn-types: (
  'text': ($color-accent, $color-accent-light),
  'text-primary': (#409eff, rgba(64, 158, 255, 0.1)),
  'text-danger': ($color-danger, rgba(245, 108, 108, 0.1)),
  'text-warning': ($color-warning, rgba(230, 162, 60, 0.1))
);

/* 批量生成文本按钮样式 */
@each $type, $colors in $text-btn-types {
  .custom-btn--#{$type} {
    @include text-btn-base;
    color: nth($colors, 1);
    
    &:hover:not(.is-disabled):not(.is-loading) {
      background-color: nth($colors, 2);
      border-color: transparent;
    }
  }
}

/* 尺寸变体 */
.custom-btn--small {
  padding: $spacing-xs - 2px $spacing-gap; // 6px 12px
  font-size: $font-size-small;
}

.custom-btn--medium {
  padding: $spacing-xs + 2px $spacing-sm; // 10px 16px
  font-size: $font-size-base;
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

/* 图标样式 */
.btn-icon {
  font-size: inherit;
  width: 1em;
  height: 1em;
}

/* Loading动画 */
.btn-loading {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.loading-spinner {
  display: inline-block;
  width: 1em;
  height: 1em;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 按钮文本 */
.btn-text {
  display: inline-block;
}
</style>

