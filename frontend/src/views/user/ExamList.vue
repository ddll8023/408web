<!-- 年份真题阅读页面：窄屏使用吸顶目录入口与底部目录抽屉，桌面端保留年份侧栏。 -->
<template>
  <ReadingLayout>
    <template #wide-nav>
      <!-- 左侧年份导航栏（窄屏自动隐藏） -->
      <YearNav
        v-model:expanded-years="expandedYears"
        :year-list="yearList"
        :active-year="activeYear"
        :active-exam-id="activeExamId"
        :loading="loadingYearList"
        @year-select="handleYearSelect"
        @exam-select="handleExamSelect"
        @collapse-change="handleNavCollapseChange"
      />
    </template>

    <template #compact-nav>
      <!-- 窄屏目录入口与抽屉 -->
      <MobileQuestionNav
        v-model:visible="navSheetVisible"
        :title="currentTitle"
        :count="displayTotal"
        kind="exam"
      >
        <template #nav>
          <YearNavList
            v-model:expanded-years="expandedYears"
            :year-list="yearList"
            :active-year="activeYear"
            :active-exam-id="activeExamId"
            :loading="loadingYearList"
            auto-scroll-active
            @year-select="handleYearSelect"
            @exam-select="handleNavSheetExamSelect"
          />
        </template>
      </MobileQuestionNav>
    </template>

    <!-- 使用 div + Tailwind 替代 el-card -->
    <div class="min-h-full bg-surface">
          <!-- 头部区域：窄屏标题已上移到目录入口，只保留导出与创建操作 -->
          <div class="flex flex-col items-stretch gap-3 px-4 py-4 border-b border-line sm:flex-row sm:items-center sm:justify-between sm:px-5">
            <div class="hidden min-w-0 flex-1 items-center gap-3 md:flex">
              <h2 class="m-0 text-ink font-semibold text-xl">{{ currentTitle }}</h2>
              <!-- 使用自定义 Tag 组件替代 el-tag -->
              <Tag v-if="displayTotal > 0" type="info">共 {{ displayTotal }} 题</Tag>
            </div>
            <!-- 年份视图：显示导出按钮和管理员创建按钮 -->
            <div class="flex flex-wrap gap-2" v-if="examList.length > 0">
              <Dropdown trigger="click" @command="handleExportCommand">
                <template #trigger>
                  <CustomButton
                    type="success"
                    :icon="['fas', 'download']"
                  >
                    导出试卷
                  </CustomButton>
                </template>

                <template #dropdown>
                  <DropdownItem command="markdown">
                    <font-awesome-icon :icon="['fas', 'file-lines']" class="mr-2" />
                    导出为 Markdown (.md)
                  </DropdownItem>
                  <DropdownItem command="docx">
                    <font-awesome-icon :icon="['fas', 'file-word']" class="mr-2" />
                    导出为 Word 文档 (.docx)
                  </DropdownItem>
                </template>
              </Dropdown>
              <CustomButton
                v-if="isAdmin"
                type="primary"
                :icon="['fas', 'plus']"
                @click="handleCreate"
              >
                创建真题
              </CustomButton>
            </div>
            <!-- 默认视图（空状态）：显示管理员创建按钮 -->
            <div class="flex flex-wrap gap-2" v-else-if="isAdmin">
              <CustomButton
                type="primary"
                :icon="['fas', 'plus']"
                @click="handleCreate"
              >
                创建真题
              </CustomButton>
            </div>
          </div>

          <!-- 年份视图:显示所有题目 -->
          <div v-if="examList.length > 0" class="mx-auto flex w-full max-w-[1100px] flex-col gap-4 px-3 py-4 sm:gap-6 sm:px-5">
            <ExamEntryCard
              v-for="exam in examList"
              :key="exam.id"
              :id="`question-${exam.id}`"
              :exam="exam"
              :is-admin="isAdmin"
              :show-answer="showAnswers[exam.id]"
              density="compact"
              @copy="(cmd) => handleCopy(cmd, exam)"
              @edit="handleEdit"
              @delete="(id: number) => handleDelete(id)"
              @toggle-answer="toggleYearAnswer(exam.id)"
              @show-adaptations="handleShowAdaptations"
            />
          </div>

          <!-- 默认提示 -->
          <div v-else-if="!loading" class="mt-2 p-4 bg-gradient-to-br from-surface to-[#F5EFE6] rounded border-2 border-line min-h-[300px] mx-5 my-4">
            <div class="flex items-center gap-2 mb-2">
              <font-awesome-icon :icon="['fas', 'book']" class="text-accent text-lg" />
              <h3 class="m-0 text-ink font-semibold text-lg">408历年真题</h3>
            </div>
            <!-- 使用 div + border 替代 el-divider -->
            <div class="border-t border-line my-3"></div>
            <div class="py-4">
              <p class="m-0 leading-relaxed text-sm text-ink text-justify indent-2em">这里收录了408考研的历年真题，包括数据结构、操作系统、计算机网络和计算机组成原理四大科目。</p>
            </div>
            <div class="flex items-center gap-1.5 p-2 mt-4 bg-white/60 rounded text-ink-soft text-xs">
              <font-awesome-icon :icon="['fas', 'arrow-right']" class="text-xs" />
              请选择左侧年份查看真题内容
            </div>
          </div>
        </div>

        <ExamEditDialog
          v-if="isAdmin"
          v-model:visible="editDialogVisible"
          :exam-id="editingExamId"
          @success="handleEditSuccess"
        />

    <AdaptationRelatedDialog
      v-model:visible="adaptationDialogVisible"
      :exam="selectedAdaptationExam"
    />
  </ReadingLayout>
