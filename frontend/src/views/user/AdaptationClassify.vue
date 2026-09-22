<!-- 改编题分类阅读页面：复用真题/模拟题的科目导航、分类分组和题目锚点跳转。 -->
<template>
  <ReadingLayout @content-ready="setContentScroller">
    <template #wide-nav>
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
      <MobileQuestionNav
        v-model:visible="navSheetVisible"
        :title="currentTitle"
        :count="displayTotal"
        :outline-items="outlineItems"
        :active-outline-id="activeOutlineId"
        kind="adaptation"
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
            @select-category="handleNavSheetCategorySelect"
          />
        </template>
      </MobileQuestionNav>
    </template>

    <div class="min-h-full bg-surface">
          <div class="p-4">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div class="hidden min-w-0 flex-1 items-center gap-3 md:flex">
                <h2 class="m-0 text-xl font-semibold text-ink">{{ currentTitle }}</h2>
                <Tag v-if="displayTotal > 0" type="info">共 {{ displayTotal }} 题</Tag>
              </div>
              <div v-if="activeSubjectId" class="flex flex-wrap gap-2">
                <RadioGroup
                  v-model="filterQuestionType"
                  aria-label="题型筛选"
                  :options="questionTypeOptions"
                  @change="handleQuestionTypeChange"
                />
              </div>
            </div>

            <div v-if="questionsLoading" class="flex items-center justify-center py-12" role="status" aria-live="polite">
              <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-2xl text-accent" aria-hidden="true" />
            </div>

            <div v-if="subjectsLoadError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
              {{ subjectsLoadError }}
              <CustomButton size="sm" type="text" @click="loadSubjects">重新读取科目</CustomButton>
            </div>

            <div v-if="questionsLoadError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
              {{ questionsLoadError }}
              <CustomButton size="sm" type="text" :disabled="questionsLoading" @click="loadQuestions(true)">重试</CustomButton>
            </div>

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
                  :id="getCategorySectionId('adaptation', group.categoryId, group.category)"
                  :key="group.categoryId ?? group.category"
                  class="category-question-section scroll-mt-14 md:scroll-mt-4"
                  :class="group.depth > 0 ? 'ml-3 md:ml-6' : ''"
                >
                  <CategorySectionHeader
                    :category="group.category"
                    :count="group.items.length"
                    kind="adaptation"
                    :depth="group.depth"
                  />
                  <div class="mt-3 flex flex-col gap-4">
                    <AdaptationEntryCard
                      v-for="adaptation in group.items"
                      :id="`adaptation-${adaptation.id}`"
                      :key="adaptation.id"
                      :adaptation="adaptation"
                      :is-admin="isAdmin"
                      :delete-loading="deletingAdaptationId === adaptation.id"
                      :show-answer="showAnswers[adaptation.id]"
                      density="compact"
                      @copy="(command) => handleCopy(command, adaptation)"
                      @show-sources="handleShowSources"
                      @edit="handleEdit"
                      @delete="handleDelete"
                      @toggle-answer="toggleAnswer(adaptation.id)"
                    />
                  </div>
                </section>
              </main>

              <CategoryOutline
                v-if="outlineItems.length > 0"
                :items="outlineItems"
                :active-id="activeOutlineId"
                kind="adaptation"
                @jump="scrollToCategory"
              />
            </div>

            <Empty
              v-if="!questionsLoadError && !subjectsLoadError && groupedQuestions.length === 0"
              :description="activeSubjectId ? '该科目暂无改编题' : '请选择左侧科目'"
            />

            <div v-if="hasMore" class="mt-4 flex justify-center py-8">
              <CustomButton
                :loading="questionsLoading"
                type="primary"
                @click="loadQuestions(false)"
              >
                {{ questionsLoading ? '加载中...' : '加载更多改编题' }}
              </CustomButton>
            </div>
          </div>
        </div>

        <AdaptationEditDialog
          v-if="isAdmin"
          v-model:visible="editDialogVisible"
          :adaptation-id="editingAdaptationId"
          @success="handleEditSuccess"
        />

        <AdaptationSourceDialog
          v-model:visible="sourceDialogVisible"
          :adaptation="selectedSourceAdaptation"
        />

      <BackTop :right="32" :bottom="32" />
  </ReadingLayout>
