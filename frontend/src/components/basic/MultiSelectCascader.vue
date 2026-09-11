<template>
  <div class="w-full relative" ref="containerRef">
    <!-- 触发区域 -->
    <div
      :id="triggerId"
      class="dropdown-control relative flex h-[40px] items-center flex-wrap gap-1.5 border px-3 py-2 text-[15px] leading-normal cursor-pointer"
      :class="[
        disabled
          ? 'dropdown-control--disabled opacity-60 cursor-not-allowed'
          : dropdownVisible
            ? 'dropdown-control--open'
            : ''
      ]"
      role="combobox"
      :tabindex="disabled ? -1 : 0"
      :aria-expanded="dropdownVisible"
      aria-haspopup="listbox"
      :aria-controls="listId"
      :aria-disabled="disabled"
      :aria-label="ariaLabel || undefined"
      @click="toggleDropdown"
      @keydown="handleTriggerKeydown"
    >
      <!-- 已选中标签 -->
      <transition-group name="tag" tag="div" class="flex flex-wrap gap-1">
        <span
          v-for="(item, index) in selectedItems"
          :key="item.value"
          class="dropdown-selection-tag"
        >
          <font-awesome-icon :icon="['fas', 'folder']" class="text-xs" />
          <span class="max-w-[100px] truncate">{{ item.label }}</span>
          <button
            v-if="!disabled"
            type="button"
            class="ml-0.5 w-4 h-4 flex items-center justify-center rounded-full hover:bg-[#8B6F47]/20 text-[#8B6F47]/70 hover:text-[#8B6F47] transition-colors"
            aria-label="移除分类"
            @click.stop="removeTag(item.value)"
          >
            <font-awesome-icon :icon="['fas', 'times']" class="text-[10px]" />
          </button>
        </span>
      </transition-group>

      <!-- placeholder -->
      <span
        v-if="selectedItems.length === 0"
        class="text-gray-400 font-normal select-none"
      >
        {{ placeholder }}
      </span>

      <!-- 下拉箭头 -->
      <div class="ml-auto flex-shrink-0 flex items-center gap-2">
        <span v-if="!disabled && selectedItems.length > 0" class="text-xs text-gray-400 hover:text-[#8B6F47] transition-colors">
          <button type="button" class="hover:bg-gray-100 px-1.5 py-0.5 rounded" @click.stop="clearAll">清空</button>
        </span>
        <font-awesome-icon
          class="text-gray-400 transition-transform duration-300"
          :class="dropdownVisible ? 'text-[#8B6F47] rotate-180' : ''"
          :icon="['fas', 'chevron-down']"
        />
      </div>
    </div>

    <!-- 下拉菜单 -->
    <transition name="dropdown">
      <div
        :id="listId"
        v-show="dropdownVisible && !disabled"
        role="listbox"
        aria-multiselectable="true"
        class="dropdown-panel absolute top-full left-0 right-0 z-50 overflow-hidden"
      >
        <!-- 搜索框 -->
        <div v-if="enableSearch" class="dropdown-panel__header">
          <div class="relative">
            <font-awesome-icon :icon="['fas', 'search']" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              v-model="searchKeyword"
              type="text"
              aria-label="搜索分类"
              class="dropdown-filter dropdown-filter--with-icon"
              placeholder="搜索分类..."
              @click.stop
            />
          </div>
        </div>

        <!-- 树形选项 -->
        <div class="dropdown-scroll max-h-[300px] overflow-y-auto">
          <div v-if="filteredOptions.length === 0" class="dropdown-empty dropdown-empty--large">
            <font-awesome-icon :icon="['fas', 'folder-open']" class="text-3xl text-gray-200 mb-2" />
            <p class="text-sm text-gray-400">暂无数据</p>
          </div>

          <transition-group v-else name="expand" tag="div" class="py-2">
            <!-- 将已展开的树按层级平铺，所有深度的节点都复用同一套选择交互。 -->
            <div
              v-for="row in visibleOptions"
              :key="row.item.value"
              class="dropdown-tree-option group"
              :class="{
                'dropdown-tree-option--selected': isSelected(row.item.value)
              }"
              :style="{ paddingLeft: `${row.level * 20 + 12}px` }"
            >
              <!-- 展开/收起子项按钮 -->
              <button
                v-if="row.item.children.length > 0"
                type="button"
                class="w-6 h-6 flex-shrink-0 flex items-center justify-center rounded-md text-gray-400 hover:text-[#8B6F47] hover:bg-[#8B6F47]/10 transition-all duration-150"
                :aria-label="`${expandedKeys.includes(row.item.value) ? '收起' : '展开'} ${row.item.label}`"
                @click.stop="toggleExpand(row.item.value)"
              >
                <font-awesome-icon
                  class="text-xs transition-transform duration-200"
                  :icon="expandedKeys.includes(row.item.value) ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']"
                />
              </button>
              <span v-else class="w-6 flex-shrink-0" aria-hidden="true"></span>

              <!-- 自定义复选框 -->
              <div
                class="relative w-5 h-5 flex-shrink-0"
                @click.stop="toggleSelect(row.item)"
              >
                <input
                  type="checkbox"
                  :checked="isSelected(row.item.value)"
                  :disabled="disabled"
                  :aria-label="row.item.label"
                  class="sr-only"
                />
                <div
                  class="dropdown-checkbox group-hover:border-[#8B6F47]"
                  :class="{ 'dropdown-checkbox--selected': isSelected(row.item.value) }"
                >
                  <font-awesome-icon
                    v-if="isSelected(row.item.value)"
                    :icon="['fas', 'check']"
                    class="text-white text-[10px] font-bold"
                  />
                </div>
              </div>

              <!-- 选项标签 -->
              <span
                class="flex-1 text-[15px] transition-colors duration-150"
                :class="[
                  isSelected(row.item.value)
                    ? 'text-[#8B6F47] font-medium'
                    : row.level > 0
                      ? 'text-gray-600 group-hover:text-[#8B6F47]'
                      : 'text-gray-700 group-hover:text-[#8B6F47]'
                ]"
                @click.stop="toggleSelect(row.item)"
              >
                {{ row.item.label }}
              </span>

              <!-- 子分类数量徽章 -->
              <span
                v-if="row.item.children.length > 0"
                class="px-2 py-0.5 text-xs rounded-full transition-colors duration-150"
                :class="[
                  getSelectedCount(row.item) > 0
                    ? 'bg-[#8B6F47]/10 text-[#8B6F47] font-medium'
                    : 'bg-gray-100 text-gray-400'
                ]"
              >
                {{ getSelectedCount(row.item) }}/{{ getDescendantCount(row.item) }}
              </span>

              <!-- 选中指示 -->
              <font-awesome-icon
                v-if="isSelected(row.item.value) && row.item.children.length === 0"
                :icon="['fas', 'check-circle']"
                class="text-[#8B6F47] text-xs"
              />
            </div>
          </transition-group>
        </div>

        <!-- 底部提示 -->
        <div class="dropdown-panel__footer">
          <span class="text-xs text-gray-400">
            <font-awesome-icon :icon="['fas', 'info-circle']" class="mr-1" />
            已选择 {{ selectedItems.length }} 个分类
          </span>
          <button
            type="button"
            class="text-xs text-[#8B6F47] hover:text-[#6B5537] font-medium transition-colors"
            @click.stop="dropdownVisible = false"
          >
            确定 <font-awesome-icon :icon="['fas', 'arrow-right']" class="ml-1" />
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { CascaderOption, NormalizedCascaderOption } from './types'
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