</template>

<script setup lang="ts">
import type { ExamNavQuestion, ExamNavYear, ExamQuestion, Subject, CategoryTreeNode } from "@/types"
import { queryString } from "@/utils/storage"
import { parseQuestionOptions } from "@/utils/questionOptions"
import { errorMessage } from "@/utils/errors"
/**
 * 真题主页面
 * 功能：左侧年份导航，右侧显示选中真题的详细内容
 * 遵循KISS原则：简单直观的内容展示
 * 
 * 改进：
 * - 左侧年份导航栏（树形结构，展示年份和题目）
 * - 右侧直接显示真题内容（不再跳转详情页）
 * - 管理员可编辑、删除真题
 */
import { ref, computed, watch, onMounted, nextTick, onActivated } from 'vue'
import { useRoute } from 'vue-router'
import { getExamNavIndex, getExamByYear, deleteExam } from '@/api/exam'
import { getDifficultyLabel } from '@/constants/exam'
import { useAuthStore } from '@/stores/auth'
import toast from '@/utils/toast'
import confirm from '@/utils/confirm'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import Tag from '@/components/basic/Tag.vue'
import ReadingLayout from '@/app/layouts/ReadingLayout.vue'
import YearNav from '@/components/business/YearNav.vue'
import YearNavList from '@/components/business/YearNavList.vue'
import MobileQuestionNav from '@/components/business/MobileQuestionNav.vue'
import ExamEntryCard from '@/components/business/ExamEntryCard.vue'
import ExamEditDialog from '@/components/business/ExamEditDialog.vue'
import AdaptationRelatedDialog from '@/components/business/AdaptationRelatedDialog.vue'

const route = useRoute()
const authStore = useAuthStore()

// 计算是否为管理员
const isAdmin = computed(() => authStore.isAdmin())

// 年份树数据：类型与年份导航列表组件共用
type NavQuestion = ExamNavQuestion
type NavYear = ExamNavYear
const yearList = ref<NavYear[]>([])
const loadingYearList = ref(false)

// 窄屏目录抽屉开关
const navSheetVisible = ref(false)

// 年份展开状态：桌面侧栏与窄屏抽屉共用同一份状态
const expandedYears = ref<number[]>([])

