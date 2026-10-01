<!-- 模拟题出题工作台：以章节树、题目卡片和出题篮组织临时出题。 -->
<template>
  <main class="compose-page mx-auto min-h-[var(--app-page-height)] w-full min-w-0 px-2 py-4 sm:px-4 sm:py-6">
    <CustomCard shadow>
      <template #header>
        <header class="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
          <h2 class="m-0 text-xl font-semibold text-ink">出题工作台</h2>
          <span v-if="filters.subjectId" class="text-sm text-gray-500">{{ currentSubjectName }}</span>
        </header>
      </template>

      <!-- 题目来源类型切换：切换后重新加载对应的章节树与题目列表，出题篮保持不变。 -->
      <section class="compose-kind-switch" aria-label="题目来源类型">
        <RadioGroup
          :model-value="questionKind"
          :options="questionKindOptions"
          aria-label="题目来源类型"
          @change="handleQuestionKindChange"
        />
        <span class="compose-kind-switch__hint">{{ questionKindHint }}</span>
      </section>

      <!-- 筛选区 -->
      <section
        class="compose-filters mb-6 rounded-xl border border-[#eadfd4] bg-white/70 p-5 shadow-sm backdrop-blur-sm"
        :class="{ 'compose-filters--adaptation': isAdaptationKind }"
        aria-label="出题筛选条件"
      >
        <div class="compose-filters__field compose-filters__field--subject">
          <label for="compose-subject" class="compose-filters__label">科目</label>
          <Select
            id="compose-subject"
            v-model="filters.subjectId"
            :options="subjectOptions.map(subject => ({ label: subject.name, value: subject.id }))"
            placeholder="先选择科目"
            aria-label="科目"
            clearable
            @change="handleSubjectChange"
          />
        </div>
        <div v-if="!isAdaptationKind" class="compose-filters__field">
          <label for="compose-source" class="compose-filters__label">来源机构</label>
          <Select
            id="compose-source"
            v-model="filters.source"
            :options="sourceOptions"
            placeholder="全部来源"
            aria-label="来源机构"
            clearable
            filterable
          />
        </div>
        <template v-else>
          <div class="compose-filters__field">
            <span class="compose-filters__label">来源年份</span>
            <WheelPicker
              v-model="filters.sourceYear"
              :options="yearOptions"
              placeholder="全部年份"
              aria-label="来源年份"
              clearable
            />
          </div>
          <div class="compose-filters__field">
            <span class="compose-filters__label">来源题号</span>
            <InputNumber
              :model-value="filters.sourceQuestionNumber ?? 0"
              :min="1"
              :max="MAX_SOURCE_QUESTION_NUMBER"
              placeholder="题号"
              aria-label="来源题号"
              @update:model-value="handleSourceNumberChange"
            />
          </div>
          <div class="compose-filters__field">
            <label for="compose-source-state" class="compose-filters__label">来源状态</label>
            <Select
              id="compose-source-state"
              v-model="filters.sourceState"
              :options="sourceStateOptions"
              aria-label="来源状态"
            />
          </div>
        </template>
        <div class="compose-filters__field compose-filters__field--keyword">
          <label for="compose-keyword" class="compose-filters__label">关键词</label>
          <CustomInput
            id="compose-keyword"
            v-model="filters.keyword"
            placeholder="搜索题目标题或内容"
            aria-label="关键词"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <font-awesome-icon :icon="['fas', 'search']" class="text-gray-400" />
            </template>
          </CustomInput>
        </div>
        <div class="compose-filters__field">
          <label for="compose-question-type" class="compose-filters__label">题目类型</label>
          <Select
            id="compose-question-type"
            v-model="filters.questionType"
            :options="questionTypeOptions"
            aria-label="题目类型"
          />
        </div>
        <div class="compose-filters__field">
          <label for="compose-status" class="compose-filters__label">出题状态</label>
          <Select
            id="compose-status"
            v-model="filters.examStatus"
            :options="examStatusOptions"
            aria-label="出题状态"
          />
        </div>
        <div class="compose-filters__actions">
          <CustomButton type="primary" size="sm" :disabled="!filters.subjectId" @click="handleSearch">
            <font-awesome-icon :icon="['fas', 'magnifying-glass']" />
            查询
          </CustomButton>
          <CustomButton type="default" size="sm" @click="handleReset">
            <font-awesome-icon :icon="['fas', 'sync']" />
            重置
          </CustomButton>
        </div>
      </section>

      <div v-if="listError && composeQuestions.length === 0" class="compose-error" role="alert">
        <span>{{ listError }}</span>
        <CustomButton size="sm" type="text" :disabled="listLoading" @click="() => loadQuestionList()">重试</CustomButton>
      </div>

      <QuestionComposeLayout
        :chapter-title="activeChapterLabel"
        :selected-count="selectedQuestions.length"
      >
        <template #chapter>
          <aside class="chapter-panel" aria-label="章节目录">
          <header class="chapter-panel__header">
            <div>
              <p class="chapter-panel__eyebrow">章节导航</p>
              <h2 class="chapter-panel__title">章节目录</h2>
            </div>
            <span v-if="chapterTree.length > 0" class="chapter-panel__count">
              {{ chapterTree.length }} 章
            </span>
          </header>

          <div v-if="!filters.subjectId" class="chapter-panel__empty">
            <span class="chapter-panel__empty-mark">01</span>
            <p>选择科目后加载章节</p>
          </div>
          <template v-else>
            <button
              type="button"
              class="chapter-panel__all"
              :class="{ 'chapter-panel__all--active': activeChapterId === null && !filters.noCategory }"
              @click="handleAllChapters"
            >
              <span class="chapter-panel__all-mark">∷</span>
              <span class="min-w-0 flex-1 text-left">全部章节</span>
              <span>{{ total }}</span>
            </button>
            <div v-if="chapterTree.length > 0" class="chapter-panel__tree custom-scrollbar">
              <QuestionChapterTree
                :nodes="chapterTree"
                :active-id="activeChapterId"
                :selected-counts="selectedCountsByCategory"
                @select="handleChapterSelect"
              />
            </div>
            <div v-else class="chapter-panel__empty chapter-panel__empty--small">
              <p>暂无可用章节</p>
            </div>
          </template>
          </aside>
        </template>

        <template #content>
          <!-- 章节题目内容 -->
          <section ref="questionScroller" class="question-content" aria-label="章节题目">
          <header class="question-content__header">
            <div>
              <p class="question-content__eyebrow">当前题目</p>
              <h2 class="question-content__title">
                {{ activeChapterLabel }}
              </h2>
            </div>
            <span v-if="filters.subjectId" class="question-content__total">
              已加载 {{ composeQuestions.length }} / {{ total }} 题
            </span>
          </header>

          <div v-if="!filters.subjectId" class="question-content__empty">
            <div class="question-content__empty-icon" aria-hidden="true">⌁</div>
            <h3>从章节开始出题</h3>
            <p>选择科目后，题目会按照章节和知识点重新排列。</p>
          </div>
          <div v-else-if="listLoading" class="question-content__loading" role="status" aria-live="polite">
            <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin" aria-hidden="true" />
            <span>正在整理章节题目...</span>
          </div>
          <div v-else-if="chapterSections.length === 0" class="question-content__empty">
            <div class="question-content__empty-icon" aria-hidden="true">∅</div>
            <h3>当前范围暂无题目</h3>
            <p>可以切换章节、来源或关键词后重新查询。</p>
          </div>
          <div v-else class="question-content__sections">
            <QuestionChapterSection
              v-for="section in chapterSections"
              :key="section.id"
              :section="section"
              :selected-keys="selectedKeys"
              @select-question="handleQuestionSelection"
              @preview="handlePreview"
              @edit="handleEdit"
              @word-copied="handleQuestionWordCopied"
              @toggle-exam-status="handleExamStatusToggle"
            />
          </div>

          <div
            v-if="filters.subjectId && chapterSections.length > 0"
            ref="loadMoreSentinel"
            class="question-content__load-more"
            aria-live="polite"
          >
            <span v-if="loadingMore" class="question-content__load-more-status">
              <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin" aria-hidden="true" />
              正在加载更多题目...
            </span>
            <button v-else-if="listError" type="button" class="question-content__retry" @click="retryQuestionLoad">
              加载失败，点击重试
            </button>
            <span v-else-if="hasMore" class="question-content__load-more-status">继续下滑加载更多</span>
            <span v-else class="question-content__load-more-status">已加载全部 {{ total }} 题</span>
          </div>
          </section>
        </template>

        <template #basket>
          <QuestionBasket
            :questions="selectedQuestions"
            :disabled="batchMarking"
            :max-count="MAX_BATCH_COPY_COUNT"
            @clear="clearSelection"
            @move="moveSelectedQuestion"
            @remove="removeSelectedQuestion"
            @word-copied="handleBatchWordCopied"
          />
        </template>
      </QuestionComposeLayout>
    </CustomCard>

    <BackTop :right="32" :bottom="32">
      <div class="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-white shadow-lg transition-transform hover:scale-110">
        <font-awesome-icon :icon="['fas', 'arrow-up']" />
      </div>
    </BackTop>

    <QuestionPreviewDrawer
      v-model:visible="previewVisible"
      :question="previewQuestion"
    />

    <MockEditDialog
      v-if="!isAdaptationKind"
      v-model:visible="editDialogVisible"
      :mock-id="editingMockId"
      :mock-data="editingMockData"
      @success="handleEditSuccess"
    />

    <AdaptationEditDialog
      v-else
      v-model:visible="editDialogVisible"
      :adaptation-id="editingAdaptationId"
      @success="handleEditSuccess"
    />
  </main>
