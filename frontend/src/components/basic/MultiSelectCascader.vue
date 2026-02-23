<template>
  <div class="w-full relative" ref="containerRef">
    <!-- 触发区域 -->
    <div
      class="h-[40px] leading-normal flex items-center flex-wrap gap-1.5 p-2 bg-white border rounded-lg cursor-pointer transition-all duration-300 ease-out"
      :class="[
        disabled
          ? 'bg-gray-50 border-gray-200 opacity-60 cursor-not-allowed'
          : dropdownVisible
            ? 'border-[#8B6F47] shadow-[0_0_0_2px_rgba(139,111,71,0.15)]'
            : 'border-gray-300 hover:border-gray-400 hover:shadow-sm'
      ]"
      @click="toggleDropdown"
    >
      <!-- 已选中标签 -->
      <transition-group name="tag" tag="div" class="flex flex-wrap gap-1">
        <span
          v-for="(item, index) in selectedItems"
          :key="item.value"
          class="inline-flex items-center gap-1 px-2 py-0.5 bg-gradient-to-r from-[#8B6F47]/10 to-[#8B6F47]/5 text-[#8B6F47] text-base font-medium rounded-md border border-[#8B6F47]/20"
        >
          <font-awesome-icon :icon="['fas', 'folder']" class="text-xs" />
          <span class="max-w-[100px] truncate">{{ item.label }}</span>
          <button
            v-if="!disabled"
            class="ml-0.5 w-4 h-4 flex items-center justify-center rounded-full hover:bg-[#8B6F47]/20 text-[#8B6F47]/70 hover:text-[#8B6F47] transition-colors"
            @click.stop="removeTag(item.value)"
          >
            <font-awesome-icon :icon="['fas', 'times']" class="text-[10px]" />
          </button>
        </span>
      </transition-group>

      <!-- placeholder -->
      <span
        v-if="selectedItems.length === 0"
        class="text-gray-400 text-base font-normal select-none"
      >
        {{ placeholder }}
      </span>

      <!-- 下拉箭头 -->
      <div class="ml-auto flex-shrink-0 flex items-center gap-2">
        <span v-if="!disabled && selectedItems.length > 0" class="text-xs text-gray-400 hover:text-[#8B6F47] transition-colors">
          <button class="hover:bg-gray-100 px-1.5 py-0.5 rounded" @click.stop="clearAll">清空</button>
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
        v-show="dropdownVisible && !disabled"
        class="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-[0_8px_30px_rgba(0,0,0,0.12)] border border-gray-100 overflow-hidden z-50"
      >
        <!-- 搜索框 -->
        <div v-if="enableSearch" class="p-3 border-b border-gray-100 bg-gray-50/50">
          <div class="relative">
            <font-awesome-icon :icon="['fas', 'search']" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              v-model="searchKeyword"
              type="text"
              class="w-full pl-9 pr-3 py-2.5 bg-white border border-gray-200 rounded-lg text-base focus:outline-none focus:border-[#8B6F47] focus:ring-2 focus:ring-[#8B6F47]/10 transition-all duration-200"
              placeholder="搜索分类..."
              @click.stop
            />
          </div>
        </div>

        <!-- 树形选项 -->
        <div class="max-h-[300px] overflow-y-auto">
          <div v-if="filteredOptions.length === 0" class="py-12 text-center">
            <font-awesome-icon :icon="['fas', 'folder-open']" class="text-3xl text-gray-200 mb-2" />
            <p class="text-base text-gray-400">暂无数据</p>
          </div>

          <div v-else class="py-2">
            <template v-for="item in filteredOptions" :key="item.value">
              <!-- 一级选项 -->
              <div
                class="group flex items-center gap-3 mx-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-150"
                :class="[
                  isSelected(item.value)
                    ? 'bg-[#8B6F47]/5'
                    : 'hover:bg-gray-50'
                ]"
              >
                <!-- 展开/收起子项按钮 -->
                <button
                  v-if="item.children && item.children.length > 0"
                  class="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-[#8B6F47] hover:bg-[#8B6F47]/10 transition-all duration-150"
                  @click.stop="toggleExpand(item.value)"
                >
                  <font-awesome-icon
                    class="text-xs transition-transform duration-200"
                    :icon="expandedKeys.includes(item.value) ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']"
                  />
                </button>
                <span v-else class="w-6"></span>

                <!-- 自定义复选框 -->
                <div
                  class="relative w-5 h-5 flex-shrink-0"
                  @click.stop="toggleSelect(item)"
                >
                  <input
                    type="checkbox"
                    :checked="isSelected(item.value)"
                    :disabled="disabled"
                    class="sr-only"
                  />
                  <div
                    class="w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all duration-200"
                    :class="[
                      isSelected(item.value)
                        ? 'bg-[#8B6F47] border-[#8B6F47]'
                        : 'border-gray-300 group-hover:border-[#8B6F47]/50'
                    ]"
                  >
                    <font-awesome-icon
                      v-if="isSelected(item.value)"
                      :icon="['fas', 'check']"
                      class="text-white text-[10px] font-bold"
                    />
                  </div>
                </div>

                <!-- 选项标签 -->
                <span
                  class="flex-1 text-base transition-colors duration-150"
                  :class="[
                    isSelected(item.value)
                      ? 'text-[#8B6F47] font-medium'
                      : 'text-gray-700 group-hover:text-[#8B6F47]'
                  ]"
                  @click.stop="toggleSelect(item)"
                >
                  {{ item.label }}
                </span>

                <!-- 子选项数量徽章 -->
                <span
                  v-if="item.children && item.children.length > 0"
                  class="px-2 py-0.5 text-xs rounded-full transition-colors duration-150"
                  :class="[
                    getSelectedCount(item) > 0
                      ? 'bg-[#8B6F47]/10 text-[#8B6F47] font-medium'
                      : 'bg-gray-100 text-gray-400'
                  ]"
                >
                  {{ getSelectedCount(item) }}/{{ item.children.length }}
                </span>
              </div>

              <!-- 子选项 -->
              <transition name="expand">
                <div
                  v-if="item.children && item.children.length > 0 && expandedKeys.includes(item.value)"
                  class="ml-4 mr-2 pl-3 border-l-2 border-gray-100"
                >
                  <template v-for="child in item.children" :key="child.value">
                    <div
                      class="group flex items-center gap-3 mx-1 px-3 py-2 rounded-lg cursor-pointer transition-all duration-150"
                      :class="[
                        isSelected(child.value)
                          ? 'bg-[#8B6F47]/5'
                          : 'hover:bg-gray-50'
                      ]"
                    >
                      <span class="w-6"></span>

                      <!-- 自定义复选框 -->
                      <div
                        class="relative w-5 h-5 flex-shrink-0"
                        @click.stop="toggleSelect(child)"
                      >
                        <input
                          type="checkbox"
                          :checked="isSelected(child.value)"
                          :disabled="disabled"
                          class="sr-only"
                        />
                        <div
                          class="w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all duration-200"
                          :class="[
                            isSelected(child.value)
                              ? 'bg-[#8B6F47] border-[#8B6F47]'
                              : 'border-gray-300 group-hover:border-[#8B6F47]/50'
                          ]"
                        >
                          <font-awesome-icon
                            v-if="isSelected(child.value)"
                            :icon="['fas', 'check']"
                            class="text-white text-[10px] font-bold"
                          />
                        </div>
                      </div>

                      <!-- 选项标签 -->
                      <span
                        class="flex-1 text-base transition-colors duration-150"
                        :class="[
                          isSelected(child.value)
                            ? 'text-[#8B6F47] font-medium'
                            : 'text-gray-600 group-hover:text-[#8B6F47]'
                        ]"
                        @click.stop="toggleSelect(child)"
                      >
                        {{ child.label }}
                      </span>

                      <!-- 选中指示 -->
                      <font-awesome-icon
                        v-if="isSelected(child.value)"
                        :icon="['fas', 'check-circle']"
                        class="text-[#8B6F47] text-xs"
                      />
                    </div>
                  </template>
                </div>
              </transition>
            </template>
          </div>
        </div>

        <!-- 底部提示 -->
        <div class="px-4 py-2.5 bg-gray-50/80 border-t border-gray-100 flex items-center justify-between">
          <span class="text-xs text-gray-400">
            <font-awesome-icon :icon="['fas', 'info-circle']" class="mr-1" />
            已选择 {{ selectedItems.length }} 个分类
          </span>
          <button
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

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