// 当前分类（来自路由查询参数）
const activeCategory = ref(queryString(route.query.category))

// 当前激活的年份和题目
const activeYear = ref<number | null>(null)
const activeExamId = ref<number | null>(null)

// 当前年份的所有题目
const examList = ref<ExamQuestion[]>([])

// 标题：显示当前年份
const currentTitle = computed(() => {
  if (activeYear.value) {
    return `${activeYear.value} 年真题`
  }
  return '请选择年份'
})

// 题目总数
const displayTotal = computed(() => {
  return examList.value?.length || 0
})

const loading = ref(false)

// 年份视图下,每道题的答案显示状态
const showAnswers = ref<Record<number, boolean>>({})

// 导航栏是否折叠
const isNavCollapsed = ref(false)

// 题目编辑弹窗状态
const editDialogVisible = ref(false)
const editingExamId = ref<number | null>(null)
const adaptationDialogVisible = ref(false)
const selectedAdaptationExam = ref<ExamQuestion | null>(null)

// 记录从哪个题目进入编辑页，以便返回时滚回该题目
const RETURN_SCROLL_KEY = 'exam-return-position'

// 导航数据缓存（按分类缓存，避免重复请求）
const navCache = new Map<string, NavYear[]>()
let navRequestVersion = 0
let examsRequestVersion = 0

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

// 从 sessionStorage 中读取并应用返回滚动位置
const applyReturnScrollIfNeeded = () => {
  try {
    const raw = sessionStorage.getItem(RETURN_SCROLL_KEY)
    if (!raw) return

    const info: unknown = JSON.parse(raw)
    if (typeof info !== 'object' || info === null) return
    if ('source' in info && info.source === 'year' && 'year' in info && info.year === activeYear.value
      && 'questionNumber' in info && typeof info.questionNumber === 'number' && info.questionNumber) {
      scrollToExamByQuestionNumber(info.questionNumber)
      sessionStorage.removeItem(RETURN_SCROLL_KEY)
    }
  } catch (error) {
    console.error('恢复滚动位置失败:', error)
  }
}

// ==================== 格式化工具函数 ====================

/**
 * 获取题目元信息标签（用于标题）
 * @param {Object} exam - 题目对象
 * @returns {string} 格式化的标签字符串，如 "[选择题] [数据结构]"
 */
const getExamTags = (exam: ExamQuestion) => {
  const questionType = exam.questionType === 'CHOICE' ? '选择题' : '主观题'
  const category = Array.isArray(exam.category) ? exam.category.join(', ') : (exam.category || '')
  const difficulty = exam.difficulty ? getDifficultyLabel(exam.difficulty) : ''
  const tags = [questionType, category, difficulty].filter(Boolean)
  return tags.length > 0 ? `[${tags.join('] [')}]` : ''
}

/**
 * 解析选项JSON为对象
 * @param {Object} exam - 题目对象
 * @returns {Object} 选项对象
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

// ==================== Markdown 格式化函数 ====================

/**
 * 格式化题目为 Markdown（与导出格式一致）
 */
const formatQuestionMarkdown = (exam: ExamQuestion) => {
  if (!exam?.content) return ''
  const parts = []
  const questionNumber = exam.questionNumber || ''
  const tags = getExamTags(exam)
  // 标题行：第X题 [标签]
  parts.push(`## 第${questionNumber}题 ${tags}`)
  parts.push('')
  parts.push('### 题目')
  parts.push(normalizeLineBreaks(exam.content))
  return parts.join('\n')
}

/**
 * 格式化选项为 Markdown
 */
const formatOptionsMarkdown = (exam: ExamQuestion) => {
  const optionsObj = parseOptions(exam)
  if (!optionsObj) return ''
  const optionKeys = Object.keys(optionsObj).sort()
  const parts = []
  parts.push('### 选项')
  optionKeys.forEach(key => {
    parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
  })
  return parts.join('\n')
}

