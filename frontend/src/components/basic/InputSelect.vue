<template>
  <div class="w-full relative" ref="containerRef">
    <!-- 输入框区域 -->
    <div
      class="relative w-full flex items-center bg-white border border-gray-200 rounded-lg px-4 py-2.5 h-[42px] text-base transition-all duration-200 hover:border-[#8B6F47]/50"
      :class="{
        'border-[#8B6F47] shadow-[0_0_0_2px_rgba(139,111,71,0.2)]': visible,
        'has-value': modelValue,
        'opacity-50 cursor-not-allowed pointer-events-none': disabled
      }"
      @click="toggleMenu"
    >
      <input
        ref="inputRef"
        :id="inputId"
        type="text"
        role="combobox"
        v-model="inputValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :aria-disabled="disabled"
        :aria-expanded="visible"
        :aria-controls="listId"
        :aria-label="ariaLabel || undefined"
        aria-autocomplete="list"
        :aria-activedescendant="activeOptionId"
        class="w-full px-3 pr-8 border-none bg-transparent text-gray-800 font-inherit outline-none cursor-pointer"
        @focus="handleFocus"
        @input="handleInput"
        @change="handleChange"
        @keydown="handleKeydown"
      />

      <!-- 后缀图标 -->
      <div class="absolute right-4 top-1/2 -translate-y-1/2 flex items-center justify-center h-full text-gray-300">
        <button
          v-if="modelValue !== '' && modelValue !== null && modelValue !== undefined && clearable"
          type="button"
          class="cursor-pointer text-sm hover:text-gray-800 mr-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8B6F47]/30 rounded"
          aria-label="清除选择"
          @click.stop="handleClear"
        >
          <font-awesome-icon :icon="['fas', 'times-circle']" aria-hidden="true" />
        </button>
        <span
          class="transition-transform duration-150 flex items-center"
          :class="{ 'rotate-180': visible }"
        >
          <i class="border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[5px] border-t-current"></i>
        </span>
      </div>
    </div>

    <!-- 下拉菜单 -->
    <transition name="zoom-in-top">
      <div
        :id="listId"
        v-show="visible"
        role="listbox"
        :aria-label="placeholder"
        class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded shadow-lg z-50 max-h-60 overflow-y-auto"
      >
        <ul v-if="filteredOptions.length > 0" class="list-none p-1">
          <li
            v-for="(item, index) in filteredOptions"
            :key="index"
            :id="`${listId}-option-${index}`"
            role="option"
            :aria-selected="isSelected(item)"
            class="px-3 h-8 leading-8 cursor-pointer text-gray-800 whitespace-nowrap overflow-hidden text-ellipsis transition-colors duration-150 hover:bg-[#FBF7F2] hover:text-[#8B6F47]"
            :class="{
              'text-[#8B6F47] font-medium bg-[#8B6F47]/10': isSelected(item),
              'bg-[#FBF7F2] text-[#8B6F47]': activeIndex === index && !isSelected(item)
            }"
            @click="handleSelect(item)"
            @mouseenter="activeIndex = index"
          >
            {{ item.label }}
          </li>
        </ul>
        <div v-else class="px-3 py-2 text-base text-gray-400 text-center">
          无匹配数据
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { SelectInput, SelectOption, OptionValue } from './types'
/**
 * 自定义可输入下拉选择组件
 * 功能：提供支持下拉选择和手动输入的选择控件
 * 遵循KISS原则：原生实现，无重依赖
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

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

const containerRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const visible = ref(false)
const inputValue = ref('')
const activeIndex = ref(-1)

const inputId = computed(() => props.id || `input-select-${++nextInputSelectId}`)
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

// 点击外部关闭
const handleClickOutside = (event: MouseEvent) => {
  if (!(event.target instanceof Element)) return
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    visible.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/**
 * 自定义可输入下拉选择组件样式
 * 动画样式（其他样式已迁移到Tailwind CSS）
 */

/* 动画 */
.zoom-in-top-enter-active {
  transition: transform 0.25s cubic-bezier(0.23, 1, 0.32, 1), opacity 0.25s cubic-bezier(0.23, 1, 0.32, 1);
  transform-origin: center top;
}

.zoom-in-top-leave-active {
  transition: transform 0.25s cubic-bezier(0.55, 0.055, 0.675, 0.19), opacity 0.25s cubic-bezier(0.55, 0.055, 0.675, 0.19);
  transform-origin: center top;
}

.zoom-in-top-enter-from,
.zoom-in-top-leave-to {
  opacity: 0;
  transform: scaleY(0);
}
</style>
