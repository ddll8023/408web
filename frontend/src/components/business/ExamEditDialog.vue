<!-- 真题编辑弹窗：表单在桌面与移动视口内自适应。 -->
<template>
  <ResponsiveDialog
    v-model:visible="dialogVisible"
    :title="isEditMode ? '编辑真题' : '新增真题'"
    width="1200px"
    max-width="1600px"
  >
    <div class="edit-form">
        <QuestionJsonImportPanel
          v-model="jsonInput"
          v-model:visible="jsonImportVisible"
          show-content-only
          show-example
          @paste="handlePasteJson"
          @parse="handleParseJson"
          @parse-content="handleParseContentJson"
          @clear="handleClearJson"
          @show-example="() => showJsonExample('exam')"
        />

        <!-- 表单 -->
        <div class="edit-form" :class="{ 'relative': loading }" :aria-busy="loading">
          <div v-if="loading" class="edit-loading" role="status" aria-live="polite">
            <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-accent" aria-hidden="true" />
            <span>正在加载...</span>
          </div>

          <!-- 元信息集中排列，题干与解析保留整行编辑宽度。 -->
          <section class="edit-section">
            <div class="edit-section-heading">
              <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'cog']" aria-hidden="true" />基础信息</h4>
              <span class="edit-hint m-0">标有 * 的字段为必填</span>
            </div>
            <div class="edit-grid edit-grid--four">
              <div>
                <FormLabel label="题型" required for-id="exam-question-type" />
                <Select
                  id="exam-question-type"
                  v-model="form.questionType"
                  :options="questionTypeOptions"
                  placeholder="请选择题型"
                  @change="handleQuestionTypeChange"
                />
              </div>
              <div>
                <FormLabel label="年份" required for-id="exam-year" />
                <Select
                  id="exam-year"
                  v-model="form.year"
                  :options="yearOptions"
                  placeholder="请选择年份"
                />
              </div>
              <div>
                <FormLabel label="科目" required for-id="exam-subject" />
                <Select
                  id="exam-subject"
                  v-model="form.subjectId"
                  :options="subjectOptions"
                  placeholder="请选择科目"
                  @change="handleSubjectChange"
                />
              </div>
              <div>
                <FormLabel label="题号" for-id="exam-question-number" hint="可选" />
                <input
                  id="exam-question-number"
                  v-model.number="form.questionNumber"
                  type="number"
                  min="1"
                  step="1"
                  class="edit-input"
                  placeholder="请输入题号（可选）"
                />
              </div>
            </div>
            <div class="edit-grid mt-4">
            <div>
              <FormLabel label="标题" for-id="exam-title" />
              <input
                id="exam-title"
                v-model="form.title"
                type="text"
                maxlength="200"
                class="edit-input"
                placeholder="请输入题目标题（可选，最多200字符）"
              />
              <div class="edit-field-meta"><span class="edit-count">{{ form.title?.length || 0 }}/200</span></div>
            </div>
            <div>
              <FormLabel label="难度" for-id="exam-difficulty" />
              <Select
                id="exam-difficulty"
                v-model="form.difficulty"
                :options="difficultyOptions"
                placeholder="请选择难度（可选）"
              />
            </div>
            <div class="edit-span-full">
              <FormLabel label="分类" for-id="exam-category" />
              <!-- 多选级联选择器 -->
              <MultiSelectCascader
                id="exam-category"
                v-model="form.category"
                :options="categoryTreeOptions"
                placeholder="请选择分类（支持多个）"
                aria-label="分类"
                :disabled="!form.subjectId"
              />
            </div>
            </div>
          </section>

          <!-- 选择题表单 -->
          <section class="edit-section">
            <div class="edit-section-heading">
              <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'file-lines']" aria-hidden="true" />题目内容</h4>
              <span class="edit-hint m-0">支持 Markdown、公式和图片</span>
            </div>
            <FormLabel :label="form.questionType === 'CHOICE' ? '题干' : '题目内容'" required :for-id="form.questionType === 'CHOICE' ? 'exam-choice-content' : 'exam-essay-content'" />
            <MarkdownEditor :id="form.questionType === 'CHOICE' ? 'exam-choice-content' : 'exam-essay-content'" aria-label="题干" v-model="form.content" height="400px" placeholder="请输入题目内容（支持 Markdown、公式和图片）..." />
            <div v-if="form.questionType === 'CHOICE'" class="edit-options-grid mt-4">
              <div class="edit-option">
                <FormLabel label="选项 A" required for-id="exam-option-a" />
                <MarkdownEditor id="exam-option-a" content-role="option" aria-label="选项 A" v-model="form.optionA" height="140px" placeholder="请输入选项 A 的内容..." />
              </div>
              <div class="edit-option">
                <FormLabel label="选项 B" required for-id="exam-option-b" />
                <MarkdownEditor id="exam-option-b" content-role="option" aria-label="选项 B" v-model="form.optionB" height="140px" placeholder="请输入选项 B 的内容..." />
              </div>
              <div class="edit-option">
                <FormLabel label="选项 C" required for-id="exam-option-c" />
                <MarkdownEditor id="exam-option-c" content-role="option" aria-label="选项 C" v-model="form.optionC" height="140px" placeholder="请输入选项 C 的内容..." />
              </div>
              <div class="edit-option">
                <FormLabel label="选项 D" required for-id="exam-option-d" />
                <MarkdownEditor id="exam-option-d" content-role="option" aria-label="选项 D" v-model="form.optionD" height="140px" placeholder="请输入选项 D 的内容..." />
              </div>
            </div>
          </section>
          <section class="edit-section">
            <div class="edit-section-heading">
              <h4 class="edit-section-title">答案解析</h4>
              <CustomButton v-if="isEditMode && authStore.isAdmin()" size="sm" type="text-primary" :disabled="loading || saving" @click="aiAnswerVisible = true">AI 生成答案</CustomButton>
              <span class="edit-hint m-0">可选</span>
            </div>
            <MarkdownEditor :id="form.questionType === 'CHOICE' ? 'exam-choice-answer' : 'exam-essay-answer'" aria-label="答案解析" v-model="form.answer" height="400px" placeholder="请输入答案与解析..." />
          </section>
        </div>
      </div>

    <AiAnswerGenerationDialog
      v-if="props.visible && aiAnswerVisible && props.examId"
      v-model:visible="aiAnswerVisible"
      question-kind="exam"
      :question-id="Number(props.examId)"
      :source="aiAnswerSource"
      draft
      @adopt="applyGeneratedAnswer"
    />

    <template #footer>
      <div class="edit-footer">
        <span class="edit-hint m-0">保存前请核对题干、选项与解析</span>
        <div class="edit-footer-actions">
          <CustomButton @click="handleCancel">取消</CustomButton>
          <CustomButton type="primary" :loading="saving" @click="handleSubmit">
            <font-awesome-icon :icon="isEditMode ? ['fas', 'save'] : ['fas', 'plus']" />
            {{ isEditMode ? '保存修改' : '创建真题' }}
          </CustomButton>
        </div>
      </div>
    </template>
  </ResponsiveDialog>
