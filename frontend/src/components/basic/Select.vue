<template>
  <div ref="rootRef" class="relative w-full">
    <!-- Select 容器 -->
    <div
      ref="triggerRef"
      class="relative flex items-center px-4 bg-white border rounded-lg transition-all duration-200 cursor-pointer select-none"
      :class="[
        containerClasses,
        {
          'opacity-50 cursor-not-allowed pointer-events-none': disabled,
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8B6F47]/20': !disabled
        }
      ]"
      role="combobox"
      :tabindex="disabled ? -1 : 0"
      :aria-expanded="visible"
      aria-haspopup="listbox"
      :aria-controls="listId"
      :aria-disabled="disabled"
      :aria-activedescendant="activeOptionId"
      :aria-label="ariaLabel || undefined"
      @click="handleContainerClick"
      @keydown="handleContainerKeydown"
    >
      <!-- 选中值显示 -->
      <div class="flex-1 min-w-0 px-4">
        <span
          v-if="selectedLabel"
          class="block w-full text-gray-700 text-base truncate"
        >
          {{ selectedLabel }}
        </span>
        <span
          v-else
          class="block w-full text-gray-400 text-base truncate"
        >
          {{ placeholder }}
        </span>
      </div>

      <!-- 下拉箭头图标 -->
      <div class="flex-shrink-0 px-3 flex items-center justify-center h-full gap-2">
        <button
          v-if="clearable && hasValue && !disabled"
          type="button"
          class="text-gray-400 hover:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8B6F47]/30 rounded"
          aria-label="清除选择"
          @click.stop="handleClear"
          @keydown.stop
        >
          <font-awesome-icon :icon="['fas', 'times-circle']" class="text-xs" aria-hidden="true" />
        </button>
        <span
          class="transition-transform duration-200 text-gray-400"
          :class="{ 'rotate-180': visible }"
        >
          <font-awesome-icon :icon="['fas', 'chevron-down']" class="text-xs" aria-hidden="true" />
        </span>
      </div>

      <!-- 原生 select（用于表单提交和无障碍） -->
      <select
        ref="selectRef"
        :id="inputId"
        :value="modelValue"
        :disabled="disabled"
        :required="required"
        tabindex="-1"
        class="absolute inset-0 w-full h-full appearance-none cursor-pointer pointer-events-none bg-transparent border-none outline-none"
        style="color: transparent; font-size: 0; line-height: 0;"
        @change="handleChange"
      >
        <option v-if="!required" value="">请选择</option>
        <option
          v-for="option in normalizedOptions"
          :key="String(option.value)"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>
    </div>

    <!-- 下拉选项列表：传送到 body，避免被弹窗内容区的 overflow 裁剪 -->
    <teleport to="body">
      <transition name="select-dropdown">
        <div
          ref="dropdownRef"
          :id="listId"
          v-show="visible"
          role="listbox"
          :aria-label="placeholder"
          class="fixed bg-white border border-gray-100 rounded-lg shadow-lg z-[99999] overflow-hidden"
          :class="dropdownClasses"
        >
        <!-- 搜索框（可选） -->
        <div
          v-if="filterable"
          class="p-2 border-b border-gray-100"
        >
          <input
            v-model="filterText"
            type="text"
            aria-label="筛选选项"
            class="w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-[#8B6F47]/20 focus:border-[#8B6F47] transition-all duration-200"
            placeholder="搜索..."
            @click.stop
            @keydown.esc="visible = false"
          />
        </div>

        <!-- 选项列表 -->
        <ul class="max-h-60 overflow-y-auto py-1">
          <li
            v-for="(option, index) in filteredOptions"
            :key="String(option.value)"
            :id="`${listId}-option-${index}`"
            role="option"
            :aria-selected="option.value === modelValue"
            class="px-4 py-2.5 text-base text-gray-700 cursor-pointer transition-colors duration-150"
            :class="[
              option.value === modelValue
                ? 'text-[#8B6F47] font-medium bg-[#8B6F47]/5'
                : 'hover:bg-gray-50'
            ]"
            @click="handleSelect(option)"
            @mouseenter="activeIndex = index"
          >
            <div class="flex items-center justify-between">
              <span class="truncate">{{ option.label }}</span>
              <!-- 选中标记 -->
              <span
                v-if="option.value === modelValue"
                class="text-[#8B6F47]"
              >
                <font-awesome-icon :icon="['fas', 'check']" class="text-xs" />
              </span>
            </div>
          </li>

          <!-- 空状态 -->
          <li
            v-if="filteredOptions.length === 0"
            class="px-4 py-6 text-base text-gray-400 text-center"
          >
            <font-awesome-icon :icon="['fas', 'folder-open']" class="text-lg mb-2 opacity-50" />
            <p>暂无数据</p>
          </li>
        </ul>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts" generic="V extends OptionValue">
