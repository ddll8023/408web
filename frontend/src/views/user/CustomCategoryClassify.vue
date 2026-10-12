<!-- 自定义分类阅读页面：按科目与自定义分类树浏览真题，页面结构与真题分类页保持一致。 -->
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
        kind="exam"
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
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div class="hidden min-w-0 items-center gap-3 md:flex">
            <h2 class="m-0 min-w-0 text-ink font-semibold text-xl">{{ currentTitle }}</h2>
            <Tag v-if="displayTotal > 0" type="info" size="sm">共 {{ displayTotal }} 题</Tag>
          </div>
          <div v-if="activeSubjectId" class="flex w-full flex-wrap items-center justify-end gap-2 lg:w-auto">
            <RadioGroup
              v-model="filterQuestionType"
              aria-label="题型筛选"
              :options="questionTypeOptions"
            />
          </div>
        </div>

        <div v-if="questionsLoading" class="flex justify-center py-8" role="status" aria-live="polite">
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

        <!-- 分类分组列表：标题显式区分自定义分类层级和题目数量 -->
        <div
          v-if="groupedQuestions.length > 0"
          class="mx-auto mt-4 w-full"
          :class="outlineItems.length > 0
            ? 'grid max-w-[1400px] grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_230px]'
            : 'flex max-w-[1100px] flex-col gap-4'"
        >
          <main class="min-w-0 flex flex-col gap-4">
            <section
              v-for="group in groupedQuestions"
              :id="getCategorySectionId('exam', group.categoryId, group.category)"
              :key="group.categoryId ?? group.category"
              class="category-question-section scroll-mt-14 md:scroll-mt-4"
              :class="group.depth > 0 ? 'ml-3 md:ml-6' : ''"
            >
              <CategorySectionHeader
                :category="group.category"
                :count="group.items.length"
                kind="exam"
                :depth="group.depth"
              />
              <div class="mt-2 flex flex-col gap-2.5">
                <ExamEntryCard
                  v-for="exam in group.items"
                  :key="exam.id"
                  :id="`exam-${exam.id}`"
                  :exam="exam"
                  :is-admin="false"
                  :show-answer="showAnswers[exam.id]"
                  density="compact"
                  @toggle-answer="toggleAnswer(exam.id)"
                />
              </div>
            </section>
          </main>

          <CategoryOutline
            v-if="outlineItems.length > 0"
            :items="outlineItems"
            :active-id="activeOutlineId"
            kind="exam"
            hide-below-xl
            @jump="scrollToCategory"
          />
        </div>
        <Empty
          v-if="!questionsLoadError && !subjectsLoadError && groupedQuestions.length === 0"
          :description="activeSubjectId ? '该科目暂无自定义分类真题' : '请选择左侧科目'"
        />

        <div v-if="hasMore" class="flex justify-center py-8 mt-4">
          <CustomButton
            :loading="questionsLoading"
            type="primary"
            @click="loadQuestions(false)"
          >
            {{ questionsLoading ? '加载中...' : '加载更多真题' }}
          </CustomButton>
        </div>
      </div>
    </div>

    <BackTop :right="32" :bottom="32" />
  </ReadingLayout>
</template>

<script setup lang="ts">
/**
 * 自定义分类浏览页面
 * 功能：按科目展示已启用的自定义分类树，并按自定义分类标签分组浏览真题
 * 设计哲学：只读浏览，编辑与管理入口保留在真题分类页与后台
 */
import type { CategoryOutlineItem, CategoryTreeNode, ExamQuestion, Subject } from '@/types'
import { computed, onMounted, ref } from 'vue'
import { getEnabledSubjects } from '@/api/subject'
import { getExamList } from '@/api/exam'
import { getCustomCategoryStats, getCustomCategoryTree } from '@/api/customCategory'
import toast from '@/utils/toast'
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
import ExamEntryCard from '@/components/business/ExamEntryCard.vue'
import { useCategoryOutline } from '@/composables/useCategoryOutline'
import { useInfiniteQuestionList } from '@/composables/useInfiniteQuestionList'
import {
  findCategoryNode,
  getCategorySectionId,
  groupExamQuestionsByCustomCategory,
  uniqueExamQuestions,
} from '@/utils/examCategoryGrouping'

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
// 题型筛选：ALL=全部，CHOICE=仅选择题，ESSAY=仅主观题（视为非CHOICE的题型）
const filterQuestionType = ref('ALL')
const questionTypeOptions = [
  { label: '全部题型', value: 'ALL' },
  { label: '选择题', value: 'CHOICE' },
  { label: '主观题', value: 'ESSAY' },
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
} = useInfiniteQuestionList<ExamQuestion>(
  (page, pageSize) => getExamList({
    page,
    size: pageSize,
    subjectId: activeSubjectId.value,
    sortField: 'year',
    sortOrder: 'asc',
    customCategory: filterCategory.value || undefined,
    // 科目级视图（未选分类）只看已挂自定义分类的题目，避免列出全量真题
    hasCustomCategory: filterCategory.value ? undefined : true,
  }),
  {
    pageSize: 50,
    mergePageItems: (currentItems, nextItems) =>
      uniqueExamQuestions([...currentItems, ...nextItems]),
    getHasMore: (items, pagination) => items.length < pagination.total,
    fallbackErrorMessage: '真题读取失败，请重试。',
    stopOnResponseError: true,
    onRequestError: error => console.error('加载真题失败:', error),
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
    return `${activeSubjectName.value} · ${filterCategory.value} · 自定义分类`
  }
  return activeSubjectName.value ? `${activeSubjectName.value} · 自定义分类` : '自定义分类浏览'
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

  if (filterQuestionType.value === 'CHOICE') {
    list = list.filter(exam => exam.questionType === 'CHOICE')
  } else if (filterQuestionType.value === 'ESSAY') {
    list = list.filter(exam => exam.questionType !== 'CHOICE')
  }

  // 父分类筛选由后端展开子孙范围，分组由左侧树顺序决定；每题只归入最后一个匹配标签。
  return groupExamQuestionsByCustomCategory(
    list,
    currentCategories.value,
    filterCategory.value,
  )
})

