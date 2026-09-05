<template>
  <div class="h-[calc(100vh-60px)] overflow-hidden flex flex-col bg-[#FBF7F2]">
    <div class="flex-1 flex relative overflow-hidden">
      <!-- 左侧科目导航栏 -->
      <SubjectSidebar
        v-model:is-collapsed="isNavCollapsed"
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

      <!-- 右侧内容区域 -->
      <div class="flex-1 w-0 overflow-y-auto bg-[#FBF7F2]">
        <div class="min-h-[calc(100vh-60px-40px)] bg-[#FBF7F2]">
          <div class="p-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3 flex-1">
                <h2 class="m-0 text-[#333] font-semibold text-xl">{{ currentTitle }}</h2>
                <Tag v-if="displayTotal > 0" type="info" size="sm">共 {{ displayTotal }} 题</Tag>
              </div>
              <div class="flex gap-2" v-if="activeSubjectId">
                <Select
                  v-model="filterQuestionType"
                  size="sm"
                  class="w-[100px] mr-2"
                  aria-label="题型筛选"
                  :options="questionTypeOptions"
                />

                <Dropdown trigger="click" @command="handleExportCommand">
                  <template #trigger>
                    <CustomButton
                      type="success"
                      :icon="['fas', 'download']"
                      size="sm"
                    >
                      导出科目
                    </CustomButton>
                  </template>

                  <template #dropdown>
                    <DropdownItem command="docx">
                      <font-awesome-icon :icon="['fas', 'file-word']" class="mr-2" />
                      导出为 Word 文档 (.docx)
                    </DropdownItem>
                  </template>
                </Dropdown>
              </div>
            </div>

            <!-- 加载状态 -->
            <div v-if="questionsLoading" class="flex justify-center py-8" role="status" aria-live="polite">
              <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-[#8B6F47] text-2xl" aria-hidden="true" />
            </div>

            <div v-if="subjectsLoadError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
              {{ subjectsLoadError }}
              <CustomButton size="sm" type="text" @click="loadSubjects">重新读取科目</CustomButton>
            </div>

            <div v-if="questionsLoadError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
              {{ questionsLoadError }}
              <CustomButton size="sm" type="text" :disabled="questionsLoading" @click="loadQuestions(true)">重试</CustomButton>
            </div>

            <!-- 普通分组列表 -->
            <div v-if="groupedQuestions.length > 0" class="w-full md:max-w-[80%] flex flex-col gap-6">
              <template v-for="group in groupedQuestions" :key="group.category">
                <!-- 分组头 -->
                <div class="flex items-center justify-between py-2 mt-4 mb-2 border-b border-[#dfe2e5]">
                  <h3 class="m-0 text-[#333] font-semibold text-lg">{{ group.category }}</h3>
                  <Tag type="info" size="sm">{{ group.items.length }} 题</Tag>
                </div>
                <!-- 题目卡片 -->
                <ExamEntryCard
                  v-for="exam in group.items"
                  :key="exam.id"
                  :id="`exam-${exam.id}`"
                  :exam="exam"
                  :is-admin="isAdmin"
                  :show-answer="showAnswers[exam.id]"
                  density="compact"
                  @copy="(cmd) => handleCopy(cmd, exam)"
                  @edit="handleEdit"
                  @delete="(id: number) => handleDelete(id)"
                  @toggle-answer="toggleAnswer(exam.id)"
                />
              </template>
            </div>
            <Empty
              v-if="!questionsLoadError && !subjectsLoadError && groupedQuestions.length === 0"
              :description="activeSubjectId ? '该科目暂无真题' : '请选择左侧科目'"
            />

            <!-- 加载更多按钮 -->
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

        <ExamEditDialog
          v-if="isAdmin"
          v-model:visible="editDialogVisible"
          :exam-id="editingExamId"
          @success="handleEditSuccess"
        />

        <BackTop :right="32" :bottom="32" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ExamQuestion, Subject, CategoryTreeNode } from "@/types"
