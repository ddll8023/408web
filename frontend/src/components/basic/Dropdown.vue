<template>
  <div ref="dropdownRef" class="relative inline-block">
    <!-- 触发器 -->
    <div
      class="dropdown-trigger"
      :class="{ 'cursor-pointer': !disabled }"
      role="button"
      :tabindex="disabled ? -1 : 0"
      :aria-expanded="visible"
      aria-haspopup="menu"
      :aria-disabled="disabled"
      @click="handleTriggerClick"
      @keydown="handleTriggerKeydown"
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
          :class="[menuClasses, menuClass]"
          role="menu"
          tabindex="-1"
          @click.stop="handleMenuClick"
          @keydown="handleMenuKeydown"
          @mouseenter="handleMenuMouseEnter"
          @mouseleave="handleMenuMouseLeave"
        >
          <slot name="dropdown" />
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
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
    validator: (value: string) => ['click', 'hover'].includes(value)
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
  },
  // 菜单容器的自定义样式类
  menuClass: {
    type: String,
    default: ''
  }
})

const emit = defineEmits<{ command: [value: string]; 'visible-change': [value: boolean] }>()

const dropdownRef = ref<HTMLElement | null>(null)
const menuRef = ref<HTMLElement | null>(null)
const visible = ref(false)
let showTimer: ReturnType<typeof setTimeout> | undefined
let hideTimer: ReturnType<typeof setTimeout> | undefined
let resizeObserver: ResizeObserver | null = null

// 菜单位置样式
const menuClasses = computed(() => {
  const placementClasses: Record<string, string> = {
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

const handleTriggerKeydown = (event: KeyboardEvent) => {
  if (props.disabled) return
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    if (props.trigger === 'click') {
      toggleVisible()
      if (visible.value) nextTick(() => menuItems()[0]?.focus())
    }
    else if (!visible.value) {
      visible.value = true
      emit('visible-change', true)
      nextTick(() => {
        updatePosition()
        menuItems()[0]?.focus()
      })
    }
  } else if (event.key === 'Escape' && visible.value) {
    event.preventDefault()
    visible.value = false
    emit('visible-change', false)
  }
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

  // 清理上一次的视口约束，避免窗口尺寸变化后残留旧高度。
  menu.style.maxHeight = ''
  menu.style.overflowY = ''

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
  const gap = 8
  const viewportPadding = 12
  const spaceBelow = Math.max(0, viewportHeight - triggerRect.bottom - gap - viewportPadding)
  const spaceAbove = Math.max(0, triggerRect.top - gap - viewportPadding)
  const preferTop = props.placement.startsWith('top')

  // 优先遵循 placement；空间不足时切换到空间更大的一侧。
  let placeAbove = preferTop
  if (!preferTop && menuHeight > spaceBelow && spaceAbove > spaceBelow) {
    placeAbove = true
  }
  if (preferTop && menuHeight > spaceAbove && spaceBelow > spaceAbove) {
    placeAbove = false
  }

  const availableHeight = placeAbove ? spaceAbove : spaceBelow
  const effectiveHeight = Math.min(menuHeight, Math.max(1, availableHeight))
  if (menuHeight > availableHeight) {
    // 菜单无法完整放入任一侧时，限制外层高度并让菜单自身滚动。
    menu.style.maxHeight = `${Math.max(1, availableHeight)}px`
    menu.style.overflowY = 'auto'
  }

  top = placeAbove
    ? triggerRect.top - effectiveHeight - gap
    : triggerRect.bottom + gap

  if (props.placement.includes('start')) {
    left = triggerRect.left
  } else if (props.placement.includes('end')) {
    left = triggerRect.right - menuWidth
  } else {
    left = triggerRect.left + (triggerRect.width - menuWidth) / 2
  }

  // 最终边界检查，保证弹窗至少保留视口边距。
  if (top + effectiveHeight > viewportHeight - viewportPadding) {
    top = viewportHeight - effectiveHeight - viewportPadding
  }
  if (top < viewportPadding) {
    top = viewportPadding
  }
  if (left + menuWidth > viewportWidth - viewportPadding) {
    left = viewportWidth - menuWidth - viewportPadding
  }
  if (left < viewportPadding) {
    left = viewportPadding
  }

  menu.style.top = `${top}px`
  menu.style.left = `${left}px`
}

// 处理菜单项点击
const handleMenuClick = (event: MouseEvent) => {
  if (!(event.target instanceof Element)) return
  // 查找被点击的菜单项元素
  const target = event.target.closest<HTMLElement>('.dropdown-item')
  if (!target) return

  // 检查是否禁用
  if (target.classList.contains('is-disabled')) return

  // 获取 command 值
  const command = target.dataset.command
  if (command !== undefined && command !== '') {
    handleCommand(command)
  }
}

const menuItems = () => Array.from(
  menuRef.value?.querySelectorAll<HTMLElement>('.dropdown-item:not(.is-disabled)') || []
)

const handleMenuKeydown = (event: KeyboardEvent) => {
  const items = menuItems()
  if (event.key === 'Escape') {
    event.preventDefault()
    visible.value = false
    emit('visible-change', false)
    dropdownRef.value?.querySelector<HTMLElement>('.dropdown-trigger')?.focus()
    return
  }

  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (items.length === 0) return
    const currentIndex = items.indexOf(document.activeElement as HTMLElement)
    const direction = event.key === 'ArrowDown' ? 1 : -1
    const nextIndex = currentIndex < 0
      ? (direction > 0 ? 0 : items.length - 1)
      : (currentIndex + direction + items.length) % items.length
    items[nextIndex]?.focus()
    return
  }

  if ((event.key === 'Enter' || event.key === ' ') && event.target instanceof HTMLElement) {
    event.preventDefault()
    event.target.click()
  }
}

// 执行命令
const handleCommand = (command: string) => {
  emit('command', command)
  visible.value = false
  emit('visible-change', false)
  dropdownRef.value?.querySelector<HTMLElement>('.dropdown-trigger')?.focus()
}

const observeMenu = () => {
  resizeObserver?.disconnect()
  resizeObserver = null
  if (menuRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      if (visible.value) updatePosition()
    })
    resizeObserver.observe(menuRef.value)
  }
}

// 点击外部关闭
const handleClickOutside = (event: MouseEvent) => {
  if (!(event.target instanceof Element)) return
  if (props.disabled) return
  const container = dropdownRef.value
  if (container && !container.contains(event.target)) {
    if (visible.value) {
      visible.value = false
      emit('visible-change', visible.value)
    }
  }
}

// 外部滚动时关闭菜单，避免触发按钮滚走后弹窗悬浮在旧位置。
// 菜单自身的滚动不关闭，用于支持长菜单在小屏中的浏览。
const handleScroll = (event: Event) => {
  if (!visible.value) return

  const target = event.target
  if (menuRef.value && target instanceof Node && menuRef.value.contains(target)) return

  visible.value = false
  emit('visible-change', false)
}

// 监听 visible 变化
watch(visible, (val) => {
  if (val) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
    document.addEventListener('scroll', handleScroll, true)
    nextTick(observeMenu)
  } else {
    document.removeEventListener('click', handleClickOutside)
    document.removeEventListener('scroll', handleScroll, true)
    resizeObserver?.disconnect()
    resizeObserver = null
  }
})

// 清理
onUnmounted(() => {
  clearTimeout(showTimer)
  clearTimeout(hideTimer)
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('scroll', handleScroll, true)
  window.removeEventListener('resize', updatePosition)
  resizeObserver?.disconnect()
  resizeObserver = null
})

onMounted(() => {
  window.addEventListener('resize', updatePosition)
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
