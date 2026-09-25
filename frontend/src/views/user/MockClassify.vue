<!-- 模拟题分类阅读页面：窄屏使用吸顶目录入口与底部目录抽屉，桌面端保留科目侧栏。 -->
<template>
  <ReadingLayout @content-ready="setContentScroller">
    <template #wide-nav>
      <!-- 左侧科目导航栏（窄屏自动隐藏） -->
      <SubjectSidebar
        v-model:is-collapsed="isNavCollapsed"
        v-model:expanded-ids="expandedCategoryIds"
        :subjects="subjects"
        :active-subject-id="activeSubjectId"
        :expanded-subject-id="expandedSubjectId"
        :subject-categories="subjectCategories"
        :filter-category="filterCategory"
        :loading="loadingSubjects"
        @select-subject="handleSubjectSelect"
        @toggle-expand="toggleSubjectExpand"
        @select-category="(payload) => handleCategorySelect(payload.subject, payload.category)"
      />
    </template>

    <template #compact-nav>
      <!-- 窄屏目录入口与抽屉 -->
      <MobileQuestionNav
        v-model:visible="navSheetVisible"
        :title="currentTitle"
        :count="displayTotal"
        :outline-items="outlineItems"
        :active-outline-id="activeOutlineId"
        kind="mock"
        @outline-jump="handleNavSheetOutlineJump"
      >
        <template #nav>
          <SubjectNavList
            v-model:expanded-ids="expandedCategoryIds"
            :subjects="subjects"
            :subject-categories="subjectCategories"
            :active-subject-id="activeSubjectId"
            :expanded-subject-id="expandedSubjectId"
            :filter-category="filterCategory"
            :loading="loadingSubjects"
            auto-scroll-active
            @select-subject="handleSubjectSelect"
            @toggle-expand="toggleSubjectExpand"
            @select-category="handleNavSheetCategorySelect"
          />
        </template>
      </MobileQuestionNav>
    </template>

    <div class="min-h-full bg-surface">
          <div class="p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div class="hidden min-w-0 flex-1 items-center gap-3 md:flex">
                <h2 class="m-0 text-ink font-semibold text-xl">{{ currentTitle }}</h2>
                <Tag v-if="displayTotal > 0" type="info">共 {{ displayTotal }} 题</Tag>
              </div>
              <div class="flex flex-wrap gap-2" v-if="activeSubjectId">
                <RadioGroup
                  v-model="filterQuestionType"
                  aria-label="题型筛选"
                  :options="questionTypeOptions"
                />
              </div>
            </div>

          <div v-if="questionsLoading" class="flex items-center justify-center py-12" role="status" aria-live="polite">
            <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-accent text-2xl" aria-hidden="true" />
          </div>

          <div v-if="subjectsLoadError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
            {{ subjectsLoadError }}
            <CustomButton size="sm" type="text" @click="loadSubjects">重新读取科目</CustomButton>
          </div>

          <div v-if="questionsLoadError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
            {{ questionsLoadError }}
            <CustomButton size="sm" type="text" :disabled="questionsLoading" @click="loadQuestions(true)">重试</CustomButton>
          </div>

          <!-- 分类分组列表：标题显式区分模拟题、父子层级和题目数量 -->
          <div
            v-if="groupedQuestions.length > 0"
            class="mx-auto mt-6 w-full"
            :class="outlineItems.length > 0
              ? 'grid max-w-[1400px] grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1fr)_230px]'
              : 'flex max-w-[1100px] flex-col gap-5'"
          >
            <main class="min-w-0 flex flex-col gap-5">
              <section
                v-for="group in groupedQuestions"
                :id="getCategorySectionId('mock', group.categoryId, group.category)"
                :key="group.categoryId ?? group.category"
                class="category-question-section scroll-mt-14 md:scroll-mt-4"
                :class="group.depth > 0 ? 'ml-3 md:ml-6' : ''"
              >
                <CategorySectionHeader
                  :category="group.category"
                  :count="group.items.length"
                  kind="mock"
                  :depth="group.depth"
                />
                <div class="mt-3 flex flex-col gap-4">
                  <MockEntryCard
                    v-for="mock in group.items"
                    :key="mock.id"
                    :id="`mock-${mock.id}`"
                    :mock="mock"
                    :is-admin="isAdmin"
                    :show-answer="showAnswers[mock.id]"
                    density="compact"
                    @copy="(cmd) => handleCopy(cmd, mock)"
                    @edit="handleEdit"
                    @delete="handleDelete"
                    @toggle-answer="toggleAnswer(mock.id)"
                    @answered="(payload) => handleAnswered(mock, payload)"
                  />
                </div>
              </section>
            </main>

            <CategoryOutline
              v-if="outlineItems.length > 0"
              :items="outlineItems"
              :active-id="activeOutlineId"
              kind="mock"
              @jump="scrollToCategory"
            />
          </div>

          <Empty
            v-if="!questionsLoadError && !subjectsLoadError && groupedQuestions.length === 0"
            :description="activeSubjectId ? '该科目暂无模拟题' : '请选择左侧科目'"
          />

          <!-- 加载更多按钮 -->
              <div v-if="hasMore" class="flex justify-center py-8 mt-4">
                <CustomButton
                  :loading="questionsLoading"
                  type="primary"
                  @click="loadQuestions(false)"
                >
                  {{ questionsLoading ? '加载中...' : '加载更多模拟题' }}
                </CustomButton>
              </div>
          </div>
        </div>

        <MockEditDialog
          v-if="isAdmin"
          v-model:visible="editDialogVisible"
          :mock-id="editingMockId"
          :mock-data="editingMockData"
          @success="handleEditSuccess"
        />

      <BackTop :right="32" :bottom="32" />
  </ReadingLayout>
