<template>
  <div class="inline-flex rounded-lg overflow-hidden border border-[#8B6F47]/20 bg-[rgba(139,111,71,0.08)] p-0.5">
    <button
      v-for="option in normalizedOptions"
      :key="option.value"
      type="button"
      class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
      :class="[
        modelValue === option.value
          ? 'bg-[#8B6F47] text-white shadow-sm'
          : 'text-[#8B6F47] hover:bg-[#8B6F47]/5'
      ]"
      @click="handleClick(option)"
    >
      {{ option.label }}
    </button>
  </div>
</template>

<script setup>
/**
 * RadioGroup 单选按钮组组件
 * 功能：替代 Element Plus 的 el-radio-group + el-radio-button，提供简洁的按钮式单选
 * 遵循 KISS 原则：简洁实现
 */
import { computed } from 'vue'

const props = defineProps({
  // v-model 绑定值
  modelValue: {
    type: [String, Number, Boolean],
    default: ''
  },
  // 选项列表
  options: {
    type: Array,
    required: true,
    default: () => []
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 标准化选项数据
const normalizedOptions = computed(() => {
  return props.options.map(item => {
    if (typeof item === 'object' && item !== null) {
      return {
        label: item.label ?? String(item.value),
        value: item.value ?? item
      }
    }
    return { label: String(item), value: item }
  })
})

// 处理点击
const handleClick = (option) => {
  if (props.disabled) return
  emit('update:modelValue', option.value)
  emit('change', option.value)
}
</script>

<style scoped>
/* 移除按钮默认样式 */
button {
  border: none;
  background: transparent;
  cursor: pointer;
  outline: none;
}

button:focus-visible {
  outline: 2px solid #8B6F47;
  outline-offset: 2px;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
</style>
