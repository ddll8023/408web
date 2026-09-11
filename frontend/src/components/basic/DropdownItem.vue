<template>
  <div
    role="menuitem"
    :tabindex="disabled ? -1 : 0"
    :aria-disabled="disabled"
    class="dropdown-item"
    :class="[
      itemClasses,
      {
        'is-disabled': disabled
      }
    ]"
    :data-command="disabled ? '' : command"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
/**
 * DropdownItem 下拉菜单项组件
 * 功能：单个菜单项，支持 disabled、divided
 * 使用方式：在 Dropdown 组件内直接使用
 */
import { computed } from 'vue'

const props = defineProps({
  // 命令值（点击时传递）
  command: {
    type: [String, Number],
    default: ''
  },
  // 是否禁用
  disabled: {
    type: Boolean,
    default: false
  },
  // 是否显示分割线
  divided: {
    type: Boolean,
    default: false
  }
})

// 菜单项样式
const itemClasses = computed(() => {
  const classes = []
  if (props.divided) {
    classes.push('border-t border-gray-100 mt-1 pt-1')
  }
  return classes
})
</script>