/**
 * 格式化答案为 Markdown
 */
const formatAnswerMarkdown = (exam: ExamQuestion) => {
  if (!exam?.answer) return ''
  const parts = []
  parts.push('### 答案')
  parts.push(normalizeLineBreaks(exam.answer))
  return parts.join('\n')
}

/**
 * 格式化完整内容为 Markdown（与导出格式一致）
 */
const formatFullMarkdown = (exam: ExamQuestion) => {
  const parts = []
  const questionNumber = exam.questionNumber || ''
  const tags = getExamTags(exam)
  
  // 标题行
  parts.push(`## 第${questionNumber}题 ${tags}`)
  parts.push('')
  
  // 题目内容
  if (exam?.content) {
    parts.push('### 题目')
    parts.push(normalizeLineBreaks(exam.content))
    parts.push('')
  }
  
  // 选项（仅选择题）
  if (exam?.questionType === 'CHOICE') {
    const optionsObj = parseOptions(exam)
    if (optionsObj) {
      const optionKeys = Object.keys(optionsObj).sort()
      parts.push('### 选项')
      optionKeys.forEach(key => {
        parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
      })
      parts.push('')
    }
  }
  
  // 答案
  if (exam?.answer) {
    parts.push('### 答案')
    parts.push(normalizeLineBreaks(exam.answer))
  }
  
  return parts.join('\n')
}

// 统一处理复制逻辑（仅支持 Markdown 格式）
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

// getDifficultyLabel 已从 @/constants/exam 导入

/**
 * 切换答案显示/隐藏(年份视图,指定题目ID)
 */
const toggleYearAnswer = (examId: number | string) => {
  showAnswers.value[Number(examId)] = !showAnswers.value[Number(examId)]
}


/**
 * 加载真题年份导航数据（可按分类过滤）
 * 使用轻量级 API + 缓存优化性能
 */
const loadYearList = async () => {
  const requestVersion = ++navRequestVersion
  // 检查缓存
  const cacheKey = activeCategory.value || 'all'
  if (navCache.has(cacheKey)) {
    yearList.value = navCache.get(cacheKey) ?? []
    loadingYearList.value = false
    return
  }

  loadingYearList.value = true
  try {
    // 使用轻量级导航 API
    const response = await getExamNavIndex({
      category: activeCategory.value || undefined
    })

    if (requestVersion !== navRequestVersion) return
    if (response.code === 200) {
      const exams = response.data || []

      const yearMap = new Map<number, NavQuestion[]>()
      exams.forEach(exam => {
        if (!yearMap.has(exam.year)) {
          yearMap.set(exam.year, [])
        }
        yearMap.get(exam.year)?.push({
          id: exam.id,
          title: exam.title,
          questionNumber: exam.questionNumber,
          category: exam.category
        })
      })

      const sortedYearList = Array.from(yearMap.entries())
        .map(([year, exams]) => ({
          year: year,
          exams: exams.sort((a, b) => (a.questionNumber || 0) - (b.questionNumber || 0))
        }))
        .sort((a, b) => b.year - a.year)

      // 存入缓存
      navCache.set(cacheKey, sortedYearList)
      yearList.value = sortedYearList
    } else {
      toast.error(response.message || '加载年份列表失败')
    }
  } catch (error) {
    if (requestVersion !== navRequestVersion) return
    toast.error('加载年份列表失败')
    console.error('加载年份列表失败:', error)
  } finally {
    if (requestVersion === navRequestVersion) loadingYearList.value = false
  }
}

/**
 * 加载指定年份的所有题目（可按分类过滤）
 */