</template>

<script setup lang="ts">
/**
 * 管理端出题工作台。
 * 支持在模拟题与改编题之间切换出题：共用科目章节树、筛选区和出题篮，题目数据仍由各自模块负责。
 */
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import type {
  AdaptationQuestion,
  AdaptationSourceState,
  ApiResponse,
  CategoryTreeNode,
  MockQuestion,
  Paginated,
  QuestionKind,
  QuestionType,
} from '@/types'
import type { RichCopyResult } from '@/utils/questionCopy'
import { queryString } from '@/utils/storage'
import { getEnabledCategoryTreeBySubjectWithStats } from '@/api/category'
import {
  getAdaptationCategoriesBySubject,
  getAdaptationList,
  setAdaptationExamMark,
  setAdaptationExamMarks,
} from '@/api/adaptation'
import {
  getAllMockSources,
  getMockCategoriesBySubject,
  getMockQuestions,
  setMockExamMark,
  setMockExamMarks,
} from '@/api/mock'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import InputNumber from '@/components/basic/InputNumber.vue'
import RadioGroup from '@/components/basic/RadioGroup.vue'
import Select from '@/components/basic/Select.vue'
import WheelPicker from '@/components/basic/WheelPicker.vue'
import BackTop from '@/components/basic/BackTop.vue'
import AdaptationEditDialog from '@/components/business/AdaptationEditDialog.vue'
import MockEditDialog from '@/components/business/MockEditDialog.vue'
import QuestionBasket from '@/components/business/QuestionBasket.vue'
import QuestionComposeLayout from '@/components/business/QuestionComposeLayout.vue'
import QuestionChapterSection from '@/components/business/QuestionChapterSection.vue'
import QuestionChapterTree from '@/components/business/QuestionChapterTree.vue'
import QuestionPreviewDrawer from '@/components/business/QuestionPreviewDrawer.vue'
import { useAdminTable } from '@/composables/useAdminTable'
import { useConfirm } from '@/composables/useConfirm'
import { useInfiniteQuestionList } from '@/composables/useInfiniteQuestionList'
import { getQuestionSelectionKey, useQuestionSelection } from '@/composables/useQuestionSelection'
import { useToast } from '@/composables/useToast'

