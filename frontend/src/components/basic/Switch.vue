<template>
  <button
    type="button"
    class="relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#8B6F47] focus:ring-offset-2"
    :class="[
      modelValue ? 'bg-[#8B6F47]' : 'bg-gray-300',
      disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
    ]"
    @click="handleClick"
    :disabled="disabled"
    role="switch"
    :aria-checked="modelValue"
  >
    <span
      class="inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-200"
      :class="modelValue ? 'translate-x-6' : 'translate-x-1'"
    />
  </button>
</template>

<script setup>
/**
 * Switch 开关组件
 * 功能：替代 Element Plus 的 el-switch，提供开/关切换功能
 * 遵循 KISS 原则：简洁实现
 */
import { computed } from 'vue'

const props = defineProps({
  // v-model 绑定值
  modelValue: {
    type: Boolean,
    default: false
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 切换开关
const handleClick = () => {
  if (props.disabled) return
  const newValue = !props.modelValue
  emit('update:modelValue', newValue)
  emit('change', newValue)
}
</script>

<style scoped>
/* 确保按钮没有默认边框 */
button {
  border: none;
  padding: 0;
}

button:focus:not(:focus-visible) {
  outline: none;
}

button:focus-visible {
  outline: none;
}
</style>