</template>

<script setup lang="ts">
import type { CategoryOutlineItem, MockQuestion, Subject, CategoryTreeNode } from "@/types"
import { queryString } from "@/utils/storage"
import { parseQuestionOptions } from "@/utils/questionOptions"
import { errorMessage } from "@/utils/errors"
/**
 * 模拟题分类浏览页面
 * 功能：按科目聚合展示模拟题，支持分类筛选
 * 设计哲学：KISS (专注模拟题浏览), SOLID (单一职责)
 */
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getEnabledSubjects } from '@/api/subject'
import {
  getMockQuestions,
  getMockQuestionById,
  deleteMockQuestion,
  getMockSubjectStats,
  recordMockWrongAnswer,
} from '@/api/mock'
import { getEnabledCategoryTreeBySubjectWithStats } from '@/api/category'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import CustomButton from '@/components/basic/CustomButton.vue'
import Tag from '@/components/basic/Tag.vue'
import RadioGroup from '@/components/basic/RadioGroup.vue'
import Empty from '@/components/basic/Empty.vue'
import BackTop from '@/components/basic/BackTop.vue'
import ReadingLayout from '@/app/layouts/ReadingLayout.vue'
import SubjectSidebar from '@/components/business/SubjectSidebar.vue'
import SubjectNavList from '@/components/business/SubjectNavList.vue'
import MobileQuestionNav from '@/components/business/MobileQuestionNav.vue'
import CategoryOutline from '@/components/business/CategoryOutline.vue'
import CategorySectionHeader from '@/components/business/CategorySectionHeader.vue'
import MockEntryCard from '@/components/business/MockEntryCard.vue'
import MockEditDialog from '@/components/business/MockEditDialog.vue'
import { useCategoryOutline } from '@/composables/useCategoryOutline'
import { useInfiniteQuestionList } from '@/composables/useInfiniteQuestionList'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'
import {
  findCategoryNode,
  getCategorySectionId,
  groupMockQuestionsByCategory,
} from '@/utils/examCategoryGrouping'

const route = useRoute()
const authStore = useAuthStore()
const { showToast } = useToast()
const { showConfirm } = useConfirm()

// 计算是否为管理员
const isAdmin = computed(() => authStore.isAdmin())

// 编辑弹窗状态
const editDialogVisible = ref(false)
const editingMockId = ref<number | null>(null)
const editingMockData = ref<MockQuestion | null>(null)  // 编辑时传递的完整数据（避免重复请求API）