/** 出题工作台题目行：按来源类型区分，保证展示字段可准确收窄。 */
type MockQuestionRow = MockQuestion & { questionKind: 'mock'; examStatusLoading?: boolean }
type AdaptationQuestionRow = AdaptationQuestion & {
  questionKind: 'adaptation'
  examStatusLoading?: boolean
}
type QuestionRow = MockQuestionRow | AdaptationQuestionRow

/** 为题目附加来源类型标记，统一为可混排的题目行。 */
const withQuestionKind = (
  question: MockQuestion | AdaptationQuestion,
  kind: QuestionKind,
): QuestionRow => {
  if (kind === 'adaptation') {
    return { ...(question as AdaptationQuestion), questionKind: 'adaptation' }
  }
  return { ...(question as MockQuestion), questionKind: 'mock' }
}

interface CategoryPathInfo {
  node: CategoryTreeNode
  path: CategoryTreeNode[]
  order: number[]
}

interface ChapterSection {
  id: number
  name: string
  path: string[]
  questions: QuestionRow[]
  order: number[]
}

type ExamStatusFilter = 'all' | 'unmarked' | 'marked'
type QuestionTypeFilter = 'all' | QuestionType

interface LoadQuestionListOptions {
  preserveScroll?: boolean
}

const MAX_BATCH_COPY_COUNT = 100
const MAX_SOURCE_QUESTION_NUMBER = 47
const FIRST_EXAM_YEAR = 2009
const UNFILED_ROOT_ID = -1
const UNFILED_ROOT_NAME = '未归档分类'
const UNFILED_CHILD_ID_BASE = -100000

const route = useRoute()
const { showToast } = useToast()
const { showConfirm } = useConfirm()
const {
  subjectOptions,
  subjectMap,
  loadSubjectOptions,
  getUrlKeyword,
} = useAdminTable()
const {
  selectedKeys,
  selectedQuestions,
  selectedCount,
  selectQuestion,
  syncQuestions,
  updateQuestion,
  removeQuestion,
  moveQuestion,
  clearSelection: clearSelectedQuestions,
} = useQuestionSelection<QuestionRow>()

const filters = reactive({
  source: '',
  subjectId: null as number | null,
  keyword: '',
  category: '',
  noCategory: false,
  examStatus: 'all' as ExamStatusFilter,
  questionType: 'all' as QuestionTypeFilter,
  sourceYear: null as number | null,
  sourceQuestionNumber: null as number | null,
  sourceState: 'all' as AdaptationSourceState,
})
const questionKind = ref<QuestionKind>('mock')
const questionKindOptions: { label: string; value: QuestionKind }[] = [
  { label: '模拟题', value: 'mock' },
  { label: '改编题', value: 'adaptation' },
]
const isAdaptationKind = computed(() => questionKind.value === 'adaptation')
const questionKindHint = computed(() =>
  isAdaptationKind.value ? '按改编来源与出处筛选' : '按来源机构筛选'
)
const examStatusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '未出题', value: 'unmarked' },
  { label: '已出题', value: 'marked' },
]
const questionTypeOptions = [
  { label: '全部类型', value: 'all' },
  { label: '选择题', value: 'CHOICE' },
  { label: '主观题', value: 'ESSAY' },
]
const sourceStateOptions = [
  { label: '全部来源', value: 'all' },
  { label: '已标注来源', value: 'with_source' },
  { label: '未标注来源', value: 'without_source' },
]
const yearOptions = computed(() => {
  const lastYear = Math.max(new Date().getFullYear(), FIRST_EXAM_YEAR)
  const options: { label: string; value: number }[] = []
  for (let year = lastYear; year >= FIRST_EXAM_YEAR; year -= 1) {
    options.push({ label: `${year} 年`, value: year })
  }
  return options
})
const sourceOptions = ref<string[]>([])
const chapterTree = ref<CategoryTreeNode[]>([])
const activeChapterId = ref<number | null>(null)
const previousSubjectId = ref<number | null>(null)
const batchMarking = ref(false)
const editDialogVisible = ref(false)
const previewVisible = ref(false)
const previewQuestion = ref<QuestionRow | null>(null)
const editingMockId = ref<number | null>(null)
const editingMockData = ref<MockQuestion | null>(null)
const editingAdaptationId = ref<number | null>(null)
const questionScroller = ref<HTMLElement | null>(null)
const loadMoreSentinel = ref<HTMLElement | null>(null)
let intersectionObserver: IntersectionObserver | null = null