import type { PropType } from 'vue'
import type { SelectInput, SelectOption, OptionValue } from './types'
/**
 * Select 下拉选择组件
 * 功能：封装原生select，提供统一的视觉样式和交互体验
 * 遵循KISS原则：简洁实现，按需启用高级功能
 * 遵循YAGNI原则：仅实现实际使用的props
 * 与InputSelect的区别：此组件为纯选择器，InputSelect支持输入
 */
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // v-model 绑定值
  modelValue: {
    type: [String, Number, Boolean, null] as PropType<V | null>,
    default: ''
  },
  // 选项列表
  options: {
    type: Array as PropType<SelectInput<V>[]>,
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
  // 是否必选（影响空值验证）
  required: {
    type: Boolean,
    default: false
  },
  // 是否支持搜索过滤
  filterable: {
    type: Boolean,
    default: false
  },
  // 是否支持清除
  clearable: {
    type: Boolean,
    default: false
  },
  // 尺寸
  size: {
    type: String,
    default: 'md',
    validator: (value: string) => ['sm', 'md', 'lg'].includes(value)
  },
  // 是否显示边框
  bordered: {
    type: Boolean,
    default: true
  },
  // 用于关联外部 FormLabel 的控件 ID
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

const emit = defineEmits<{ 'update:modelValue': [value: V | '']; change: [value: V | ''] }>()

let nextSelectId = 0

const rootRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLElement | null>(null)
const selectRef = ref<HTMLSelectElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)
const visible = ref(false)
const filterText = ref('')
const activeIndex = ref(-1)

const inputId = computed(() => props.id || `select-${++nextSelectId}`)
const listId = computed(() => `${inputId.value}-list`)
const hasValue = computed(() => props.modelValue !== '' && props.modelValue !== null && props.modelValue !== undefined)

// 标准化选项数据结构
const normalizedOptions = computed<SelectOption<V | ''>[]>(() => {
  if (!props.options) return []
  return props.options.map(item => {
    if (typeof item === 'object' && item !== null) {
      return {
        label: item.label ?? item.name ?? String(item.value),
        value: item.value ?? item.id ?? ''
      }
    }
    return { label: String(item), value: item }
  })
})

// 过滤后的选项
const filteredOptions = computed(() => {
  if (!props.filterable || !filterText.value) return normalizedOptions.value
  const keyword = filterText.value.toLowerCase()
  return normalizedOptions.value.filter(item =>
    String(item.label).toLowerCase().includes(keyword)
  )
})

watch(filteredOptions, (options) => {
  if (options.length === 0) {
    activeIndex.value = -1
    return
  }
  if (activeIndex.value >= options.length) activeIndex.value = options.length - 1
})

const activeOptionId = computed(() => {
  if (activeIndex.value < 0 || activeIndex.value >= filteredOptions.value.length) return undefined
  return `${listId.value}-option-${activeIndex.value}`
})

// 选中项的显示文本
const selectedLabel = computed(() => {
  if (props.modelValue === '' || props.modelValue === null || props.modelValue === undefined) {
    return ''
  }
  const option = normalizedOptions.value.find(opt => opt.value === props.modelValue)
  return option ? option.label : String(props.modelValue)
})