import { queryString } from "@/utils/storage"
import { parseQuestionOptions } from "@/utils/questionOptions"
import { errorMessage } from "@/utils/errors"
/**
 * 真题分类浏览页面 (重构版)
 * 功能：按科目聚合展示真题，支持分类与年份筛选
 * 设计哲学：KISS (专注真题浏览), SOLID (单一职责)
 */
import { ref, onMounted, computed, nextTick, onActivated, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getEnabledSubjects } from '@/api/subject'
import { getExamList, deleteExam, getExamDetail, exportExamsBySubject } from '@/api/exam'
import { getEnabledCategoryTreeBySubject } from '@/api/category'
import { useAuthStore } from '@/stores/auth'
import toast from '@/utils/toast'
import confirm from '@/utils/confirm'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import Tag from '@/components/basic/Tag.vue'
import Select from '@/components/basic/Select.vue'
import Empty from '@/components/basic/Empty.vue'
import BackTop from '@/components/basic/BackTop.vue'
import SubjectSidebar from '@/components/business/SubjectSidebar.vue'
import ExamEntryCard from '@/components/business/ExamEntryCard.vue'
import ExamEditDialog from '@/components/business/ExamEditDialog.vue'

const route = useRoute()
const authStore = useAuthStore()

// 计算是否为管理员
const isAdmin = computed(() => authStore.isAdmin())

// 记录从哪个题目进入编辑页，以便返回时滚回该题目
const RETURN_SCROLL_KEY = 'exam-return-position'

// UI State
const isNavCollapsed = ref(false)
const loadingSubjects = ref(false)
const questionsLoading = ref(false)
const subjectsLoadError = ref('')
const questionsLoadError = ref('')
let questionsRequestVersion = 0

// 题目编辑弹窗状态
const editDialogVisible = ref(false)
const editingExamId = ref<number | null>(null)

// Data
const subjects = ref<Subject[]>([])
const subjectCategories = ref<Record<number, CategoryTreeNode[]>>({})
const activeSubjectId = ref<number | null>(null)
const activeSubjectName = ref('')
const expandedSubjectId = ref<number | null>(null)

// Pagination State
const currentPage = ref(1)
const hasMore = ref(false)
const pageSize = ref(50) // Reduce batch size for faster initial render

// Filter Data
const filterCategory = ref('')
// 题型筛选：ALL=全部，CHOICE=仅选择题，ESSAY=仅主观题（视为非CHOICE的题型）
const filterQuestionType = ref('ALL')

// 题型选项
const questionTypeOptions = [
  { label: '全部题型', value: 'ALL' },
  { label: '选择题', value: 'CHOICE' },
  { label: '主观题', value: 'ESSAY' }
]

// Questions Data
const questionList = ref<ExamQuestion[]>([])
const total = ref(0)
const showAnswers = ref<Record<number, boolean>>({}) // map: { examId: boolean }



// Computed
const currentTitle = computed(() => {
  if (activeSubjectName.value && filterCategory.value) {
    return `${activeSubjectName.value} · ${filterCategory.value} · 真题`
  }
  return activeSubjectName.value ? `${activeSubjectName.value} · 真题` : '真题分类浏览'
})

const compareQuestions = (a: ExamQuestion, b: ExamQuestion) => {
  const yearDifference = a.year - b.year
  if (yearDifference !== 0) return yearDifference

  const questionNumberA = a.questionNumber ?? Number.POSITIVE_INFINITY
  const questionNumberB = b.questionNumber ?? Number.POSITIVE_INFINITY
  const questionNumberDifference = questionNumberA - questionNumberB
  if (questionNumberDifference !== 0) return questionNumberDifference

  return a.id - b.id
}

const uniqueQuestions = (questions: readonly ExamQuestion[]) => {
  const seenIds = new Set<number>()
  return questions
    .filter((exam) => {
      if (seenIds.has(exam.id)) return false
      seenIds.add(exam.id)
      return true
    })
    .sort(compareQuestions)
}

const findCategoryNode = (
  categories: readonly CategoryTreeNode[],
  categoryName: string,
): CategoryTreeNode | undefined => {
  for (const category of categories) {
    if (category.name === categoryName) return category
    const child = findCategoryNode(category.children, categoryName)
    if (child) return child
  }
  return undefined
}

