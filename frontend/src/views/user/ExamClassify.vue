<template>
  <div class="exam-classify-page-container">
    <div class="main-content-wrapper">
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
      <div class="content-area">
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <div class="header-left">
                <h2>{{ currentTitle }}</h2>
                <el-tag v-if="displayTotal > 0" type="info" size="small">共 {{ displayTotal }} 题</el-tag>
              </div>
              <div class="header-actions" v-if="activeSubjectId">
                <el-select 
                  v-model="filterQuestionType" 
                  size="small" 
                  style="width: 100px; margin-right: 8px"
                >
                  <el-option label="全部题型" value="ALL" />
                  <el-option label="选择题" value="CHOICE" />
                  <el-option label="主观题" value="ESSAY" />
                </el-select>


                <el-dropdown trigger="click" @command="handleExportCommand">
                  <CustomButton
                    type="success"
                    :icon="Download"
                    size="small"
                  >
                    导出科目
                  </CustomButton>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="docx">
                        <el-icon><Document /></el-icon>
                        导出为 Word 文档 (.docx)
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>

          <div class="questions-pane">
            <div v-loading="questionsLoading" class="question-list-container">
              <!-- 普通分组列表 -->
              <div v-if="groupedQuestions.length > 0" class="exam-list-grouped">
                <template v-for="group in groupedQuestions" :key="group.category">
                  <!-- 分组头 -->
                  <div class="category-group-header">
                    <h3 class="category-title">{{ group.category }}</h3>
                    <el-tag size="small" type="info">{{ group.items.length }} 题</el-tag>
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
                    @delete="(id) => handleDelete(id)"
                    @toggle-answer="toggleAnswer(exam.id)"
                  />
                </template>
              </div>
              <el-empty 
                v-if="groupedQuestions.length === 0"
                :description="activeSubjectId ? '该科目暂无真题' : '请选择左侧科目'" 
              />
              
              <!-- 加载更多按钮 -->
              <div class="load-more-container" v-if="hasMore">
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
        </el-card>

        <ExamEditDialog
          v-if="isAdmin"
          v-model:visible="editDialogVisible"
          :exam-id="editingExamId"
          @success="handleEditSuccess"
        />

        <el-backtop
          :right="32"
          :bottom="32"
        >
          <div class="back-top-inner">
            <el-icon><ArrowUp /></el-icon>
          </div>
        </el-backtop>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 真题分类浏览页面 (重构版)
 * 功能：按科目聚合展示真题，支持分类与年份筛选
 * 设计哲学：KISS (专注真题浏览), SOLID (单一职责)
 */
import { ref, onMounted, computed, nextTick, onActivated } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Document, Download,
  ArrowUp
} from '@element-plus/icons-vue'
import { getEnabledSubjects } from '@/api/subject'
import { getExamList, deleteExam, getExamDetail } from '@/api/exam'
import { getEnabledCategoryTreeBySubject } from '@/api/category'
import { useAuthStore } from '@/stores/auth'
import CustomButton from '@/components/basic/CustomButton.vue'
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

// 题目编辑弹窗状态
const editDialogVisible = ref(false)
const editingExamId = ref(null)

// Data
const subjects = ref([])
const subjectCategories = ref({})
const activeSubjectId = ref(null)
const activeSubjectName = ref('')
const expandedSubjectId = ref(null)

// Pagination State
const currentPage = ref(1)
const hasMore = ref(false)
const pageSize = ref(50) // Reduce batch size for faster initial render

// Filter Data
const filterCategory = ref('')
// 题型筛选：ALL=全部，CHOICE=仅选择题，ESSAY=仅主观题（视为非CHOICE的题型）
const filterQuestionType = ref('ALL')

// Questions Data
const questionList = ref([])
const total = ref(0)
const showAnswers = ref({}) // map: { examId: boolean }



// Computed
const currentTitle = computed(() => {
  if (activeSubjectName.value && filterCategory.value) {
    return `${activeSubjectName.value} · ${filterCategory.value} · 真题`
  }
  return activeSubjectName.value ? `${activeSubjectName.value} · 真题` : '真题分类浏览'
})

