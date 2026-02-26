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

    <!-- 图标 -->
    <template v-if="icon && !loading">
      <!-- Element Plus 图标组件 -->
      <component
        v-if="isElementPlusIcon"
        :is="icon"
        class="inline-flex items-center justify-center text-inherit w-[1em] h-[1em]"
      />
      <!-- Font Awesome 图标 -->
      <font-awesome-icon
        v-else
        :icon="icon"
        class="inline-flex items-center justify-center text-inherit w-4 h-4"
      />
    </template>

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
 * 遵循前端组件规范：使用baseClasses、sizeClasses、variantClasses三常量分离模式
 */
import { computed } from 'vue'

/**
 * 判断是否为 Element Plus 图标组件
 * Font Awesome 图标格式为数组: ['fas', 'icon-name']
 * Element Plus 图标格式为对象（组件）
 */
const isElementPlusIcon = computed(() => {
  return props.icon && typeof props.icon === 'object' && !Array.isArray(props.icon)
})

const props = defineProps({
  // 按钮类型
  type: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'primary', 'success', 'danger', 'warning', 'text', 'text-primary', 'text-danger', 'text-warning'].includes(value)
  },
  // 按钮尺寸：sm, md, lg
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  // 是否加载中
  loading: {
    type: Boolean,
    default: false
  },
  // 图标：支持 Element Plus 图标组件 或 Font Awesome 图标数组 ['fas', 'icon-name']
  icon: {
    type: [Object, Array],
    default: null
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 是否块级按钮
  block: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

// 基础样式 - 简洁字符串，包含默认尺寸和focus ring
const baseClasses = 'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#8B6F47] focus:ring-offset-2 px-4 py-2.5 text-sm'

// 尺寸样式 - 覆盖基础样式中的尺寸
const sizeClasses = {
  sm: '!px-3.5 !py-2 !text-base h-[36px]',
  md: 'px-5 py-3 text-base h-[42px]',
  lg: '!px-6 !py-3.5 !text-lg h-[48px]'
}

// 变体样式 - 使用项目中一致的颜色
const variantClasses = {
  default: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-400 hover:cursor-pointer',
  primary: 'border border-transparent bg-[#8B6F47] text-white hover:bg-[#a88559] hover:cursor-pointer',
  success: 'border border-transparent bg-green-600 text-white hover:bg-green-500 hover:cursor-pointer',
  danger: 'border border-transparent bg-red-600 text-white hover:bg-red-500 hover:cursor-pointer',
  warning: 'border border-transparent bg-orange-500 text-white hover:bg-orange-400 hover:cursor-pointer',
  text: 'border-transparent bg-transparent text-[#8B6F47] hover:bg-[rgba(139,111,71,0.1)] hover:cursor-pointer',
  'text-primary': 'border-transparent bg-transparent text-blue-500 hover:bg-blue-50 hover:cursor-pointer',
  'text-danger': 'border-transparent bg-transparent text-red-500 hover:bg-red-50 hover:cursor-pointer',
  'text-warning': 'border-transparent bg-transparent text-orange-500 hover:bg-orange-50 hover:cursor-pointer'
}

/**
 * 计算按钮样式类名
 * 按照规范：三常量分离模式（baseClasses、sizeClasses、variantClasses）
 */
const buttonClasses = computed(() => {
  const size = sizeClasses[props.size] || sizeClasses.md
  const variant = variantClasses[props.type] || variantClasses.default

  // 状态样式
  const classes = [baseClasses, size, variant]

  // 块级按钮
  if (props.block) {
    classes.push('w-full', 'justify-center')
  }

  // 禁用状态
  if (props.disabled || props.loading) {
    classes.push('opacity-50', 'cursor-not-allowed')
  }

  return classes.join(' ')
})

/**
 * 处理点击事件
 * 避免在loading或disabled状态下触发
 */
const handleClick = (event) => {
  if (!props.loading && !props.disabled) {
    emit('click', event)
  }
}
</script>
