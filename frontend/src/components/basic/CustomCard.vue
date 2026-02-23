<template>
  <div
    :class="cardClasses"
    :style="cardStyle"
  >
    <!-- 头部 -->
    <div v-if="$slots.header || title" class="px-6 py-4 border-b border-gray-200">
      <slot name="header">
        <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
      </slot>
    </div>

    <!-- 内容区 -->
    <div class="px-6 py-4">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
/**
 * CustomCard 自定义卡片组件
 * 功能：替代 Element Plus 的 el-card，提供统一的卡片样式
 * 遵循 KISS 原则：简洁实现，只包含必需功能
 */
import { computed } from 'vue'

const props = defineProps({
  // 卡片标题
  title: {
    type: String,
    default: ''
  },
  // 是否显示阴影
  shadow: {
    type: Boolean,
    default: true
  },
  // 宽度
  width: {
    type: String,
    default: ''
  },
  // 最大宽度
  maxWidth: {
    type: String,
    default: ''
  }
})

// 卡片样式类名
const cardClasses = computed(() => {
  return props.shadow
    ? 'bg-white rounded-lg shadow-[0_2px_8px_rgba(0,0,0,0.1)] overflow-hidden'
    : 'bg-white rounded-lg border border-gray-200 overflow-hidden'
})

// 卡片样式
const cardStyle = computed(() => {
  const style = {}
  if (props.width) {
    style.width = props.width
  }
  if (props.maxWidth) {
    style.maxWidth = props.maxWidth
  }
  return style
})
</script>