const getCategoryScopeNames = (categoryName: string) => {
  const currentCategories = activeSubjectId.value === null
    ? undefined
    : subjectCategories.value[activeSubjectId.value]
  const selectedCategory = currentCategories
    ? findCategoryNode(currentCategories, categoryName)
    : undefined

  if (!selectedCategory) return new Set([categoryName])

  const scopeNames = new Set<string>()
  const collectNames = (category: CategoryTreeNode) => {
    scopeNames.add(category.name)
    category.children.forEach(collectNames)
  }
  collectNames(selectedCategory)
  return scopeNames
}

const groupedQuestions = computed(() => {
  let list = questionList.value || []
  if (!list.length) return []

  // 先按题型做前端过滤
  if (filterQuestionType.value === 'CHOICE') {
    list = list.filter(exam => exam.questionType === 'CHOICE')
  } else if (filterQuestionType.value === 'ESSAY') {
    list = list.filter(exam => exam.questionType !== 'CHOICE')
  }

  // 同一题可能被多个分类引用，分类视图中只展示一次，并统一按年份升序排列。
  list = uniqueQuestions(list)

  // 选中分类后，内容区只保留当前分类分组，标题与左侧副标题保持一致。
  if (filterCategory.value) {
    const categoryScopeNames = getCategoryScopeNames(filterCategory.value)
    const categoryItems = list.filter((exam) => (
      Array.isArray(exam.category) && exam.category.some((category) => (
        categoryScopeNames.has(category)
      ))
    ))

    return categoryItems.length > 0
      ? [{ category: filterCategory.value, items: categoryItems }]
      : []
  }

  const groupsMap = new Map<string, ExamQuestion[]>()
  const displayedIds = new Set<number>()

  list.forEach((exam: ExamQuestion) => {
    const categories = Array.isArray(exam.category) && exam.category.length
      ? exam.category
      : ['未分类']

    // 未选择分类时也只归入一个分组，避免多分类题在不同分组中重复渲染。
    const category = categories[0]
    if (!category || displayedIds.has(exam.id)) return
    displayedIds.add(exam.id)

    if (!groupsMap.has(category)) {
      groupsMap.set(category, [])
    }
    groupsMap.get(category)?.push(exam)
  })

  // 构建分类名称到 orderNum 的映射表（直接在 computed 内访问响应式数据）
  const orderNumMap = new Map<string, number>()
  const currentCategories = (activeSubjectId.value === null ? undefined : subjectCategories.value[activeSubjectId.value])
  if (currentCategories && Array.isArray(currentCategories)) {
    currentCategories.forEach((cat, parentIndex) => {
      // 父分类使用其 orderNum，若无则用索引
      orderNumMap.set(cat.name, cat.orderNum ?? parentIndex)
      // 子分类
      if (cat.children && Array.isArray(cat.children)) {
        cat.children.forEach((child, childIndex) => {
          // 子分类排序：父分类orderNum * 1000 + 子分类orderNum（确保子分类跟在父分类后）
          const parentOrder = cat.orderNum ?? parentIndex
          const childOrder = child.orderNum ?? childIndex
          orderNumMap.set(child.name, parentOrder * 1000 + childOrder)
        })
      }
    })
  }

  // 按后台设置的 orderNum 排序（而非拼音排序）
  return Array.from(groupsMap.entries())
    .map(([category, items]) => ({ category, items }))
    .sort((a, b) => {
      const orderA = orderNumMap.get(a.category) ?? Infinity
      const orderB = orderNumMap.get(b.category) ?? Infinity
      return orderA - orderB
    })
})

const displayTotal = computed(() => {
  if (!questionList.value || !questionList.value.length) return 0
  // 当前展示题目总数（按过滤后的分组统计）
  return groupedQuestions.value.reduce((sum, group) => sum + group.items.length, 0)
})




// Initialization
onMounted(() => {
  initPage()
})


