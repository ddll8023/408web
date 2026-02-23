<template>
  <div ref="dropdownRef" class="relative inline-block">
    <!-- 触发器 -->
    <div
      class="dropdown-trigger"
      :class="{ 'cursor-pointer': !disabled }"
      @click="handleTriggerClick"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    >
      <slot name="trigger" />
    </div>

    <!-- 菜单容器 - 使用 teleport 传送到 body -->
    <teleport to="body">
      <transition name="dropdown">
        <div
          v-if="visible"
          ref="menuRef"
          class="dropdown-menu"
          @click.stop="handleMenuClick"
          @mouseenter="handleMenuMouseEnter"
          @mouseleave="handleMenuMouseLeave"
        >
          <slot name="dropdown" />
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
/**
 * Dropdown 下拉菜单组件
 * 功能：提供下拉菜单功能，支持 click 和 hover 触发方式
 * 遵循项目规范：Vue 3 + script setup + Tailwind CSS
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  // 触发方式
  trigger: {
    type: String,
    default: 'click',
    validator: (value) => ['click', 'hover'].includes(value)
  },
  // 菜单位置
  placement: {
    type: String,
    default: 'bottom-start'
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['command', 'visible-change'])

const dropdownRef = ref(null)
const menuRef = ref(null)
const visible = ref(false)
let showTimer = null
let hideTimer = null

// 菜单位置样式
const menuClasses = computed(() => {
  const placementClasses = {
    'bottom': 'left-1/2 -translate-x-1/2',
    'bottom-start': 'left-0',
    'bottom-end': 'right-0',
    'top': 'left-1/2 -translate-x-1/2',
    'top-start': 'left-0',
    'top-end': 'right-0'
  }
  return placementClasses[props.placement] || placementClasses['bottom-start']
})

// 切换显示状态
const toggleVisible = () => {
  if (props.disabled) return
  visible.value = !visible.value
  emit('visible-change', visible.value)
  if (visible.value) {
    // 使用 nextTick + requestAnimationFrame 确保在 teleport 完成后计算位置
    nextTick(() => {
      requestAnimationFrame(() => {
        requestAnimationFrame(updatePosition)
      })
    })
  }
}

// 点击触发器
const handleTriggerClick = () => {
  if (props.trigger !== 'click' || props.disabled) return
  toggleVisible()
}

// 鼠标进入触发器
const handleMouseEnter = () => {
  if (props.trigger !== 'hover' || props.disabled) return
  clearTimeout(hideTimer)
  showTimer = setTimeout(() => {
    visible.value = true
    emit('visible-change', visible.value)
    nextTick(() => {
      requestAnimationFrame(() => {
        requestAnimationFrame(updatePosition)
      })
    })
  }, 300)
}

// 鼠标离开触发器
const handleMouseLeave = () => {
  if (props.trigger !== 'hover' || props.disabled) return
  clearTimeout(showTimer)
  hideTimer = setTimeout(() => {
    visible.value = false
    emit('visible-change', visible.value)
  }, 300)
}

// 鼠标进入菜单（阻止关闭）
const handleMenuMouseEnter = () => {
  if (props.trigger === 'hover') {
    clearTimeout(hideTimer)
  }
}

// 鼠标离开菜单
const handleMenuMouseLeave = () => {
  if (props.trigger === 'hover') {
    hideTimer = setTimeout(() => {
      visible.value = false
      emit('visible-change', visible.value)
    }, 300)
  }
}

// 计算菜单位置
const updatePosition = () => {
  if (!dropdownRef.value || !menuRef.value) return

  const trigger = dropdownRef.value.querySelector('.dropdown-trigger')
  const menu = menuRef.value

  if (!trigger) return

  const triggerRect = trigger.getBoundingClientRect()

  // 强制计算菜单尺寸 - 先给一个临时尺寸让浏览器布局
  if (!menu.style.width) {
    menu.style.minWidth = `${triggerRect.width}px`
  }

  // 获取菜单尺寸（需要强制重排）
  const menuWidth = menu.offsetWidth || triggerRect.width
  const menuHeight = menu.offsetHeight || 200

  const viewportHeight = window.innerHeight
  const viewportWidth = window.innerWidth

  let top = 0
  let left = 0
  const gap = 8 // 间距

  // 根据 placement 计算位置
  if (props.placement.startsWith('bottom')) {
    top = triggerRect.bottom + gap
  } else if (props.placement.startsWith('top')) {
    top = triggerRect.top - menuHeight - gap
  }

  if (props.placement.includes('start')) {
    left = triggerRect.left
  } else if (props.placement.includes('end')) {
    left = triggerRect.right - menuWidth
  } else {
    left = triggerRect.left + (triggerRect.width - menuWidth) / 2
  }

  // 边界检查
  if (top + menuHeight > viewportHeight - gap) {
    top = triggerRect.top - menuHeight - gap
  }
  if (top < gap) {
    top = triggerRect.bottom + gap
  }
  if (left + menuWidth > viewportWidth - gap) {
    left = viewportWidth - menuWidth - gap
  }
  if (left < gap) {
    left = gap
  }

  menu.style.top = `${top}px`
  menu.style.left = `${left}px`
}

// 处理菜单项点击
const handleMenuClick = (event) => {
  // 查找被点击的菜单项元素
  const target = event.target.closest('.dropdown-item')
  if (!target) return

  // 检查是否禁用
  if (target.classList.contains('is-disabled')) return

  // 获取 command 值
  const command = target.dataset.command
  if (command !== undefined && command !== '') {
    handleCommand(command)
  }
}

// 执行命令
const handleCommand = (command) => {
  emit('command', command)
  visible.value = false
  emit('visible-change', false)
}

// 点击外部关闭
const handleClickOutside = (event) => {
  if (props.disabled) return
  const container = dropdownRef.value
  if (container && !container.contains(event.target)) {
    if (visible.value) {
      visible.value = false
      emit('visible-change', visible.value)
    }
  }
}

// 监听 visible 变化
watch(visible, (val) => {
  if (val) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

// 清理
onUnmounted(() => {
  clearTimeout(showTimer)
  clearTimeout(hideTimer)
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', updatePosition)
})

onMounted(() => {
  window.addEventListener('resize', updatePosition)

  // 使用 ResizeObserver 监听菜单尺寸变化
  if (menuRef.value && typeof ResizeObserver !== 'undefined') {
    const observer = new ResizeObserver(() => {
      if (visible.value) {
        updatePosition()
      }
    })
    // 需要在菜单渲染后观察
  }
})

// 暴露方法供外部调用
defineExpose({
  toggleVisible,
  visible
})
</script>

<style>
/* Dropdown 样式 - 不使用 scoped 以便正确应用给 slot 内容 */
.dropdown-menu {
  position: fixed;
  min-width: 160px;
  background: white;
  border: 1px solid #f3f4f6;
  border-radius: 0.5rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 99999;
}

.dropdown-menu .dropdown-item {
  display: flex;
  align-items: center;
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.dropdown-menu .dropdown-item:hover:not(.is-disabled) {
  background-color: #f9fafb;
  color: #8B6F47;
}

.dropdown-menu .dropdown-item.is-disabled {
  color: #9ca3af;
  cursor: not-allowed;
  background-color: transparent;
}

.dropdown-menu .dropdown-item[data-divided] {
  border-top: 1px solid #f3f4f6;
  margin-top: 4px;
  padding-top: 8px;
}

/* 过渡动画 */
.dropdown-enter-active {
  transition: opacity 0.2s cubic-bezier(0.4, 0, 0.2, 1), transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-leave-active {
  transition: opacity 0.15s cubic-bezier(0.4, 0, 0.2, 1), transform 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
