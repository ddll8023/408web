<template>
  <div class="flex items-center justify-end gap-2">
    <!-- 总数显示 -->
    <span v-if="showTotal" class="text-sm text-gray-600">
      共 {{ total }} 条
    </span>

    <!-- 每页条数选择 -->
    <div v-if="showSizes" class="flex items-center gap-1">
      <select
        :value="pageSize"
        class="px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#8B6F47]/50"
        @change="handleSizeChange"
      >
        <option v-for="size in pageSizes" :key="size" :value="size">
          {{ size }} 条/页
        </option>
      </select>
    </div>

    <!-- 上一页按钮 -->
    <button
      :disabled="currentPage <= 1"
      class="px-2 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      @click="handlePrev"
    >
      <font-awesome-icon :icon="['fas', 'chevron-left']" />
    </button>

    <!-- 页码按钮 -->
    <template v-for="page in visiblePages" :key="page">
      <span v-if="page === '...'" class="px-1 text-gray-400">...</span>
      <button
        v-else
        class="px-3 py-1 border rounded text-sm transition-colors"
        :class="page === currentPage
          ? 'bg-[#8B6F47] text-white border-[#8B6F47]'
          : 'border-gray-300 hover:bg-gray-50'"
        @click="handlePageClick(page)"
      >
        {{ page }}
      </button>
    </template>

    <!-- 下一页按钮 -->
    <button
      :disabled="currentPage >= totalPages"
      class="px-2 py-1 border border-gray-300 rounded text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      @click="handleNext"
    >
      <font-awesome-icon :icon="['fas', 'chevron-right']" />
    </button>

    <!-- 跳转输入框 -->
    <div v-if="showJumper" class="flex items-center gap-1 ml-2">
      <span class="text-sm text-gray-600">到</span>
      <input
        v-model="jumpPage"
        type="number"
        min="1"
        :max="totalPages"
        class="w-14 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#8B6F47]/50"
        @keyup.enter="handleJump"
      />
      <span class="text-sm text-gray-600">页</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  // 当前页码
  currentPage: {
    type: Number,
    default: 1
  },
  // 每页条数
  pageSize: {
    type: Number,
    default: 10
  },
  // 可选每页条数
  pageSizes: {
    type: Array,
    default: () => [10, 20, 50, 100]
  },
  // 总数
  total: {
    type: Number,
    default: 0
  },
  // 是否显示总数
  showTotal: {
    type: Boolean,
    default: true
  },
  // 是否显示每页条数选择
  showSizes: {
    type: Boolean,
    default: true
  },
  // 是否显示跳转
  showJumper: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:currentPage', 'update:pageSize', 'current-change', 'size-change'])

const jumpPage = ref(props.currentPage)

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(props.total / props.pageSize) || 1
})

// 计算显示的页码
const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = props.currentPage

  if (total <= 7) {
    // 总页数小于等于7，显示全部
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // 总页数大于7，显示省略号
    if (current <= 3) {
      // 前面几页
      pages.push(1, 2, 3, 4, '...', total)
    } else if (current >= total - 2) {
      // 最后几页
      pages.push(1, '...', total - 3, total - 2, total - 1, total)
    } else {
      // 中间
      pages.push(1, '...', current - 1, current, current + 1, '...', total)
    }
  }

  return pages
})

// 上一页
const handlePrev = () => {
  if (props.currentPage > 1) {
    emit('update:currentPage', props.currentPage - 1)
    emit('current-change', props.currentPage - 1)
  }
}

// 下一页
const handleNext = () => {
  if (props.currentPage < totalPages.value) {
    emit('update:currentPage', props.currentPage + 1)
    emit('current-change', props.currentPage + 1)
  }
}

// 点击页码
const handlePageClick = (page) => {
  if (page !== '...' && page !== props.currentPage) {
    emit('update:currentPage', page)
    emit('current-change', page)
  }
}

// 每页条数变化
const handleSizeChange = (event) => {
  const newSize = parseInt(event.target.value, 10)
  emit('update:pageSize', newSize)
  emit('size-change', newSize)
}

// 跳转
const handleJump = () => {
  let page = parseInt(jumpPage.value, 10)
  if (isNaN(page) || page < 1) {
    page = 1
  } else if (page > totalPages.value) {
    page = totalPages.value
  }
  jumpPage.value = page
  emit('update:currentPage', page)
  emit('current-change', page)
}

// 监听 currentPage 变化，同步 jumpPage
watch(() => props.currentPage, (val) => {
  jumpPage.value = val
})
</script>