// UI State
const isNavCollapsed = ref(false)
// 窄屏目录抽屉开关
const navSheetVisible = ref(false)
// 分类展开状态：桌面侧栏与窄屏抽屉共用同一份状态
const expandedCategoryIds = ref<number[]>([])
const loadingSubjects = ref(false)
const subjectsLoadError = ref('')

// Data
const subjects = ref<Subject[]>([])
const subjectCategories = ref<Record<number, CategoryTreeNode[]>>({})
const activeSubjectId = ref<number | null>(null)
const activeSubjectName = ref('')
const expandedSubjectId = ref<number | null>(null)

// Filter Data
const filterCategory = ref('')
const filterQuestionType = ref('ALL')

// 题型选项
const questionTypeOptions = [
  { label: '全部题型', value: 'ALL' },
  { label: '选择题', value: 'CHOICE' },
  { label: '主观题', value: 'ESSAY' }
]

// Questions Data
const {
  items: questionList,
  loading: initialQuestionsLoading,
  loadingMore: loadingMoreQuestions,
  error: questionsLoadError,
  hasMore: hasMorePages,
  reload: reloadQuestions,
  loadMore: loadMoreQuestions,
  reset: resetQuestions,
} = useInfiniteQuestionList<MockQuestion>(
  (page, pageSize) => getMockQuestions({
    page,
    size: pageSize,
    subjectId: activeSubjectId.value,
    category: filterCategory.value || undefined,
  }),
  {
    pageSize: 50,
    getHasMore: (items, pagination) => items.length < pagination.total,
    fallbackErrorMessage: '模拟题读取失败，请重试。',
    stopOnResponseError: true,
    onRequestError: error => console.error('加载模拟题失败:', error),
  },
)
const questionsLoading = computed(() => initialQuestionsLoading.value || loadingMoreQuestions.value)
const hasMore = computed(() => activeSubjectId.value !== null && hasMorePages.value)
const showAnswers = ref<Record<number, boolean>>({})
const contentScroller = ref<HTMLElement | null>(null)
const setContentScroller = (element: HTMLElement | null) => {
  contentScroller.value = element
}



// Computed
const currentTitle = computed(() => {
  if (activeSubjectName.value && filterCategory.value) {
    return `${activeSubjectName.value} · ${filterCategory.value} · 模拟题`
  }
  return activeSubjectName.value ? `${activeSubjectName.value} · 模拟题` : '模拟题分类浏览'
})

const currentCategories = computed<CategoryTreeNode[]>(() => {
  if (activeSubjectId.value === null) return []
  return subjectCategories.value[activeSubjectId.value] || []
})

const selectedCategoryNode = computed(() => {
  if (!filterCategory.value) return undefined
  return findCategoryNode(currentCategories.value, filterCategory.value)
})

const groupedQuestions = computed(() => {
  let list = questionList.value || []
  if (!list.length) return []

  // 按题型筛选
  if (filterQuestionType.value === 'CHOICE') {
    list = list.filter(q => q.questionType === 'CHOICE')
  } else if (filterQuestionType.value === 'ESSAY') {
    list = list.filter(q => q.questionType !== 'CHOICE')
  }

  // 父分类筛选由后端展开子孙范围；按分类树顺序分组，并让父分类自身题目独立排在首组。
  return groupMockQuestionsByCategory(list, currentCategories.value, filterCategory.value)
})

const outlineItems = computed<CategoryOutlineItem[]>(() => {
  if (!selectedCategoryNode.value?.children.length || groupedQuestions.value.length === 0) {
    return []
  }

  return groupedQuestions.value.map(group => ({
    anchorId: getCategorySectionId('mock', group.categoryId, group.category),
    label: group.category,
    depth: group.depth,
    count: group.items.length,
  }))
})

const { activeId: activeOutlineId, scrollToCategory } = useCategoryOutline({
  containerRef: contentScroller,
  items: outlineItems,
})