/**
 * 多选级联选择器组件
 * 功能：支持多选、树形层级、搜索过滤
 * 设计：精致学术风，使用项目主题色 #8B6F47
 */
const props = defineProps({
  modelValue: {
    type: Array as PropType<string[]>,
    default: () => []
  },
  options: {
    type: Array as PropType<CascaderOption[]>,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '请选择分类（支持多个）'
  },
  disabled: {
    type: Boolean,
    default: false
  },
  enableSearch: {
    type: Boolean,
    default: true
  },
  // 用于关联外部标签和下拉列表的 ID
  id: {
    type: String,
    default: ''
  },
  // 无法通过原生 label 关联时使用的可访问名称
  ariaLabel: {
    type: String,
    default: ''
  }
})

const emit = defineEmits<{ 'update:modelValue': [value: string[]]; change: [value: string[]] }>()

const containerRef = ref<HTMLElement | null>(null)
const dropdownVisible = ref(false)
const searchKeyword = ref('')
const expandedKeys = ref<string[]>([])

let nextCascaderId = 0
const generatedTriggerId = `cascader-${++nextCascaderId}`
const triggerId = computed(() => props.id || generatedTriggerId)
const listId = computed(() => `${triggerId.value}-list`)

// 标准化选项数据
const normalizedOptions = computed(() => {
  const normalize = (items: CascaderOption[]): NormalizedCascaderOption[] => {
    return items.map(item => ({
      value: item.value || item.name || '',
      label: item.label || item.name || '',
      children: item.children ? normalize(item.children) : []
    }))
  }
  return normalize(props.options || [])
})

// 过滤后的选项
const filteredOptions = computed(() => {
  if (!searchKeyword.value) return normalizedOptions.value

  const keyword = searchKeyword.value.toLowerCase()
  const result: NormalizedCascaderOption[] = []

  const filterItems = (items: NormalizedCascaderOption[]): NormalizedCascaderOption[] => {
    const matched = []
    for (const item of items) {
      const labelMatch = item.label.toLowerCase().includes(keyword)
      let children: NormalizedCascaderOption[] = []

      if (item.children && item.children.length > 0) {
        children = filterItems(item.children)
      }

      if (labelMatch || children.length > 0) {
        matched.push({
          ...item,
          children: children.length > 0 ? children : item.children
        })
      }
    }
    return matched
  }

  return filterItems(normalizedOptions.value)
})

