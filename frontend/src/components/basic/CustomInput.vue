<template>
  <div class="flex flex-col gap-1">
    <!-- 标签 -->
    <label v-if="label" :for="inputId" class="text-sm font-medium text-gray-700">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>

    <!-- 输入框容器 -->
    <div class="relative">
      <input
        :id="inputId"
        ref="inputRef"
        :type="computedType"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :class="inputClasses"
        @input="handleInput"
        @blur="handleBlur"
        @focus="handleFocus"
        @keydown.enter="handleEnter"
      />

      <!-- 后缀图标：清空按钮 -->
      <button
        v-if="clearable && modelValue && !disabled"
        type="button"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
        @click="handleClear"
      >
        <font-awesome-icon :icon="['fas', 'times-circle']" class="text-sm" />
      </button>

      <!-- 后缀图标：密码显示切换 -->
      <button
        v-if="type === 'password'"
        type="button"
        class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
        @click="showPassword = !showPassword"
      >
        <font-awesome-icon :icon="showPassword ? ['fas', 'eye-slash'] : ['fas', 'eye']" class="text-sm" />
      </button>
    </div>

    <!-- 错误信息 -->
    <span v-if="error" class="text-sm text-red-500">{{ error }}</span>
  </div>
</template>

<script setup>
/**
 * CustomInput 自定义输入框组件
 * 功能：替代 Element Plus 的 el-input，支持密码显示切换、清空按钮、错误提示
 * 遵循 KISS 原则：简洁实现，只包含必需功能
 * 遵循 YAGNI 原则：只实现项目实际使用的 props
 */
import { ref, computed } from 'vue'

const props = defineProps({
  // v-model 绑定值
  modelValue: {
    type: [String, Number],
    default: ''
  },
  // 输入框类型
  type: {
    type: String,
    default: 'text',
    validator: (value) => ['text', 'password', 'email', 'number', 'tel', 'url'].includes(value)
  },
  // 占位符
  placeholder: {
    type: String,
    default: ''
  },
  // 标签文本
  label: {
    type: String,
    default: ''
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 是否可清空
  clearable: {
    type: Boolean,
    default: false
  },
  // 是否必填（仅用于显示 * 标记）
  required: {
    type: Boolean,
    default: false
  },
  // 错误信息
  error: {
    type: String,
    default: ''
  },
  // 输入框 ID（用于关联 label）
  id: {
    type: String,
    default: ''
  },
  // 尺寸
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue', 'blur', 'focus', 'enter', 'clear'])

const inputRef = ref(null)
const showPassword = ref(false)

// 生成唯一 ID
const inputId = computed(() => props.id || `input-${Math.random().toString(36).substr(2, 9)}`)

// 计算实际类型
const computedType = computed(() => {
  if (props.type === 'password') {
    return showPassword.value ? 'text' : 'password'
  }
  return props.type
})

// 输入框样式类名
const inputClasses = computed(() => {
  const baseClasses = 'w-full border rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-0'

  // 尺寸样式
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm h-9',
    md: 'px-4 py-2.5 text-base h-[42px]',
    lg: 'px-4 py-3 text-lg h-12'
  }

  // 状态样式
  const stateClasses = props.error
    ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
    : 'border-gray-300 focus:border-[#8B6F47] focus:ring-[#8B6F47]/20'

  const disabledClasses = props.disabled
    ? 'bg-gray-100 cursor-not-allowed opacity-60'
    : 'bg-white'

  return `${baseClasses} ${sizeClasses[props.size]} ${stateClasses} ${disabledClasses}`
})

// 处理输入事件
const handleInput = (event) => {
  const value = event.target.value
  emit('update:modelValue', value)
}

// 处理失焦事件
const handleBlur = (event) => {
  emit('blur', event)
}

// 处理聚焦事件
const handleFocus = (event) => {
  emit('focus', event)
}

// 处理回车事件
const handleEnter = (event) => {
  emit('enter', event)
}

// 处理清空
const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
  // 聚焦输入框
  inputRef.value?.focus()
}

// 暴露方法供外部调用
defineExpose({
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur()
})
</script>