const displayTotal = computed(() => {
  if (!questionList.value || !questionList.value.length) return 0
  return groupedQuestions.value.reduce((sum, group) => sum + group.items.length, 0)
})




// Initialization
onMounted(() => {
  initPage()
})



const initPage = async () => {
  await loadSubjects()
}

// 1. Load Subjects
const loadSubjects = async () => {
  loadingSubjects.value = true
  try {
    const res = await getEnabledSubjects()
    if (res.code === 200) {
      subjectsLoadError.value = ''
      subjects.value = res.data || []
      
      // 加载模拟题的科目统计，覆盖默认的真题统计
      try {
        const statsRes = await getMockSubjectStats()
        if (statsRes.code === 200 && statsRes.data) {
          const statsMap: Record<number, number> = {}
          statsRes.data.forEach(item => {
            statsMap[item.subjectId] = item.count
          })
          // 覆盖 subjects 中的 questionCount
          subjects.value = subjects.value.map(sub => ({
            ...sub,
            questionCount: statsMap[sub.id] || 0
          }))
        }
      } catch (statsErr) {
        console.error('加载模拟题统计失败:', statsErr)
      }
      
      // 检查URL参数
      const subjectFromRoute = queryString(route.query.subject)
      const categoryFromRoute = queryString(route.query.category)
      
      let initialSubject: Subject | undefined
      
      if (subjectFromRoute && subjects.value.length > 0) {
        initialSubject = subjects.value.find(s => s.name === subjectFromRoute)
        if (initialSubject && categoryFromRoute) {
          filterCategory.value = categoryFromRoute
        }
      }
      
      if (!initialSubject && subjects.value.length > 0) {
        initialSubject = subjects.value[0]
      }
      
      if (initialSubject) {
        await handleSubjectSelect(initialSubject)
        
        // 静默加载其他科目的分类
        subjects.value.forEach(sub => {
          if (sub.id !== activeSubjectId.value) {
            loadCategoriesForSubject(sub.id)
          }
        })
        
        // 处理URL hash跳转（从管理页面"查看"按钮跳转过来）
        await handleHashScroll()
      }
    } else {
      subjectsLoadError.value = res.message || '科目读取失败，请重试。'
      showToast(subjectsLoadError.value, 'error')
    }
  } catch (e) {
    subjectsLoadError.value = '科目读取失败，请重试。'
    showToast(subjectsLoadError.value, 'error')
    console.error('加载科目失败:', e)
  } finally {
    loadingSubjects.value = false
  }
}

/**
 * 处理URL hash跳转
 * 支持从模拟题管理页面的"查看"按钮跳转到具体题目
 * URL格式: /mock?subject=科目名称#mock-题目ID
 */
const handleHashScroll = async () => {
  const hash = window.location.hash
  if (!hash || !hash.startsWith('#mock-')) return

  const mockId = hash.slice('#mock-'.length)
  if (!mockId || Number.isNaN(Number(mockId))) return

  try {
    const response = await getMockQuestionById(Number(mockId))
    if (response.code !== 200 || !response.data) {
      console.warn('目标模拟题不存在:', mockId)
      return
    }

    const targetMock = response.data
    if (targetMock.subjectId != null && targetMock.subjectId !== activeSubjectId.value) {
      const targetSubject = subjects.value.find(subject => subject.id === targetMock.subjectId)
      if (!targetSubject) return
      await handleSubjectSelect(targetSubject)
    }

    if (targetMock.category && targetMock.category.length > 0) {
      filterCategory.value = targetMock.category[0]
      await loadQuestions(true)
    }

    if (!questionList.value.some(question => question.id === targetMock.id)) {
      questionList.value.unshift(targetMock)
    }

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const element = document.getElementById(`mock-${mockId}`)
    if (!element) return

    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.classList.add('highlight-card')
    setTimeout(() => {
      element.classList.remove('highlight-card')
    }, 2000)
  } catch (error) {
    console.error('处理模拟题 hash 跳转失败:', error)
  }
}