</template>

<script setup lang="ts">
/**
 * 改编题分类阅读页面。
 * 以科目和分类组织改编题，支持通过 hash 在新标签页中定位到指定题目。
 */
import type { AdaptationQueryParams, AdaptationQuestion, CategoryOutlineItem, CategoryTreeNode, Subject } from '@/types'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { queryString } from '@/utils/storage'
import { parseQuestionOptions } from '@/utils/questionOptions'
import {
  deleteAdaptation,
  getAdaptationDetail,
  getAdaptationList,
} from '@/api/adaptation'
import { getCategoryStats, getEnabledCategoryTreeBySubjectWithStats } from '@/api/category'
import { getEnabledSubjects } from '@/api/subject'
import ReadingLayout from '@/app/layouts/ReadingLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import Empty from '@/components/basic/Empty.vue'
import RadioGroup from '@/components/basic/RadioGroup.vue'
import Tag from '@/components/basic/Tag.vue'
import BackTop from '@/components/basic/BackTop.vue'
import SubjectSidebar from '@/components/business/SubjectSidebar.vue'
import SubjectNavList from '@/components/business/SubjectNavList.vue'
import MobileQuestionNav from '@/components/business/MobileQuestionNav.vue'
import CategoryOutline from '@/components/business/CategoryOutline.vue'
import CategorySectionHeader from '@/components/business/CategorySectionHeader.vue'
import AdaptationEntryCard from '@/components/business/AdaptationEntryCard.vue'
import AdaptationEditDialog from '@/components/business/AdaptationEditDialog.vue'
import AdaptationSourceDialog from '@/components/business/AdaptationSourceDialog.vue'
import { useCategoryOutline } from '@/composables/useCategoryOutline'
import {
  findCategoryNode,
  getCategorySectionId,
  groupAdaptationQuestionsByCategory,
  uniqueAdaptationQuestions,
} from '@/utils/examCategoryGrouping'

const route = useRoute()
const authStore = useAuthStore()
const { showConfirm } = useConfirm()
const { showToast } = useToast()
const isAdmin = computed(() => authStore.isAdmin())

const isNavCollapsed = ref(false)
const navSheetVisible = ref(false)
const expandedCategoryIds = ref<number[]>([])
const loadingSubjects = ref(false)
const questionsLoading = ref(false)
const subjectsLoadError = ref('')
const questionsLoadError = ref('')
let questionsRequestVersion = 0

const subjects = ref<Subject[]>([])
const subjectCategories = ref<Record<number, CategoryTreeNode[]>>({})
const activeSubjectId = ref<number | null>(null)
const activeSubjectName = ref('')
const expandedSubjectId = ref<number | null>(null)

const currentPage = ref(1)
const hasMore = ref(false)
const pageSize = ref(50)

const filterCategory = ref('')
const filterQuestionType = ref<'ALL' | 'CHOICE' | 'ESSAY'>('ALL')
const questionTypeOptions = [
  { label: '全部题型', value: 'ALL' },
  { label: '选择题', value: 'CHOICE' },
  { label: '主观题', value: 'ESSAY' },
]

const questionList = ref<AdaptationQuestion[]>([])
const total = ref(0)
const showAnswers = ref<Record<number, boolean>>({})
const editDialogVisible = ref(false)
const editingAdaptationId = ref<number | null>(null)
const sourceDialogVisible = ref(false)
const selectedSourceAdaptation = ref<AdaptationQuestion | null>(null)
const deletingAdaptationId = ref<number | null>(null)
const contentScroller = ref<HTMLElement | null>(null)
const setContentScroller = (element: HTMLElement | null) => {
  contentScroller.value = element
}