/**
 * 多选级联选择器组件
 * 功能：支持多选、树形层级、搜索过滤
 * 设计：精致学术风，使用项目主题色 #8B6F47
 */
const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  options: {
    type: Array,
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
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const containerRef = ref(null)
const dropdownVisible = ref(false)
const searchKeyword = ref('')
const expandedKeys = ref([])

// 标准化选项数据
const normalizedOptions = computed(() => {
  const normalize = (items) => {
    return items.map(item => ({
      value: item.value || item.name,
      label: item.label || item.name,
      children: item.children ? normalize(item.children) : []
    }))
  }
  return normalize(props.options || [])
})

// 过滤后的选项
const filteredOptions = computed(() => {
  if (!searchKeyword.value) return normalizedOptions.value

  const keyword = searchKeyword.value.toLowerCase()
  const result = []

  const filterItems = (items) => {
    const matched = []
    for (const item of items) {
      const labelMatch = item.label.toLowerCase().includes(keyword)
      let children = []

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
  const result = []
  const findItems = (items) => {
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
const isSelected = (value) => {
  return selectedValues.value.includes(value)
}

// 切换选择
const toggleSelect = (item) => {
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
const removeTag = (value) => {
  const newValues = selectedValues.value.filter(v => v !== value)
  selectedValues.value = newValues
}

// 清空所有
const clearAll = () => {
  selectedValues.value = []
}

// 切换展开
const toggleExpand = (value) => {
  const index = expandedKeys.value.indexOf(value)
  if (index > -1) {
    expandedKeys.value.splice(index, 1)
  } else {
    expandedKeys.value.push(value)
  }
}

// 获取子项选中数量
const getSelectedCount = (item) => {
  if (!item.children || item.children.length === 0) return 0
  return item.children.filter(child => selectedValues.value.includes(child.value)).length
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

// 点击外部关闭
const handleClickOutside = (event) => {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    dropdownVisible.value = false
  }
}

// 监听 options 变化，自动展开
watch(() => props.options, (newOptions) => {
  if (newOptions && newOptions.length > 0) {
    // 保持已选择的分类展开状态
    const selectedValuesSet = new Set(selectedValues.value)
    const keysToExpand = []

    const findParentKeys = (items, parentKey = null) => {
      for (const item of items) {
        if (selectedValuesSet.has(item.value) && parentKey) {
          keysToExpand.push(parentKey)
        }
        if (item.children && item.children.length > 0) {
          findParentKeys(item.children, item.value)
        }
      }
    }

    findParentKeys(newOptions)

    // 合并新的展开键
    const newExpandedKeys = [...new Set([...expandedKeys.value, ...keysToExpand])]
    if (newExpandedKeys.length > 0) {
      expandedKeys.value = newExpandedKeys
    }
  }
}, { deep: true })

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* 下拉菜单动画 */
.dropdown-enter-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
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

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
