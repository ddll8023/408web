<template>
  <div class="w-full relative" ref="containerRef">
    <!-- 触发区域 -->
    <div
      :id="triggerId"
      class="dropdown-control relative flex min-h-[42px] w-full items-center gap-2 border px-3 py-2 text-[15px] leading-normal cursor-pointer"
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
      <!-- 已选中分类和占位符 -->
      <div class="min-w-0 flex-1">
        <template v-if="multiple">
          <transition-group name="tag" tag="div" class="flex flex-wrap items-center gap-1">
            <span
              v-for="item in selectedItems"
              :key="item.value"
              class="dropdown-selection-tag max-w-full"
            >
              <font-awesome-icon :icon="['fas', 'folder']" class="flex-shrink-0 text-xs" />
              <span class="min-w-0 max-w-[100px] truncate">{{ item.label }}</span>
              <button
                v-if="!disabled"
                type="button"
                class="ml-0.5 flex h-4 w-4 flex-shrink-0 items-center justify-center rounded-full text-accent/70 transition-colors hover:bg-accent/20 hover:text-accent"
                aria-label="移除分类"
                @click.stop="removeTag(item.value)"
              >
                <font-awesome-icon :icon="['fas', 'times']" class="text-[10px]" />
              </button>
            </span>
          </transition-group>
        </template>
        <span v-else-if="selectedItems.length > 0" class="block truncate text-gray-700">
          {{ selectedItems[0].label }}
        </span>

        <span
          v-if="selectedItems.length === 0"
          class="block truncate font-normal text-gray-400 select-none"
        >
          {{ placeholder }}
        </span>
      </div>

      <!-- 下拉箭头 -->
      <div class="ml-auto flex-shrink-0 flex items-center gap-2">
        <button
          v-if="!disabled && selectedItems.length > 0"
          type="button"
          class="flex h-6 w-6 items-center justify-center rounded-full text-gray-400 transition-colors hover:bg-accent/10 hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/30"
          aria-label="清空分类"
          title="清空分类"
          @click.stop="clearAll"
        >
          <font-awesome-icon :icon="['fas', 'times-circle']" class="text-sm" aria-hidden="true" />
        </button>
        <font-awesome-icon
          class="text-gray-400 transition-transform duration-300"
          :class="dropdownVisible ? 'text-accent rotate-180' : ''"
          :icon="['fas', 'chevron-down']"
        />
      </div>
    </div>

    <!-- 下拉菜单：传送到 body，避免被弹窗等滚动容器的 overflow 裁剪 -->
    <Teleport to="body">
      <transition name="dropdown">
        <div
          :id="listId"
          ref="panelRef"
          v-show="dropdownVisible && !disabled"
          role="listbox"
          :aria-multiselectable="multiple ? 'true' : undefined"
          class="dropdown-panel category-cascader-panel fixed z-[99999] flex flex-col overflow-hidden"
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
          <div class="dropdown-scroll min-h-0 max-h-[300px] overflow-y-auto">
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
                  class="w-6 h-6 flex-shrink-0 flex items-center justify-center rounded-md text-gray-400 hover:text-accent hover:bg-accent/10 transition-all duration-150"
                  :aria-label="`${expandedKeys.includes(row.item.value) ? '收起' : '展开'} ${row.item.label}`"
                  @click.stop="toggleExpand(row.item.value)"
                >
                  <font-awesome-icon
                    class="text-xs transition-transform duration-200"
                    :icon="expandedKeys.includes(row.item.value) ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']"
                  />
                </button>
                <span v-else class="w-6 flex-shrink-0" aria-hidden="true"></span>

                <!-- 多选使用复选框，单选使用选中图标 -->
                <div
                  v-if="multiple && row.item.selectable"
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
                    class="dropdown-checkbox group-hover:border-accent"
                    :class="{ 'dropdown-checkbox--selected': isSelected(row.item.value) }"
                  >
                    <font-awesome-icon
                      v-if="isSelected(row.item.value)"
                      :icon="['fas', 'check']"
                      class="text-white text-[10px] font-bold"
                    />
                  </div>
                </div>
                <!-- 单选模式不额外预留复选框列，避免展开图标与文本之间出现大间距。 -->

                <!-- 选项标签 -->
                <span
                  class="min-w-0 flex-1 truncate whitespace-nowrap text-[15px] transition-colors duration-150"
                  :title="row.item.label"
                  :class="[
                    isSelected(row.item.value)
                      ? 'text-accent font-medium'
                      : row.level > 0
                        ? 'text-gray-600 group-hover:text-accent'
                        : 'text-gray-700 group-hover:text-accent'
                  ]"
                  @click.stop="handleItemClick(row.item)"
                >
                  {{ row.item.label }}
                </span>

                <!-- 子分类数量徽章 -->
                <span
                  v-if="row.item.children.length > 0"
                  class="px-2 py-0.5 text-xs rounded-full transition-colors duration-150"
                  :class="[
                    multiple && getSelectedCount(row.item) > 0
                      ? 'bg-accent/10 text-accent font-medium'
                      : 'bg-gray-100 text-gray-400'
                  ]"
                >
                  <template v-if="multiple">
                    {{ getSelectedCount(row.item) }}/{{ getDescendantCount(row.item) }}
                  </template>
                  <template v-else>
                    {{ getDescendantCount(row.item) }} 个子项
                  </template>
                </span>

                <!-- 选中指示 -->
                <font-awesome-icon
                  v-if="row.item.selectable && isSelected(row.item.value) && (multiple ? row.item.children.length === 0 : true)"
                  :icon="['fas', 'check-circle']"
                  class="text-accent text-xs"
                />
              </div>
            </transition-group>
          </div>

          <!-- 多选需要确认区，单选选择后立即关闭下拉框。 -->
          <div v-if="multiple" class="dropdown-panel__footer">
            <span class="text-xs text-gray-400">
              <font-awesome-icon :icon="['fas', 'info-circle']" class="mr-1" />
              已选择 {{ selectedItems.length }} 个分类
            </span>
            <button
              type="button"
              class="text-xs text-accent hover:text-accent-deep font-medium transition-colors"
              @click.stop="dropdownVisible = false"
            >
              确定 <font-awesome-icon :icon="['fas', 'arrow-right']" class="ml-1" />
            </button>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import type { PropType } from 'vue'
