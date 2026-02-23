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
                <Tag v-if="displayTotal > 0" variant="info">共 {{ displayTotal }} 题</Tag>
              </div>
              <div class="flex gap-2" v-if="activeSubjectId">
                <Select
                  v-model="filterQuestionType"
                  size="sm"
                  class="w-[100px] mr-2"
                  :options="questionTypeOptions"
                />
              </div>
            </div>

          <div v-if="questionsLoading" class="flex items-center justify-center py-12">
            <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-[#8B6F47] text-2xl" />
          </div>

          <!-- 普通分组列表 -->
          <div v-if="groupedQuestions.length > 0" class="flex flex-col gap-6 max-w-[80%]">
            <template v-for="group in groupedQuestions" :key="group.category">
              <!-- 分组头 -->
              <div class="flex items-center justify-between py-2 mt-4 mb-2 border-b border-[#dfe2e5]">
                <h3 class="m-0 text-[#333] font-semibold text-lg">{{ group.category }}</h3>
                <Tag variant="info">{{ group.items.length }} 题</Tag>
              </div>
              <!-- 题目卡片 -->
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
              />
            </template>
          </div>

          <Empty
            v-if="groupedQuestions.length === 0"
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
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 模拟题分类浏览页面
 * 功能：按科目聚合展示模拟题，支持分类筛选
 * 设计哲学：KISS (专注模拟题浏览), SOLID (单一职责)
 */
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { getEnabledSubjects } from '@/api/subject'
import { getMockQuestions, deleteMockQuestion, getMockSubjectStats } from '@/api/mock'
import { getEnabledCategoryTreeBySubjectWithStats } from '@/api/category'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import Tag from '@/components/basic/Tag.vue'
import Select from '@/components/basic/Select.vue'
import Empty from '@/components/basic/Empty.vue'
import BackTop from '@/components/basic/BackTop.vue'
import SubjectSidebar from '@/components/business/SubjectSidebar.vue'
import MockEntryCard from '@/components/business/MockEntryCard.vue'
import MockEditDialog from '@/components/business/MockEditDialog.vue'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'

const route = useRoute()
const authStore = useAuthStore()
const { showToast } = useToast()

// 计算是否为管理员
const isAdmin = computed(() => authStore.isAdmin())

// 编辑弹窗状态
const editDialogVisible = ref(false)
const editingMockId = ref(null)
const editingMockData = ref(null)  // 编辑时传递的完整数据（避免重复请求API）

// UI State
const isNavCollapsed = ref(false)
const loadingSubjects = ref(false)
const questionsLoading = ref(false)

// Data
const subjects = ref([])
const subjectCategories = ref({})
const activeSubjectId = ref(null)
const activeSubjectName = ref('')
const expandedSubjectId = ref(null)

// Pagination State
const currentPage = ref(1)
const hasMore = ref(false)
const pageSize = ref(50)

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
const questionList = ref([])
const total = ref(0)
const showAnswers = ref({})



// Computed
const currentTitle = computed(() => {
  if (activeSubjectName.value && filterCategory.value) {
    return `${activeSubjectName.value} · ${filterCategory.value} · 模拟题`
  }
  return activeSubjectName.value ? `${activeSubjectName.value} · 模拟题` : '模拟题分类浏览'
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

  const groupsMap = new Map()

  list.forEach((question) => {
    const categories = Array.isArray(question.category) && question.category.length
      ? question.category
      : ['未分类']

    categories.forEach((cat) => {
      if (filterCategory.value && cat !== filterCategory.value) return
      if (!groupsMap.has(cat)) {
        groupsMap.set(cat, [])
      }
      groupsMap.get(cat).push(question)
    })
  })

  return Array.from(groupsMap.entries())
    .map(([category, items]) => ({ category, items }))
    .sort((a, b) => a.category.localeCompare(b.category, 'zh-CN'))
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
      subjects.value = res.data || []
      
      // 加载模拟题的科目统计，覆盖默认的真题统计
      try {
        const statsRes = await getMockSubjectStats()
        if (statsRes.code === 200 && statsRes.data) {
          const statsMap = {}
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
      const subjectFromRoute = route.query.subject
      const categoryFromRoute = route.query.category
      
      let initialSubject = null
      
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
    }
  } catch (e) {
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
  
  // 等待DOM渲染完成
  await nextTick()
  // 给予数据DOM渲染的额外时间
  await new Promise(resolve => setTimeout(resolve, 300))
  
  const elementId = hash.slice(1) // 移除#号
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
}

const loadCategoriesForSubject = async (subjectId) => {
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
const handleSubjectSelect = async (subject) => {
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

const toggleSubjectExpand = async (subject) => {
  const id = subject.id

  if (expandedSubjectId.value === id) {
    expandedSubjectId.value = null
    return
  }

  await loadCategoriesForSubject(id)
  expandedSubjectId.value = id
}

const handleCategorySelect = (subject, category) => {
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



const toggleAnswer = (id) => {
  showAnswers.value[id] = !showAnswers.value[id]
}

// 难度辅助函数已从 @/constants/exam 导入

// Core: Load Questions
const loadQuestions = async (isReset = false) => {
  if (!activeSubjectId.value) {
    questionList.value = []
    total.value = 0
    return
  }

  if (isReset) {
    currentPage.value = 1
    questionList.value = []
    hasMore.value = true
  }

  questionsLoading.value = true
  if (isReset) {
    showAnswers.value = {}
  }

  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      subjectId: activeSubjectId.value,
      category: filterCategory.value || undefined
    }

    const res = await getMockQuestions(params)
    if (res.code === 200) {
      const pageData = res.data?.data || []
      const serverTotal = res.data?.total || 0
      
      if (isReset) {
        questionList.value = pageData
      } else {
        questionList.value.push(...pageData)
      }

      total.value = serverTotal
      hasMore.value = questionList.value.length < serverTotal
      
      if (pageData.length > 0) {
        currentPage.value++
      }
    } else {
      hasMore.value = false
    }
  } catch (e) {
    console.error('加载模拟题失败:', e)
    if (isReset) {
      questionList.value = []
      total.value = 0
    }
  } finally {
    questionsLoading.value = false
  }
}

// 复制工具函数
const copyToClipboard = async (text) => {
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
const normalizeLineBreaks = (text) => {
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
const parseOptions = (mock) => {
  if (mock?.questionType !== 'CHOICE' || !mock?.options) return null
  try {
    return JSON.parse(mock.options)
  } catch (e) {
    return null
  }
}

/**
 * 获取题目元信息标签
 */
const getMockTags = (mock) => {
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
const getMockTitleLine = (mock) => {
  const parts = []
  if (mock?.title) parts.push(mock.title)
  if (mock?.questionNumber) parts.push(`第${mock.questionNumber}题`)
  return parts.join(' · ')
}

const formatQuestionMarkdown = (mock) => {
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

const formatOptionsMarkdown = (mock) => {
  const optionsObj = parseOptions(mock)
  if (!optionsObj) return ''
  const parts = ['### 选项']
  Object.keys(optionsObj).sort().forEach(key => {
    parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
  })
  return parts.join('\n')
}

const formatAnswerMarkdown = (mock) => {
  if (!mock?.answer) return ''
  return ['### 答案', normalizeLineBreaks(mock.answer)].join('\n')
}

const formatFullMarkdown = (mock) => {
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

// ==================== 纯文本格式化函数 ====================

const formatQuestionText = (mock) => {
  if (!mock?.content) return ''
  const questionType = mock.questionType === 'CHOICE' ? '选择题' : '主观题'
  const category = Array.isArray(mock.category) ? mock.category.join(', ') : (mock.category || '')
  const titleLine = getMockTitleLine(mock)
  
  const parts = []
  // 标题行: 包含标题和题号
  if (titleLine) {
    parts.push(`${titleLine} (${questionType}${category ? ' - ' + category : ''})`)
  } else {
    parts.push(`模拟题 (${questionType}${category ? ' - ' + category : ''})`)
  }
  parts.push('')
  parts.push('【题目】')
  parts.push(normalizeLineBreaks(mock.content))
  return parts.join('\n')
}

const formatOptionsText = (mock) => {
  const optionsObj = parseOptions(mock)
  if (!optionsObj) return ''
  const parts = ['【选项】']
  Object.keys(optionsObj).sort().forEach(key => {
    parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
  })
  return parts.join('\n')
}

const formatAnswerText = (mock) => {
  if (!mock?.answer) return ''
  return ['【答案】', normalizeLineBreaks(mock.answer)].join('\n')
}

const formatFullText = (mock) => {
  const questionType = mock.questionType === 'CHOICE' ? '选择题' : '主观题'
  const category = Array.isArray(mock.category) ? mock.category.join(', ') : (mock.category || '')
  const titleLine = getMockTitleLine(mock)
  
  const parts = []
  // 标题行: 包含标题和题号
  if (titleLine) {
    parts.push(`${titleLine} (${questionType}${category ? ' - ' + category : ''})`)
  } else {
    parts.push(`模拟题 (${questionType}${category ? ' - ' + category : ''})`)
  }
  parts.push('')
  
  if (mock?.content) {
    parts.push('【题目】')
    parts.push(normalizeLineBreaks(mock.content))
    parts.push('')
  }
  
  if (mock?.questionType === 'CHOICE') {
    const optionsObj = parseOptions(mock)
    if (optionsObj) {
      parts.push('【选项】')
      Object.keys(optionsObj).sort().forEach(key => {
        parts.push(`${key}. ${normalizeLineBreaks(optionsObj[key])}`)
      })
      parts.push('')
    }
  }
  
  if (mock?.answer) {
    parts.push('【答案】')
    parts.push(normalizeLineBreaks(mock.answer))
  }
  
  return parts.join('\n')
}

// 统一处理复制逻辑（支持 md-* 和 text-* 两种格式）
const handleCopy = async (command, mock) => {
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
      // 纯文本格式
      case 'text-question':
        text = formatQuestionText(mock)
        message = '题目已复制 (纯文本)'
        break
      case 'text-options':
        text = formatOptionsText(mock)
        message = '选项已复制 (纯文本)'
        break
      case 'text-answer':
        text = formatAnswerText(mock)
        message = '答案已复制 (纯文本)'
        break
      case 'text-all':
        text = formatFullText(mock)
        message = '完整内容已复制 (纯文本)'
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

const handleEdit = (mock) => {
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

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm(
      '此操作将永久删除该模拟题，是否继续？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await deleteMockQuestion(id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      await loadQuestions(true)
    } else {
      showToast(response.message || '删除失败', 'error')
    }
  } catch (error) {
    if (error !== 'cancel') {
      // 错误消息已由axios拦截器统一处理
      console.error('删除失败:', error)
    }
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
  background-color: #FBF7F2;
}

/* 从管理页面"查看"按钮跳转过来时的高亮效果 */
:deep(.mock-entry-card.highlight-card) {
  animation: highlightPulse 2s ease-out;
  border-color: #8B6F47;
  box-shadow: 0 0 20px rgba(139, 111, 71, 0.3);
}

/* 高亮脉冲动画 */
@keyframes highlightPulse {
  0%, 100% {
    box-shadow: 0 0 20px rgba(139, 111, 71, 0.3);
  }
  50% {
    box-shadow: 0 0 30px rgba(139, 111, 71, 0.5);
  }
}

/* 响应式布局 */
@media (max-width: 768px) {
  .content-area {
    width: 100%;
  }
}
</style>
