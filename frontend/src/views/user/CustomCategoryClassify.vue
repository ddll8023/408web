<!-- 自定义分类阅读页面：按科目与自定义分类树浏览真题，页面结构与真题分类页保持一致，管理员可直接在卡片上编辑题目。 -->
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
          <CustomButton size="sm" type="text" :disabled="questionsLoading" @click="loadQuestions()">重试</CustomButton>
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
                  :is-admin="isAdmin"
                  :show-answer="showAnswers[exam.id]"
                  density="compact"
                  category-source="custom"
                  @copy="(cmd) => handleCopy(cmd, exam)"
                  @edit="handleEdit"
                  @generate-answer="handleGenerateAnswer"
                  @delete="(id: number) => handleDelete(id)"
                  @toggle-answer="toggleAnswer(exam.id)"
                  @show-adaptations="handleShowAdaptations"
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
            @jump="scrollToCategoryImmediately"
          />
        </div>
        <Empty
          v-if="!questionsLoadError && !subjectsLoadError && groupedQuestions.length === 0"
          :description="activeSubjectId ? '该科目暂无自定义分类真题' : '请选择左侧科目'"
        />
      </div>
    </div>

    <ExamEditDialog
      v-if="isAdmin"
      v-model:visible="editDialogVisible"
      :exam-id="editingExamId"
      :answer-candidate="answerCandidate"
      @success="handleEditSuccess"
    />

    <AiAnswerGenerationDialog
      v-if="isAdmin && answerGenerationTarget"
      v-model:visible="aiAnswerVisible"
      question-kind="exam"
      :question-id="answerGenerationTarget.id"
      :source="answerSourceFromQuestion(answerGenerationTarget)"
      @adopt="handleAdoptGeneratedAnswer"
    />

    <AdaptationRelatedDialog
      v-model:visible="adaptationDialogVisible"
      :exam="selectedAdaptationExam"
    />

    <BackTop :right="32" :bottom="32" />
  </ReadingLayout>
</template>

<script setup lang="ts">
/**
 * 自定义分类浏览页面
 * 功能：按科目展示已启用的自定义分类树，并按自定义分类标签分组浏览真题
 * 设计哲学：默认只读浏览；管理员可直接在卡片上编辑、删除题目并查看改编题
 */
import type { CategoryOutlineItem, CategoryTreeNode, ExamQuestion, Subject } from '@/types'
import type { AiAnswerCandidate } from '@/types/aiAnswer'
import { computed, onMounted, ref } from 'vue'
import { getEnabledSubjects } from '@/api/subject'
import { deleteExam, getExamList } from '@/api/exam'
import { getCustomCategoryStats, getCustomCategoryTree } from '@/api/customCategory'
import { useAuthStore } from '@/stores/auth'
import { useConfirm } from '@/composables/useConfirm'
import { answerSourceFromQuestion } from '@/utils/aiAnswer'
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
import ExamEditDialog from '@/components/business/ExamEditDialog.vue'
import AiAnswerGenerationDialog from '@/components/business/AiAnswerGenerationDialog.vue'
import AdaptationRelatedDialog from '@/components/business/AdaptationRelatedDialog.vue'
import { useCategoryOutline } from '@/composables/useCategoryOutline'
import { useInfiniteQuestionList } from '@/composables/useInfiniteQuestionList'
import {
  findCategoryNode,
  getCategorySectionId,
  groupExamQuestionsByCustomCategory,
  uniqueExamQuestions,
} from '@/utils/examCategoryGrouping'
import { buildExamTitleLine, copyFullMarkdown } from '@/utils/questionMarkdown'

const authStore = useAuthStore()
const { showConfirm } = useConfirm()

/** 是否管理员：决定题目卡片上的编辑、删除与生成答案入口 */
const isAdmin = computed(() => authStore.isAdmin())