const loadCategoriesForSubject = async (subjectId: number) => {
  if (subjectCategories.value[subjectId]) {
    return
  }

  try {
    // 使用新的树形分类API，返回带模拟题统计的多级分类结构
    const res = await getEnabledCategoryTreeBySubjectWithStats(subjectId, 'mock')
    if (res.code === 200) {
      const tree = res.data || []
      subjectCategories.value = {
        ...subjectCategories.value,
        [subjectId]: tree
      }
    }
  } catch (e) {
    console.error('加载科目分类失败:', e)
  }
}

// Interaction: Select Subject
const handleSubjectSelect = async (subject: Subject) => {
  // 当前科目的展开/收起由侧栏箭头负责，点击名称只负责切换题目范围。
  if (activeSubjectId.value === subject.id) return

  activeSubjectId.value = subject.id
  activeSubjectName.value = subject.name

  filterCategory.value = ''
  filterQuestionType.value = 'ALL'
  expandedSubjectId.value = subject.id
  showAnswers.value = {}

  await Promise.all([
    loadCategoriesForSubject(subject.id),
    loadQuestions(true)
  ])
}

const toggleSubjectExpand = async (subject: Subject | null) => {
  if (!subject) { expandedSubjectId.value = null; return }
  const id = subject.id

  if (expandedSubjectId.value === id) {
    expandedSubjectId.value = null
    return
  }

  // 先更新箭头状态，分类请求完成后只补充树数据，不阻塞侧栏反馈。
  expandedSubjectId.value = id
  await loadCategoriesForSubject(id)
}

const handleCategorySelect = (subject: Subject, category: string) => {
  if (activeSubjectId.value !== subject.id) {
    activeSubjectId.value = subject.id
    activeSubjectName.value = subject.name
  }
  if (filterCategory.value === category) {
    filterCategory.value = ''
  } else {
    filterCategory.value = category
  }

  showAnswers.value = {}
  loadQuestions(true)
}

/**
 * 抽屉内选择分类：先收起抽屉再加载该分类题目
 * 科目行仍保留原处理函数，便于在抽屉内继续展开分类树
 */
const handleNavSheetCategorySelect = (selection: { subject: Subject; category: string }) => {
  navSheetVisible.value = false
  handleCategorySelect(selection.subject, selection.category)
}

/**
 * 抽屉内选择分组锚点：先收起抽屉再滚到对应分组
 */
const handleNavSheetOutlineJump = (anchorId: string) => {
  navSheetVisible.value = false
  scrollToCategory(anchorId)
}



const toggleAnswer = (id: number) => {
  showAnswers.value[id] = !showAnswers.value[id]
}

/**
 * 只为模拟题记录选择错误次数；计数不在学习页面展示。
 */
const handleAnswered = (
  mock: MockQuestion,
  payload: { optionKey: string; correct: boolean },
) => {
  if (payload.correct) return

  void recordMockWrongAnswer(mock.id).catch((error: unknown) => {
    // 计数失败不影响当前答题反馈，保留日志便于管理员排查。
    console.error('记录模拟题错题计数失败:', error)
  })
}

// 难度辅助函数已从 @/constants/exam 导入

// Core: Load Questions
const loadQuestions = async (isReset = false) => {
  if (!activeSubjectId.value) {
    resetQuestions()
    return
  }

  if (isReset) {
    showAnswers.value = {}
    await reloadQuestions()
    return
  }

  await loadMoreQuestions()
}

// keep-alive 页面再次复用时同步外部科目/分类查询参数
watch(
  () => [route.query.subject, route.query.category] as const,
  async ([subjectValue, categoryValue], [oldSubjectValue, oldCategoryValue]) => {
    if (subjectValue === oldSubjectValue && categoryValue === oldCategoryValue) return

    const subjectName = queryString(subjectValue)
    const categoryName = queryString(categoryValue)
    const subject = subjects.value.find(item => item.name === subjectName)
    if (subject && subject.id !== activeSubjectId.value) {
      await handleSubjectSelect(subject)
    }
    if (subject && categoryName !== filterCategory.value) {
      filterCategory.value = categoryName
      await loadQuestions(true)
    }
  }
)

// 复制工具函数
const copyToClipboard = async (text: string) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
    return true
  } catch (error) {
    console.error('复制失败:', error)
    throw error
  }
}