/** 给模拟题响应附加来源类型，统一列表元素类型。 */
const tagMockResponse = (
  response: ApiResponse<Paginated<MockQuestion>>,
): ApiResponse<Paginated<QuestionRow>> => ({
  ...response,
  data: {
    ...response.data,
    lists: response.data.lists.map(question => withQuestionKind(question, 'mock')),
  },
})

/** 给改编题响应附加来源类型，统一列表元素类型。 */
const tagAdaptationResponse = (
  response: ApiResponse<Paginated<AdaptationQuestion>>,
): ApiResponse<Paginated<QuestionRow>> => ({
  ...response,
  data: {
    ...response.data,
    lists: response.data.lists.map(question => withQuestionKind(question, 'adaptation')),
  },
})

/** 按当前题目来源类型加载一页题目，两个模块的筛选条件在各自分支内拼装。 */
const loadQuestionPage = async (
  page: number,
  pageSize: number,
): Promise<ApiResponse<Paginated<QuestionRow>>> => {
  const isExamMarked = filters.examStatus === 'all'
    ? undefined
    : filters.examStatus === 'marked'

  if (isAdaptationKind.value) {
    const response = await getAdaptationList({
      page,
      pageSize,
      subjectId: filters.subjectId || undefined,
      category: filters.category || undefined,
      keyword: filters.keyword || undefined,
      noCategory: filters.noCategory || undefined,
      questionType: filters.questionType === 'all' ? undefined : filters.questionType,
      isExamMarked,
      sourceYear: filters.sourceYear ?? undefined,
      sourceQuestionNumber: filters.sourceQuestionNumber ?? undefined,
      sourceState: filters.sourceState,
      sortField: 'update_time',
      sortOrder: 'desc',
    })
    return tagAdaptationResponse(response)
  }

  const response = await getMockQuestions({
    page,
    pageSize,
    source: filters.source || undefined,
    subjectId: filters.subjectId || undefined,
    category: filters.category || undefined,
    keyword: filters.keyword || undefined,
    noCategory: filters.noCategory || undefined,
    questionType: filters.questionType === 'all' ? undefined : filters.questionType,
    isExamMarked,
    sortField: 'update_time',
    sortOrder: 'desc',
  })
  return tagMockResponse(response)
}

const {
  items: composeQuestions,
  total,
  loading: listLoading,
  loadingMore,
  hasMore,
  error: listError,
  reload: reloadQuestions,
  loadMore: loadMoreQuestions,
  retry: retryQuestionLoad,
  reset: resetQuestions,
} = useInfiniteQuestionList<QuestionRow>(loadQuestionPage, {
  pageSize: 50,
  getItemKey: getQuestionSelectionKey,
})

const currentSubjectName = computed(() => {
  if (!filters.subjectId) return ''
  return subjectMap.value[filters.subjectId] || '当前科目'
})

const activeChapterLabel = computed(() => {
  if (!filters.subjectId) return '等待选择科目'
  if (filters.noCategory) return UNFILED_ROOT_NAME
  if (!filters.category) return '全部章节'
  return filters.category
})

const categoryIndex = computed(() => {
  const byName = new Map<string, CategoryPathInfo>()
  const byId = new Map<number, CategoryPathInfo>()

  const visit = (nodes: CategoryTreeNode[], parentPath: CategoryTreeNode[], parentOrder: number[]) => {
    nodes.forEach((node, index) => {
      const info: CategoryPathInfo = { node, path: [...parentPath, node], order: [...parentOrder, index] }
      byName.set(node.name, info)
      byId.set(node.id, info)
      visit(node.children, info.path, info.order)
    })
  }

  visit(chapterTree.value, [], [])
  return { byName, byId }
})

const getQuestionCategoryInfos = (question: MockQuestion | AdaptationQuestion) => {
  const names = Array.isArray(question.category)
    ? question.category.filter(category => category.trim())
    : []
  const infos = names
    .map(name => categoryIndex.value.byName.get(name))
    .filter((info): info is CategoryPathInfo => Boolean(info))

  if (infos.length === 0) {
    const unfiledInfo = categoryIndex.value.byName.get(UNFILED_ROOT_NAME)
    return unfiledInfo ? [unfiledInfo] : []
  }

  const deepestLevel = Math.max(...infos.map(info => info.path.length))
  return infos.filter(info => info.path.length === deepestLevel)
}

const selectedCountsByCategory = computed(() => {
  const counts: Record<number, number> = {}

  selectedQuestions.value.forEach(question => {
    const nodeIds = new Set<number>()
    getQuestionCategoryInfos(question).forEach(info => {
      info.path.forEach(node => nodeIds.add(node.id))
    })
    nodeIds.forEach(nodeId => {
      counts[nodeId] = (counts[nodeId] || 0) + 1
    })
  })

  return counts
})

const buildActiveChapterSection = (info: CategoryPathInfo): ChapterSection[] => {
  const questions = composeQuestions.value.filter(question =>
    getQuestionCategoryInfos(question).some(categoryInfo =>
      categoryInfo.path.some(node => node.id === info.node.id),
    ),
  )
  if (questions.length === 0) return []

  return [{
    id: info.node.id,
    name: info.node.name,
    path: info.path.map(node => node.name),
    order: info.order,
    questions,
  }]
}