const outlineItems = computed<CategoryOutlineItem[]>(() => {
  if (!selectedCategoryNode.value?.children.length || groupedQuestions.value.length === 0) {
    return []
  }

  return groupedQuestions.value.map(group => ({
    anchorId: getCategorySectionId('exam', group.categoryId, group.category),
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
  void loadSubjects()
})

/** 加载启用科目，并静默预取各科目的自定义分类树供侧栏展示。 */
const loadSubjects = async () => {
  loadingSubjects.value = true
  try {
    const res = await getEnabledSubjects()
    if (res.code === 200) {
      subjectsLoadError.value = ''
      subjects.value = res.data || []
      await applyCustomCategoryCounts()
      subjects.value.forEach(subject => {
        if (subject.id !== activeSubjectId.value) {
          void loadCategoriesForSubject(subject.id)
        }
      })
    } else {
      subjectsLoadError.value = res.message || '科目读取失败，请重试。'
      toast.error(subjectsLoadError.value)
    }
  } catch (error) {
    subjectsLoadError.value = '科目读取失败，请重试。'
    toast.error(subjectsLoadError.value)
    console.error('加载科目失败:', error)
  } finally {
    loadingSubjects.value = false
  }
}

/** 用「已挂自定义分类的题目数」覆盖科目徽标数量，未打标的科目不显示徽标。 */
const applyCustomCategoryCounts = async () => {
  try {
    const res = await getCustomCategoryStats()
    if (res.code !== 200) return
    const counts = new Map(
      (res.data?.subjectStats || []).map(item => [item.subjectId, item.questionCount]),
    )
    subjects.value = subjects.value.map(subject => ({
      ...subject,
      questionCount: counts.get(subject.id) ?? 0,
    }))
  } catch (error) {
    console.error('加载自定义分类题量失败:', error)
  }
}

/** 按科目读取启用的自定义分类树，已缓存时不重复请求。 */
const loadCategoriesForSubject = async (subjectId: number) => {
  if (subjectCategories.value[subjectId]) return

  try {
    const res = await getCustomCategoryTree(subjectId, { enabledOnly: true })
    if (res.code === 200) {
      subjectCategories.value = {
        ...subjectCategories.value,
        [subjectId]: res.data || [],
      }
    }
  } catch (error) {
    console.error('加载科目自定义分类失败:', error)
  }
}

/** 切换浏览科目，重置分类与题型筛选后重新加载题目。 */
const handleSubjectSelect = async (subject: Subject) => {
  if (activeSubjectId.value === subject.id) return

  activeSubjectId.value = subject.id
  activeSubjectName.value = subject.name
  filterCategory.value = ''
  filterQuestionType.value = 'ALL'
  expandedSubjectId.value = subject.id
  showAnswers.value = {}

  await Promise.all([
    loadCategoriesForSubject(subject.id),
    loadQuestions(true),
  ])
}

/** 展开或收起科目分类树，展开前补拉分类数据。 */
const toggleSubjectExpand = async (subject: Subject | null) => {
  if (!subject) {
    expandedSubjectId.value = null
    return
  }

  if (expandedSubjectId.value === subject.id) {
    expandedSubjectId.value = null
    return
  }

  expandedSubjectId.value = subject.id
  await loadCategoriesForSubject(subject.id)
}

/** 选择自定义分类节点；再次点击同一节点表示取消筛选。 */
const handleCategorySelect = (subject: Subject, category: string) => {
  if (activeSubjectId.value !== subject.id) {
    activeSubjectId.value = subject.id
    activeSubjectName.value = subject.name
  }

  filterCategory.value = filterCategory.value === category ? '' : category
  showAnswers.value = {}

  void loadQuestions(true)
}

/** 抽屉内选择分类：先收起抽屉再加载该分类题目。 */
const handleNavSheetCategorySelect = (selection: { subject: Subject; category: string }) => {
  navSheetVisible.value = false
  handleCategorySelect(selection.subject, selection.category)
}

/** 抽屉内选择分组锚点：先收起抽屉再滚到对应分组。 */
const handleNavSheetOutlineJump = (anchorId: string) => {
  navSheetVisible.value = false
  scrollToCategory(anchorId)
}

/** 切换指定题目的答案显示状态。 */
const toggleAnswer = (examId: number | string) => {
  showAnswers.value[Number(examId)] = !showAnswers.value[Number(examId)]
}

/** 重置或追加加载当前科目的题目。 */
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
</script>