// ==================== 格式化工具函数 ====================

/**
 * 智能换行处理函数
 * 识别常见的编号模式并在其前面添加换行符，解决复制后内容连在一起的问题
 * 支持的模式：
 * - 罗马数字：I. II. III. IV. V. VI. VII. VIII. IX. X. 等
 * - 圆括号数字：(1) (2) (3) 等
 * - 带圈数字：① ② ③ ④ ⑤ 等
 * - 方括号数字：[1] [2] [3] 等
 * - 大写字母 + 括号：(A) (B) (C) (D) 等
 */
const normalizeLineBreaks = (text: string) => {
  if (!text || typeof text !== 'string') return text
  
  // 如果文本已经在这些模式前有换行符，跳过处理
  // 定义需要识别的模式 (在这些模式前添加换行符)
  const patterns = [
    // 罗马数字模式: I. II. III. IV. V. VI. VII. VIII. IX. X. XI. XII.
    // 注意：只匹配前面没有换行符的情况，且前面有空格或其他字符
    /(?<!\n)(?<=\S)\s*((?:I{1,3}|IV|VI{0,3}|IX|X{1,3}|XI{1,3}|XII)\.\s)/gi,
    // 圆括号数字模式: (1) (2) (3) ...
    /(?<!\n)(?<=\S)\s*(\([1-9]\d?\)\s*)/g,
    // 带圈数字模式: ① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ 等
    /(?<!\n)(?<=\S)\s*([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮])/g,
    // 方括号数字模式: [1] [2] [3] ...
    /(?<!\n)(?<=\S)\s*(\[[1-9]\d?\]\s*)/g,
    // 大写字母括号模式: (A) (B) (C) (D) 等
    /(?<!\n)(?<=\S)\s*(\([A-Z]\)\s*)/g
  ]
  
  let result = text
  
  // 逐一应用每个模式
  patterns.forEach(pattern => {
    result = result.replace(pattern, '\n$1')
  })
  
  // 清理可能产生的多余换行符（连续多个换行变成最多两个）
  result = result.replace(/\n{3,}/g, '\n\n')
  
  return result
}

/**
 * 解析选项JSON为对象
 */
const parseOptions = (mock: MockQuestion) => {
  if (mock?.questionType !== 'CHOICE' || !mock?.options) return null
  try {
    return parseQuestionOptions(mock.options)
  } catch (e) {
    return null
  }
}

/**
 * 获取题目元信息标签
 */
const getMockTags = (mock: MockQuestion) => {
  const questionType = mock.questionType === 'CHOICE' ? '选择题' : '主观题'
  const category = Array.isArray(mock.category) ? mock.category.join(', ') : (mock.category || '')
  const tags = [questionType, category].filter(Boolean)
  return tags.length > 0 ? `[${tags.join('] [')}]` : ''
}

// ==================== Markdown 格式化函数 ====================

/**
 * 获取标题和题号组合的标识字符串
 * 格式: "标题·第X题" 或 "标题" 或 "第X题"
 */
const getMockTitleLine = (mock: MockQuestion) => {
  const parts = []
  if (mock?.title) parts.push(mock.title)
  if (mock?.questionNumber) parts.push(`第${mock.questionNumber}题`)
  return parts.join(' · ')
}

const formatQuestionMarkdown = (mock: MockQuestion) => {
  if (!mock?.content) return ''
  const parts = []
  const tags = getMockTags(mock)
  const titleLine = getMockTitleLine(mock)
  
  // 标题行: 包含标题和题号
  if (titleLine) {
    parts.push(`## ${titleLine} ${tags}`)
  } else {
    parts.push(`## 模拟题 ${tags}`)
  }
  parts.push('')
  parts.push('### 题目')
  parts.push(normalizeLineBreaks(mock.content))
  return parts.join('\n')
}

const formatOptionsMarkdown = (mock: MockQuestion) => {
  const optionsObj = parseOptions(mock)
  if (!optionsObj) return ''
  const parts = ['### 选项']
  Object.keys(optionsObj).sort().forEach(key => {
    parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
  })
  return parts.join('\n')
}

