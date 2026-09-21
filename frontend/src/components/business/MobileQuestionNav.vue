<!-- 移动端题目导航：吸顶目录入口与底部目录抽屉，替代桌面侧栏在窄屏下的呈现。 -->
<template>
  <div class="mobile-question-nav md:hidden">
    <!-- 目录入口：内容区第一个元素，吸顶在全局导航下方 -->
    <button
      type="button"
      class="mobile-question-nav__trigger"
      aria-haspopup="dialog"
      :aria-expanded="visible"
      @click="open"
    >
      <span class="mobile-question-nav__icon" aria-hidden="true">
        <font-awesome-icon :icon="['fas', 'bars']" />
      </span>
      <span class="mobile-question-nav__title">{{ title }}</span>
      <span v-if="count > 0" class="mobile-question-nav__count">共 {{ count }} 题</span>
      <font-awesome-icon :icon="['fas', 'chevron-down']" class="mobile-question-nav__caret" aria-hidden="true" />
    </button>

    <BottomSheet
      :visible="visible"
      aria-label="题目目录"
      :title="`目录 · ${title}`"
      @update:visible="(value) => emit('update:visible', value)"
    >
      <p v-if="count > 0" class="mobile-question-nav__hint">共 {{ count }} 题，点击条目跳转</p>

      <slot name="nav" />

      <!-- 本页分组锚点：仅在选择父分类后出现，跳转后由页面关闭抽屉 -->
      <section v-if="outlineItems.length > 0" class="mobile-question-nav__outline" :aria-labelledby="outlineTitleId">
        <h3 :id="outlineTitleId" class="mobile-question-nav__outline-title">本页分组</h3>
        <ul class="mobile-question-nav__outline-list">
          <li v-for="item in outlineItems" :key="item.anchorId">
            <button
              type="button"
              class="mobile-question-nav__outline-item"
              :class="activeOutlineId === item.anchorId ? theme.active : 'text-gray-600 hover:bg-black/[0.04]'"
              :style="{ paddingLeft: `${10 + item.depth * 14}px` }"
              :aria-current="activeOutlineId === item.anchorId ? 'location' : undefined"
              @click="emit('outline-jump', item.anchorId)"
            >
              <span
                class="mobile-question-nav__outline-dot"
                :class="activeOutlineId === item.anchorId ? theme.dot : 'bg-gray-300'"
                aria-hidden="true"
              />
              <span class="min-w-0 flex-1 truncate">{{ item.label }}</span>
              <span class="shrink-0 text-xs text-gray-400">{{ item.count }}题</span>
            </button>
          </li>
        </ul>
      </section>
    </BottomSheet>
  </div>
</template>

<script setup lang="ts">
/**
 * 移动端题目导航
 * 入口栏收敛了原有侧栏的标题与折叠按钮；抽屉内容由页面通过 #nav 插槽注入，
 * 使用户在窄屏下不再被 220px 的导航区块挤压题目正文
 */
import type { PropType } from 'vue'
import type { CategoryOutlineItem } from '@/types'
import { computed, onDeactivated, onMounted, onUnmounted } from 'vue'
import BottomSheet from '@/components/basic/BottomSheet.vue'

interface OutlineTheme {
  active: string
  dot: string
}

const outlineThemes = {
  exam: { active: 'bg-exam-surface text-exam-strong', dot: 'bg-exam-accent' },
  mock: { active: 'bg-mock-surface text-mock-strong', dot: 'bg-mock-accent' },
  adaptation: { active: 'bg-accent/10 text-accent', dot: 'bg-accent' },
} satisfies Record<'exam' | 'mock' | 'adaptation', OutlineTheme>

let nextNavId = 0
const outlineTitleId = `mobile-nav-outline-title-${++nextNavId}`

const props = defineProps({
  // 是否展开抽屉
  visible: {
    type: Boolean,
    default: false
  },
  // 当前筛选范围的标题，例如「2023 年真题」或「数据结构 · 线性表 · 真题」
  title: {
    type: String,
    default: '题目目录'
  },
  // 当前范围内的题目总数
  count: {
    type: Number,
    default: 0
  },
  // 页内分组锚点
  outlineItems: {
    type: Array as PropType<readonly CategoryOutlineItem[]>,
    default: () => []
  },
  // 当前所在的分组锚点
  activeOutlineId: {
    type: String,
    default: ''
  },
  // 科目类型，决定锚点激活色
  kind: {
    type: String as PropType<'exam' | 'mock' | 'adaptation'>,
    default: 'exam'
  }
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'outline-jump': [anchorId: string]
}>()

const theme = computed(() => outlineThemes[props.kind])

const open = () => emit('update:visible', true)

// 抽屉挂载在 body 上不受根节点 md:hidden 约束，视口变宽时主动收起，避免残留遮罩
let desktopQuery: MediaQueryList | null = null
const handleDesktopChange = (event: MediaQueryListEvent) => {
  if (event.matches) emit('update:visible', false)
}

onMounted(() => {
  if (typeof window === 'undefined' || !window.matchMedia) return
  desktopQuery = window.matchMedia('(min-width: 768px)')
  desktopQuery.addEventListener('change', handleDesktopChange)
})

onUnmounted(() => {
  desktopQuery?.removeEventListener('change', handleDesktopChange)
  desktopQuery = null
})

// 页面被 keep-alive 缓存时先行收起，避免返回该页面时弹层仍然打开
onDeactivated(() => {
  if (props.visible) emit('update:visible', false)
})
</script>

<style scoped>
/* 吸顶由根节点负责：sticky 元素会被父级内容盒约束，因此不能挂在按钮上 */
.mobile-question-nav {
  position: sticky;
  top: 0;
  z-index: 20;
}

.mobile-question-nav__trigger {
  display: flex;
  width: 100%;
  min-height: 52px;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 0;
  border-bottom: 1px solid color-mix(in srgb, var(--brand-accent) 14%, transparent);
  background: color-mix(in srgb, var(--brand-surface) 94%, transparent);
  backdrop-filter: blur(10px);
  color: var(--brand-ink);
  cursor: pointer;
  text-align: left;
}

.mobile-question-nav__trigger:focus-visible {
  outline: 2px solid #8b6f47;
  outline-offset: -2px;
}

.mobile-question-nav__icon {
  display: inline-flex;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: color-mix(in srgb, var(--brand-accent) 10%, transparent);
  color: #8b6f47;
  font-size: 13px;
}

.mobile-question-nav__title {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  font-size: 15px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-question-nav__count {
  flex: 0 0 auto;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 8px;
  color: #8b6f47;
  font-size: 12px;
}

.mobile-question-nav__caret {
  flex: 0 0 auto;
  color: #8b6f47;
  font-size: 12px;
}

.mobile-question-nav__hint {
  margin: 0 0 8px;
  color: #9ca3af;
  font-size: 12px;
}

.mobile-question-nav__outline {
  margin-top: 14px;
  border-top: 1px solid #ece5db;
  padding-top: 12px;
}

.mobile-question-nav__outline-title {
  margin: 0 0 6px;
  color: #8b6f47;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.mobile-question-nav__outline-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.mobile-question-nav__outline-item {
  display: flex;
  min-height: 36px;
  width: 100%;
  align-items: center;
  gap: 8px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  padding-right: 8px;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.mobile-question-nav__outline-dot {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 999px;
}

@media (max-width: 419px) {
  .mobile-question-nav__count {
    display: none;
  }
}
</style>
