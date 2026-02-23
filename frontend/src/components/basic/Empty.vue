<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <div class="mb-4 text-gray-300">
      <font-awesome-icon :icon="icon" class="text-6xl" />
    </div>
    <p class="text-gray-500 text-base">{{ description }}</p>
  </div>
</template>

<script setup>
/**
 * 空状态组件
 * 用于展示列表为空、暂无数据等状态
 */
defineProps({
  description: {
    type: String,
    default: '暂无数据'
  },
  icon: {
    type: Array,
    default: () => ['fas', 'folder-open']
  }
})
</script>
