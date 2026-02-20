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
    <span v-if="$slots.default" class="inline-flex items-center">
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
  // 基础样式
  const baseClasses = [
    'inline-flex',
    'items-center',
    'justify-center',
    'gap-1.5',
    'border',
    'rounded',
    'font-medium',
    'leading-normal',
    'cursor-pointer',
    'transition-all',
    'duration-150',
    'focus:outline-none',
    'whitespace-nowrap',
    'select-none',
    'bg-white',
    'text-[#333]',
    'border-black/15',
    'px-4',
    'py-2.5',
    'text-sm',
    // 默认状态的 hover 和 active
    'hover:text-[#8B6F47]',
    'hover:border-[#8B6F47]',
    'hover:bg-[#8B6F47/10]',
    'active:opacity-80',
    // 禁用和加载状态
    {
      'cursor-not-allowed opacity-80': props.loading,
      'cursor-not-allowed opacity-50 pointer-events-none': props.disabled
    }
  ]

  // 尺寸样式
  const sizeClasses = {
    small: ['px-3', 'py-1.5', 'text-xs'],
    medium: ['px-4', 'py-2.5', 'text-sm']
  }

  // 类型样式
  const typeClasses = {
    default: [],
    primary: [
      'bg-[#8B6F47]',
      'border-[#8B6F47]',
      'text-white',
      'hover:bg-[#a88559]',
      'hover:border-[#a88559]',
      'hover:text-white'
    ],
    text: [
      'border-transparent',
      'bg-transparent',
      'px-2',
      'text-[#8B6F47]',
      'hover:bg-[#8B6F47/10]',
      'hover:border-transparent'
    ],
    'text-primary': [
      'border-transparent',
      'bg-transparent',
      'px-2',
      'text-blue-500',
      'hover:bg-blue-50',
      'hover:border-transparent'
    ],
    'text-danger': [
      'border-transparent',
      'bg-transparent',
      'px-2',
      'text-red-500',
      'hover:bg-red-50',
      'hover:border-transparent'
    ],
    'text-warning': [
      'border-transparent',
      'bg-transparent',
      'px-2',
      'text-orange-500',
      'hover:bg-orange-50',
      'hover:border-transparent'
    ],
    success: [
      'bg-green-500',
      'border-green-500',
      'text-white',
      'hover:bg-green-400',
      'hover:border-green-400',
      'hover:text-white'
    ],
    danger: [
      'bg-red-500',
      'border-red-500',
      'text-white',
      'hover:bg-red-400',
      'hover:border-red-400',
      'hover:text-white'
    ],
    warning: [
      'bg-orange-500',
      'border-orange-500',
      'text-white',
      'hover:bg-orange-400',
      'hover:border-orange-400',
      'hover:text-white'
    ]
  }

  return [
    ...baseClasses,
    ...(sizeClasses[props.size] || sizeClasses.medium),
    ...(typeClasses[props.type] || typeClasses.default)
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