const loadExamsByYear = async (year: number | null) => {
  const requestVersion = ++examsRequestVersion
  if (!year) {
    examList.value = []
    loading.value = false
    return
  }

  loading.value = true
  // 重置答案显示状态
  showAnswers.value = {}
  
  try {
    const response = await getExamByYear(year, {
      category: activeCategory.value || undefined
    })
    if (requestVersion !== examsRequestVersion) return
    if (response.code === 200) {
      examList.value = response.data || []
    } else {
      examList.value = []
      toast.error(response.message || '加载失败')
    }
  } catch (error) {
    if (requestVersion !== examsRequestVersion) return
    examList.value = []
    toast.error('加载真题失败')
    console.error('加载真题失败:', error)
  } finally {
    if (requestVersion === examsRequestVersion) loading.value = false
  }
}

/**
 * 处理年份选择
 */
const handleYearSelect = (year: number | null) => {
  activeYear.value = year
  activeExamId.value = null
  // 加载该年份的所有题目
  loadExamsByYear(year)
}

/**
 * 滚动到指定题目
 */
const scrollToExam = (examId: number | string | null | undefined) => {
  if (examId === null || examId === undefined) return
  nextTick(() => {
    const targetElement = document.getElementById(`question-${examId}`)
    if (targetElement) {
      targetElement.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
        inline: 'nearest'
      })
    }
  })
}

const scrollToExamByQuestionNumber = (questionNumber: number) => {
  const exam = examList.value.find(item => item.questionNumber === questionNumber)
  if (exam) scrollToExam(exam.id)
}

// 组件从 keep-alive 中激活时，尝试恢复滚动到上次编辑的题目
onActivated(() => {
  applyReturnScrollIfNeeded()
})

/**
 * 处理题目选择（锚点滚动）
 */
const handleExamSelect = (exam: NavQuestion) => {
  // 查找题目所属年份
  const yearData = yearList.value.find(y => 
    y.exams.some(e => e.id === exam.id)
  )
  
  if (yearData) {
    // 如果不在当前年份，先切换年份
    if (activeYear.value !== yearData.year) {
      activeYear.value = yearData.year
      loadExamsByYear(yearData.year).then(() => {
        scrollToExam(exam.id)
      })
    } else {
      // 已在当前年份，直接滚动
      scrollToExam(exam.id)
    }
    activeExamId.value = exam.id
  }
}

/**
 * 抽屉内选择题目：先收起抽屉再滚动到对应题目
 * 年份行仍保留原处理函数，便于在抽屉内继续展开该年份的题号
 */
const handleNavSheetExamSelect = (exam: NavQuestion) => {
  navSheetVisible.value = false
  handleExamSelect(exam)
}

/**
 * 处理导航栏折叠状态变化
 */
const handleNavCollapseChange = (collapsed: boolean) => {
  isNavCollapsed.value = collapsed
}

/**
 * 处理创建（打开真题编辑弹窗）
 */
const handleCreate = () => {
  editingExamId.value = null
  editDialogVisible.value = true
}

/**
 * 处理编辑（跳转编辑页面）
 */
const handleEdit = (exam: ExamQuestion) => {
  if (!exam || !exam.id) {
    return
  }

  editingExamId.value = exam.id
  editDialogVisible.value = true
}

const handleShowAdaptations = (exam: ExamQuestion) => {
  if (exam.questionNumber == null) return
  selectedAdaptationExam.value = exam
  adaptationDialogVisible.value = true
}

const handleEditSuccess = async () => {
  if (activeYear.value) {
    await loadExamsByYear(activeYear.value)
  }
  navCache.clear()
  await loadYearList()
}

/**
 * 处理删除
 */
