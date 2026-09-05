<template>
  <div
    ref="rootRef"
    class="relative inline-block"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @focusin="handleFocusIn"
    @focusout="handleFocusOut"
    @click="handleClick"
  >
    <!-- 触发元素 -->
    <slot />

    <!-- 提示框 -->
    <transition name="tooltip">
      <div
        v-if="visible"
        ref="tooltipRef"
        role="tooltip"
        class="absolute z-50 px-2.5 py-1.5 text-xs text-white bg-gray-800 rounded-md shadow-lg whitespace-nowrap pointer-events-none"
        :class="placementClass"
      >
        <slot name="content">{{ content }}</slot>
        <!-- 小箭头 -->
        <div class="absolute w-2 h-2 bg-gray-800 transform rotate-45" :class="arrowClass"></div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
/**
 * Tooltip 工具提示组件
 * 功能：提供鼠标悬停显示提示信息
 * 遵循 KISS 原则：简洁实现
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // 提示内容
  content: {
    type: String,
    default: ''
  },
  // 显示位置
  placement: {
    type: String,
    default: 'top',
    validator: (value: string) => ['top', 'bottom', 'left', 'right'].includes(value)
  },
  // 触发方式
  trigger: {
    type: String,
    default: 'hover',
    validator: (value: string) => ['hover', 'click'].includes(value)
  },
  // 延迟显示（毫秒）
  showDelay: {
    type: Number,
    default: 200
  },
  // 延迟隐藏（毫秒）
  hideDelay: {
    type: Number,
    default: 100
  }
})

const emit = defineEmits<{ show: []; hide: [] }>()

const visible = ref(false)
const rootRef = ref<HTMLElement | null>(null)
const tooltipRef = ref<HTMLElement | null>(null)
let showTimer: ReturnType<typeof setTimeout> | undefined
let hideTimer: ReturnType<typeof setTimeout> | undefined

// 计算提示框位置
const placementClass = computed(() => {
  const classes: Record<string, string> = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  }
  return classes[props.placement] || classes.top
})

// 计算箭头位置
const arrowClass = computed(() => {
  const classes: Record<string, string> = {
    top: 'left-1/2 -translate-x-1/2 -bottom-1',
    bottom: 'left-1/2 -translate-x-1/2 -top-1',
    left: 'top-1/2 -translate-y-1/2 -right-1',
    right: 'top-1/2 -translate-y-1/2 -left-1'
  }
  return classes[props.placement] || classes.top
})

// 显示提示
const show = () => {
  clearTimeout(hideTimer)
  showTimer = setTimeout(() => {
    visible.value = true
    emit('show')
  }, props.showDelay)
}

// 隐藏提示
const hide = () => {
  clearTimeout(showTimer)
  hideTimer = setTimeout(() => {
    visible.value = false
    emit('hide')
  }, props.hideDelay)
}

// 鼠标进入
const handleMouseEnter = () => {
  if (props.trigger === 'hover') {
    show()
  }
}

// 鼠标离开
const handleMouseLeave = () => {
  if (props.trigger === 'hover') {
    hide()
  }
}

// 键盘焦点与鼠标悬停保持一致，避免提示只对鼠标用户可见
const handleFocusIn = () => {
  if (props.trigger === 'hover') show()
}

const handleFocusOut = (event: FocusEvent) => {
  if (props.trigger !== 'hover') return
  const nextTarget = event.relatedTarget
  if (!(nextTarget instanceof Node) || !rootRef.value?.contains(nextTarget)) {
    hide()
  }
}

// 点击切换（click 触发模式）
const handleClick = () => {
  if (props.trigger === 'click') {
    if (visible.value) {
      hide()
    } else {
      show()
    }
  }
}

// 点击外部关闭
const handleClickOutside = (event: MouseEvent) => {
  if (!(event.target instanceof Element)) return
  if (props.trigger === 'click' && visible.value) {
    if (rootRef.value && !rootRef.value.contains(event.target)) {
      hide()
    }
  }
}

onMounted(() => {
  if (props.trigger === 'click') {
    document.addEventListener('click', handleClickOutside)
  }
})

onUnmounted(() => {
  clearTimeout(showTimer)
  clearTimeout(hideTimer)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.tooltip-enter-active,
.tooltip-leave-active {
  transition: all 0.2s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(4px);
}

.tooltip-leave-to {
  transform: translateX(-50%) translateY(-4px);
}

/* 左侧/右侧特殊处理 */
.left-full .tooltip-enter-from,
.left-full .tooltip-leave-to {
  transform: translateY(-50%) translateX(4px);
}

.right-full .tooltip-enter-from,
.right-full .tooltip-leave-to {
  transform: translateY(-50%) translateX(-4px);
}
</style>