const chapterSections = computed<ChapterSection[]>(() => {
  const activeInfo = activeChapterId.value === null
    ? null
    : categoryIndex.value.byId.get(activeChapterId.value)
  if (activeInfo) return buildActiveChapterSection(activeInfo)

  const sectionMap = new Map<number, ChapterSection>()
  const sectionQuestionKeys = new Map<number, Set<string>>()

  composeQuestions.value.forEach(question => {
    getQuestionCategoryInfos(question).forEach(info => {
      const nodeId = info.node.id
      if (!sectionMap.has(nodeId)) {
        sectionMap.set(nodeId, {
          id: nodeId,
          name: info.node.name,
          path: info.path.map(node => node.name),
          order: info.order,
          questions: [],
        })
        sectionQuestionKeys.set(nodeId, new Set())
      }

      const keys = sectionQuestionKeys.get(nodeId)
      const questionKey = getQuestionSelectionKey(question)
      if (!keys || keys.has(questionKey)) return
      keys.add(questionKey)
      sectionMap.get(nodeId)?.questions.push(question)
    })
  })

  return [...sectionMap.values()].sort((left, right) => {
    const length = Math.max(left.order.length, right.order.length)
    for (let index = 0; index < length; index += 1) {
      const leftValue = left.order[index] ?? -1
      const rightValue = right.order[index] ?? -1
      if (leftValue !== rightValue) return leftValue - rightValue
    }
    return left.name.localeCompare(right.name, 'zh-CN')
  })
})

watch(composeQuestions, questions => {
  syncQuestions(questions)
})

const loadSourceOptions = async () => {
  try {
    const response = await getAllMockSources()
    if (response.code === 200) {
      sourceOptions.value = response.data?.sources?.map(item => item.source) || []
    }
  } catch (error) {
    console.error('加载来源机构列表失败:', error)
  }
}

const buildUnfiledTree = (subjectId: number, formalTree: CategoryTreeNode[], categoryNames: string[]) => {
  const knownNames = new Set<string>()
  const collectNames = (nodes: CategoryTreeNode[]) => {
    nodes.forEach(node => {
      knownNames.add(node.name)
      collectNames(node.children)
    })
  }
  collectNames(formalTree)

  const unfiledNames = categoryNames.filter(name => name && !knownNames.has(name))
  const children = unfiledNames.map((name, index) => ({
    id: UNFILED_CHILD_ID_BASE - index,
    subjectId,
    parentId: UNFILED_ROOT_ID,
    parentName: UNFILED_ROOT_NAME,
    name,
    code: `__unfiled_${index}`,
    description: '历史题目中存在但当前目录未收录的分类',
    orderNum: index,
    enabled: true,
    questionCount: null,
    subtreeQuestionCount: null,
    children: [],
  }))

  return {
    id: UNFILED_ROOT_ID,
    subjectId,
    parentId: null,
    parentName: null,
    name: UNFILED_ROOT_NAME,
    code: '__unfiled__',
    description: '未映射到当前章节目录的历史分类或无分类题目',
    orderNum: formalTree.length,
    enabled: true,
    questionCount: null,
    subtreeQuestionCount: null,
    children,
  } satisfies CategoryTreeNode
}

const loadChapterTree = async (subjectId: number) => {
  try {
    const kind = questionKind.value
    const [treeResponse, namesResponse] = await Promise.all([
      getEnabledCategoryTreeBySubjectWithStats(subjectId, kind),
      kind === 'adaptation'
        ? getAdaptationCategoriesBySubject(subjectId)
        : getMockCategoriesBySubject(subjectId),
    ])

    if (treeResponse.code !== 200 || namesResponse.code !== 200) {
      chapterTree.value = []
      return
    }

    const formalTree = treeResponse.data || []
    const categoryNames = namesResponse.data || []
    chapterTree.value = [...formalTree, buildUnfiledTree(subjectId, formalTree, categoryNames)]
  } catch (error) {
    chapterTree.value = []
    showToast('章节目录加载失败，请重试', 'error')
    console.error('加载出题章节树失败:', error)
  }
}

const loadQuestionList = async ({ preserveScroll = false }: LoadQuestionListOptions = {}) => {
  const scrollTop = preserveScroll ? questionScroller.value?.scrollTop ?? 0 : null
  if (!preserveScroll) {
    questionScroller.value?.scrollTo({ top: 0, behavior: 'auto' })
  }
  if (!filters.subjectId) {
    resetQuestions()
    return
  }
  await reloadQuestions()
  if (scrollTop === null) return

  await nextTick()
  questionScroller.value?.scrollTo({ top: scrollTop, behavior: 'auto' })
}

const observeLoadMoreSentinel = () => {
  if (!intersectionObserver) return
  intersectionObserver.disconnect()
  if (loadMoreSentinel.value) intersectionObserver.observe(loadMoreSentinel.value)
}

const handleLoadMoreIntersection = (entries: IntersectionObserverEntry[]) => {
  if (!entries.some(entry => entry.isIntersecting)) return
  if (!filters.subjectId || listError.value || !hasMore.value) return
  void loadMoreQuestions()
}

watch([loadMoreSentinel, questionScroller], observeLoadMoreSentinel)