// 当从编辑页面返回时，如果 sessionStorage 中记录了题目ID，则自动滚动回对应题目卡片
onActivated(() => {
  try {
    const raw = sessionStorage.getItem(RETURN_SCROLL_KEY)
    if (!raw) return

    const info: unknown = JSON.parse(raw)
    if (typeof info !== 'object' || info === null) return
    if ('source' in info && info.source === 'classify' && 'examId' in info
      && typeof info.examId === 'number' && info.examId) {
      scrollToExamById(info.examId)
      sessionStorage.removeItem(RETURN_SCROLL_KEY)
    }
  } catch (error) {
    console.error('恢复滚动位置失败:', error)
  }
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
      
      // 检查URL参数，支持从收藏页面跳转
      const subjectFromRoute = queryString(route.query.subject)
      const categoryFromRoute = queryString(route.query.category)
      
      // 只有URL明确指定科目时才自动选中并加载题目
      if (subjectFromRoute && subjects.value.length > 0) {
        const initialSubject = subjects.value.find(s => s.name === subjectFromRoute)
        if (initialSubject) {
          await handleSubjectSelect(initialSubject)
          
          // 在科目选择后再设置分类筛选
          if (categoryFromRoute) {
            filterCategory.value = categoryFromRoute
            await loadQuestions(true)
          }
          
          // 处理URL hash跳转（从管理页面"查看"按钮跳转过来）
          await handleHashScroll()
        }
      }
      
      // 静默加载所有科目的分类，以便显示侧边栏统计
      subjects.value.forEach(sub => {
        if (sub.id !== activeSubjectId.value) {
          loadCategoriesForSubject(sub.id)
        }
      })
    } else {
      subjectsLoadError.value = res.message || '科目读取失败，请重试。'
      toast.error(subjectsLoadError.value)
    }
  } catch (e) {
    subjectsLoadError.value = '科目读取失败，请重试。'
    toast.error(subjectsLoadError.value)
    console.error('加载科目失败:', e)
  } finally {
    loadingSubjects.value = false
  }
}

// 根据题目ID滚动到对应题目卡片
const scrollToExamById = (examId: number | string) => {
  nextTick(() => {
    const targetElement = document.getElementById(`exam-${examId}`)
    if (targetElement) {
      targetElement.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      })
    }
  })
}

/**
 * 处理URL hash跳转
 * 支持从真题管理页面的"查看"按钮跳转到具体题目
 * URL格式: /exam/classify?subject=科目名称#exam-题目ID
 * 
 * 修复：先通过API获取目标题目详情，确保题目数据已加载后再滚动
 */
const handleHashScroll = async () => {
  const hash = window.location.hash
  if (!hash || !hash.startsWith('#exam-')) return
  
  // 从hash中提取题目ID
  const examId = hash.slice(6) // 移除 '#exam-' 前缀
  if (!examId || isNaN(Number(examId))) return
  
  try {
    // 1. 先获取目标题目的详细信息
    const res = await getExamDetail(Number(examId))
    if (res.code !== 200 || !res.data) {
      console.warn('目标题目不存在:', examId)
      return
    }
    
    const targetExam = res.data
    
    // 2. 如果题目有分类，设置分类筛选以缩小数据范围
    if (targetExam.category && Array.isArray(targetExam.category) && targetExam.category.length > 0) {
      // 使用第一个分类作为筛选条件
      filterCategory.value = targetExam.category[0]
      // 重新加载该分类下的题目
      await loadQuestions(true)
    }
    
    // 3. 检查题目是否已在当前列表中，如果不在则直接插入到列表开头
    const existsInList = questionList.value.some(q => q.id === targetExam.id)
    if (!existsInList) {
      // 将目标题目插入到列表开头，确保能够滚动到
      questionList.value.unshift(targetExam)
    }
    
    // 4. 等待DOM渲染完成后滚动
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))
    
    const elementId = `exam-${examId}`
    const element = document.getElementById(elementId)
    
    if (element) {
      // 滚动到元素位置
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      
      // 添加高亮效果
      element.classList.add('highlight-card')
      setTimeout(() => {
        element.classList.remove('highlight-card')
      }, 2000)
    }
  } catch (error) {
    console.error('处理hash跳转失败:', error)
  }
}

