<template>
  <div ref="rootRef" class="relative w-full">
    <!-- 输入框区域 -->
    <div
      ref="triggerRef"
      class="dropdown-control relative flex h-[42px] w-full items-center border px-3 text-[15px]"
      :class="{
        'dropdown-control--open': visible,
        'dropdown-control--disabled': disabled,
        'opacity-60 cursor-not-allowed pointer-events-none': disabled
      }"
      @click="toggleMenu"
    >
      <input
        ref="inputRef"
        :id="inputId"
        v-model="inputValue"
        type="text"
        role="combobox"
        :placeholder="placeholder"
        :disabled="disabled"
        :aria-disabled="disabled"
        :aria-expanded="visible"
        :aria-controls="listId"
        :aria-label="ariaLabel || undefined"
        aria-autocomplete="list"
        aria-haspopup="listbox"
        :aria-activedescendant="activeOptionId"
        class="min-w-0 flex-1 border-none bg-transparent px-0 text-[15px] text-gray-700 placeholder:text-gray-400 font-inherit outline-none cursor-text disabled:cursor-not-allowed"
        @focus="handleFocus"
        @input="handleInput"
        @change="handleChange"
        @keydown="handleKeydown"
      />

      <!-- 后缀图标 -->
      <div class="ml-2 flex flex-shrink-0 items-center justify-center gap-2 text-gray-400">
        <button
          v-if="modelValue !== '' && modelValue !== null && modelValue !== undefined && clearable"
          type="button"
          class="rounded text-gray-400 transition-colors hover:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8B6F47]/30"
          aria-label="清除选择"
          @click.stop="handleClear"
        >
          <font-awesome-icon :icon="['fas', 'times-circle']" class="text-xs" aria-hidden="true" />
        </button>
        <span
          class="flex items-center text-gray-400 transition-transform duration-200"
          :class="{ 'rotate-180 text-[#8B6F47]': visible }"
        >
          <font-awesome-icon :icon="['fas', 'chevron-down']" class="text-xs" aria-hidden="true" />
        </span>
      </div>
    </div>

    <!-- 下拉菜单：传送到 body，避免被弹窗或滚动容器裁剪 -->
    <teleport to="body">
      <transition name="select-dropdown">
        <div
          ref="dropdownRef"
          :id="listId"
          v-show="visible"
          role="listbox"
          :aria-label="placeholder"
          class="dropdown-panel fixed z-[99999] overflow-hidden"
        >
          <ul class="dropdown-scroll dropdown-option-list overflow-y-auto py-1">
            <li
              v-for="(item, index) in filteredOptions"
              :key="String(item.value)"
              :id="`${listId}-option-${index}`"
              role="option"
              :aria-selected="isSelected(item)"
              class="dropdown-option"
              :class="{
                'dropdown-option--selected': isSelected(item),
                'dropdown-option--active': !isSelected(item) && activeIndex === index
              }"
              @click="handleSelect(item)"
              @mouseenter="activeIndex = index"
            >
              <span class="min-w-0 truncate">{{ item.label }}</span>
              <font-awesome-icon
                v-if="isSelected(item)"
                :icon="['fas', 'check']"
                class="flex-shrink-0 text-xs text-[#8B6F47]"
                aria-hidden="true"
              />
            </li>

            <li
              v-if="filteredOptions.length === 0"
              class="dropdown-empty"
            >
              <font-awesome-icon :icon="['fas', 'folder-open']" class="mb-2 text-lg opacity-50" aria-hidden="true" />
              <p>暂无数据</p>
            </li>
          </ul>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { SelectOption } from './types'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

/**
 * 自定义可输入下拉选择组件
 * 功能：提供支持下拉选择和手动输入的选择控件
 * 遵循 KISS 原则：原生实现，无重依赖
 */

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array as PropType<(string | number | SelectOption<string | number>)[]>,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '请选择或输入'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: true
  },
  // 用于关联外部 FormLabel 的输入框 ID
  id: {
    type: String,
    default: ''
  },
  // 无法通过原生 label 关联时使用的可访问名称
  ariaLabel: {
    type: String,
    default: ''
  }
})

const emit = defineEmits<{ 'update:modelValue': [value: string | number]; change: [value: string | number] }>()

let nextInputSelectId = 0

const rootRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)
const visible = ref(false)
const inputValue = ref('')
const activeIndex = ref(-1)
const generatedInputId = `input-select-${++nextInputSelectId}`

const inputId = computed(() => props.id || generatedInputId)
const listId = computed(() => `${inputId.value}-list`)

// 标准化选项数据结构
const normalizedOptions = computed(() => {
  if (!Array.isArray(props.options)) return []
  return props.options.map(item => {
    if (typeof item === 'object' && item !== null) {
      return {
        label: String(item.label ?? item.value),
        value: item.value ?? item.label
      }
    }
    return { label: String(item), value: item }
  })
})

// 过滤后的选项
const filteredOptions = computed(() => {
  if (!inputValue.value) return normalizedOptions.value
  const keyword = inputValue.value.toLowerCase()
  return normalizedOptions.value.filter(item =>
    String(item.label).toLowerCase().includes(keyword)
  )
})