const handleSubjectChange = async (subjectId: string | number | null) => {
  const nextSubjectId = subjectId ? Number(subjectId) : null
  if (nextSubjectId !== previousSubjectId.value && selectedCount.value > 0) {
    const confirmed = await showConfirm({
      title: '切换科目',
      message: '切换科目后，当前出题篮中的题目将被清空。是否继续？',
      confirmText: '继续切换',
      cancelText: '保留当前题目',
      type: 'warning',
    })
    if (!confirmed) {
      filters.subjectId = previousSubjectId.value
      return
    }
    clearSelectedQuestions()
  }

  previousSubjectId.value = nextSubjectId
  filters.subjectId = nextSubjectId
  filters.category = ''
  filters.noCategory = false
  activeChapterId.value = null
  chapterTree.value = []
  resetQuestions()

  if (!nextSubjectId) return
  await loadChapterTree(nextSubjectId)
  await loadQuestionList()
}

/** 切换题目来源类型：重置章节与类型专属筛选，保留科目与出题篮。 */
const handleQuestionKindChange = async (value: QuestionKind | '') => {
  if (value !== 'mock' && value !== 'adaptation') return
  if (value === questionKind.value) return

  questionKind.value = value
  activeChapterId.value = null
  filters.category = ''
  filters.noCategory = false
  filters.source = ''
  filters.sourceYear = null
  filters.sourceQuestionNumber = null
  filters.sourceState = 'all'
  chapterTree.value = []
  resetQuestions()

  if (!filters.subjectId) return
  await loadChapterTree(filters.subjectId)
  await loadQuestionList()
}

/** 同步来源题号输入：非正数视为未筛选。 */
const handleSourceNumberChange = (value: number | null) => {
  filters.sourceQuestionNumber = typeof value === 'number' && value > 0 ? value : null
}

const handleChapterSelect = async (node: CategoryTreeNode) => {
  activeChapterId.value = node.id
  if (node.id === UNFILED_ROOT_ID) {
    filters.category = ''
    filters.noCategory = true
  } else {
    filters.category = node.name
    filters.noCategory = false
  }
  await loadQuestionList()
}

const handleAllChapters = async () => {
  activeChapterId.value = null
  filters.category = ''
  filters.noCategory = false
  await loadQuestionList()
}

const handleSearch = () => {
  if (!filters.subjectId) {
    showToast('请先选择科目', 'warning')
    return
  }
  void loadQuestionList()
}

const handleReset = () => {
  filters.source = ''
  filters.keyword = ''
  filters.category = ''
  filters.noCategory = false
  filters.examStatus = 'all'
  filters.questionType = 'all'
  filters.sourceYear = null
  filters.sourceQuestionNumber = null
  filters.sourceState = 'all'
  activeChapterId.value = null
  void loadQuestionList()
}

const handleQuestionSelection = (question: QuestionRow, selected: boolean) => {
  selectQuestion(question, selected)
}

const clearSelection = () => {
  clearSelectedQuestions()
}

const moveSelectedQuestion = (questionKey: string, direction: -1 | 1) => {
  moveQuestion(questionKey, direction)
}

const removeSelectedQuestion = (questionKey: string) => {
  removeQuestion(questionKey)
}

const handlePreview = (row: QuestionRow) => {
  previewQuestion.value = row
  previewVisible.value = true
}

/** 按题目类型打开对应的编辑弹窗。 */
const handleEdit = (row: QuestionRow) => {
  if (row.questionKind === 'adaptation') {
    editingAdaptationId.value = row.id
  } else {
    editingMockId.value = row.id
    editingMockData.value = row
  }
  editDialogVisible.value = true
}

/** 编辑完成后同步列表与出题篮中的题目数据。 */
const handleEditSuccess = (question: MockQuestion | AdaptationQuestion | null) => {
  if (question) {
    const kind = isAdaptationKind.value ? 'adaptation' : 'mock'
    const updatedRow = withQuestionKind(question, kind)
    const index = composeQuestions.value.findIndex(
      row => row.questionKind === kind && row.id === question.id,
    )
    if (index !== -1) {
      composeQuestions.value[index] = updatedRow
    }
    updateQuestion(updatedRow)
  }
  editingMockId.value = null
  editingMockData.value = null
  editingAdaptationId.value = null
  void loadQuestionList({ preserveScroll: true })
}

const saveExamStatus = async (row: QuestionRow, marked: boolean, automatic = false) => {
  if (row.examStatusLoading) return

  row.examStatusLoading = true
  try {
    const response = row.questionKind === 'adaptation'
      ? await setAdaptationExamMark(row.id, marked)
      : await setMockExamMark(row.id, marked)
    if (response.code !== 200 || !response.data) {
      showToast(response.message || '出题状态保存失败', 'error')
      return
    }

    row.isExamMarked = response.data.isExamMarked
    row.examStatusLoading = false
    updateQuestion(row)
    showToast(
      automatic ? '已自动设置为已出题' : (marked ? '出题状态已切换为已出题' : '出题状态已切换为未出题'),
      'success',
    )

    const filteredOut = (filters.examStatus === 'marked' && !marked) ||
      (filters.examStatus === 'unmarked' && marked)
    if (filteredOut) await loadQuestionList()
  } catch (error) {
    console.error('保存出题状态失败:', error)
    showToast('出题状态保存失败，请稍后重试', 'error')
  } finally {
    row.examStatusLoading = false
  }
}

const handleQuestionWordCopied = (row: QuestionRow, _result: RichCopyResult) => {
  if (!row.isExamMarked) void saveExamStatus(row, true, true)
}

const handleExamStatusToggle = (row: QuestionRow) => {
  void saveExamStatus(row, !row.isExamMarked)
}