const handleDelete = async (id: number) => {
  const confirmed = await confirm(
    '此操作将永久删除该真题，是否继续？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
  if (!confirmed) return

  try {
    const response = await deleteExam(id)
    if (response.code === 200) {
      toast.success('删除成功')
      // 重新加载年份列表
      navCache.clear()
      await loadYearList()
      // 清空当前激活的题目
      activeExamId.value = null
      // 如果当前在年份视图，重新加载该年份的题目
      if (activeYear.value) {
        await loadExamsByYear(activeYear.value)
      }
    } else {
      toast.error(response.message || '删除失败')
    }
  } catch (error) {
    toast.error('删除失败')
    console.error('删除失败:', error)
  }
}

/**
 * 处理导出命令（下拉菜单）
 */
const handleExportCommand = (command: string) => {
  switch (command) {
    case 'markdown':
      exportAsMarkdown()
      break
    case 'docx':
      exportAsDocx()
      break
    default:
      toast.warning('不支持的导出格式')
  }
}

/**
 * 导出为 Markdown 文件
 * 遵循KISS原则：复用现有格式化函数，简单拼接
 */
const exportAsMarkdown = () => {
  if (!examList.value || examList.value.length === 0) {
    toast.warning('当前年份没有题目可导出')
    return
  }

  try {
    // 构建Markdown内容
    const year = activeYear.value
    const parts = []
    
    // 标题
    parts.push(`# 408计算机统考 - ${year}年真题`)
    parts.push('')
    parts.push('---')
    parts.push('')
    
    // 遍历所有题目
    examList.value.forEach((exam, index) => {
      // 题目标题
      const questionNumber = exam.questionNumber || (index + 1)
      const questionType = exam.questionType === 'CHOICE' ? '选择题' : '主观题'
      const category = Array.isArray(exam.category) ? exam.category.join(', ') : (exam.category || '未分类')
      const difficulty = exam.difficulty ? getDifficultyLabel(exam.difficulty) : ''
      
      let header = `## 第${questionNumber}题`
      if (questionType || category || difficulty) {
        const tags = [questionType, category, difficulty].filter(Boolean)
        header += ` [${tags.join('] [')}]`
      }
      parts.push(header)
      parts.push('')
      
      // 题目内容
      const question = normalizeLineBreaks(exam.content)
      if (question) {
        parts.push('### 题目')
        parts.push(question)
        parts.push('')
      }
      
      // 选项（仅选择题）
      if (exam.questionType === 'CHOICE') {
        const options = formatOptionsMarkdown(exam)
        if (options) {
          parts.push(options)
          parts.push('')
        }
      }
      
      // 答案
      const answer = formatAnswerMarkdown(exam)
      if (answer) {
        parts.push(answer)
        parts.push('')
      }
      
      // 题目间分隔
      parts.push('---')
      parts.push('')
    })
    
    // 合并为完整的Markdown字符串
    const markdown = parts.join('\n')
    
    // 触发下载
    const filename = `408计算机统考-${year}年真题.md`
    downloadFile(markdown, filename, 'text/markdown')
    
    toast.success(`已导出 ${examList.value.length} 道题目（Markdown格式）`)
  } catch (error) {
    toast.error('导出失败，请重试')
    console.error('Markdown导出失败:', error)
  }
}

/**
 * 导出为 DOCX 文件
 * 注意：需要先安装依赖 npm install docx
 */
const exportAsDocx = async () => {
  if (!examList.value || examList.value.length === 0) {
    toast.warning('当前年份没有题目可导出')
    return
  }

  try {
    // 动态导入 docx 库
    const { Document, Paragraph, TextRun, HeadingLevel, AlignmentType, Packer } = await import('docx')
    
    const year = activeYear.value
    const children = []
    
    // 文档标题
    children.push(
      new Paragraph({
        text: `408计算机统考 - ${year}年真题`,
        heading: HeadingLevel.TITLE,
        alignment: AlignmentType.CENTER,
        spacing: { after: 400 }
      })
    )
    
    // 遍历所有题目
    examList.value.forEach((exam, index) => {
      const questionNumber = exam.questionNumber || (index + 1)
      const questionType = exam.questionType === 'CHOICE' ? '选择题' : '主观题'
      const category = Array.isArray(exam.category) ? exam.category.join(', ') : (exam.category || '未分类')
      const difficulty = exam.difficulty ? getDifficultyLabel(exam.difficulty) : ''
      
      // 题目标题
      let headerText = `第${questionNumber}题`
      if (questionType || category || difficulty) {
        const tags = [questionType, category, difficulty].filter(Boolean)
        headerText += ` [${tags.join('] [')}]`
      }
      
      children.push(
        new Paragraph({
          text: headerText,
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 400, after: 200 }
        })
      )
      
      // 题目内容
      const question = formatQuestionMarkdown(exam)
      if (question) {
        children.push(
          new Paragraph({
            text: '题目',
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 200, after: 100 }
          })
        )
        // 将Markdown文本转为段落（简单处理，保留换行）
        question.split('\n').forEach(line => {
          children.push(
            new Paragraph({
              text: line,
              spacing: { after: 100 }
            })
          )
        })
      }
      
      // 选项（仅选择题）
      if (exam.questionType === 'CHOICE') {
        const options = formatOptionsMarkdown(exam)
        if (options) {
          children.push(
            new Paragraph({
              text: '选项',
              heading: HeadingLevel.HEADING_3,
              spacing: { before: 200, after: 100 }
            })
          )
          options.split('\n').forEach(line => {
            children.push(
              new Paragraph({
                text: line,
                spacing: { after: 100 }
              })
            )
          })
        }
      }
      
      // 答案
      const answer = formatAnswerMarkdown(exam)
      if (answer) {
        children.push(
          new Paragraph({
            text: '答案',
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 200, after: 100 }
          })
        )
        answer.split('\n').forEach(line => {
          children.push(
            new Paragraph({
              text: line,
              spacing: { after: 100 }
            })
          )
        })
      }
      
      // 题目间分隔线（空段落）
      children.push(
        new Paragraph({
          text: '',
          spacing: { after: 400 }
        })
      )
    })
    
    // 创建文档
    const doc = new Document({
      sections: [{
        properties: {},
        children: children
      }]
    })
    
    // 生成 Blob 并触发下载
    const blob = await Packer.toBlob(doc)
    const filename = `408计算机统考-${year}年真题.docx`
    
    // 创建下载链接
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    toast.success(`已导出 ${examList.value.length} 道题目（Word格式）`)
  } catch (error) {
    if (errorMessage(error, '').includes('Cannot find module')) {
      toast.error('请先安装 docx 依赖：npm install docx')
    } else {
      toast.error('DOCX导出失败，请重试')
    }
    console.error('DOCX导出失败:', error)
  }
}