const formatAnswerMarkdown = (mock: MockQuestion) => {
  if (!mock?.answer) return ''
  return ['### 答案', normalizeLineBreaks(mock.answer)].join('\n')
}

const formatFullMarkdown = (mock: MockQuestion) => {
  const parts = []
  const tags = getMockTags(mock)
  const titleLine = getMockTitleLine(mock)
  
  // 标题行: 包含标题和题号
  if (titleLine) {
    parts.push(`## ${titleLine} ${tags}`)
  } else {
    parts.push(`## 模拟题 ${tags}`)
  }
  parts.push('')
  
  if (mock?.content) {
    parts.push('### 题目')
    parts.push(normalizeLineBreaks(mock.content))
    parts.push('')
  }
  
  if (mock?.questionType === 'CHOICE') {
    const optionsObj = parseOptions(mock)
    if (optionsObj) {
      parts.push('### 选项')
      Object.keys(optionsObj).sort().forEach(key => {
        parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
      })
      parts.push('')
    }
  }
  
  if (mock?.answer) {
    parts.push('### 答案')
    parts.push(normalizeLineBreaks(mock.answer))
  }
  
  return parts.join('\n')
}

// 统一处理 Markdown 复制逻辑
const handleCopy = async (command: string, mock: MockQuestion) => {
  let text = ''
  let message = ''

  try {
    switch (command) {
      // Markdown 格式
      case 'md-question':
        text = formatQuestionMarkdown(mock)
        message = '题目已复制 (Markdown)'
        break
      case 'md-options':
        text = formatOptionsMarkdown(mock)
        message = '选项已复制 (Markdown)'
        break
      case 'md-answer':
        text = formatAnswerMarkdown(mock)
        message = '答案已复制 (Markdown)'
        break
      case 'md-all':
        text = formatFullMarkdown(mock)
        message = '完整内容已复制 (Markdown)'
        break
      default:
        return
    }

    if (!text) {
      showToast('没有可复制的内容', 'warning')
      return
    }

    await copyToClipboard(text)
    showToast(message, 'success')
  } catch (error) {
    showToast('复制失败，请重试', 'error')
  }
}

const handleEdit = (mock: MockQuestion) => {
  if (!mock?.id) return
  editingMockId.value = mock.id
  editingMockData.value = mock  // 传递完整数据，避免重复请求API
  editDialogVisible.value = true
}

const handleEditSuccess = async () => {
  await loadQuestions(true)
  // 重置编辑数据
  editingMockId.value = null
  editingMockData.value = null
}

const handleDelete = async (id: number) => {
  const confirmed = await showConfirm({
    message: '此操作将永久删除该模拟题，是否继续？',
    title: '警告',
    confirmText: '确定',
    cancelText: '取消',
    type: 'warning'
  })
  if (!confirmed) return

  try {
    const response = await deleteMockQuestion(id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      await loadQuestions(true)
    } else {
      showToast(response.message || '删除失败', 'error')
    }
  } catch (error) {
    // 错误消息已由axios拦截器统一处理
    console.error('删除失败:', error)
  }
}
</script>

<style scoped>
/**
 * 模拟题分类浏览页面样式
 * 使用 Tailwind CSS
 */

/* 模拟题卡片页面级样式覆盖 */
:deep(.mock-entry-card) {
  background-color: var(--brand-surface);
}

/* 从管理页面"查看"按钮跳转过来时的高亮效果 */
:deep(.mock-entry-card.highlight-card) {
  animation: highlightPulse 2s ease-out;
  border-color: var(--brand-accent);
  box-shadow: 0 0 20px color-mix(in srgb, var(--brand-accent) 30%, transparent);
}

/* 高亮脉冲动画 */
@keyframes highlightPulse {
  0%, 100% {
    box-shadow: 0 0 20px color-mix(in srgb, var(--brand-accent) 30%, transparent);
  }
  50% {
    box-shadow: 0 0 30px color-mix(in srgb, var(--brand-accent) 50%, transparent);
  }
}

</style>
