<template>
  <div class="overflow-x-auto">
    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <slot name="loading">
        <div class="flex items-center justify-center">
          <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-2xl text-[#8B6F47]" />
          <span class="ml-3 text-gray-600">加载中...</span>
        </div>
      </slot>
    </div>

    <!-- 表格内容 -->
    <table v-else class="w-full border-collapse" :style="fontStyle">
      <thead>
        <tr class="bg-gray-50 border-b border-gray-200">
          <th
            v-for="column in columns"
            :key="column.prop"
            class="px-4 py-3 font-semibold text-gray-700"
            :class="[
              sizeClasses.th,
              column.width ? `w-[${column.width}]` : '',
              column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left',
              column.sortable ? 'cursor-pointer select-none hover:bg-gray-100' : ''
            ]"
            :style="column.width ? { width: column.width } : {}"
            @click="column.sortable ? handleSort(column) : null"
          >
            <div class="flex items-center gap-1" :class="column.align === 'center' ? 'justify-center' : column.align === 'right' ? 'justify-end' : 'justify-start'">
              <span>{{ column.label }}</span>
              <template v-if="column.sortable">
                <font-awesome-icon
                  v-if="sortConfig.prop === column.prop"
                  :icon="sortConfig.order === 'ascending' ? ['fas', 'sort-up'] : ['fas', 'sort-down']"
                  class="text-xs text-[#8B6F47]"
                />
                <font-awesome-icon
                  v-else
                  :icon="['fas', 'sort']"
                  class="text-xs text-gray-400"
                />
              </template>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in data"
          :key="index"
          class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
        >
          <td
            v-for="column in columns"
            :key="column.prop"
            class="px-4 text-gray-700"
            :class="[
              sizeClasses.py,
              sizeClasses.td,
              column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left'
            ]"
          >
            <slot :name="column.prop" :row="row" :column="column">
              {{ row[column.prop] }}
            </slot>
          </td>
        </tr>
        <tr v-if="!data || data.length === 0">
          <td :colspan="columns.length" class="px-4 py-8 text-center text-gray-400">
            <slot name="empty">
              <div class="flex flex-col items-center">
                <font-awesome-icon :icon="['fas', 'inbox']" class="text-2xl mb-2 opacity-50" />
                <span>暂无数据</span>
              </div>
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'

/**
 * Table 表格组件
 * 功能：替代 Element Plus 的 el-table，提供基本的表格展示功能
 * 支持：排序功能、字体大小控制
 * 遵循 KISS 原则：简洁实现，只包含必需功能
 */
const props = defineProps({
  // 表格数据
  data: {
    type: Array,
    default: () => []
  },
  // 列配置
  columns: {
    type: Array,
    default: () => [],
    required: true
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  // 表格尺寸：sm(小)、md(中)、lg(大)
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  // 自定义字体大小（数值，单位 px），优先级高于 size
  fontSize: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['sort-change'])

// 计算字体样式
const fontStyle = computed(() => {
  if (props.fontSize) {
    return {
      fontSize: `${props.fontSize}px`,
      lineHeight: `${props.fontSize * 1.5}px`
    }
  }
  return null
})

// 根据 size 计算字体大小类名（当没有自定义 fontSize 时使用）
const sizeClasses = computed(() => {
  const classes = {
    sm: {
      th: 'text-xs',
      td: 'text-xs',
      py: 'py-2'
    },
    md: {
      th: 'text-sm',
      td: 'text-sm',
      py: 'py-3'
    },
    lg: {
      th: 'text-base',
      td: 'text-base',
      py: 'py-4'
    }
  }
  // 如果有自定义 fontSize，返回空类名，因为使用内联样式
  return props.fontSize ? { th: '', td: '', py: '' } : (classes[props.size] || classes.md)
})

// 排序配置
const sortConfig = reactive({
  prop: null,
  order: null
})

// 处理排序
const handleSort = (column) => {
  let order = 'ascending'
  if (sortConfig.prop === column.prop) {
    // 切换排序顺序
    if (sortConfig.order === 'ascending') {
      order = 'descending'
    } else if (sortConfig.order === 'descending') {
      // 第三次点击取消排序
      sortConfig.prop = null
      sortConfig.order = null
      emit('sort-change', { prop: null, order: null })
      return
    }
  }

  sortConfig.prop = column.prop
  sortConfig.order = order
  emit('sort-change', { prop: column.prop, order: order })
}
</script>