// 按展开状态平铺可见节点，支持任意层级的分类选择。
interface VisibleOption {
  item: NormalizedCascaderOption
  level: number
}

const visibleOptions = computed<VisibleOption[]>(() => {
  const result: VisibleOption[] = []

  const flatten = (items: NormalizedCascaderOption[], level: number) => {
    for (const item of items) {
      result.push({ item, level })
      if (item.children.length > 0 && expandedKeys.value.includes(item.value)) {
        flatten(item.children, level + 1)
      }
    }
  }

  flatten(filteredOptions.value, 0)
  return result
})

// 选中的值数组
const selectedValues = computed({
  get: () => props.modelValue || [],
  set: (val) => {
    emit('update:modelValue', val)
    emit('change', val)
  }
})

// 选中的选项
const selectedItems = computed(() => {
  const result: NormalizedCascaderOption[] = []
  const findItems = (items: NormalizedCascaderOption[]) => {
    for (const item of items) {
      if (selectedValues.value.includes(item.value)) {
        result.push(item)
      }
      if (item.children && item.children.length > 0) {
        findItems(item.children)
      }
    }
  }
  findItems(normalizedOptions.value)
  return result
})

// 判断是否选中
const isSelected = (value: string) => {
  return selectedValues.value.includes(value)
}

// 切换选择
const toggleSelect = (item: NormalizedCascaderOption) => {
  const newValues = [...selectedValues.value]
  const index = newValues.indexOf(item.value)

  if (index > -1) {
    newValues.splice(index, 1)
  } else {
    newValues.push(item.value)
  }

  selectedValues.value = newValues
}

// 移除标签
const removeTag = (value: string) => {
  const newValues = selectedValues.value.filter(v => v !== value)
  selectedValues.value = newValues
}

// 清空所有
const clearAll = () => {
  selectedValues.value = []
}

// 切换展开
const toggleExpand = (value: string) => {
  const index = expandedKeys.value.indexOf(value)
  if (index > -1) {
    expandedKeys.value.splice(index, 1)
  } else {
    expandedKeys.value.push(value)
  }
}

// 获取当前分类下所有后代数量，用于展示多级选择进度。
const getDescendantCount = (item: NormalizedCascaderOption): number => {
  return item.children.reduce((count, child) => count + 1 + getDescendantCount(child), 0)
}

const getSelectedCount = (item: NormalizedCascaderOption): number => {
  return item.children.reduce((count, child) => {
    const selected = selectedValues.value.includes(child.value) ? 1 : 0
    return count + selected + getSelectedCount(child)
  }, 0)
}

// 切换下拉
const toggleDropdown = () => {
  if (props.disabled) return

  dropdownVisible.value = !dropdownVisible.value
  if (dropdownVisible.value) {
    searchKeyword.value = ''
    // 默认展开第一个有子选项的分类
    if (normalizedOptions.value.length > 0 && expandedKeys.value.length === 0) {
      const firstWithChildren = normalizedOptions.value.find(item => item.children && item.children.length > 0)
      if (firstWithChildren) {
        expandedKeys.value = [firstWithChildren.value]
      }
    }
  }
}

const handleTriggerKeydown = (event: KeyboardEvent) => {
  if (props.disabled) return
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    toggleDropdown()
  } else if (event.key === 'Escape' && dropdownVisible.value) {
    event.preventDefault()
    dropdownVisible.value = false
  }
}

// 点击外部关闭
const handleClickOutside = (event: MouseEvent) => {
  if (!(event.target instanceof Element)) return
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    dropdownVisible.value = false
  }
}

// 分类树或已选值变化时，展开所有已选分类的祖先，确保深层选中项可见。
const expandSelectedParents = () => {
  if (normalizedOptions.value.length === 0) return

  const selectedValuesSet = new Set(selectedValues.value)
  const keysToExpand: string[] = []

  const findParentKeys = (items: NormalizedCascaderOption[], parentKeys: string[] = []) => {
    for (const item of items) {
      if (selectedValuesSet.has(item.value)) {
        keysToExpand.push(...parentKeys)
      }
      if (item.children.length > 0) {
        findParentKeys(item.children, [...parentKeys, item.value])
      }
    }
  }

  findParentKeys(normalizedOptions.value)

  // 合并新的展开键，保留用户已经手动展开的节点。
  expandedKeys.value = [...new Set([...expandedKeys.value, ...keysToExpand])]
}

watch([normalizedOptions, selectedValues], expandSelectedParents, { deep: true, immediate: true })

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* 展开/收起动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s ease-out;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}

.expand-enter-to,
.expand-leave-from {
  max-height: 500px;
  transform: translateY(0);
}

/* 标签动画 */
.tag-enter-active,
.tag-leave-active {
  transition: all 0.2s ease;
}

.tag-enter-from {
  opacity: 0;
  transform: scale(0.8);
}

.tag-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

</style>