const loadCategoriesForSubject = async (subjectId: number) => {
  if (subjectCategories.value[subjectId]) {
    return
  }

  try {
    // 使用新的树形分类 API
    const res = await getEnabledCategoryTreeBySubject(subjectId)
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
  if (activeSubjectId.value === subject.id) {
    expandedSubjectId.value = expandedSubjectId.value === subject.id ? null : subject.id
    return
  }

  activeSubjectId.value = subject.id
  activeSubjectName.value = subject.name

  // 默认不过滤分类，展示该科目下的全部分类
  filterCategory.value = ''
  // 重置题型筛选为全部
  filterQuestionType.value = 'ALL'

  // 选中科目时默认展开该科目的分类
  expandedSubjectId.value = subject.id

  // 重置状态
  showAnswers.value = {}

  // 并行加载分类和题目，减少等待时间
  await Promise.all([
    loadCategoriesForSubject(subject.id),
    loadQuestions(true)
  ])
}

// Toggle subject categories expansion without changing active subject
const toggleSubjectExpand = async (subject: Subject | null) => {
  // 处理全部折叠的情况
  if (!subject) {
    expandedSubjectId.value = null
    return
  }

  const id = subject.id

  // 收起当前展开的科目
  if (expandedSubjectId.value === id) {
    expandedSubjectId.value = null
    return
  }

  // 展开前确保分类已加载
  await loadCategoriesForSubject(id)
  expandedSubjectId.value = id
}

const handleCategorySelect = (subject: Subject, category: string) => {
  if (activeSubjectId.value !== subject.id) {
    activeSubjectId.value = subject.id
    activeSubjectName.value = subject.name
  }
  // 再次点击同一分类，表示取消分类过滤，展示全部分类
  if (filterCategory.value === category) {
    filterCategory.value = ''
  } else {
    filterCategory.value = category
  }

  showAnswers.value = {}

  loadQuestions(true)
}



/**
 * 切换指定题目的答案显示/隐藏（分类视图）
 * 与 ExamList 中的 toggleYearAnswer 行为保持一致
 */
const toggleAnswer = (examId: number | string) => {
  showAnswers.value[Number(examId)] = !showAnswers.value[Number(examId)]
}

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
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      try {
        document.execCommand('copy')
      } catch (err) {
        console.error('复制失败:', err)
        throw err
      }
      document.body.removeChild(textArea)
    }
    return true
  } catch (error) {
    console.error('复制失败:', error)
    throw error
  }
}

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

  const patterns = [
    // 罗马数字模式: I. II. III. IV. V. VI. VII. VIII. IX. X. XI. XII.
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
  patterns.forEach(pattern => {
    result = result.replace(pattern, '\n$1')
  })
  result = result.replace(/\n{3,}/g, '\n\n')

  return result
}

/**
 * 解析选项JSON为对象
 */
const parseOptions = (exam: ExamQuestion) => {
  if (exam?.questionType !== 'CHOICE' || !exam?.options) return null
  try {
    return parseQuestionOptions(exam.options)
  } catch (e) {
    console.error('解析选项失败:', e)
    return null
  }
}

const formatQuestionMarkdown = (exam: ExamQuestion) => {
  if (!exam?.content) return ''
  return normalizeLineBreaks(exam.content)
}

const formatOptionsMarkdown = (exam: ExamQuestion) => {
  if (exam?.questionType !== 'CHOICE' || !exam?.options) {
    return ''
  }
  let optionsObj: Record<string, string> | null = null
  try {
    optionsObj = parseQuestionOptions(exam.options)
  } catch (e) {
    console.error('解析选项失败:', e)
    return ''
  }
  if (!optionsObj) return ''
  const optionKeys = Object.keys(optionsObj).sort()
  const optionLines = optionKeys.map(key => `${key}. ${normalizeLineBreaks(optionsObj[key])}`)
  return optionLines.join('\n')
}