const groupedQuestions = computed(() => {
  let list = questionList.value || []
  if (!list.length) return []

  // 先按题型做前端过滤
  if (filterQuestionType.value === 'CHOICE') {
    list = list.filter(exam => exam.questionType === 'CHOICE')
  } else if (filterQuestionType.value === 'ESSAY') {
    list = list.filter(exam => exam.questionType !== 'CHOICE')
  }

  const groupsMap = new Map()

  list.forEach((exam) => {
    const categories = Array.isArray(exam.category) && exam.category.length
      ? exam.category
      : ['未分类']

    categories.forEach((cat) => {
      if (filterCategory.value && cat !== filterCategory.value) return
      if (!groupsMap.has(cat)) {
        groupsMap.set(cat, [])
      }
      groupsMap.get(cat).push(exam)
    })
  })

  // 构建分类名称到 orderNum 的映射表（直接在 computed 内访问响应式数据）
  const orderNumMap = new Map()
  const currentCategories = subjectCategories.value[activeSubjectId.value]
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

    const info = JSON.parse(raw)
    if (info.source === 'classify' && info.examId) {
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
      subjects.value = res.data || []
      
      // 检查URL参数，支持从收藏页面跳转
      const subjectFromRoute = route.query.subject
      const categoryFromRoute = route.query.category
      
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
    }
  } catch (e) {
    console.error('加载科目失败:', e)
  } finally {
    loadingSubjects.value = false
  }
}

