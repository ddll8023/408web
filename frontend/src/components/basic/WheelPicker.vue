<template>
  <div class="wheel-picker-container relative" ref="containerRef">
    <!-- 触发器（显示选中值或占位符） -->
    <div
      :id="pickerId"
      class="dropdown-control wheel-picker-trigger relative flex items-center border px-3 cursor-pointer"
      :class="[
        sizeClasses,
        {
          'dropdown-control--disabled': disabled,
          'dropdown-control--open': isOpen,
          'opacity-60 cursor-not-allowed pointer-events-none': disabled
        }
      ]"
      role="combobox"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
      :aria-controls="listId"
      :aria-activedescendant="activeOptionId"
      :aria-label="ariaLabel || undefined"
      :tabindex="disabled ? -1 : 0"
      @click="toggleDropdown"
      @keydown="handleTriggerKeydown"
    >
      <!-- 选中值显示 -->
      <div class="flex-1 min-w-0 truncate">
        <span
          v-if="selectedLabel"
          class="text-gray-700"
        >
          {{ selectedLabel }}
        </span>
        <span
          v-else
          class="text-gray-400"
        >
          {{ placeholder }}
        </span>
      </div>

      <!-- 下拉箭头 -->
      <div class="flex-shrink-0 ml-2">
        <font-awesome-icon
          :icon="['fas', 'chevron-down']"
          class="text-gray-400 text-xs transition-transform duration-200"
          :class="{ 'rotate-180': isOpen }"
          aria-hidden="true"
        />
      </div>

      <!-- 清除按钮 -->
      <button
        v-if="clearable && modelValue !== null && modelValue !== '' && !isOpen"
        type="button"
        class="ml-2 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8B6F47]/30 rounded"
        aria-label="清除选择"
        @click.stop="handleClear"
      >
        <font-awesome-icon :icon="['fas', 'times-circle']" class="text-sm" aria-hidden="true" />
      </button>
    </div>

    <!-- 下拉滚动选择器 -->
    <transition name="wheel-dropdown">
      <div
        :id="listId"
        v-show="isOpen"
        role="listbox"
        :aria-label="placeholder"
        class="dropdown-panel absolute top-full left-0 right-0 mt-2 z-50 overflow-hidden"
        :style="{ height: `${containerHeight}px` }"
      >
        <div
          ref="pickerRef"
          class="wheel-picker relative h-full overflow-hidden cursor-pointer select-none"
          @wheel.prevent="handleWheel"
          @mousedown="handleMouseDown"
          @touchstart.passive="handleTouchStart"
        >
          <!-- 高亮区域 -->
          <div
            class="absolute left-0 right-0 pointer-events-none z-10"
            :style="highlightStyle"
          >
            <div class="dropdown-wheel-highlight"></div>
          </div>

          <!-- 选项列表 -->
          <div
            class="wheel-options"
            :style="{
              transform: `translateY(${offset}px)`,
              transition: isAnimating ? 'transform 0.15s ease-out' : 'none'
            }"
          >
            <!-- 顶部占位 -->
            <div :style="{ height: `${paddingHeight}px` }"></div>

            <!-- 选项 -->
            <div
              v-for="(option, index) in options"
              :key="option.value"
              :id="`${listId}-option-${index}`"
              role="option"
              :aria-selected="option.value === modelValue"
              class="wheel-option flex items-center justify-center cursor-pointer transition-all duration-150"
              :class="[
                option.value === modelValue ? 'text-[#8B6F47] font-semibold' : 'text-gray-500',
                getOptionOpacity(index)
              ]"
              :style="{ height: `${itemHeight}px` }"
              @click.stop="handleSelect(option, index)"
            >
              {{ option.label }}
            </div>

            <!-- 底部占位 -->
            <div :style="{ height: `${paddingHeight}px` }"></div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { SelectInput, SelectOption, OptionValue } from './types'