const formatAnswerMarkdown = (exam: ExamQuestion) => {
  if (!exam?.answer) return ''
  return normalizeLineBreaks(exam.answer)
}

const formatFullMarkdown = (exam: ExamQuestion) => {
  const parts = []

  const question = formatQuestionMarkdown(exam)
  if (question) {
    parts.push('## 题目')
    parts.push(question)
    parts.push('')
  }

  if (exam?.questionType === 'CHOICE') {
    const options = formatOptionsMarkdown(exam)
    if (options) {
      parts.push('## 选项')
      parts.push(options)
      parts.push('')
    }
  }

  const answer = formatAnswerMarkdown(exam)
  if (answer) {
    parts.push('## 答案')
    parts.push(answer)
  }

  return parts.join('\n')
}

// ==================== 纯文本格式化函数 ====================

const formatQuestionText = (exam: ExamQuestion) => {
  if (!exam?.content) return ''
  const questionNumber = exam.questionNumber || ''
  const questionType = exam.questionType === 'CHOICE' ? '选择题' : '主观题'
  const category = Array.isArray(exam.category) ? exam.category.join(', ') : (exam.category || '')

  const parts = []
  parts.push(`第${questionNumber}题 (${questionType}${category ? ' - ' + category : ''})`)
  parts.push('')
  parts.push('【题目】')
  parts.push(normalizeLineBreaks(exam.content))
  return parts.join('\n')
}

const formatOptionsText = (exam: ExamQuestion) => {
  const optionsObj = parseOptions(exam)
  if (!optionsObj) return ''
  const optionKeys = Object.keys(optionsObj).sort()
  const parts = []
  parts.push('【选项】')
  optionKeys.forEach(key => {
    parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
  })
  return parts.join('\n')
}

const formatAnswerText = (exam: ExamQuestion) => {
  if (!exam?.answer) return ''
  const parts = []
  parts.push('【答案】')
  parts.push(normalizeLineBreaks(exam.answer))
  return parts.join('\n')
}

const formatFullText = (exam: ExamQuestion) => {
  const parts = []
  const questionNumber = exam.questionNumber || ''
  const questionType = exam.questionType === 'CHOICE' ? '选择题' : '主观题'
  const category = Array.isArray(exam.category) ? exam.category.join(', ') : (exam.category || '')

  // 标题行
  parts.push(`第${questionNumber}题 (${questionType}${category ? ' - ' + category : ''})`)
  parts.push('')

  // 题目内容
  if (exam?.content) {
    parts.push('【题目】')
    parts.push(normalizeLineBreaks(exam.content))
    parts.push('')
  }

  // 选项（仅选择题）
  if (exam?.questionType === 'CHOICE') {
    const optionsObj = parseOptions(exam)
    if (optionsObj) {
      const optionKeys = Object.keys(optionsObj).sort()
      parts.push('【选项】')
      optionKeys.forEach(key => {
        parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
      })
      parts.push('')
    }
  }

  // 答案
  if (exam?.answer) {
    parts.push('【答案】')
    parts.push(normalizeLineBreaks(exam.answer))
  }

  return parts.join('\n')
}

const handleCopy = async (command: string, exam: ExamQuestion) => {
  let text = ''
  let message = ''

  try {
    switch (command) {
      // Markdown 格式
      case 'md-question':
        text = formatQuestionMarkdown(exam)
        message = '题目已复制 (Markdown)'
        break
      case 'md-options':
        text = formatOptionsMarkdown(exam)
        message = '选项已复制 (Markdown)'
        break
      case 'md-answer':
        text = formatAnswerMarkdown(exam)
        message = '答案已复制 (Markdown)'
        break
      case 'md-all':
        text = formatFullMarkdown(exam)
        message = '完整内容已复制 (Markdown)'
        break
      // 纯文本格式
      case 'text-question':
        text = formatQuestionText(exam)
        message = '题目已复制 (纯文本)'
        break
      case 'text-options':
        text = formatOptionsText(exam)
        message = '选项已复制 (纯文本)'
        break
      case 'text-answer':
        text = formatAnswerText(exam)
        message = '答案已复制 (纯文本)'
        break
      case 'text-all':
        text = formatFullText(exam)
        message = '完整内容已复制 (纯文本)'
        break
      default:
        return
    }

    if (!text) {
      toast.warning('没有可复制的内容')
      return
    }

    await copyToClipboard(text)
    toast.success(message)
  } catch (error) {
    toast.error('复制失败，请重试')
  }
}

