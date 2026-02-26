<template>
  <div class="flex items-center gap-1">
    <!-- 减少按钮 -->
    <button
      type="button"
      class="w-8 h-[42px] flex items-center justify-center rounded-md border border-gray-200 bg-white text-gray-500 hover:border-[#8B6F47] hover:text-[#8B6F47] transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:border-gray-200 disabled:hover:text-gray-500"
      :disabled="disabled || modelValue <= min"
      @click="decrement"
    >
      <font-awesome-icon :icon="['fas', 'minus-circle']" class="text-xs" />
    </button>

    <!-- 输入框 -->
    <input
      ref="inputRef"
      type="number"
      class="w-16 h-[42px] text-center text-sm border border-gray-200 rounded-md bg-white focus:outline-none focus:border-[#8B6F47] focus:ring-2 focus:ring-[#8B6F47]/20 transition-all duration-200 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
      :value="modelValue"
      :min="min"
      :max="max"
      :disabled="disabled"
      :placeholder="placeholder"
      @input="handleInput"
      @blur="handleBlur"
      @focus="handleFocus"
    />

    <!-- 增加按钮 -->
    <button
      type="button"
      class="w-8 h-[42px] flex items-center justify-center rounded-md border border-gray-200 bg-white text-gray-500 hover:border-[#8B6F47] hover:text-[#8B6F47] transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:border-gray-200 disabled:hover:text-gray-500"
      :disabled="disabled || modelValue >= max"
      @click="increment"
    >
      <font-awesome-icon :icon="['fas', 'plus']" class="text-xs" />
    </button>
  </div>
</template>

<script setup>
/**
 * InputNumber 数字输入组件
 * 功能：替代 Element Plus 的 el-input-number，支持数值增减和直接输入
 * 遵循 KISS 原则：简洁实现，只包含必需功能
 */
import { ref, watch } from 'vue'

const props = defineProps({
  // v-model 绑定值
  modelValue: {
    type: Number,
    default: 0
  },
  // 最小值
  min: {
    type: Number,
    default: 0
  },
  // 最大值
  max: {
    type: Number,
    default: 9999
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 步进值
  step: {
    type: Number,
    default: 1
  },
  // 占位符
  placeholder: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'blur', 'focus'])

const inputRef = ref(null)

// 减少数值
const decrement = () => {
  if (props.disabled) return
  const newValue = props.modelValue - props.step
  if (newValue >= props.min) {
    emit('update:modelValue', newValue)
    emit('change', newValue)
  }
}

// 增加数值
const increment = () => {
  if (props.disabled) return
  const newValue = props.modelValue + props.step
  if (newValue <= props.max) {
    emit('update:modelValue', newValue)
    emit('change', newValue)
  }
}

// 处理输入
const handleInput = (event) => {
  let value = parseInt(event.target.value) || props.min
  // 限制范围
  if (value < props.min) value = props.min
  if (value > props.max) value = props.max
  emit('update:modelValue', value)
  emit('change', value)
}

// 处理失焦
const handleBlur = (event) => {
  emit('blur', event)
}

// 处理聚焦
const handleFocus = (event) => {
  emit('focus', event)
}

// 暴露方法
defineExpose({
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur()
})
</script>

<style scoped>
/* 隐藏 number 输入框的上下箭头 */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

input[type="number"] {
  -moz-appearance: textfield;
}
</style>