/**
 * WheelPicker 滚动选择器组件
 * 功能：实现类似手机调闹钟时间的滚动选择效果
 * 特性：
 * - 点击展开/收起下拉框
 * - 支持鼠标滚轮滚动选择
 * - 支持点击选择
 * - 支持触摸拖动
 * - 惯性滚动动画
 * - 高亮选中区域
 * - 可清除选择
 * 遵循 `规范文档/前端规范文档.md`：使用 Tailwind CSS + Font Awesome
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  // v-model 绑定值
  modelValue: {
    type: [Number, String, null],
    default: null
  },
  // 选项列表 [{ label: '2024年', value: 2024 }, ...]
  options: {
    type: Array as PropType<SelectOption<string | number>[]>,
    default: () => [],
    required: true
  },
  // 占位符
  placeholder: {
    type: String,
    default: '请选择'
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 是否可清除
  clearable: {
    type: Boolean,
    default: false
  },
  // 可见选项数量（奇数）
  visibleCount: {
    type: Number,
    default: 5,
    validator: (value: number) => value % 2 === 1 && value >= 3
  },
  // 选项高度（像素）
  itemHeight: {
    type: Number,
    default: 40
  },
  // 尺寸
  size: {
    type: String,
    default: 'md',
    validator: (value: string) => ['sm', 'md', 'lg'].includes(value)
  },
  ariaLabel: {
    type: String,
    default: ''
  },
  id: {
    type: String,
    default: ''
  }
})

const emit = defineEmits<{ 'update:modelValue': [value: string | number | null]; change: [value: string | number | null] }>()

let nextWheelPickerId = 0
const generatedPickerId = `wheel-picker-${++nextWheelPickerId}`
const containerRef = ref<HTMLElement | null>(null)
const pickerRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const offset = ref(0)
const isAnimating = ref(false)
const isDragging = ref(false)
const startY = ref(0)
const startOffset = ref(0)
const pickerId = computed(() => props.id || generatedPickerId)
const listId = computed(() => `${pickerId.value}-list`)

// 计算属性：容器高度
const containerHeight = computed(() => props.itemHeight * props.visibleCount)

// 计算属性：上下内边距高度
const paddingHeight = computed(() => props.itemHeight * Math.floor(props.visibleCount / 2))

// 计算属性：高亮区域样式
const highlightStyle = computed(() => ({
  top: `${paddingHeight.value}px`,
  height: `${props.itemHeight}px`
}))

// 计算属性：当前选中索引
const currentIndex = computed(() => {
  const index = props.options.findIndex(opt => opt.value === props.modelValue)
  return index >= 0 ? index : 0
})

const activeOptionId = computed(() => `${listId.value}-option-${currentIndex.value}`)

// 计算属性：选中项的显示文本
const selectedLabel = computed(() => {
  if (props.modelValue === null || props.modelValue === '') return ''
  const option = props.options.find(opt => opt.value === props.modelValue)
  return option ? option.label : ''
})

// 计算属性：尺寸样式
const sizeClasses = computed(() => {
  const sizeMap: Record<string, string> = {
    sm: 'py-2 h-9 text-sm',
    md: 'py-2.5 h-[42px] text-[15px]',
    lg: 'py-3 h-12 text-base'
  }
  return sizeMap[props.size] || sizeMap.md
})

// 计算属性：获取选项透明度类名
const getOptionOpacity = (index: number) => {
  const distance = Math.abs(index - currentIndex.value)
  if (distance === 0) return 'opacity-100'
  if (distance === 1) return 'opacity-70'
  if (distance === 2) return 'opacity-50'
  return 'opacity-30'
}

// 切换下拉框
const toggleDropdown = () => {
  if (props.disabled) return
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => {
      scrollToIndex(currentIndex.value, false)
    })
  }
}

const handleTriggerKeydown = (event: KeyboardEvent) => {
  if (props.disabled) return
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (!isOpen.value) toggleDropdown()
    const direction = event.key === 'ArrowDown' ? 1 : -1
    const nextIndex = Math.max(0, Math.min(currentIndex.value + direction, props.options.length - 1))
    const option = props.options[nextIndex]
    if (option && option.value !== props.modelValue) {
      emit('update:modelValue', option.value)
      emit('change', option.value)
    }
    scrollToIndex(nextIndex)
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    toggleDropdown()
  } else if (event.key === 'Escape' && isOpen.value) {
    event.preventDefault()
    closeDropdown()
  }
}

// 关闭下拉框
const closeDropdown = () => {
  isOpen.value = false
}

// 滚动到指定索引
const scrollToIndex = (index: number, animate = true) => {
  if (props.disabled || props.options.length === 0) return

  // 确保索引在有效范围内
  index = Math.max(0, Math.min(index, props.options.length - 1))

  const targetOffset = -index * props.itemHeight

  if (animate) {
    isAnimating.value = true
  }

  offset.value = targetOffset

  if (animate) {
    setTimeout(() => {
      isAnimating.value = false
    }, 150)
  }
}

// 处理鼠标滚轮
const handleWheel = (e: WheelEvent) => {
  if (props.disabled || props.options.length === 0) return

  const delta = e.deltaY > 0 ? 1 : -1
  let newIndex = currentIndex.value + delta
  newIndex = Math.max(0, Math.min(props.options.length - 1, newIndex))

  // 直接更新值
  const option = props.options[newIndex]
  if (option && option.value !== props.modelValue) {
    emit('update:modelValue', option.value)
    emit('change', option.value)
  }

  scrollToIndex(newIndex)
}

// 处理鼠标按下（拖动开始）
const handleMouseDown = (e: MouseEvent) => {
  if (props.disabled || props.options.length === 0) return

  isDragging.value = true
  startY.value = e.clientY
  startOffset.value = offset.value
  isAnimating.value = false

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// 处理鼠标移动（拖动中）
const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return

  const deltaY = e.clientY - startY.value
  offset.value = startOffset.value + deltaY
}

// 处理鼠标释放（拖动结束）
const handleMouseUp = (e: MouseEvent) => {
  if (!isDragging.value) return

  isDragging.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)

  // 计算最近的索引并滚动到该位置
  const deltaY = e.clientY - startY.value
  const indexDelta = Math.round(-deltaY / props.itemHeight)
  let newIndex = currentIndex.value + indexDelta
  newIndex = Math.max(0, Math.min(props.options.length - 1, newIndex))

  // 更新值
  const option = props.options[newIndex]
  if (option && option.value !== props.modelValue) {
    emit('update:modelValue', option.value)
    emit('change', option.value)
  }

  scrollToIndex(newIndex)
}

// 处理触摸开始
const handleTouchStart = (e: TouchEvent) => {
  if (props.disabled || props.options.length === 0) return

  isDragging.value = true
  startY.value = e.touches[0].clientY
  startOffset.value = offset.value
  isAnimating.value = false

  document.addEventListener('touchmove', handleTouchMove, { passive: false })
  document.addEventListener('touchend', handleTouchEnd)
}

// 处理触摸移动
const handleTouchMove = (e: TouchEvent) => {
  if (!isDragging.value) return
  e.preventDefault()

  const deltaY = e.touches[0].clientY - startY.value
  offset.value = startOffset.value + deltaY
}

// 处理触摸结束
const handleTouchEnd = (e: TouchEvent) => {
  if (!isDragging.value) return

  isDragging.value = false
  document.removeEventListener('touchmove', handleTouchMove)
  document.removeEventListener('touchend', handleTouchEnd)

  // 计算最近的索引并滚动到该位置
  const deltaY = e.changedTouches[0].clientY - startY.value
  const indexDelta = Math.round(-deltaY / props.itemHeight)
  let newIndex = currentIndex.value + indexDelta
  newIndex = Math.max(0, Math.min(props.options.length - 1, newIndex))

  // 更新值
  const option = props.options[newIndex]
  if (option && option.value !== props.modelValue) {
    emit('update:modelValue', option.value)
    emit('change', option.value)
  }

  scrollToIndex(newIndex)
}

// 处理点击选项
const handleSelect = (option: SelectOption<string | number>, index: number) => {
  if (props.disabled) return

  emit('update:modelValue', option.value)
  emit('change', option.value)
  scrollToIndex(index)

  // 选择后关闭下拉框
  setTimeout(() => {
    closeDropdown()
  }, 150)
}

// 处理清除
const handleClear = () => {
  emit('update:modelValue', null)
  emit('change', null)
}

// 点击外部关闭下拉框
const handleClickOutside = (e: MouseEvent) => {
  if (!(e.target instanceof Node)) return
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    closeDropdown()
  }
}

// 监听 isOpen 变化，添加/移除点击外部监听
watch(isOpen, (val) => {
  if (val) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

// 监听 modelValue 变化，更新滚动位置
watch(() => props.modelValue, () => {
  if (isOpen.value) {
    nextTick(() => {
      scrollToIndex(currentIndex.value, true)
    })
  }
})

// 组件挂载时初始化位置
onMounted(() => {
  if (props.modelValue !== null && props.modelValue !== '') {
    scrollToIndex(currentIndex.value, false)
  }
})

// 组件卸载时清理事件监听
onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  document.removeEventListener('touchmove', handleTouchMove)
  document.removeEventListener('touchend', handleTouchEnd)
  document.removeEventListener('click', handleClickOutside)
})

// 暴露方法
defineExpose({
  scrollToIndex,
  open: () => { isOpen.value = true },
  close: closeDropdown
})
</script>

<style scoped>
.wheel-picker {
  user-select: none;
  -webkit-user-select: none;
}

.wheel-options {
  will-change: transform;
}

.wheel-option {
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

</style>