// Core: Load Questions
const loadQuestions = async (isReset = false) => {
  const requestVersion = ++questionsRequestVersion
  if (!activeSubjectId.value) {
    questionList.value = []
    total.value = 0
    questionsLoadError.value = ''
    questionsLoading.value = false
    return
  }

  if (isReset) {
    currentPage.value = 1
    questionList.value = []
    hasMore.value = true
    questionsLoadError.value = ''
  }

  questionsLoading.value = true
  // Don't reset showAnswers on load more, only on reset
  if (isReset) {
    showAnswers.value = {}
  }

  try {
    const params: import("@/types").ExamQueryParams = {
      page: currentPage.value,
      size: pageSize.value,
      subjectId: activeSubjectId.value,
      sortField: 'year',
      sortOrder: 'asc',
      category: filterCategory.value || undefined // Server-side filtering
    }

    const res = await getExamList(params)
    if (requestVersion !== questionsRequestVersion) return
    if (res.code === 200) {
      questionsLoadError.value = ''
      const pageData = res.data?.lists || []
      const serverTotal = res.data?.pagination?.total || 0
      
      if (isReset) {
        questionList.value = uniqueQuestions(pageData)
      } else {
        // 分页追加时按题目 ID 合并，避免重复记录进入展示状态。
        questionList.value = uniqueQuestions([...questionList.value, ...pageData])
      }

      total.value = serverTotal
      
      // Update hasMore status
      hasMore.value = questionList.value.length < serverTotal
      
      if (pageData.length > 0) {
        currentPage.value++
      }
    } else {
      hasMore.value = false
      questionsLoadError.value = res.message || '真题读取失败，请重试。'
    }
  } catch (e) {
    console.error('加载真题失败:', e)
    if (requestVersion === questionsRequestVersion) {
      questionsLoadError.value = '真题读取失败，请重试。'
    }
    if (requestVersion === questionsRequestVersion && isReset) {
      questionList.value = []
      total.value = 0
    }
  } finally {
    if (requestVersion === questionsRequestVersion) questionsLoading.value = false
  }
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

/**
 * 统一导出处理函数
 * 遵循KISS原则：直接调用后端导出API
 */
const handleExportCommand = async (format: string) => {
  if (!activeSubjectId.value) {
    toast.warning('请先选择科目')
    return
  }
  if (format !== 'markdown') {
    toast.warning('当前仅支持 Markdown 导出')
    return
  }

  try {
    const response = await exportExamsBySubject(activeSubjectId.value, format)
    const blob = response.data
    const downloadUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `408-${activeSubjectName.value}-全部真题.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(downloadUrl)
    toast.success('Markdown 导出已开始')
  } catch (error) {
    toast.error('导出失败，请重试')
    console.error('Markdown 导出失败:', error)
  }
}

const handleEdit = (exam: ExamQuestion) => {
  if (!exam || !exam.id) {
    return
  }

  editingExamId.value = exam.id
  editDialogVisible.value = true
}

const handleEditSuccess = async () => {
  // Reload current list (simplest is to reset, or we could just reload current page but that's complex)
  await loadQuestions(true)
}

const handleDelete = async (id: number) => {
  const confirmed = await confirm(
    '此操作将永久删除该真题，是否继续？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'danger'
    }
  )
  if (!confirmed) return

  try {
    const response = await deleteExam(id)
    if (response.code === 200) {
      toast.success('删除成功')
      await loadQuestions(true)
    } else {
      toast.error(response.message || '删除失败')
    }
  } catch (error) {
    toast.error('删除失败')
    console.error('删除失败:', error)
  }
}

</script>
