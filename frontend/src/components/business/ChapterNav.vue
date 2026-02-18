<template>
  <div class="chapter-nav" :class="{ collapsed: isCollapsed }">
    <!-- 顶部标题栏 -->
    <div class="chapter-nav-header" @click="toggleCollapse">
      <el-icon class="collapse-icon" :size="20">
        <DArrowRight v-if="isCollapsed" />
        <DArrowLeft v-else />
      </el-icon>
      <span class="header-title" v-show="!isCollapsed">隐藏章节栏</span>
    </div>

    <!-- 章节列表 -->
    <div class="chapter-list" v-show="!isCollapsed">
      <div
        v-for="chapter in chapters"
        :key="chapter.id"
        class="chapter-item"
        :class="{ active: activeChapterId === chapter.id, expanded: expandedChapters.includes(chapter.id) }"
      >
        <!-- 章节标题 -->
        <div class="chapter-title" @click="toggleChapter(chapter.id)">
          <el-icon class="expand-icon" :class="{ 'is-expanded': expandedChapters.includes(chapter.id) }">
            <CaretRight />
          </el-icon>
          <span class="chapter-name" @click.stop="handleChapterClick(chapter)">{{ chapter.name }}</span>
          <el-icon
            class="favorite-icon"
            :class="{ 'is-favorite': isFavorite(chapter.id) }"
            @click.stop="handleToggleFavorite(chapter)"
          >
            <Star />
          </el-icon>
        </div>

        <!-- 子章节列表 -->
        <div
          v-show="expandedChapters.includes(chapter.id)"
          class="sub-chapters"
        >
          <div
            v-for="subChapter in chapter.children"
            :key="subChapter.id"
            class="sub-chapter-item"
            :class="{ active: activeChapterId === subChapter.id }"
          >
            <span class="dot"></span>
            <span class="sub-name" @click="handleSubChapterClick(subChapter)">{{ subChapter.name }}</span>
            <el-icon
              class="favorite-icon sub-favorite"
              :class="{ 'is-favorite': isFavorite(subChapter.id) }"
              @click.stop="handleToggleFavorite(subChapter)"
            >
              <Star />
            </el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 章节导航栏组件
 * 功能：展示可展开/折叠的章节导航，支持章节选择
 * 遵循KISS原则：简单的树形结构导航
 * 
 * Props:
 * - chapters: 章节数据数组
 * - activeChapterId: 当前激活的章节ID
 * 
 * Events:
 * - chapter-select: 章节被选中时触发
 */
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { DArrowLeft, DArrowRight, CaretRight, Star } from '@element-plus/icons-vue'
import { useFavorites } from '@/composables/useFavorites'

const props = defineProps({
  // 章节数据，格式：[{ id, name, children: [{ id, name }] }]
  chapters: {
    type: Array,
    default: () => []
  },
  // 当前激活的章节ID
  activeChapterId: {
    type: [Number, String],
    default: null
  },
  // 科目ID（用于收藏功能）
  subjectId: {
    type: Number,
    required: true
  },
  // 科目名称（用于收藏功能）
  subjectName: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['chapter-select', 'collapse-change'])

// 导航栏是否折叠
const isCollapsed = ref(false)

// 展开的章节ID列表
const expandedChapters = ref([])

// 收藏功能
const { isFavorite, toggleFavorite } = useFavorites()

/**
 * 切换导航栏折叠状态
 */
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  emit('collapse-change', isCollapsed.value)
}

/**
 * 切换章节展开/折叠
 */
const toggleChapter = (chapterId) => {
  const index = expandedChapters.value.indexOf(chapterId)
  if (index > -1) {
    expandedChapters.value.splice(index, 1)
  } else {
    expandedChapters.value.push(chapterId)
  }
}

/**
 * 处理章节点击
 */
const handleChapterClick = (chapter) => {
  emit('chapter-select', chapter)
}

/**
 * 处理子章节点击
 */
const handleSubChapterClick = (subChapter) => {
  emit('chapter-select', subChapter)
}

/**
 * 处理收藏切换
 */
const handleToggleFavorite = (chapter) => {
  const chapterData = {
    id: chapter.id,
    name: chapter.name,
    subjectId: props.subjectId,
    subjectName: props.subjectName
  }
  
  const isFavorited = toggleFavorite(chapterData)
  
  if (isFavorited) {
    ElMessage.success('已添加到收藏夹')
  } else {
    ElMessage.info('已取消收藏')
  }
}

