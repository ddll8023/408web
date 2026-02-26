<template>
  <div class="wheel-picker-container relative" ref="containerRef">
    <!-- 触发器（显示选中值或占位符） -->
    <div
      class="wheel-picker-trigger relative flex items-center px-4 bg-white border border-gray-200 rounded-lg cursor-pointer transition-all duration-200"
      :class="[
        { 'opacity-50 cursor-not-allowed pointer-events-none': disabled },
        { 'border-[#8B6F47] ring-2 ring-[#8B6F47]/20': isOpen },
        sizeClasses
      ]"
      @click="toggleDropdown"
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
        />
      </div>

      <!-- 清除按钮 -->
      <div
        v-if="clearable && modelValue !== null && modelValue !== '' && !isOpen"
        class="ml-2 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors"
        @click.stop="handleClear"
      >
        <font-awesome-icon :icon="['fas', 'times-circle']" class="text-sm" />
      </div>
    </div>

    <!-- 下拉滚动选择器 -->
    <transition name="wheel-dropdown">
      <div
        v-show="isOpen"
        class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden"
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
            <div class="h-full bg-[#8B6F47]/10 border-y-2 border-[#8B6F47]/30 rounded-sm"></div>
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

<script setup>
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
 * 遵循前端页面规范：使用 Tailwind CSS + Font Awesome
 */
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  // v-model 绑定值
  modelValue: {
    type: [Number, String],
    default: null
  },
  // 选项列表 [{ label: '2024年', value: 2024 }, ...]
  options: {
    type: Array,
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
    validator: (value) => value % 2 === 1 && value >= 3
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
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const containerRef = ref(null)
const pickerRef = ref(null)
const isOpen = ref(false)
const offset = ref(0)
const isAnimating = ref(false)
const isDragging = ref(false)
const startY = ref(0)
const startOffset = ref(0)

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

// 计算属性：选中项的显示文本
const selectedLabel = computed(() => {
  if (props.modelValue === null || props.modelValue === '') return ''
  const option = props.options.find(opt => opt.value === props.modelValue)
  return option ? option.label : ''
})

// 计算属性：尺寸样式
const sizeClasses = computed(() => {
  const sizeMap = {
    sm: 'py-2 h-9 text-sm',
    md: 'py-2.5 h-[42px] text-base',
    lg: 'py-3 h-12 text-lg'
  }
  return sizeMap[props.size] || sizeMap.md
})

// 计算属性：获取选项透明度类名
const getOptionOpacity = (index) => {
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

// 关闭下拉框
const closeDropdown = () => {
  isOpen.value = false
}

// 滚动到指定索引
const scrollToIndex = (index, animate = true) => {
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
const handleWheel = (e) => {
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
const handleMouseDown = (e) => {
  if (props.disabled || props.options.length === 0) return

  isDragging.value = true
  startY.value = e.clientY
  startOffset.value = offset.value
  isAnimating.value = false

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

// 处理鼠标移动（拖动中）
const handleMouseMove = (e) => {
  if (!isDragging.value) return

  const deltaY = e.clientY - startY.value
  offset.value = startOffset.value + deltaY
}

// 处理鼠标释放（拖动结束）
const handleMouseUp = (e) => {
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
const handleTouchStart = (e) => {
  if (props.disabled || props.options.length === 0) return

  isDragging.value = true
  startY.value = e.touches[0].clientY
  startOffset.value = offset.value
  isAnimating.value = false

  document.addEventListener('touchmove', handleTouchMove, { passive: false })
  document.addEventListener('touchend', handleTouchEnd)
}

// 处理触摸移动
const handleTouchMove = (e) => {
  if (!isDragging.value) return
  e.preventDefault()

  const deltaY = e.touches[0].clientY - startY.value
  offset.value = startOffset.value + deltaY
}

// 处理触摸结束
const handleTouchEnd = (e) => {
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
const handleSelect = (option, index) => {
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
const handleClickOutside = (e) => {
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

/* 下拉动画 */
.wheel-dropdown-enter-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.wheel-dropdown-leave-active {
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

.wheel-dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.wheel-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>