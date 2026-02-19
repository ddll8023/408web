<template>
  <div class="year-nav-container w-[280px] h-full bg-[#FBF7F2] border-r border-black/[0.05] flex flex-col transition-all duration-300 flex-shrink-0 z-10" :class="{ collapsed: isCollapsed }">
    <!-- 顶部标题栏 -->
    <div class="year-nav-header h-14 flex items-center justify-between px-4 border-b border-black/[0.05] flex-shrink-0 gap-2">
      <div class="toggle-btn w-8 h-8 flex items-center justify-center rounded-md cursor-pointer text-[#8B6F47] transition-all duration-200 flex-shrink-0 hover:bg-black/[0.05]" @click="toggleCollapse">
        <el-icon :size="20">
          <DArrowRight v-if="isCollapsed" />
          <DArrowLeft v-else />
        </el-icon>
      </div>
      <transition name="fade">
        <span class="header-title font-semibold text-base text-[#8B6F47] whitespace-nowrap overflow-hidden flex-1" v-if="!isCollapsed">年份导航</span>
      </transition>
      <div class="header-actions flex items-center gap-2 flex-shrink-0">
        <div class="collapse-all-btn flex items-center gap-1 px-2 py-1 rounded cursor-pointer text-gray-400 text-[13px] transition-all duration-200 whitespace-nowrap hover:bg-black/[0.05] hover:text-[#8B6F47]" @click="collapseAll" v-if="!isCollapsed">
          <el-icon><Fold /></el-icon>
          <span>全部折叠</span>
        </div>
      </div>
    </div>

    <!-- 年份列表 -->
    <div class="year-list-scroll flex-1 overflow-y-auto px-2 py-3" v-show="!isCollapsed" v-loading="loading">
      <div
        v-for="yearData in yearList"
        :key="yearData.year"
        class="year-group mb-1"
      >
        <!-- 年份标题 -->
        <div
          class="year-title-item px-2 mb-0.5 rounded-lg cursor-pointer transition-all duration-200"
          :class="{ active: activeYear === yearData.year }"
        >
          <div class="title-content flex items-center h-11 px-2 w-full" @click="handleYearClick(yearData.year)">
            <div class="icon-area flex items-center justify-center w-6 h-6 mr-1 rounded transition-bg duration-200 hover:bg-black/[0.05]" @click.stop="toggleYear(yearData.year)">
              <el-icon class="expand-icon text-sm transition-transform duration-300 text-gray-400" :class="{ 'is-expanded': expandedYears.includes(yearData.year) }">
                <CaretRight />
              </el-icon>
            </div>
            <span class="year-text flex-1 text-[15px] text-gray-800">{{ yearData.year }}年</span>
            <span class="count-badge text-xs text-gray-400 bg-black/[0.05] px-1.5 py-0.5 rounded-full">{{ yearData.exams.length }}</span>
          </div>
        </div>

        <!-- 题目列表 -->
        <el-collapse-transition>
          <div
            v-if="expandedYears.includes(yearData.year)"
            class="exam-sub-list mt-0.5 pb-1"
          >
            <div
              v-for="exam in yearData.exams"
              :key="exam.id"
              class="exam-sub-item flex items-center h-9 px-3 pl-9 mb-0.5 rounded-md cursor-pointer text-gray-500 text-[13px] transition-all duration-200"
              :class="{ active: activeExamId === exam.id }"
              @click="handleExamClick(exam)"
            >
              <el-icon class="exam-icon mr-2 text-sm opacity-70"><Document /></el-icon>
              <span class="exam-title flex-1 whitespace-nowrap overflow-hidden text-ellipsis">{{ getExamDisplayText(exam) }}</span>
            </div>
          </div>
        </el-collapse-transition>
      </div>

      <!-- 空状态提示 -->
      <div v-if="!loading && yearList.length === 0" class="empty-state flex flex-col items-center justify-center gap-2 p-8 text-gray-400 text-xs">
        <el-icon><WarningFilled /></el-icon>
        <span>暂无真题数据</span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 年份导航栏组件
 * 功能：展示可展开/折叠的年份导航，支持题目选择
 * 遵循KISS原则：简单的树形结构导航
 * 
 * Props:
 * - yearList: 年份数据数组，格式：[{ year, exams: [{ id, title, questionNumber }] }]
 * - activeYear: 当前激活的年份
 * - activeExamId: 当前激活的题目ID
 * - loading: 加载状态
 * 
 * Events:
 * - exam-select: 题目被选中时触发
 */
import { ref, watch } from 'vue'
import { WarningFilled, DArrowLeft, DArrowRight, CaretRight, Document, Fold } from '@element-plus/icons-vue'

