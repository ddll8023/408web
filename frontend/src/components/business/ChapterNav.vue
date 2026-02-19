<template>
  <div class="chapter-nav fixed left-0 top-[60px] w-[280px] h-[calc(100vh-60px)] bg-[#FBF7F2] border-r border-black/[0.06] shadow-[2px_0_8px_rgba(0,0,0,0.02)] transition-all duration-300 flex flex-col z-[999]" :class="{ collapsed: isCollapsed }">
    <!-- 顶部标题栏 -->
    <div class="chapter-nav-header flex items-center justify-start px-6 py-4 border-b border-black/[0.06] cursor-pointer select-none text-[#8B6F47] h-14 box-border hover:bg-black/[0.03]" @click="toggleCollapse">
      <el-icon class="collapse-icon mr-4 transition-transform duration-200 text-[#8B6F47]" :size="20">
        <DArrowRight v-if="isCollapsed" />
        <DArrowLeft v-else />
      </el-icon>
      <span class="header-title font-semibold text-[15px] whitespace-nowrap overflow-hidden" v-show="!isCollapsed">隐藏章节栏</span>
    </div>

    <!-- 章节列表 -->
    <div class="chapter-list flex-1 overflow-y-auto p-4" v-show="!isCollapsed">
      <div
        v-for="chapter in chapters"
        :key="chapter.id"
        class="chapter-item mb-0.5"
        :class="{ active: activeChapterId === chapter.id, expanded: expandedChapters.includes(chapter.id) }"
      >
        <!-- 章节标题 -->
        <div class="chapter-title flex items-center justify-start px-3 py-2.5 mb-0.5 rounded-lg cursor-pointer select-none text-[#8B6F47] transition-all duration-200 hover:bg-black/[0.04]" @click="toggleChapter(chapter.id)">
          <el-icon class="expand-icon mr-2 text-sm transition-transform duration-300 text-[#8B6F47] opacity-80" :class="{ 'is-expanded': expandedChapters.includes(chapter.id) }">
            <CaretRight />
          </el-icon>
          <span class="chapter-name flex-1 text-[15px] font-medium leading-[1.4]" @click.stop="handleChapterClick(chapter)">{{ chapter.name }}</span>
          <el-icon
            class="favorite-icon text-sm text-black/25 transition-all duration-200 opacity-0 cursor-pointer hover:text-[#8B6F47] hover:scale-120"
            :class="{ 'is-favorite': isFavorite(chapter.id) }"
            @click.stop="handleToggleFavorite(chapter)"
          >
            <Star />
          </el-icon>
        </div>

        <!-- 子章节列表 -->
        <div
          v-show="expandedChapters.includes(chapter.id)"
          class="sub-chapters py-0.5 pb-1"
        >
          <div
            v-for="subChapter in chapter.children"
            :key="subChapter.id"
            class="sub-chapter-item relative flex items-center py-2 pl-8 pr-3 m-0.5 rounded-md cursor-pointer select-none text-gray-800 text-sm transition-all duration-200 hover:bg-black/[0.04] hover:pl-9"
            :class="{ active: activeChapterId === subChapter.id }"
          >
            <span class="dot w-1 h-1 rounded-full bg-black/20 mr-2.5 transition-all duration-200"></span>
            <span class="sub-name flex-1 cursor-pointer" @click="handleSubChapterClick(subChapter)">{{ subChapter.name }}</span>
            <el-icon
              class="favorite-icon sub-favorite text-xs ml-2"
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
 * 主要使用Tailwind类名，保留必要的自定义样式和动画
 */

/* 导航栏容器 - 使用Tailwind类名在template中已实现 */

.chapter-nav.collapsed {
  @apply w-14;
}

.chapter-nav.collapsed .chapter-nav-header {
  @apply justify-center py-4;
}

.chapter-nav.collapsed .chapter-nav-header .collapse-icon {
  @apply mr-0;
}

/* 章节导航头部 - 使用Tailwind类名在template中已实现 */

/* 折叠图标 */
.chapter-nav-header .collapse-icon {
  @apply mr-4 transition-transform duration-200 text-[#8B6F47];
}

.chapter-nav-header:hover .collapse-icon {
  @apply scale-110;
}

/* 章节列表容器 */
.chapter-list::-webkit-scrollbar {
  @apply w-1 h-1;
}

.chapter-list::-webkit-scrollbar-thumb {
  @apply bg-black/20 rounded;
}

.chapter-list::-webkit-scrollbar-thumb:hover {
  @apply bg-black/30;
}

.chapter-list::-webkit-scrollbar-track {
  @apply bg-transparent;
}

/* 章节项 - 使用Tailwind类名在template中已实现 */

/* 章节标题 - 使用Tailwind类名在template中已实现 */

/* 展开图标旋转 */
.chapter-title .expand-icon.is-expanded {
  @apply rotate-90;
}

/* 收藏图标 */
.chapter-item .favorite-icon {
  @apply text-black/25 transition-all duration-200 opacity-0 cursor-pointer;
}

.chapter-item:hover .favorite-icon {
  @apply opacity-100;
}

.chapter-item .favorite-icon:hover {
  @apply text-[#8B6F47] scale-120;
}

.chapter-item .favorite-icon.is-favorite {
  @apply text-[#8B6F47] opacity-100;
}

/* 激活状态的章节 */
.chapter-item.active > .chapter-title {
  @apply bg-black/[0.06] text-[#6B5333] font-semibold;
}

/* 子章节列表动画 */
.chapter-item .sub-chapters {
  @apply py-0.5 pb-1;
  animation: slideDown 0.2s ease-out;
  transform-origin: top;
}

/* 子章节项 - 使用Tailwind类名在template中已实现 */

.chapter-item .sub-chapter-item .dot {
  @apply w-1 h-1 rounded-full bg-black/20 mr-2.5 transition-all duration-200;
}

/* 子章节激活状态 */
.chapter-item .sub-chapter-item.active {
  @apply bg-[rgba(139,111,71,0.08)] font-semibold text-[#8B6F47];
}

.chapter-item .sub-chapter-item.active .dot {
  @apply bg-[#8B6F47] scale-150;
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
    @apply w-60;
  }

  .chapter-nav.collapsed {
    @apply w-12 -translate-x-0;
  }
}
</style>