</template>

<script setup lang="ts">
import type { ExamCreateRequest, ExamQuestion } from '@/types'
import type { PropType } from 'vue'
import type { AiAnswerCandidate } from '@/types/aiAnswer'
import { answerSourceFromForm, answerSourceKey } from '@/utils/aiAnswer'
import { useAuthStore } from '@/stores/auth'
import AiAnswerGenerationDialog from '@/components/business/AiAnswerGenerationDialog.vue'
/**
 * ExamEditDialog 真题编辑弹窗组件
 * 功能：创建和编辑考研真题题目，支持选择题和主观题两种题型
 * 遵循原则：KISS（保持简洁）、YAGNI（不会需要）
 * 依赖：MarkdownEditor、CustomButton、MultiSelectCascader 基础组件
 * 依赖：useQuestionForm、useJsonImport、useToast composables
 */
import { computed, watch, ref } from 'vue'
import { getExamDetail, updateExam, createExam } from '@/api/exam'
import { useQuestionForm } from '@/composables/useQuestionForm'
import { useJsonImport } from '@/composables/useJsonImport'
import { useToast } from '@/composables/useToast'
import MarkdownEditor from '@/components/basic/MarkdownEditor.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import MultiSelectCascader from '@/components/basic/MultiSelectCascader.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import QuestionJsonImportPanel from '@/components/business/QuestionJsonImportPanel.vue'
import Select from '@/components/basic/Select.vue'
import '@/styles/edit-form.css'

