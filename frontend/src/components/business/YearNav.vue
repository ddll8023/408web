<template>
  <div class="year-nav-container" :class="{ collapsed: isCollapsed }">
    <!-- 顶部标题栏 -->
    <div class="year-nav-header">
      <div class="toggle-btn" @click="toggleCollapse">
        <el-icon :size="20">
          <DArrowRight v-if="isCollapsed" />
          <DArrowLeft v-else />
        </el-icon>
      </div>
      <transition name="fade">
        <span class="header-title" v-if="!isCollapsed">年份导航</span>
      </transition>
      <div class="header-actions">
        <div class="collapse-all-btn" @click="collapseAll" v-if="!isCollapsed">
          <el-icon><Fold /></el-icon>
          <span>全部折叠</span>
        </div>
      </div>
    </div>

    <!-- 年份列表 -->
    <div class="year-list-scroll" v-show="!isCollapsed" v-loading="loading">
      <div
        v-for="yearData in yearList"
        :key="yearData.year"
        class="year-group"
      >
        <!-- 年份标题 -->
        <div 
          class="year-title-item" 
          :class="{ active: activeYear === yearData.year }"
        >
          <div class="title-content" @click="handleYearClick(yearData.year)">
            <div class="icon-area" @click.stop="toggleYear(yearData.year)">
              <el-icon class="expand-icon" :class="{ 'is-expanded': expandedYears.includes(yearData.year) }">
                <CaretRight />
              </el-icon>
            </div>
            <span class="year-text">{{ yearData.year }}年</span>
            <span class="count-badge">{{ yearData.exams.length }}</span>
          </div>
        </div>

        <!-- 题目列表 -->
        <el-collapse-transition>
          <div
            v-if="expandedYears.includes(yearData.year)"
            class="exam-sub-list"
          >
            <div
              v-for="exam in yearData.exams"
              :key="exam.id"
              class="exam-sub-item"
              :class="{ active: activeExamId === exam.id }"
              @click="handleExamClick(exam)"
            >
              <el-icon class="exam-icon"><Document /></el-icon>
              <span class="exam-title">{{ getExamDisplayText(exam) }}</span>
            </div>
          </div>
        </el-collapse-transition>
      </div>

      <!-- 空状态提示 -->
      <div v-if="!loading && yearList.length === 0" class="empty-state">
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

<style lang="scss" scoped>
@use 'sass:color';

/**
 * 年份导航栏组件样式
 * 优化版：Flex布局，Paper主题
 */

.year-nav-container {
  width: 280px;
  height: 100%;
  background-color: $color-primary; // 米色背景
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  z-index: 10;

  &.collapsed {
    width: 56px;
    
    .year-nav-header {
      justify-content: center;
      padding: 0;
      
      .toggle-btn {
        margin: 0;
      }
    }
  }
}

.year-nav-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  gap: 8px;
  
  .toggle-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    cursor: pointer;
    color: $color-accent;
    transition: all 0.2s;
    flex-shrink: 0;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
    }
  }

  .header-title {
    font-weight: 600;
    font-size: 16px;
    color: $color-accent;
    white-space: nowrap;
    overflow: hidden;
    flex: 1;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }
  
  .collapse-all-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
    color: $color-text-secondary;
    font-size: 13px;
    transition: all 0.2s;
    white-space: nowrap;
    
    .el-icon {
      font-size: 14px;
    }
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
      color: $color-accent;
    }
  }
}

.year-list-scroll {
  flex: 1;
  overflow-y: auto;
  @include scrollbar(4px);
  padding: 12px 8px;
}

.year-group {
  margin-bottom: 4px;
}

.year-title-item {
  padding: 0 8px;
  margin-bottom: 2px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  
  .title-content {
    display: flex;
    align-items: center;
    height: 44px;
    padding: 0 8px;
    width: 100%;
  }
  
  .icon-area {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    margin-right: 4px;
    border-radius: 4px;
    transition: background-color 0.2s;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
    }
  }
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.03);
  }
  
  &.active {
    background-color: rgba($color-accent, 0.08);
    
    .year-text, .count-badge, .expand-icon {
      color: $color-accent;
      font-weight: 600;
    }
  }

  .expand-icon {
    font-size: 14px;
    transition: transform 0.3s ease;
    color: $color-text-secondary;
    
    &.is-expanded {
      transform: rotate(90deg);
    }
  }

  .year-text {
    flex: 1;
    font-size: 15px;
    color: $color-text-primary;
  }
  
  .count-badge {
    font-size: 12px;
    color: $color-text-secondary;
    background-color: rgba(0,0,0,0.05);
    padding: 2px 6px;
    border-radius: 10px;
  }
}

.exam-sub-list {
  margin-top: 2px;
  padding-bottom: 4px;
}

.exam-sub-item {
  display: flex;
  align-items: center;
  height: 36px;
  padding: 0 12px 0 36px; // Indent
  margin-bottom: 2px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: $color-text-regular;
  transition: all 0.2s ease;
  
  .exam-icon {
    margin-right: 8px;
    font-size: 14px;
    opacity: 0.7;
  }
  
  .exam-title {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.03);
    color: $color-text-primary;
  }

  &.active {
    background-color: transparent; // 透明背景
    color: $color-accent;
    font-weight: 500;
    position: relative;
    
    .exam-icon {
      color: $color-accent;
      opacity: 1;
    }
    
    // 左侧指示条
    &::before {
      content: '';
      position: absolute;
      left: 24px;
      height: 14px;
      width: 2px;
      background-color: $color-accent;
      border-radius: 2px;
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $spacing-xs;
  padding: $spacing-lg;
  color: $color-text-secondary;
  font-size: $font-size-small;
  
  .el-icon {
    font-size: $font-size-xl;
    color: $color-warning;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式布局 */
@include mobile {
  .year-nav-container {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    
    &.collapsed {
      width: 100%;
    }
    
    .year-list-scroll {
      max-height: 300px;
    }
  }
}
</style>