const currentTitle = computed(() => {
  if (activeSubjectName.value && filterCategory.value) {
    return `${activeSubjectName.value} · ${filterCategory.value} · 改编题`
  }
  return activeSubjectName.value ? `${activeSubjectName.value} · 改编题` : '改编题分类浏览'
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
    list = list.filter(question => question.questionType === 'CHOICE')
  } else if (filterQuestionType.value === 'ESSAY') {
    list = list.filter(question => question.questionType !== 'CHOICE')
  }

  return groupAdaptationQuestionsByCategory(list, currentCategories.value, filterCategory.value)
})

const outlineItems = computed<CategoryOutlineItem[]>(() => {
  if (!selectedCategoryNode.value?.children.length || groupedQuestions.value.length === 0) {
    return []
  }

  return groupedQuestions.value.map(group => ({
    anchorId: getCategorySectionId('adaptation', group.categoryId, group.category),
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
  return groupedQuestions.value.reduce((sum, group) => sum + group.items.length, 0)
})

const mergeSubjectAdaptationCounts = (subjectList: Subject[], counts: ReadonlyMap<number, number>) => {
  return subjectList.map(subject => ({
    ...subject,
    questionCount: counts.get(subject.id) ?? 0,
  }))
}

onMounted(() => {
  void initPage()
})

const initPage = async () => {
  await loadSubjects()
}

const loadSubjects = async () => {
  loadingSubjects.value = true
  subjectsLoadError.value = ''
  try {
    const response = await getEnabledSubjects()
    if (response.code !== 200) {
      subjectsLoadError.value = response.message || '科目读取失败，请重试。'
      return
    }

    let subjectList = response.data || []
    try {
      const statsResponse = await getCategoryStats('adaptation')
      if (statsResponse.code === 200 && statsResponse.data) {
        const adaptationCounts = new Map(
          statsResponse.data.subjectStats.map(item => [item.subjectId, item.questionCount]),
        )
        subjectList = mergeSubjectAdaptationCounts(subjectList, adaptationCounts)
      } else {
        subjectList = subjectList.map(subject => ({ ...subject, questionCount: 0 }))
      }
    } catch (error) {
      subjectList = subjectList.map(subject => ({ ...subject, questionCount: 0 }))
      console.error('加载改编题科目统计失败:', error)
    }

    subjects.value = subjectList
    const subjectFromRoute = queryString(route.query.subject)
    const categoryFromRoute = queryString(route.query.category)
    const initialSubject = subjects.value.find(subject => subject.name === subjectFromRoute) || subjects.value[0]

    if (initialSubject) {
      await handleSubjectSelect(initialSubject)
      if (categoryFromRoute) {
        filterCategory.value = categoryFromRoute
        await loadQuestions(true)
      }

      subjects.value.forEach(subject => {
        if (subject.id !== activeSubjectId.value) void loadCategoriesForSubject(subject.id)
      })
    }

    await handleHashScroll()
  } catch (error) {
    subjectsLoadError.value = '科目读取失败，请重试。'
    console.error('加载改编题科目失败:', error)
  } finally {
    loadingSubjects.value = false
  }
}

const loadCategoriesForSubject = async (subjectId: number) => {
  if (subjectCategories.value[subjectId]) return

  try {
    const response = await getEnabledCategoryTreeBySubjectWithStats(subjectId, 'adaptation')
    if (response.code === 200) {
      subjectCategories.value = {
        ...subjectCategories.value,
        [subjectId]: response.data || [],
      }
    }
  } catch (error) {
    console.error('加载改编题分类失败:', error)
  }
}

const handleSubjectSelect = async (subject: Subject) => {
  if (activeSubjectId.value === subject.id) {
    expandedSubjectId.value = expandedSubjectId.value === subject.id ? null : subject.id
    return
  }

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

const toggleSubjectExpand = async (subject: Subject | null) => {
  if (!subject) {
    expandedSubjectId.value = null
    return
  }

  if (expandedSubjectId.value === subject.id) {
    expandedSubjectId.value = null
    return
  }

  await loadCategoriesForSubject(subject.id)
  expandedSubjectId.value = subject.id
}

const handleCategorySelect = (subject: Subject, category: string) => {
  if (activeSubjectId.value !== subject.id) {
    activeSubjectId.value = subject.id
    activeSubjectName.value = subject.name
  }

  filterCategory.value = filterCategory.value === category ? '' : category
  showAnswers.value = {}
  void loadQuestions(true)
}

const handleNavSheetCategorySelect = (selection: { subject: Subject; category: string }) => {
  navSheetVisible.value = false
  handleCategorySelect(selection.subject, selection.category)
}

const handleNavSheetOutlineJump = (anchorId: string) => {
  navSheetVisible.value = false
  scrollToCategory(anchorId)
}

const toggleAnswer = (id: number) => {
  showAnswers.value[id] = !showAnswers.value[id]
}

const handleShowSources = (question: AdaptationQuestion) => {
  selectedSourceAdaptation.value = question
  sourceDialogVisible.value = true
}

const handleEdit = (question: AdaptationQuestion) => {
  if (!isAdmin.value) return
  editingAdaptationId.value = question.id
  editDialogVisible.value = true
}

const handleEditSuccess = async () => {
  editDialogVisible.value = false
  editingAdaptationId.value = null
  await loadQuestions(true)
}

const handleDelete = async (id: number) => {
  if (!isAdmin.value) return
  const question = questionList.value.find(item => item.id === id)
  const label = `ID ${id}`
  const confirmed = await showConfirm({
    title: '警告',
    message: `确定要删除改编题“${label}”吗？其来源引用会一并删除。`,
    confirmText: '确定',
    cancelText: '取消',
    type: 'warning',
  })
  if (!confirmed) return

  deletingAdaptationId.value = id
  try {
    const response = await deleteAdaptation(id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      await loadQuestions(true)
    } else {
      showToast(response.message || '删除失败', 'error')
    }
  } catch (error) {
    showToast('删除失败', 'error')
    console.error('删除改编题失败:', error)
  } finally {
    deletingAdaptationId.value = null
  }
}

const handleQuestionTypeChange = () => {
  if (activeSubjectId.value !== null) void loadQuestions(true)
}

const normalizeLineBreaks = (text: string) => {
  if (!text) return text
  return text
    .replace(/(?<!\\n)(?<=\\S)\\s*(\\([1-9]\\d?\\)\\s*)/g, '\\n$1')
    .replace(/\\n{3,}/g, '\\n\\n')
}

const formatQuestionMarkdown = (question: AdaptationQuestion) => {
  return [
    `## 改编题 #${question.id}`,
    '',
    '### 题目',
    normalizeLineBreaks(question.content),
  ].join('\\n')
}

const formatOptionsMarkdown = (question: AdaptationQuestion) => {
  if (question.questionType !== 'CHOICE') return ''
  const options = parseQuestionOptions(question.options)
  if (!options) return ''
  return ['### 选项', ...Object.entries(options).map(([key, value]) => `${key}. ${normalizeLineBreaks(value)}`)].join('\\n')
}

const formatAnswerMarkdown = (question: AdaptationQuestion) => {
  if (!question.answer) return ''
  return ['### 答案', normalizeLineBreaks(question.answer)].join('\\n')
}

const formatFullMarkdown = (question: AdaptationQuestion) => {
  return [
    formatQuestionMarkdown(question),
    formatOptionsMarkdown(question),
    formatAnswerMarkdown(question),
  ].filter(Boolean).join('\\n\\n')
}

const copyToClipboard = async (text: string) => {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-999999px'
  document.body.appendChild(textArea)
  try {
    textArea.focus()
    textArea.select()
    if (!document.execCommand('copy')) throw new Error('COPY_FAILED')
  } finally {
    document.body.removeChild(textArea)
  }
}

const handleCopy = async (command: string, question: AdaptationQuestion) => {
  const content = command === 'md-question'
    ? formatQuestionMarkdown(question)
    : command === 'md-options'
      ? formatOptionsMarkdown(question)
      : command === 'md-answer'
        ? formatAnswerMarkdown(question)
        : command === 'md-all'
          ? formatFullMarkdown(question)
          : ''

  if (!content) {
    showToast('没有可复制的内容', 'warning')
    return
  }

  try {
    await copyToClipboard(content)
    showToast('内容已复制', 'success')
  } catch (error) {
    showToast('复制失败，请重试', 'error')
    console.error('复制改编题失败:', error)
  }
}

const loadQuestions = async (isReset = false) => {
  const requestVersion = ++questionsRequestVersion
  if (!activeSubjectId.value) {
    questionList.value = []
    total.value = 0
    hasMore.value = false
    questionsLoadError.value = ''
    questionsLoading.value = false
    return
  }

  if (isReset) {
    currentPage.value = 1
    questionList.value = []
    hasMore.value = true
    questionsLoadError.value = ''
    showAnswers.value = {}
  }

  questionsLoading.value = true
  try {
    const params: AdaptationQueryParams = {
      page: currentPage.value,
      pageSize: pageSize.value,
      subjectId: activeSubjectId.value,
      category: filterCategory.value || undefined,
      questionType: filterQuestionType.value === 'ALL' ? undefined : filterQuestionType.value,
      sortField: 'update_time',
      sortOrder: 'desc',
    }
    const response = await getAdaptationList(params)
    if (requestVersion !== questionsRequestVersion) return

    if (response.code === 200) {
      const pageData = response.data?.lists || []
      const serverTotal = response.data?.pagination?.total || 0
      questionList.value = isReset
        ? uniqueAdaptationQuestions(pageData)
        : uniqueAdaptationQuestions([...questionList.value, ...pageData])
      total.value = serverTotal
      hasMore.value = questionList.value.length < serverTotal
      questionsLoadError.value = ''
      if (pageData.length > 0) currentPage.value += 1
    } else {
      hasMore.value = false
      questionsLoadError.value = response.message || '改编题读取失败，请重试。'
    }
  } catch (error) {
    if (requestVersion !== questionsRequestVersion) return
    questionsLoadError.value = '改编题读取失败，请重试。'
    if (isReset) {
      questionList.value = []
      total.value = 0
    }
    console.error('加载改编题失败:', error)
  } finally {
    if (requestVersion === questionsRequestVersion) questionsLoading.value = false
  }
}

const handleHashScroll = async () => {
  const hash = window.location.hash
  if (!hash.startsWith('#adaptation-')) return

  const adaptationId = Number(hash.slice('#adaptation-'.length))
  if (!Number.isInteger(adaptationId) || adaptationId <= 0) return

  try {
    const response = await getAdaptationDetail(adaptationId)
    if (response.code !== 200 || !response.data) return

    const target = response.data
    if (target.subjectId != null && target.subjectId !== activeSubjectId.value) {
      const targetSubject = subjects.value.find(subject => subject.id === target.subjectId)
      if (targetSubject) await handleSubjectSelect(targetSubject)
    }

    if (target.category?.length && filterCategory.value !== target.category[0]) {
      filterCategory.value = target.category[0]
      await loadQuestions(true)
    }

    if (!questionList.value.some(question => question.id === target.id)) {
      questionList.value = uniqueAdaptationQuestions([target, ...questionList.value])
    }

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))
    const element = document.getElementById(`adaptation-${adaptationId}`)
    if (!element) return

    element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    element.classList.add('highlight-card')
    window.setTimeout(() => element.classList.remove('highlight-card'), 2000)
  } catch (error) {
    console.error('处理改编题 hash 跳转失败:', error)
  }
}

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
  },
)
</script>
