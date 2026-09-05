<template>
  <div class="border border-gray-200 rounded-lg overflow-hidden">
    <button
      type="button"
      class="flex w-full items-center justify-between px-4 py-3 bg-gray-50 text-left cursor-pointer hover:bg-gray-100 transition-colors"
      :aria-expanded="isOpen"
      :aria-controls="contentId"
      @click="toggle"
    >
      <span class="font-medium text-gray-700">{{ title }}</span>
      <font-awesome-icon
        class="text-gray-400 transition-transform duration-200"
        :icon="isOpen ? ['fas', 'chevron-up'] : ['fas', 'chevron-down']"
        aria-hidden="true"
      />
    </button>
    <transition name="collapse">
      <div v-show="isOpen" :id="contentId" class="p-4 bg-white">
        <slot />
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, type PropType } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Array, String] as PropType<string | string[]>,
    default: () => []
  },
  name: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: ''
  }
})

let nextCollapseId = 0
const contentId = `collapse-content-${++nextCollapseId}`

const emit = defineEmits<{ 'update:modelValue': [value: string | string[]] }>()

// 是否展开
const isOpen = ref(false)

// 初始化状态
const initStatus = () => {
  if (Array.isArray(props.modelValue)) {
    isOpen.value = props.modelValue.includes(props.name)
  } else {
    isOpen.value = props.modelValue === props.name
  }
}

initStatus()

// 监听 modelValue 变化
watch(() => props.modelValue, () => {
  initStatus()
})

// 切换展开状态
const toggle = () => {
  const newValue = !isOpen.value

  if (Array.isArray(props.modelValue)) {
    const arr = [...props.modelValue]
    const index = arr.indexOf(props.name)
    if (newValue && index === -1) {
      arr.push(props.name)
    } else if (!newValue && index > -1) {
      arr.splice(index, 1)
    }
    emit('update:modelValue', arr)
  } else {
    emit('update:modelValue', newValue ? props.name : '')
  }

  isOpen.value = newValue
}
</script>

<style scoped>
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: 500px;
}
</style>