watch(filteredOptions, (options) => {
  if (options.length === 0) {
    activeIndex.value = -1
  } else if (activeIndex.value >= options.length) {
    activeIndex.value = options.length - 1
  }

  if (visible.value) void nextTick(updatePosition)
})

const activeOptionId = computed(() => {
  if (activeIndex.value < 0 || activeIndex.value >= filteredOptions.value.length) return undefined
  return `${listId.value}-option-${activeIndex.value}`
})

// 监听外部值变化，同步到输入框显示
watch(() => props.modelValue, (val) => {
  const option = normalizedOptions.value.find(opt => opt.value === val)
  // 如果找到对应的选项，显示label；否则直接显示值（支持手动输入的情况）
  inputValue.value = option ? option.label : String(val ?? '')
}, { immediate: true })

// 判断是否被选中
const isSelected = (item: SelectOption<string | number>) => {
  return props.modelValue === item.value
}

let justFocused = false

// 处理输入框聚焦
const handleFocus = () => {
  if (props.disabled) return
  if (!visible.value) {
    visible.value = true
    justFocused = true
    activeIndex.value = Math.max(0, filteredOptions.value.findIndex(option => option.value === props.modelValue))
    setTimeout(() => { justFocused = false }, 200)
  }
}

// 切换菜单显示状态
const toggleMenu = () => {
  if (props.disabled) return
  if (justFocused) return

  if (visible.value) {
    visible.value = false
  } else {
    visible.value = true
    activeIndex.value = Math.max(0, filteredOptions.value.findIndex(option => option.value === props.modelValue))
    inputRef.value?.focus()
  }
}

// 键盘操作：支持上下移动、回车选择和 Escape 关闭
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (!visible.value) visible.value = true
    const direction = event.key === 'ArrowDown' ? 1 : -1
    const nextIndex = activeIndex.value < 0
      ? (direction > 0 ? 0 : filteredOptions.value.length - 1)
      : activeIndex.value + direction
    activeIndex.value = filteredOptions.value.length > 0
      ? Math.max(0, Math.min(nextIndex, filteredOptions.value.length - 1))
      : -1
    return
  }

  if (event.key === 'Enter' && visible.value) {
    event.preventDefault()
    const option = filteredOptions.value[activeIndex.value]
    if (option) handleSelect(option)
    return
  }

  if (event.key === 'Escape' && visible.value) {
    event.preventDefault()
    visible.value = false
    activeIndex.value = -1
  }
}

// 处理输入事件
const handleInput = () => {
  if (props.disabled) return
  visible.value = true
  // 实时更新模式：手动输入也被视为一种值
  emit('update:modelValue', inputValue.value)
  emit('change', inputValue.value)
}

// 处理 change 事件 (回车或失焦由原生input触发)
const handleChange = () => {
  if (props.disabled) return
  emit('change', inputValue.value)
}

// 选择下拉项
const handleSelect = (item: SelectOption<string | number>) => {
  if (props.disabled) return
  inputValue.value = item.label
  emit('update:modelValue', item.value)
  emit('change', item.value)
  visible.value = false
  activeIndex.value = -1
}

// 清除值
const handleClear = () => {
  if (props.disabled) return
  inputValue.value = ''
  emit('update:modelValue', '')
  emit('change', '')
  visible.value = false
  activeIndex.value = -1
}

// 计算下拉框位置；空间不足时自动显示在控件上方。
const updatePosition = () => {
  if (!visible.value || !triggerRef.value || !dropdownRef.value) return

  const triggerRect = triggerRef.value.getBoundingClientRect()
  const menu = dropdownRef.value
  const gap = 8
  const width = triggerRect.width
  const maxLeft = Math.max(gap, window.innerWidth - width - gap)
  const left = Math.min(Math.max(triggerRect.left, gap), maxLeft)

  // 先设置宽度，再读取高度，确保位置计算使用最终尺寸。
  menu.style.width = `${width}px`
  const menuHeight = menu.offsetHeight
  const spaceBelow = window.innerHeight - triggerRect.bottom - gap
  const spaceAbove = triggerRect.top - gap
  const openAbove = spaceBelow < menuHeight && spaceAbove > spaceBelow
  const top = openAbove
    ? Math.max(gap, triggerRect.top - menuHeight - gap)
    : triggerRect.bottom + gap

  menu.style.top = `${top}px`
  menu.style.left = `${left}px`
}

// 点击外部关闭下拉
const handleClickOutside = (event: MouseEvent) => {
  if (!(event.target instanceof Element)) return
  if (rootRef.value?.contains(event.target) || dropdownRef.value?.contains(event.target)) return
  visible.value = false
}

watch(visible, (value) => {
  if (value) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
    void nextTick(updatePosition)
    return
  }

  document.removeEventListener('click', handleClickOutside)
  activeIndex.value = -1
})

onMounted(() => {
  window.addEventListener('resize', updatePosition)
  window.addEventListener('scroll', updatePosition, true)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('resize', updatePosition)
  window.removeEventListener('scroll', updatePosition, true)
})
</script>