/** 把选择键按题目来源类型拆分成两组 ID，供两个模块的批量接口分别调用。 */
const splitSelectionKeys = (keys: string[]) => {
  const mockIds: number[] = []
  const adaptationIds: number[] = []

  keys.forEach(key => {
    const separatorIndex = key.indexOf(':')
    if (separatorIndex === -1) return
    const id = Number(key.slice(separatorIndex + 1))
    if (!Number.isFinite(id)) return
    if (key.slice(0, separatorIndex) === 'adaptation') adaptationIds.push(id)
    else mockIds.push(id)
  })

  return { mockIds, adaptationIds }
}

/** 按题目来源类型调用各自的批量出题标记接口，返回实际更新的选择键。 */
const markQuestions = async (
  ids: number[],
  kind: QuestionKind,
): Promise<string[]> => {
  if (ids.length === 0) return []
  const response = kind === 'adaptation'
    ? await setAdaptationExamMarks(ids, true)
    : await setMockExamMarks(ids, true)
  if (response.code !== 200 || !response.data) {
    throw new Error(response.message || '批量更新出题状态失败')
  }
  return response.data.questionIds.map(id => `${kind}:${id}`)
}

const handleBatchWordCopied = async (_result: RichCopyResult, copiedKeys: string[]) => {
  const keys = [...new Set(copiedKeys)]
  if (keys.length === 0 || keys.length > MAX_BATCH_COPY_COUNT || batchMarking.value) return

  const { mockIds, adaptationIds } = splitSelectionKeys(keys)
  const markedKeys = new Set<string>()
  const failedLabels: string[] = []

  batchMarking.value = true
  try {
    const targets: { kind: QuestionKind; label: string; ids: number[] }[] = [
      { kind: 'mock', label: '模拟题', ids: mockIds },
      { kind: 'adaptation', label: '改编题', ids: adaptationIds },
    ]

    for (const target of targets) {
      if (target.ids.length === 0) continue
      try {
        const keysOfKind = await markQuestions(target.ids, target.kind)
        keysOfKind.forEach(key => markedKeys.add(key))
      } catch (error) {
        failedLabels.push(target.label)
        console.error('批量更新出题状态失败:', error)
      }
    }

    composeQuestions.value.forEach(row => {
      if (markedKeys.has(getQuestionSelectionKey(row))) row.isExamMarked = true
    })
    selectedQuestions.value.forEach(question => {
      if (!markedKeys.has(getQuestionSelectionKey(question))) return
      question.isExamMarked = true
      updateQuestion(question)
    })

    if (failedLabels.length === 0) {
      showToast('选中题目已复制，并已标记为已出题', 'success')
    } else {
      showToast(`题目已复制，${failedLabels.join('、')}的出题状态更新失败`, 'warning')
    }

    if (filters.examStatus === 'unmarked') await loadQuestionList()
  } finally {
    batchMarking.value = false
  }
}

onMounted(async () => {
  if (typeof IntersectionObserver !== 'undefined') {
    intersectionObserver = new IntersectionObserver(handleLoadMoreIntersection, {
      root: questionScroller.value,
      rootMargin: '0px 0px 320px 0px',
      threshold: 0,
    })
    observeLoadMoreSentinel()
  }

  void loadSourceOptions()
  await loadSubjectOptions()
  const urlKeyword = getUrlKeyword()
  if (urlKeyword) filters.keyword = urlKeyword
})

onBeforeUnmount(() => {
  intersectionObserver?.disconnect()
  intersectionObserver = null
})

watch(() => route.query.keyword, newKeyword => {
  if (newKeyword !== undefined) {
    filters.keyword = queryString(newKeyword)
    if (filters.subjectId) void loadQuestionList()
  }
})
</script>

<style scoped>
.compose-page {
  --compose-line: #eadfd4;
}

.chapter-panel__eyebrow,
.question-content__eyebrow {
  margin: 0 0 5px;
  color: #8b6f47;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: normal;
}

.compose-kind-switch {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 14px;
}

.compose-kind-switch__hint {
  color: #8b9593;
  font-size: 12px;
}

.compose-filters {
  display: grid;
  grid-template-columns: minmax(170px, 1fr) minmax(150px, 0.9fr) minmax(220px, 1.5fr) minmax(112px, 0.7fr) minmax(112px, 0.7fr) auto;
  align-items: end;
  gap: 12px;
}

/* 改编题有 7 个筛选项，宽屏单独 8 列，保证一行放完且题号列宽跟控件对齐。 */
.compose-filters--adaptation {
  grid-template-columns: minmax(140px, 1fr) minmax(120px, 0.85fr) minmax(136px, 0.6fr) minmax(120px, 0.85fr) minmax(180px, 1.4fr) minmax(112px, 0.7fr) minmax(112px, 0.7fr) auto;
}

/* 改编题下按钮固定在最后一列，折行时始终落在右下角。 */
.compose-filters--adaptation .compose-filters__actions {
  grid-column: -1;
}

.compose-filters__field {
  min-width: 0;
}

.compose-filters__label {
  display: block;
  margin-bottom: 6px;
  color: #6f7778;
  font-size: 11px;
  font-weight: 700;
}

.compose-filters__actions {
  display: flex;
  gap: 7px;
  justify-content: flex-end;
}

.compose-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0 0 16px;
  border: 1px solid #f0caca;
  border-radius: 10px;
  background: #fff4f4;
  padding: 10px 12px;
  color: #a23d3d;
  font-size: 12px;
}