const props = defineProps({
  visible: { type: Boolean, default: false },
  examId: { type: [Number, String] as PropType<number | string | null>, default: null },
  answerCandidate: { type: Object as PropType<AiAnswerCandidate | null>, default: null }
})

const emit = defineEmits<{ 'update:visible': [visible: boolean]; success: [question: ExamQuestion | null] }>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

// 是否为编辑模式（有ID为编辑，无ID为新建）
const isEditMode = computed(() => !!props.examId)

// 使用公共 composable
const {
  form, loading, saving,
  subjectOptions, categoryTreeOptions,
  loadSubjectOptions,
  handleSubjectChange, handleQuestionTypeChange,
  fillFormFromData, fillContentFromData
} = useQuestionForm({
  extraFields: { year: new Date().getFullYear(), questionNumber: null }
})

const { showToast } = useToast()
const authStore = useAuthStore()
const aiAnswerVisible = ref(false)
const aiAnswerSource = computed(() => answerSourceFromForm(form))

/** 只填答案；题面或原答案在生成后变化时拒绝覆盖。 */
function applyGeneratedAnswer(candidate: AiAnswerCandidate): void {
  if (!props.visible || !authStore.isAdmin() || candidate.questionKind !== 'exam'
    || candidate.questionId !== Number(props.examId)) return
  if (answerSourceKey(candidate.source) !== answerSourceKey(aiAnswerSource.value)) {
    showToast('题面或原答案已变化，未填入新答案，请重新生成', 'warning')
    return
  }
  form.answer = candidate.answer
  showToast('新答案已填入，点击保存修改后才会更新题库', 'success')
}

const {
  jsonInput,
  parseJsonWithRelaxedSupport, handlePasteJson,
  handleClearJson, showJsonExample
} = useJsonImport()

// JSON 导入区域显示状态
const jsonImportVisible = ref(false)

// 年份选项：从 2009 年生成到当前年份，避免年份列表过期
const firstExamYear = 2009
const yearOptions = ref<number[]>([])
const refreshYearOptions = () => {
  const lastExamYear = Math.max(new Date().getFullYear(), firstExamYear)
  yearOptions.value = Array.from(
    { length: lastExamYear - firstExamYear + 1 },
    (_, i) => firstExamYear + i
  )
}
refreshYearOptions()

// 题型选项
const questionTypeOptions = [
  { label: '选择题', value: 'CHOICE' },
  { label: '主观题', value: 'ESSAY' }
]

// 难度选项
const difficultyOptions = [
  { label: '简单', value: 'EASY' },
  { label: '中等', value: 'MEDIUM' },
  { label: '困难', value: 'HARD' }
]

// 表单验证规则（简化版：手动验证）
const validateForm = () => {
  if (!form.questionType) {
    showToast('请选择题型', 'warning')
    return false
  }
  if (!form.year) {
    showToast('请选择年份', 'warning')
    return false
  }
  if (!form.content) {
    showToast('请输入题目内容', 'warning')
    return false
  }
  if (form.questionType === 'CHOICE') {
    if (!form.optionA || !form.optionB || !form.optionC || !form.optionD) {
      showToast('请完善选择题选项', 'warning')
      return false
    }
  }
  return true
}

