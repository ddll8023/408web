<template>
  <div class="w-full relative" ref="containerRef">
    <!-- 输入框区域 -->
    <div
      class="relative w-full flex items-center bg-white border border-gray-200 rounded-lg px-4 py-2.5 h-[42px] text-base transition-all duration-200 hover:border-[#8B6F47]/50"
      :class="{ 'border-[#8B6F47] shadow-[0_0_0_2px_rgba(139,111,71,0.2)]': visible, 'has-value': modelValue }"
      @click="toggleMenu"
    >
      <input
        ref="inputRef"
        type="text"
        v-model="inputValue"
        :placeholder="placeholder"
        class="w-full px-3 pr-8 border-none bg-transparent text-gray-800 font-inherit outline-none cursor-pointer"
        @focus="handleFocus"
        @input="handleInput"
        @change="handleChange"
      />

      <!-- 后缀图标 -->
      <div class="absolute right-4 top-1/2 -translate-y-1/2 flex items-center justify-center h-full text-gray-300">
        <span
          v-if="modelValue && clearable"
          class="hidden cursor-pointer text-sm hover:text-gray-800 mr-2"
          @click.stop="handleClear"
        >
          ×
        </span>
        <span
          class="transition-transform duration-15 flex items-center"
          :class="{ 'rotate-180': visible }"
        >
          <i class="border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[5px] border-t-currentColor"></i>
        </span>
      </div>
    </div>

    <!-- 下拉菜单 -->
    <transition name="zoom-in-top">
      <div v-show="visible" class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded shadow-lg z-50 max-h-60 overflow-y-auto">
        <ul v-if="filteredOptions.length > 0" class="list-none p-1">
          <li
            v-for="(item, index) in filteredOptions"
            :key="index"
            class="px-3 h-8 leading-8 cursor-pointer text-gray-800 whitespace-nowrap overflow-hidden text-ellipsis transition-colors duration-15"
            :class="{ 'text-[#8B6F47] font-medium bg-gray-100': isSelected(item) }"
            @click="handleSelect(item)"
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

<script setup>
/**
 * 自定义可输入下拉选择组件
 * 功能：替代Element Plus Select，支持下拉选择和手动输入
 * 遵循KISS原则：原生实现，无重依赖
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '请选择或输入'
  },
  clearable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const containerRef = ref(null)
const visible = ref(false)
const inputValue = ref('')

// 标准化选项数据结构
const normalizedOptions = computed(() => {
  if (!Array.isArray(props.options)) return []
  return props.options.map(item => {
    if (typeof item === 'object' && item !== null) {
      return {
        label: item.label || item.value,
        value: item.value || item.label
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

// 监听外部值变化，同步到输入框显示
watch(() => props.modelValue, (val) => {
  const option = normalizedOptions.value.find(opt => opt.value === val)
  // 如果找到对应的选项，显示label；否则直接显示值（支持手动输入的情况）
  inputValue.value = option ? option.label : (val || '')
}, { immediate: true })

// 判断是否被选中
const isSelected = (item) => {
  return props.modelValue === item.value
}

let justFocused = false

// 处理输入框聚焦
const handleFocus = () => {
  if (!visible.value) {
    visible.value = true
    justFocused = true
    setTimeout(() => { justFocused = false }, 200)
  }
}

// 切换菜单显示状态
const toggleMenu = () => {
  if (justFocused) return
  
  if (visible.value) {
    visible.value = false
  } else {
    visible.value = true
    if (containerRef.value.querySelector('input')) {
      containerRef.value.querySelector('input').focus()
    }
  }
}

// 处理输入事件
const handleInput = () => {
  visible.value = true
  // 实时更新模式：手动输入也被视为一种值
  emit('update:modelValue', inputValue.value)
  emit('change', inputValue.value)
}

// 处理 change 事件 (回车或失焦由原生input触发)
const handleChange = () => {
  emit('change', inputValue.value)
}

// 选择下拉项
const handleSelect = (item) => {
  inputValue.value = item.label
  emit('update:modelValue', item.value)
  emit('change', item.value)
  visible.value = false
}

// 清除值
const handleClear = () => {
  inputValue.value = ''
  emit('update:modelValue', '')
  emit('change', '')
}

// 点击外部关闭
const handleClickOutside = (event) => {
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