const props = defineProps({
  // 年份数据，格式：[{ year: 2024, exams: [{ id, title, questionNumber, category }] }]
  yearList: {
    type: Array,
    default: () => []
  },
  // 当前激活的年份
  activeYear: {
    type: Number,
    default: null
  },
  // 当前激活的题目ID
  activeExamId: {
    type: [Number, String],
    default: null
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['exam-select', 'year-select', 'collapse-change'])

// 导航栏是否折叠
const isCollapsed = ref(false)

// 展开的年份列表
const expandedYears = ref([])

/**
 * 切换导航栏折叠状态
 */
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  emit('collapse-change', isCollapsed.value)
}

/**
 * 切换年份展开/折叠
 */
const toggleYear = (year) => {
  const index = expandedYears.value.indexOf(year)
  if (index > -1) {
    expandedYears.value.splice(index, 1)
  } else {
    expandedYears.value.push(year)
  }
}

/**
 * 处理年份点击
 */
const handleYearClick = (year) => {
  emit('year-select', year)
}

/**
 * 处理题目点击
 */
const handleExamClick = (exam) => {
  emit('exam-select', exam)
}

/**
 * 获取题目显示文本
 */
const getExamDisplayText = (exam) => {
  // 优先显示标题
  if (exam.title) {
    return exam.title
  }
  // 其次显示题号
  if (exam.questionNumber) {
    return `第 ${exam.questionNumber} 题`
  }
  // 最后显示分类
  return exam.category || '真题'
}

/**
 * 全部折叠：折叠所有展开的年份
 */
const collapseAll = () => {
  expandedYears.value = []
}

// 监听激活题目变化，自动展开包含该题目的年份
watch(() => props.activeExamId, (newId) => {
  if (!newId) return
  
  // 查找包含当前激活题目的年份并展开
  props.yearList.forEach(yearData => {
    const hasActiveExam = yearData.exams.some(exam => exam.id === newId)
    if (hasActiveExam && !expandedYears.value.includes(yearData.year)) {
      expandedYears.value.push(yearData.year)
    }
  })
}, { immediate: true })

// 监听激活年份变化
watch(() => props.activeYear, (newYear) => {
  if (newYear && !expandedYears.value.includes(newYear)) {
    expandedYears.value.push(newYear)
  }
}, { immediate: true })
</script>

<style scoped>
/**
 * 年份导航栏组件样式
 * 使用纯CSS样式，兼容Tailwind CSS 4
 */

/* 导航栏容器 - 使用Tailwind类名在template中已实现 */

.year-nav-container.collapsed {
  width: 56px;
}

.year-nav-container.collapsed .year-nav-header {
  justify-content: center;
  padding: 0;
}

.year-nav-container.collapsed .year-nav-header .toggle-btn {
  margin: 0;
}

/* 年份导航头部 - 使用Tailwind类名在template中已实现 */

/* 折叠按钮 - 使用Tailwind类名在template中已实现 */

/* 全部折叠按钮 - 使用Tailwind类名在template中已实现 */

.collapse-all-btn .el-icon {
  font-size: 14px;
}

/* 年份列表滚动容器 - 使用Tailwind类名在template中已实现 */

/* 自定义滚动条 */
.year-list-scroll::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.year-list-scroll::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.year-list-scroll::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

.year-list-scroll::-webkit-scrollbar-track {
  background-color: transparent;
}

/* 年份标题项 - 使用Tailwind类名在template中已实现 */

/* 展开图标旋转 */
.year-title-item .expand-icon.is-expanded {
  transform: rotate(90deg);
}

/* 年份激活状态 */
.year-title-item.active {
  background-color: rgba(139, 111, 71, 0.08);
}

.year-title-item.active .year-text,
.year-title-item.active .count-badge,
.year-title-item.active .expand-icon {
  color: #8B6F47;
  font-weight: 600;
}

/* 题目列表 - 使用Tailwind类名在template中已实现 */

/* 题目项激活状态 */
.exam-sub-item.active {
  background-color: transparent;
  color: #8B6F47;
  font-weight: 500;
  position: relative;
}

.exam-sub-item.active .exam-icon {
  color: #8B6F47;
  opacity: 1;
}

/* 左侧指示条 */
.exam-sub-item.active::before {
  content: '';
  position: absolute;
  left: 24px;
  height: 14px;
  width: 2px;
  background-color: #8B6F47;
  border-radius: 1px;
}

/* 空状态 - 使用Tailwind类名在template中已实现 */

.empty-state .el-icon {
  font-size: 20px;
  color: #fb923c;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .year-nav-container {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  }

  .year-nav-container.collapsed {
    width: 100%;
  }

  .year-nav-container .year-list-scroll {
    max-height: 300px;
  }
}
</style>

