<template>
  <div class="overflow-x-auto" :aria-busy="loading">
    <!-- 加载状态 -->
    <div v-if="loading" class="py-12">
      <slot name="loading">
        <div class="flex items-center justify-center" role="status" aria-live="polite">
          <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-2xl text-[#8B6F47]" aria-hidden="true" />
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
            scope="col"
            :aria-sort="column.sortable ? getAriaSort(column) : undefined"
            :tabindex="column.sortable ? 0 : undefined"
            :class="[
              sizeClasses.th,
              column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left',
              column.sortable ? 'cursor-pointer select-none hover:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#8B6F47]' : '',
              column.fixed ? 'sticky right-0 z-10 bg-white' : ''
            ]"
            :style="columnStyle(column)"
            @click="column.sortable ? handleSort(column) : null"
            @keydown.enter.prevent="column.sortable ? handleSort(column) : null"
            @keydown.space.prevent="column.sortable ? handleSort(column) : null"
          >
            <div class="flex items-center gap-1" :class="column.align === 'center' ? 'justify-center' : column.align === 'right' ? 'justify-end' : 'justify-start'">
              <span>{{ column.label }}</span>
              <template v-if="column.sortable">
                <font-awesome-icon
                  v-if="sortConfig.prop === column.prop"
                  :icon="sortConfig.order === 'ascending' ? ['fas', 'sort-up'] : ['fas', 'sort-down']"
                  class="text-xs text-[#8B6F47]"
                  aria-hidden="true"
                />
                <font-awesome-icon
                  v-else
                  :icon="['fas', 'sort']"
                  class="text-xs text-gray-400"
                  aria-hidden="true"
                />
              </template>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in data"
          :key="getRowKey(row, index)"
          class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
          :class="{ 'even:bg-gray-50': stripe }"
        >
          <td
            v-for="column in columns"
            :key="column.prop"
            class="px-4 text-gray-700"
            :class="[
              sizeClasses.py,
              sizeClasses.td,
              column.align === 'center' ? 'text-center' : column.align === 'right' ? 'text-right' : 'text-left',
              column.fixed ? 'sticky right-0 z-10 bg-white' : ''
            ]"
            :style="columnStyle(column)"
          >
            <slot :name="column.prop" :row="row" :column="column">
              {{ cellValue(row, column.prop) }}
            </slot>
          </td>
        </tr>
        <tr v-if="!data || data.length === 0">
          <td :colspan="columns.length" class="px-4 py-8 text-center text-gray-400">
            <slot name="empty">
              <div class="flex flex-col items-center">
                <font-awesome-icon :icon="['fas', 'inbox']" class="text-2xl mb-2 opacity-50" aria-hidden="true" />
                <span>暂无数据</span>
              </div>
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts" generic="T extends object">
import type { TableColumn, TableSort } from './types'
import { reactive, computed } from 'vue'

/**
 * Table 表格组件
 * 功能：提供基本的表格展示功能
 * 支持：排序功能、字体大小控制
 * 遵循 KISS 原则：简洁实现，只包含必需功能
 */
const props = withDefaults(defineProps<{
  data?: T[]
  columns: TableColumn[]
  loading?: boolean
  stripe?: boolean
  rowKey?: string | ((row: T, index: number) => string | number)
  size?: 'sm' | 'md' | 'lg'
  fontSize?: number | null
}>(), { data: () => [], loading: false, stripe: false, rowKey: '', size: 'md', fontSize: null })
const emit = defineEmits<{ 'sort-change': [sort: TableSort] }>()
defineSlots<{ loading?: () => unknown; empty?: () => unknown } & { [name: string]: (props: { row: T; column: TableColumn }) => unknown }>()
const cellValue = (row: T, key: string): unknown => Reflect.get(row, key)

const getRowKey = (row: T, index: number) => {
  if (typeof props.rowKey === 'function') return props.rowKey(row, index)
  if (props.rowKey) return String(Reflect.get(row, props.rowKey))
  const id = Reflect.get(row, 'id')
  return id === undefined || id === null ? index : String(id)
}

const normalizeSize = (value: string) => /^\d+(?:\.\d+)?$/.test(value.trim()) ? `${value}px` : value

const columnStyle = (column: TableColumn) => ({
  ...(column.width ? { width: normalizeSize(column.width) } : {}),
  ...(column.minWidth ? { minWidth: normalizeSize(column.minWidth) } : {})
})

const getAriaSort = (column: TableColumn): 'ascending' | 'descending' | 'none' => {
  if (sortConfig.prop !== column.prop || !sortConfig.order) return 'none'
  return sortConfig.order
}

// 计算字体样式
const fontStyle = computed(() => {
  if (props.fontSize) {
    return {
      fontSize: `${props.fontSize}px`,
      lineHeight: `${props.fontSize * 1.5}px`
    }
  }
  return undefined
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
const sortConfig = reactive<TableSort>({
  prop: null,
  order: null
})

// 处理排序
const handleSort = (column: TableColumn) => {
  let order: TableSort['order'] = 'ascending'
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