// 监听激活章节变化，自动展开包含该章节的父级章节
watch(() => props.activeChapterId, (newId) => {
  if (!newId) return
  
  // 查找包含当前激活章节的父章节并展开
  props.chapters.forEach(chapter => {
    const hasActiveChild = chapter.children?.some(child => child.id === newId)
    if (hasActiveChild && !expandedChapters.value.includes(chapter.id)) {
      expandedChapters.value.push(chapter.id)
    }
  })
}, { immediate: true })
</script>

<style scoped>
/**
 * 章节导航栏组件样式
 * 设计：米色背景、圆角卡片风格、Element Plus 图标
 */

.chapter-nav {
  position: fixed;
  left: 0;
  top: 60px;
  width: 280px;
  height: calc(100vh - 60px);
  background-color: #FBF7F2;
  /* 米色背景 */
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.02);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  z-index: 999;

  &.collapsed {
    width: 56px;

    .chapter-nav-header {
      justify-content: center;
      padding: 16px 0;

      .collapse-icon {
        margin-right: 0;
      }
    }
  }
}

.chapter-nav-header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  cursor: pointer;
  user-select: none;
  color: #8B6F47;
  /* 棕色文字 */
  height: 56px;
  box-sizing: border-box;

  &:hover {
    background-color: rgba(0, 0, 0, 0.03);

    .collapse-icon {
      transform: scale(1.1);
    }
  }

  .collapse-icon {
    margin-right: 16px;
    transition: transform 0.2s ease;
    color: #8B6F47;
  }

  .header-title {
    font-weight: 600;
    font-size: 15px;
    white-space: nowrap;
    overflow: hidden;
  }
}

.chapter-list {
  flex: 1;
  overflow-y: auto;
  /* 自定义滚动条样式 */
  padding: 16px;
}
.chapter-list::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}
.chapter-list::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}
.chapter-list::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}
.chapter-list::-webkit-scrollbar-track {
  background-color: transparent;
}

.chapter-item {
  margin-bottom: 2px;

  .chapter-title {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding: 10px 12px;
    margin-bottom: 2px;
    border-radius: 8px;
    cursor: pointer;
    user-select: none;
    color: #8B6F47;
    transition: all 0.2s ease;

    &:hover {
      background-color: rgba(0, 0, 0, 0.04);
    }

    .expand-icon {
      margin-right: 8px;
      font-size: 14px;
      transition: transform 0.3s ease;
      color: #8B6F47;
      opacity: 0.8;

      &.is-expanded {
        transform: rotate(90deg);
      }
    }

    .chapter-name {
      flex: 1;
      font-size: 15px;
      font-weight: 500;
      line-height: 1.4;
    }

    .favorite-icon {
      font-size: 16px;
      color: rgba(0, 0, 0, 0.25);
      transition: all 0.2s ease;
      opacity: 0;
      cursor: pointer;

      &:hover {
        color: #8B6F47;
        transform: scale(1.2);
      }

      &.is-favorite {
        color: #8B6F47;
        opacity: 1;
      }
    }
  }

  &:hover .favorite-icon {
    opacity: 1;
  }

  /* 激活状态的章节(作为整体) */
  &.active > .chapter-title {
    background-color: rgba(0, 0, 0, 0.06);
    color: #6B5333;
    font-weight: 600;
  }

  .sub-chapters {
    padding: 2px 0 4px 0;
    /* 简单的展开动画提示 */
    animation: slideDown 0.2s ease-out;
    transform-origin: top;
  }

  .sub-chapter-item {
    position: relative;
    display: flex;
    align-items: center;
    padding: 8px 12px 8px 34px;
    margin: 2px 0;
    border-radius: 6px;
    cursor: pointer;
    user-select: none;
    color: #333;
    font-size: 14px;
    transition: all 0.2s ease;

    &:hover {
      background-color: rgba(0, 0, 0, 0.04);
      padding-left: 38px;
      /* 悬停微动效 */
    }

    .dot {
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background-color: rgba(0, 0, 0, 0.2);
      margin-right: 10px;
      transition: all 0.2s ease;
    }

    .sub-name {
      flex: 1;
      cursor: pointer;
    }

    .sub-favorite {
      font-size: 14px;
      margin-left: 8px;
    }

    &.active {
      background-color: rgba(139, 111, 71, 0.08);
      font-weight: 600;
      color: #8B6F47;

      .dot {
        background-color: #8B6F47;
        transform: scale(1.5);
      }
    }
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式布局 */
@media (max-width: 768px) {
  .chapter-nav {
    width: 240px;

    &.collapsed {
      width: 48px;
      transform: none;
    }
  }
}
</style>