// 题目编辑与答案生成弹窗状态
const editDialogVisible = ref(false)
const editingExamId = ref<number | null>(null)
const answerCandidate = ref<AiAnswerCandidate | null>(null)
const aiAnswerVisible = ref(false)
const answerGenerationTarget = ref<ExamQuestion | null>(null)
// 关联改编题弹窗状态
const adaptationDialogVisible = ref(false)
const selectedAdaptationExam = ref<ExamQuestion | null>(null)

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
  loadingAll: loadingAllQuestions,
  error: questionsLoadError,
  loadAll: loadAllQuestions,
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
    pageSize: 100,
    mergePageItems: (currentItems, nextItems) =>
      uniqueExamQuestions([...currentItems, ...nextItems]),
    getHasMore: (items, pagination) => items.length < pagination.total,
    fallbackErrorMessage: '真题读取失败，请重试。',
    stopOnResponseError: true,
    onRequestError: error => console.error('加载真题失败:', error),
  },
)
const questionsLoading = computed(() =>
  initialQuestionsLoading.value || loadingMoreQuestions.value || loadingAllQuestions.value,
)
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

const {
  activeId: activeOutlineId,
  scrollToCategory,
  scrollToCategoryImmediately,
} = useCategoryOutline({
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
    loadQuestions(),
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

  void loadQuestions()
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

/** Markdown 完整内容复制：标题级别由菜单命令决定。 */
const handleCopy = async (command: string, exam: ExamQuestion) => {
  await copyFullMarkdown(command, exam, buildExamTitleLine(exam))
}

/** 打开题目编辑弹窗；采用 AI 生成答案时携带候选答案。 */
const handleEdit = (exam: ExamQuestion, candidate: AiAnswerCandidate | null = null) => {
  if (!isAdmin.value || !exam?.id) return
  answerCandidate.value = candidate
  editingExamId.value = exam.id
  editDialogVisible.value = true
}

/**
 * 编辑成功后原位更新：列表重载会把滚动容器压回顶部，
 * 因此不再重新拉取；groupedQuestions 是 computed，标签改动会自动重新分组。
 */
const handleEditSuccess = (updatedExam: ExamQuestion | null) => {
  editDialogVisible.value = false
  editingExamId.value = null
  answerCandidate.value = null
  if (!updatedExam) return

  const index = questionList.value.findIndex(item => item.id === updatedExam.id)
  if (index === -1) return

  // 改到其他科目或清空自定义分类标签后，该题已不属于本页任何视图
  const tags = Array.isArray(updatedExam.customCategory) ? updatedExam.customCategory : []
  if (updatedExam.subjectId !== activeSubjectId.value || tags.length === 0) {
    questionList.value.splice(index, 1)
    return
  }

  questionList.value[index] = updatedExam
}

/** 管理员删除真题；服务端已确认删除，本地移除以避免重载重置滚动位置。 */
const handleDelete = async (id: number) => {
  if (!isAdmin.value) return
  const confirmed = await showConfirm({
    title: '警告',
    message: '此操作将永久删除该真题，是否继续？',
    confirmText: '确定',
    cancelText: '取消',
    type: 'danger',
  })
  if (!confirmed) return

  try {
    const response = await deleteExam(id)
    if (response.code === 200) {
      toast.success('删除成功')
      const index = questionList.value.findIndex(item => item.id === id)
      if (index !== -1) questionList.value.splice(index, 1)
    } else {
      toast.error(response.message || '删除失败')
    }
  } catch (error) {
    toast.error('删除失败')
    console.error('删除真题失败:', error)
  }
}

/** 打开 AI 生成答案弹窗，同一时间只允许一个生成任务。 */
const handleGenerateAnswer = (exam: ExamQuestion) => {
  if (!isAdmin.value || aiAnswerVisible.value) return
  answerGenerationTarget.value = exam
  aiAnswerVisible.value = true
}

/** 采纳生成的答案后转入编辑弹窗，由管理员确认后再保存。 */
const handleAdoptGeneratedAnswer = (candidate: AiAnswerCandidate) => {
  const target = answerGenerationTarget.value
  if (isAdmin.value && target?.id === candidate.questionId) handleEdit(target, candidate)
}

/** 查看该真题的关联改编题；无题号的历史数据不提供该入口。 */
const handleShowAdaptations = (exam: ExamQuestion) => {
  if (exam.questionNumber == null) return
  selectedAdaptationExam.value = exam
  adaptationDialogVisible.value = true
}

/** 重置并一次性加载当前范围的全部题目。 */
const loadQuestions = async () => {
  if (!activeSubjectId.value) {
    resetQuestions()
    return
  }

  showAnswers.value = {}
  await loadAllQuestions()
}
</script>