.compose-workspace {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr) 292px;
  align-items: start;
  gap: 0;
  padding: 0;
}

.chapter-panel {
  position: sticky;
  top: 16px;
  min-width: 0;
  max-height: calc(var(--app-page-height) - 52px);
  overflow: hidden;
  border-right: 1px solid var(--compose-line);
  padding: 5px 17px 5px 8px;
}

.chapter-panel__header,
.question-content__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.chapter-panel__title,
.question-content__title {
  margin: 0;
  color: #344047;
  font-size: 17px;
  font-weight: 800;
}

.chapter-panel__count,
.question-content__total {
  color: #9a9f9d;
  font-size: 11px;
}

.chapter-panel__all {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 7px;
  margin: 16px 0 7px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  padding: 9px 10px;
  color: #65706f;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.chapter-panel__all:hover,
.chapter-panel__all--active {
  border-color: color-mix(in srgb, var(--brand-accent) 18%, transparent);
  background: color-mix(in srgb, var(--brand-accent) 8%, transparent);
  color: #704f2d;
}

.chapter-panel__all-mark {
  display: inline-flex;
  width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: color-mix(in srgb, var(--brand-accent) 12%, transparent);
  color: #8b6f47;
  font-size: 16px;
}

.chapter-panel__tree {
  max-height: calc(var(--app-page-height) - 170px);
  overflow-y: auto;
  scrollbar-gutter: stable;
  padding: 2px 0 12px;
  scrollbar-gutter: stable;
}

.chapter-panel__empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  min-height: 210px;
  color: #9aa3a2;
  text-align: center;
  font-size: 12px;
}

.chapter-panel__empty--small {
  min-height: 120px;
}

.chapter-panel__empty-mark {
  margin-bottom: 10px;
  color: #b49a7b;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 24px;
  font-weight: 800;
}

.question-content {
  min-width: 0;
  max-height: calc(var(--app-page-height) - 52px);
  overflow-y: auto;
  scrollbar-gutter: stable;
  padding: 5px 18px;
  scrollbar-gutter: stable;
}

.question-content__header {
  min-height: 45px;
  border-bottom: 1px solid var(--compose-line);
  padding: 0 2px 13px;
}

.question-content__sections {
  display: grid;
  gap: 14px;
  padding-top: 14px;
}

.question-content__empty,
.question-content__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  min-height: 340px;
  color: #899392;
  text-align: center;
}

.question-content__empty h3 {
  margin: 12px 0 4px;
  color: #596664;
  font-size: 16px;
}

.question-content__empty p {
  margin: 0;
  font-size: 12px;
}

.question-content__empty-icon {
  display: flex;
  width: 52px;
  height: 52px;
  align-items: center;
  justify-content: center;
  border: 1px dashed #c9b79e;
  border-radius: 16px;
  color: #a78966;
  font-size: 24px;
}

.question-content__loading {
  gap: 10px;
  min-height: 340px;
  color: #8b6f47;
  font-size: 13px;
}

.question-content__loading svg {
  font-size: 24px;
}

.question-content__load-more {
  display: flex;
  min-height: 52px;
  align-items: center;
  justify-content: center;
  border-top: 1px solid var(--compose-line);
  margin-top: 16px;
  color: #8a9693;
  font-size: 12px;
}

.question-content__load-more-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.question-content__retry {
  border: 0;
  background: transparent;
  color: #9d5b4d;
  cursor: pointer;
  font-size: 12px;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.question-basket-slot {
  min-width: 0;
  border-left: 1px solid var(--compose-line);
  padding: 5px 8px 5px 18px;
}

@media (max-width: 1399px) {
  .compose-filters--adaptation {
    grid-template-columns: repeat(5, minmax(0, 1fr));
  }
}

@media (max-width: 1279px) {
  .compose-filters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .compose-filters--adaptation {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .compose-filters__field--keyword {
    grid-column: span 2;
  }

  .compose-filters--adaptation .compose-filters__field--keyword {
    grid-column: auto;
  }

  .compose-filters__actions {
    justify-content: flex-start;
  }

  .compose-workspace {
    grid-template-columns: 238px minmax(0, 1fr);
  }

  .question-basket-slot {
    grid-column: 1 / -1;
    border-top: 1px solid var(--compose-line);
    border-left: 0;
    margin-top: 16px;
    padding: 16px 0 0;
  }
}

@media (max-width: 767px) {
  .compose-page {
    padding-right: 8px;
    padding-left: 8px;
  }

  .compose-filters {
    grid-template-columns: 1fr;
    padding: 14px 18px;
  }

  .compose-filters--adaptation {
    grid-template-columns: 1fr;
  }

  .compose-filters__field--keyword {
    grid-column: auto;
  }

  .compose-filters__actions {
    justify-content: flex-start;
  }

  .compose-workspace {
    grid-template-columns: 1fr;
    padding: 10px;
  }

  .chapter-panel {
    position: static;
    max-height: none;
    border-right: 0;
    border-bottom: 1px solid var(--compose-line);
    padding: 8px 4px 14px;
  }

  .chapter-panel__tree {
    max-height: 300px;
  }

  .question-content {
    max-height: none;
    overflow: visible;
    padding: 14px 0 0;
  }

  .question-basket-slot {
    margin-top: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .question-content__sections {
    scroll-behavior: auto;
  }
}
</style>
