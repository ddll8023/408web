<template>
  <div class="relative w-full">
    <!-- Select 容器 -->
    <div
      class="relative flex items-center px-4 bg-white border rounded-lg transition-all duration-200 cursor-pointer select-none"
      :class="[
        containerClasses,
        {
          'opacity-50 cursor-not-allowed pointer-events-none': disabled
        }
      ]"
      @click="handleContainerClick"
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
      <div class="flex-shrink-0 px-3 flex items-center justify-center h-full">
        <span
          class="transition-transform duration-200 text-gray-400"
          :class="{ 'rotate-180': visible }"
        >
          <font-awesome-icon :icon="['fas', 'chevron-down']" class="text-xs" />
        </span>
      </div>

      <!-- 原生 select（用于表单提交和无障碍） -->
      <select
        ref="selectRef"
        :value="modelValue"
        :disabled="disabled"
        class="absolute inset-0 w-full h-full appearance-none cursor-pointer pointer-events-none bg-transparent border-none outline-none"
        style="color: transparent; font-size: 0; line-height: 0;"
        @change="handleChange"
      >
        <option v-if="!required" value="">请选择</option>
        <option
          v-for="option in normalizedOptions"
          :key="option.value"
          :value="option.value"
        >
          {{ option.label }}
        </option>
      </select>
    </div>

    <!-- 下拉选项列表 -->
    <transition name="select-dropdown">
      <div
        v-show="visible"
        class="absolute top-full left-0 right-0 mt-1.5 bg-white border border-gray-100 rounded-lg shadow-lg z-50 overflow-hidden"
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
            class="w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-[#8B6F47]/20 focus:border-[#8B6F47] transition-all duration-200"
            placeholder="搜索..."
            @click.stop
            @keydown.esc="visible = false"
          />
        </div>

        <!-- 选项列表 -->
        <ul class="max-h-60 overflow-y-auto py-1">
          <li
            v-for="option in filteredOptions"
            :key="option.value"
            class="px-4 py-2.5 text-base text-gray-700 cursor-pointer transition-colors duration-150"
            :class="[
              option.value === modelValue
                ? 'text-[#8B6F47] font-medium bg-[#8B6F47]/5'
                : 'hover:bg-gray-50'
            ]"
            @click="handleSelect(option)"
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
  </div>
</template>

<script setup>
/**
 * Select 下拉选择组件
 * 功能：封装原生select，提供统一的视觉样式和交互体验
 * 遵循KISS原则：简洁实现，按需启用高级功能
 * 遵循YAGNI原则：仅实现实际使用的props
 * 与InputSelect的区别：此组件为纯选择器，InputSelect支持输入
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  // v-model 绑定值
  modelValue: {
    type: [String, Number, Boolean],
    default: ''
  },
  // 选项列表
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
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  // 是否显示边框
  bordered: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const selectRef = ref(null)
const visible = ref(false)
const filterText = ref('')

// 标准化选项数据结构
const normalizedOptions = computed(() => {
  if (!props.options) return []
  return props.options.map(item => {
    if (typeof item === 'object' && item !== null) {
      return {
        label: item.label ?? item.name ?? String(item.value),
        value: item.value ?? item.id ?? item
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
  const sizeClasses = {
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

// 监听外部值变化
watch(() => props.modelValue, () => {
  // 值变化时同步（如果需要）
})

// 点击其他地方关闭下拉
const handleClickOutside = (event) => {
  const container = selectRef.value?.closest('.relative')
  if (container && !container.contains(event.target)) {
    visible.value = false
    filterText.value = ''
  }
}

// 容器点击处理
const handleContainerClick = () => {
  if (!props.disabled) {
    visible.value = !visible.value
    if (!visible.value) {
      filterText.value = ''
    }
  }
}

// 选择选项
const handleSelect = (option) => {
  emit('update:modelValue', option.value)
  emit('change', option.value)
  visible.value = false
  filterText.value = ''
}

// 原生 select change 事件
const handleChange = (event) => {
  const value = event.target.value
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听可见状态变化，添加/移除点击外部监听
watch(visible, (val) => {
  if (val) {
    setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
  } else {
    document.removeEventListener('click', handleClickOutside)
    filterText.value = ''
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
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