import type { CascaderOption, NormalizedCascaderOption } from './types'
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

/**
 * 多选级联选择器组件
 * 功能：支持单选/多选、树形层级、搜索过滤
 * 设计：精致学术风，使用项目品牌色（--brand-accent）
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
  },
  // false 时作为单选分类树使用，选择节点后立即关闭下拉框。
  multiple: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits<{ 'update:modelValue': [value: string[]]; change: [value: string[]] }>()

const containerRef = ref<HTMLElement | null>(null)
const panelRef = ref<HTMLElement | null>(null)
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
      children: item.children ? normalize(item.children) : [],
      selectable: item.selectable !== false
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
const handleItemClick = (item: NormalizedCascaderOption) => {
  if (!item.selectable && item.children.length > 0) {
    toggleExpand(item.value)
    return
  }
  toggleSelect(item)
}

const toggleSelect = (item: NormalizedCascaderOption) => {
  if (!item.selectable) return
  if (!props.multiple) {
    selectedValues.value = [item.value]
    dropdownVisible.value = false
    return
  }

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

// 弹层与触发控件、视口边缘的间距。
const PANEL_GAP = 6
const VIEWPORT_PADDING = 12

/**
 * 在视口内定位弹层。
 * 弹层已传送到 body，不再受弹窗等滚动容器裁剪，因此需要自行保证不被视口截断：
 * 优先贴在触发控件下方，下方空间不足且上方更宽裕时上翻，空间仍不足时限制高度交回列表滚动。
 */
const updatePanelPosition = () => {
  if (!dropdownVisible.value || !containerRef.value || !panelRef.value) return

  const trigger = containerRef.value.querySelector<HTMLElement>('.dropdown-control')
  const panel = panelRef.value
  const list = panel.querySelector<HTMLElement>('.dropdown-scroll')
  if (!trigger) return

  // 先清空上一次的高度约束，按内容重新测量
  panel.style.maxHeight = ''
  if (list) list.style.maxHeight = ''

  const triggerRect = trigger.getBoundingClientRect()
  const panelWidth = panel.offsetWidth
  const panelHeight = panel.offsetHeight
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  const maxLeft = Math.max(VIEWPORT_PADDING, viewportWidth - panelWidth - VIEWPORT_PADDING)
  const left = Math.min(Math.max(triggerRect.left, VIEWPORT_PADDING), maxLeft)

  const spaceBelow = viewportHeight - triggerRect.bottom - PANEL_GAP - VIEWPORT_PADDING
  const spaceAbove = triggerRect.top - PANEL_GAP - VIEWPORT_PADDING
  const placeAbove = panelHeight > spaceBelow && spaceAbove > spaceBelow
  const availableHeight = Math.max(1, placeAbove ? spaceAbove : spaceBelow)

  if (panelHeight > availableHeight) {
    // 高度不足时固定面板高度，压缩列表高度，保留搜索框和底部操作区可见。
    panel.style.maxHeight = `${availableHeight}px`
    if (list) {
      const chromeHeight = panelHeight - list.offsetHeight
      list.style.maxHeight = `${Math.max(80, availableHeight - chromeHeight)}px`
    }
  }

  const top = placeAbove
    ? Math.max(VIEWPORT_PADDING, triggerRect.top - PANEL_GAP - panel.offsetHeight)
    : triggerRect.bottom + PANEL_GAP

  panel.style.top = `${top}px`
  panel.style.left = `${left}px`
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
    // 等弹层渲染完成后再测量尺寸定位。
    nextTick(updatePanelPosition)
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

// 点击外部关闭；弹层已传送到 body，需要单独判断是否点在弹层内部。
const handleClickOutside = (event: MouseEvent) => {
  if (!(event.target instanceof Element)) return
  if (containerRef.value?.contains(event.target)) return
  if (panelRef.value?.contains(event.target)) return
  dropdownVisible.value = false
}

// 页面滚动或视口变化时重新定位，弹层内部的滚动不触发重算。
const handleViewportScroll = (event: Event) => {
  if (!dropdownVisible.value) return
  const target = event.target
  if (panelRef.value && target instanceof Node && panelRef.value.contains(target)) return
  updatePanelPosition()
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

// 展开节点、搜索过滤或异步载入选项后高度会变化，需要重新定位弹层。
watch(visibleOptions, () => {
  if (dropdownVisible.value) nextTick(updatePanelPosition)
})

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('scroll', handleViewportScroll, true)
  window.addEventListener('resize', updatePanelPosition)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('scroll', handleViewportScroll, true)
  window.removeEventListener('resize', updatePanelPosition)
})
</script>

<style scoped>
/* 分类树弹层保持足够宽度，避免父子分类名称被过早截断。 */
.category-cascader-panel {
  width: min(380px, calc(100vw - 24px));
  min-width: min(320px, calc(100vw - 24px));
  max-width: calc(100vw - 24px);
}

.category-cascader-panel :deep(.dropdown-tree-option) {
  min-height: 42px;
}

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
