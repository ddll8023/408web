<template>
  <div class="custom-input-select" ref="containerRef">
    <!-- 输入框区域 -->
    <div 
      class="select-trigger" 
      :class="{ 'is-focused': visible, 'has-value': modelValue }"
      @click="toggleMenu"
    >
      <input
        ref="inputRef"
        type="text"
        v-model="inputValue"
        :placeholder="placeholder"
        class="select-input"
        @focus="handleFocus"
        @input="handleInput"
        @change="handleChange"
      />
      
      <!-- 后缀图标 -->
      <div class="suffix-wrapper">
        <span 
          v-if="modelValue && clearable" 
          class="icon-clear" 
          @click.stop="handleClear"
        >
          ×
        </span>
        <span 
          class="icon-arrow" 
          :class="{ 'is-reverse': visible }"
        >
          <i class="arrow-down"></i>
        </span>
      </div>
    </div>

    <!-- 下拉菜单 -->
    <transition name="zoom-in-top">
      <div v-show="visible" class="select-dropdown">
        <ul v-if="filteredOptions.length > 0" class="select-dropdown__list">
          <li
            v-for="(item, index) in filteredOptions"
            :key="index"
            class="select-dropdown__item"
            :class="{ 'is-selected': isSelected(item) }"
            @click="handleSelect(item)"
          >
            {{ item.label }}
          </li>
        </ul>
        <div v-else class="select-dropdown__empty">
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
  if (!props.options) return []
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
 * 已迁移至纯CSS
 */

.custom-input-select {
  position: relative;
  width: 100%;
  font-size: 14px;
}

.select-trigger {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  background-color: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.select-trigger:hover {
  border-color: #c8c9cc;
}

.select-trigger:hover .icon-clear {
  display: block;
}

.select-trigger:hover .icon-arrow {
  display: none;
}

.select-trigger.is-focused {
  border-color: #8B6F47;
  box-shadow: 0 0 0 2px rgba(139, 111, 71, 0.2);
}

.select-input {
  width: 100%;
  height: 32px;
  padding: 0 16px;
  padding-right: 30px;
  border: none;
  background: transparent;
  color: #333;
  font-size: inherit;
  outline: none;
  cursor: pointer;
}

.select-input::placeholder {
  color: #a8abb2;
}

.suffix-wrapper {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #a8abb2;
}

.icon-arrow {
  transition: transform 0.15s ease;
  display: flex;
  align-items: center;
}

.icon-arrow.is-reverse {
  transform: rotate(180deg);
}

.arrow-down {
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 5px solid currentColor;
}

.icon-clear {
  display: none;
  cursor: pointer;
  font-size: 14px;
}

.icon-clear:hover {
  color: #333;
}

/* 下拉菜单 */
.select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1000;
  width: 100%;
  margin-top: 4px;
  background-color: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  max-height: 200px;
  overflow-y: auto;
}

.select-dropdown__list {
  list-style: none;
  padding: 4px 0;
  margin: 0;
}

.select-dropdown__item {
  padding: 0 16px;
  height: 34px;
  line-height: 34px;
  cursor: pointer;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background-color 0.15s ease;
}

.select-dropdown__item:hover {
  background-color: #f5f7fa;
}

.select-dropdown__item.is-selected {
  color: #8B6F47;
  font-weight: 500;
  background-color: #f5f7fa;
}

.select-dropdown__empty {
  padding: 10px 0;
  margin: 0;
  text-align: center;
  color: #999;
  font-size: 12px;
}

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