/**
 * 下载文件工具函数
 * @param {string} content - 文件内容
 * @param {string} filename - 文件名
 * @param {string} mimeType - MIME类型
 */
const downloadFile = (content: BlobPart, filename: string, mimeType: string) => {
  // 创建Blob对象
  const blob = new Blob([content], { type: mimeType })
  
  // 创建下载链接
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  
  // 触发下载
  document.body.appendChild(link)
  link.click()
  
  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// 监听路由参数变化（年份）
watch(
  () => route.params.year,
  (newYear) => {
    if (newYear) {
      const year = parseInt(queryString(newYear))
      activeYear.value = year
      handleYearSelect(year)
    }
  }
)

// 监听路由查询参数变化（分类），重新加载年份树和当前视图
watch(
  () => route.query.category,
  (newCategory, oldCategory) => {
    // 如果分类变化，清除缓存
    if (newCategory !== oldCategory) {
      navCache.clear()
    }
    activeCategory.value = queryString(newCategory)

    // 使用缓存或重新加载
    loadYearList()

    // 如果当前在年份视图，刷新数据
    if (activeYear.value) {
      loadExamsByYear(activeYear.value)
    }
  }
)

// 组件挂载时加载数据（优化：使用 Promise.all 并行加载）
onMounted(async () => {
  // 先尝试从缓存加载年份列表
  await loadYearList()

  // 如果路由有 year 参数，加载对应年份的真题
  if (route.params.year) {
    const year = parseInt(queryString(route.params.year))
    activeYear.value = year
    await loadExamsByYear(year)
  }
})
</script>