// 容器样式
const containerClasses = computed(() => {
  const sizeClasses: Record<string, string> = {
    sm: 'py-2 h-9 text-base',
    md: 'py-2.5 h-[42px] text-base',
    lg: 'py-3 text-lg'
  }

  const borderClasses = props.bordered
    ? 'border-gray-200 hover:border-[#8B6F47]/50 focus-within:border-[#8B6F47] focus-within:ring-2 focus-within:ring-[#8B6F47]/20'
    : 'border-transparent bg-transparent hover:bg-gray-50'

  return `${sizeClasses[props.size]} ${borderClasses}`
})

// 下拉框样式
const dropdownClasses = computed(() => {
  return 'border border-gray-100 shadow-[0_4px_12px_rgba(0,0,0,0.08)]'
})

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

// 点击其他地方关闭下拉
const handleClickOutside = (event: MouseEvent) => {
  if (!(event.target instanceof Element)) return
  if (rootRef.value?.contains(event.target) || dropdownRef.value?.contains(event.target)) return
  visible.value = false
  filterText.value = ''
}

// 容器点击处理
const handleContainerClick = () => {
  if (!props.disabled) {
    visible.value = !visible.value
    if (visible.value) {
      activeIndex.value = Math.max(0, filteredOptions.value.findIndex(option => option.value === props.modelValue))
    }
    if (!visible.value) {
      filterText.value = ''
      activeIndex.value = -1
    }
  }
}

// 键盘操作：支持展开、选择、上下移动和 Escape 关闭
const handleContainerKeydown = (event: KeyboardEvent) => {
  if (props.disabled) return

  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (!visible.value) {
      visible.value = true
      activeIndex.value = Math.max(0, filteredOptions.value.findIndex(option => option.value === props.modelValue))
      return
    }

    const direction = event.key === 'ArrowDown' ? 1 : -1
    const nextIndex = activeIndex.value < 0
      ? (direction > 0 ? 0 : filteredOptions.value.length - 1)
      : activeIndex.value + direction
    activeIndex.value = Math.max(0, Math.min(nextIndex, filteredOptions.value.length - 1))
    return
  }

  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    if (!visible.value) {
      handleContainerClick()
      return
    }
    const option = filteredOptions.value[activeIndex.value]
    if (option) handleSelect(option)
    return
  }

  if (event.key === 'Escape' && visible.value) {
    event.preventDefault()
    visible.value = false
    filterText.value = ''
    activeIndex.value = -1
  }
}

// 选择选项
const handleSelect = (option: SelectOption<V | ''>) => {
  emit('update:modelValue', option.value)
  emit('change', option.value)
  visible.value = false
  filterText.value = ''
  activeIndex.value = -1
}

// 清除选择
const handleClear = () => {
  const emptyValue = '' as V | ''
  emit('update:modelValue', emptyValue)
  emit('change', emptyValue)
  visible.value = false
  filterText.value = ''
  activeIndex.value = -1
}

// 原生 select change 事件
const handleChange = (event: Event) => {
  if (!(event.target instanceof HTMLSelectElement)) return
  const rawValue = event.target.value
  const selected = normalizedOptions.value.find(option => String(option.value) === rawValue)
  const value = selected?.value ?? ''
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听可见状态变化，添加/移除点击外部监听
watch(visible, (val) => {
  if (val) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
    void nextTick(updatePosition)
  } else {
    document.removeEventListener('click', handleClickOutside)
    filterText.value = ''
    activeIndex.value = -1
  }
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

<style scoped>
/* 下拉动画 */
.select-dropdown-enter-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.select-dropdown-leave-active {
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

.select-dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}

.select-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* 滚动条样式 */
.max-h-60::-webkit-scrollbar {
  width: 6px;
}

.max-h-60::-webkit-scrollbar-track {
  background: #f9fafb;
}

.max-h-60::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.max-h-60::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