// 根据题目ID滚动到对应题目卡片
const scrollToExamById = (examId) => {
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

const loadCategoriesForSubject = async (subjectId) => {
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
const handleSubjectSelect = async (subject) => {
  if (activeSubjectId.value === subject.id) return

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
const toggleSubjectExpand = async (subject) => {
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

const handleCategorySelect = (subject, category) => {
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
const toggleAnswer = (examId) => {
  showAnswers.value[examId] = !showAnswers.value[examId]
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
const normalizeLineBreaks = (text) => {
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

const formatQuestionMarkdown = (exam) => {
  if (!exam?.content) return ''
  return normalizeLineBreaks(exam.content)
}

const formatOptionsMarkdown = (exam) => {
  if (exam?.questionType !== 'CHOICE' || !exam?.options) {
    return ''
  }
  let optionsObj = {}
  try {
    optionsObj = JSON.parse(exam.options)
  } catch (e) {
    console.error('解析选项失败:', e)
    return ''
  }
  const optionKeys = Object.keys(optionsObj).sort()
  const optionLines = optionKeys.map(key => `${key}. ${normalizeLineBreaks(optionsObj[key])}`)
  return optionLines.join('\n')
}

const formatAnswerMarkdown = (exam) => {
  if (!exam?.answer) return ''
  return normalizeLineBreaks(exam.answer)
}

const formatFullMarkdown = (exam) => {
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

const handleCopy = async (command, exam) => {
  let text = ''
  let message = ''

  try {
    switch (command) {
      case 'question':
        text = formatQuestionMarkdown(exam)
        message = '题目已复制到剪贴板'
        break
      case 'options':
        text = formatOptionsMarkdown(exam)
        message = '选项已复制到剪贴板'
        break
      case 'answer':
        text = formatAnswerMarkdown(exam)
        message = '答案已复制到剪贴板'
        break
      case 'all':
        text = formatFullMarkdown(exam)
        message = '完整内容已复制到剪贴板'
        break
      default:
        return
    }

    if (!text) {
      ElMessage.warning('没有可复制的内容')
      return
    }

    await copyToClipboard(text)
    ElMessage.success(message)
  } catch (error) {
    ElMessage.error('复制失败，请重试')
  }
}

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
  // Don't reset showAnswers on load more, only on reset
  if (isReset) {
    showAnswers.value = {}
  }

  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      subjectId: activeSubjectId.value,
      sortField: 'year',
      sortOrder: 'asc',
      category: filterCategory.value || undefined // Server-side filtering
    }

    const res = await getExamList(params)
    if (res.code === 200) {
      const pageData = res.data?.data || []
      const serverTotal = res.data?.total || 0
      
      if (isReset) {
        questionList.value = pageData
      } else {
        // Append new data
        questionList.value.push(...pageData)
      }

      total.value = serverTotal
      
      // Update hasMore status
      hasMore.value = questionList.value.length < serverTotal
      
      if (pageData.length > 0) {
        currentPage.value++
      }
    } else {
      hasMore.value = false
    }
  } catch (e) {
    console.error('加载真题失败:', e)
    if (isReset) {
      questionList.value = []
      total.value = 0
    }
  } finally {
    questionsLoading.value = false
  }
}

/**
 * 统一导出处理函数
 * 遵循KISS原则：直接调用后端导出API
 */
const handleExportCommand = async (format) => {
  if (!activeSubjectId.value) {
    ElMessage.warning('请先选择科目')
    return
  }

  const formatMap = {
    'markdown': { ext: 'md', label: 'Markdown' },
    'docx': { ext: 'docx', label: 'Word' }
  }

  const config = formatMap[format]
  if (!config) {
    ElMessage.warning('不支持的导出格式')
    return
  }

  try {
    const subjectName = activeSubjectName.value
    const filename = `408-${subjectName}-全部真题.${config.ext}`
    
    // 直接通过URL下载（后端返回文件流）
    const url = `/api/exam/export?subjectId=${activeSubjectId.value}&format=${format}`
    
    // 创建下载链接
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success(`${config.label} 导出已开始`)
  } catch (error) {
    ElMessage.error('导出失败，请重试')
    console.error(`${config.label}导出失败:`, error)
  }
}

const handleEdit = (exam) => {
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

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm(
      '此操作将永久删除该真题，是否继续？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await deleteExam(id)
    if (response.code === 200) {
      ElMessage.success('删除成功')
      await loadQuestions(true)
    } else {
      ElMessage.error(response.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error('删除失败:', error)
    }
  }
}

</script>

<style lang="scss" scoped>
.exam-classify-page-container {
  height: calc(100vh - #{$nav-height});
  overflow: hidden;
  @include flex-column;
  background-color: $color-primary; // 使用主题米色背景
}

.main-content-wrapper {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}



/* 右侧内容区 */
.content-area {
  flex: 1;
  width: 0; // 防止 Flex 子元素溢出
  padding: 0;
  overflow-y: auto; // 全局滚动
  @include scrollbar;
  background-color: $color-primary; // 使用主题米色背景
}

.content-card {
  min-height: calc(100vh - #{$nav-height} - 40px);
  box-shadow: none; // 移除阴影，与背景融合
  background-color: $color-primary; // 使用主题米色背景
  border: none; // 移除边框，与背景融合
  
  // 给卡片内容添加内边距（对齐 ExamList.vue）
  :deep(.el-card__body) {
    padding: $spacing-md;
  }
  
  :deep(.el-card__header) {
    padding: $spacing-md;
    padding-bottom: $spacing-sm; // 减少 header 下方间隔
    border-bottom: 1px solid $color-border-light;
    background-color: transparent;
  }
}

.card-header {
  @include flex-between;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    
    h2 {
      margin: 0;
      font-size: $font-size-xl + 2px;
      color: $color-text-primary;
    }
  }
  
  .header-actions {
    display: flex;
    gap: $spacing-xs;
  }
}


.questions-pane {
  padding: 0;
}

// 分组列表样式（对齐 ExamList.vue 的 .exam-list-year）
.exam-list-grouped {
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
  width: 100%;
  max-width: 80%;
}



.category-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm 0;
  margin-top: $spacing-md;
  margin-bottom: $spacing-sm;
  border-bottom: 1px solid $color-border-light;
  
  &:first-child {
    margin-top: 0;
  }
}

.category-title {
  margin: 0;
  font-size: $font-size-large;
  font-weight: 600;
  color: $color-text-primary;
}



.load-more-container {
  display: flex;
  justify-content: center;
  padding: $spacing-lg 0;
  margin-top: $spacing-md;
}

.back-top-inner {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background-color: $color-accent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

/* 响应式布局 */
@include mobile {
  .exam-classify-page-container {
    padding: $spacing-sm;
  }
  
  .main-content-wrapper {
    flex-direction: column;
    align-items: stretch;
  }

  .content-area {
    width: 100%; // 移动端恢复宽度
  }
  
  .exam-list-grouped {
    max-width: 100%; // 移动端取消宽度限制
  }
  
  .exam-item-card {
    padding: $spacing-sm;
  }
}
</style>