// 加载真题数据
const loadExamData = async (id: number | string | null) => {
  if (!id) return
  loading.value = true
  try {
    const response = await getExamDetail(Number(id))
    if (response.code === 200) {
      const data = response.data
      await fillFormFromData(data)
      form.year = data.year
      form.questionNumber = data.questionNumber ?? null
      if (props.answerCandidate) applyGeneratedAnswer(props.answerCandidate)
    } else {
      showToast(response.message || '加载失败', 'error')
    }
  } catch (error) {
    showToast('加载真题数据失败', 'error')
    console.error('加载真题数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化弹窗
const initDialog = async () => {
  // 每次打开弹窗重新读取当前年份，避免页面长时间运行后年份列表过期
  refreshYearOptions()

  // 新建模式：直接显示空表单，不需要重置（表单初始状态就是空的）
  // 编辑模式：先加载数据，显示 loading 遮罩，加载完成后再显示内容
  if (props.examId) {
    // 编辑模式：先显示 loading 状态
    loading.value = true
    jsonImportVisible.value = false // 编辑模式收起 JSON 导入区域
  } else {
    // 新建模式：直接设置默认值并显示
    form.year = new Date().getFullYear()
    form.questionNumber = null
    jsonInput.value = ''
    jsonImportVisible.value = true // 新建模式展开 JSON 导入区域
  }

  // 加载科目选项（所有模式都需要）
  await loadSubjectOptions()

  // 编辑模式：加载已有数据
  if (props.examId) {
    await loadExamData(props.examId)
  }
}

watch(() => props.visible, async (visible) => {
  aiAnswerVisible.value = false
  if (visible) await initDialog()
})

// 解析JSON并填充表单
const handleParseJson = async () => {
  if (!jsonInput.value.trim()) {
    showToast('请先粘贴JSON数据', 'warning')
    return
  }

  try {
    const data = parseJsonWithRelaxedSupport(jsonInput.value)

    // 宽松验证：仅验证格式（如果提供）
    if (data.questionType && !['CHOICE', 'ESSAY'].includes(data.questionType)) {
      showToast('questionType必须是CHOICE或ESSAY', 'error')
      return
    }
    if (data.difficulty && !['EASY', 'MEDIUM', 'HARD'].includes(data.difficulty)) {
      showToast('difficulty必须是EASY、MEDIUM或HARD', 'error')
      return
    }

    // 填充表单
    await fillFormFromData(data)
    form.year = data.year || form.year
    form.questionNumber = data.questionNumber || null


    showToast('JSON解析成功，已填充到表单', 'success')
    jsonImportVisible.value = false
  } catch (e) {
    showToast('JSON格式错误：' + (e instanceof Error ? e.message : String(e)), 'error')
  }
}

// 仅解析并更新题目内容，不修改基础信息
const handleParseContentJson = () => {
  if (!jsonInput.value.trim()) {
    showToast('请先粘贴JSON数据', 'warning')
    return
  }

  try {
    const data = parseJsonWithRelaxedSupport(jsonInput.value)
    if (data.questionType && data.questionType !== form.questionType) {
      showToast('仅更新题目内容时，JSON题型必须与当前题型一致', 'error')
      return
    }

    const hasContentFields = data.content !== undefined ||
      data.answer !== undefined ||
      (form.questionType === 'CHOICE' && data.options !== undefined)
    if (!hasContentFields) {
      showToast('JSON中没有当前题型可更新的题目、选项或答案内容', 'warning')
      return
    }

    fillContentFromData(data)
    showToast('JSON解析成功，仅更新题目、选项和答案，基础信息未改变', 'success')
    jsonImportVisible.value = false
  } catch (e) {
    showToast('JSON格式错误：' + (e instanceof Error ? e.message : String(e)), 'error')
  }
}

// 提交表单
const handleSubmit = async () => {
  const valid = validateForm()
  if (!valid) return

  saving.value = true
  try {
    // 构建提交数据
    const data: ExamCreateRequest = {
      questionType: form.questionType,
      year: form.year,
      subjectId: form.subjectId,
      title: form.title || null,
      content: form.content,
      answer: form.answer || null,
      difficulty: form.difficulty || null,
      questionNumber: form.questionNumber || null,
      category: form.category ? (Array.isArray(form.category) ? form.category : [form.category]) : []
    }

    // 选择题额外字段
    if (form.questionType === 'CHOICE') {
      data.options = {
        A: form.optionA,
        B: form.optionB,
        C: form.optionC,
        D: form.optionD
      }
    }

    let response
    if (isEditMode.value) {
      // 编辑模式：调用更新API
      const id = Number(props.examId)
      response = await updateExam(id, data)
    } else {
      // 新建模式：调用创建API
      response = await createExam(data)
    }

    if (response.code === 200) {
      showToast(isEditMode.value ? '更新成功' : '创建成功', 'success')
      emit('success', response.data || null)
      dialogVisible.value = false
    } else {
      showToast(response.message || (isEditMode.value ? '更新失败' : '创建失败'), 'error')
    }
  } catch (error) {
    showToast(isEditMode.value ? '更新失败' : '创建失败', 'error')
    console.error('提交失败:', error)
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  dialogVisible.value = false
}

</script>

<style scoped>
/* JSON 区域滑入动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
