<!-- 改编题编辑弹窗：维护内容与来源引用，支持新增时自动填入入口传来的真题来源。 -->
<template>
  <ResponsiveDialog
    v-model:visible="dialogVisible"
    :title="isEditMode ? '编辑改编题' : '新增改编题'"
    width="1000px"
    max-width="calc(100vw - 24px)"
    @close="handleClose"
  >
    <form id="adaptation-edit-form" class="edit-form" :aria-busy="loading" @submit.prevent="handleSubmit">
      <QuestionJsonImportPanel
        v-model="jsonInput"
        v-model:visible="jsonImportVisible"
        @paste="handlePasteJson"
        @parse="handleParseJson"
        @clear="handleClearJson"
      />

      <!-- 基础信息 -->
      <section class="edit-section">
        <div class="edit-section-heading">
          <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'cog']" aria-hidden="true" />基础信息</h4>
          <span class="edit-hint m-0">标有 * 的字段为必填</span>
        </div>
        <div class="edit-grid edit-grid--four">
          <div>
            <FormLabel label="题型" required for-id="adaptation-question-type" />
            <Select
              id="adaptation-question-type"
              v-model="form.questionType"
              :options="questionTypeOptions"
              placeholder="请选择题型"
              @change="handleQuestionTypeChange"
            />
          </div>
          <div>
            <FormLabel label="难度" for-id="adaptation-difficulty" />
            <Select
              id="adaptation-difficulty"
              v-model="form.difficulty"
              :options="difficultyOptions"
              placeholder="请选择难度"
              clearable
            />
          </div>
          <div class="sm:col-span-2">
            <FormLabel label="科目" for-id="adaptation-subject" />
            <Select
              id="adaptation-subject"
              v-model="form.subjectId"
              :options="subjectOptions"
              placeholder="请选择科目"
              clearable
              @change="handleSubjectChange"
            />
          </div>
          <div class="edit-span-full">
            <FormLabel label="分类" for-id="adaptation-category" />
            <MultiSelectCascader
              id="adaptation-category"
              v-model="form.category"
              :options="categoryTreeOptions"
              placeholder="请选择分类（支持多个）"
              :disabled="!form.subjectId"
            />
          </div>
        </div>
      </section>

      <!-- 改编来源 -->
      <section class="edit-section">
        <div class="edit-section-heading">
          <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'link-slash']" aria-hidden="true" />改编来源</h4>
          <span class="edit-hint m-0">按年份和题号核对真题引用</span>
        </div>
        <AdaptationSourceEditor v-model="sources" :disabled="loading || saving" />
      </section>

      <!-- 题目内容 -->
      <section class="edit-section">
        <div class="edit-section-heading">
          <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'file-lines']" aria-hidden="true" />题目内容</h4>
          <span class="edit-hint m-0">支持 Markdown、公式和图片</span>
        </div>
        <FormLabel label="题干" required for-id="adaptation-content" />
        <MarkdownEditor
          id="adaptation-content"
          v-model="form.content"
          height="320px"
          placeholder="请输入题干（支持 Markdown 与 LaTeX）"
          aria-label="题干"
        />

        <div v-if="form.questionType === 'CHOICE'" class="edit-options-grid mt-4">
          <div v-for="option in optionFields" :key="option.key" class="edit-option">
            <FormLabel
              :label="`选项 ${option.key}`"
              required
              :for-id="`adaptation-option-${option.key}`"
            />
            <MarkdownEditor
              :id="`adaptation-option-${option.key}`"
              v-model="option.model.value"
              content-role="option"
              height="140px"
              :placeholder="`请输入选项 ${option.key}（支持 Markdown 与 LaTeX）`"
              :aria-label="`选项 ${option.key}`"
            />
          </div>
        </div>

      </section>
      <section class="edit-section">
        <div class="edit-section-heading">
          <h4 class="edit-section-title">答案解析</h4>
          <CustomButton v-if="isEditMode && authStore.isAdmin()" size="sm" type="text-primary" :disabled="loading || saving" @click="aiAnswerVisible = true">AI 生成答案</CustomButton>
          <span class="edit-hint m-0">可选</span>
        </div>
        <MarkdownEditor
          id="adaptation-answer"
          v-model="form.answer"
          height="240px"
          placeholder="请输入答案解析"
          aria-label="答案解析"
        />
      </section>
    </form>

    <AiAnswerGenerationDialog
      v-if="props.visible && aiAnswerVisible && props.adaptationId"
      v-model:visible="aiAnswerVisible"
      question-kind="adaptation"
      :question-id="Number(props.adaptationId)"
      :source="aiAnswerSource"
      draft
      @adopt="applyGeneratedAnswer"
    />

    <template #footer>
      <div class="edit-footer">
        <span class="edit-hint m-0">
          {{ sourceSummaryHint }}
        </span>
        <div class="edit-footer-actions">
          <CustomButton type="default" :disabled="saving" @click="dialogVisible = false">
            取消
          </CustomButton>
          <CustomButton type="primary" :loading="saving" @click="handleSubmit">
            保存
          </CustomButton>
        </div>
      </div>
    </template>
  </ResponsiveDialog>
</template>

<script setup lang="ts">
/**
 * AdaptationEditDialog 改编题编辑弹窗
 * 功能：新增或编辑改编题，维护题干、选项、答案解析与来源引用
 * 依赖：ResponsiveDialog、MarkdownEditor、Select、MultiSelectCascader 等基础组件
 * 依赖：useQuestionForm、useToast composables 与 AdaptationSourceEditor 业务组件
 */
import type { AdaptationQuestion, AdaptationSourceRefInput } from '@/types'
import type { PropType } from 'vue'
import type { AiAnswerCandidate } from '@/types/aiAnswer'
import { answerSourceFromForm, answerSourceKey } from '@/utils/aiAnswer'
import { useAuthStore } from '@/stores/auth'
import AiAnswerGenerationDialog from '@/components/business/AiAnswerGenerationDialog.vue'
import { computed, ref, toRef, watch } from 'vue'
import {
  createAdaptation,
  getAdaptationDetail,
  updateAdaptation
} from '@/api/adaptation'
import { useJsonImport } from '@/composables/useJsonImport'
import { useQuestionForm } from '@/composables/useQuestionForm'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import MarkdownEditor from '@/components/basic/MarkdownEditor.vue'
import MultiSelectCascader from '@/components/basic/MultiSelectCascader.vue'
import Select from '@/components/basic/Select.vue'
import AdaptationSourceEditor from '@/components/business/AdaptationSourceEditor.vue'
import QuestionJsonImportPanel from '@/components/business/QuestionJsonImportPanel.vue'
import '@/styles/edit-form.css'

const props = defineProps({
  visible: { type: Boolean, default: false },
  adaptationId: { type: [Number, String] as PropType<number | string | null>, default: null },
  answerCandidate: { type: Object as PropType<AiAnswerCandidate | null>, default: null },
  initialSources: {
    type: Array as PropType<AdaptationSourceRefInput[]>,
    default: () => []
  }
})

const emit = defineEmits<{
  'update:visible': [visible: boolean]
  success: [question: AdaptationQuestion | null]
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value)
})

const isEditMode = computed(() => !!props.adaptationId)

const {
  form,
  loading,
  saving,
  subjectOptions,
  categoryTreeOptions,
  loadSubjectOptions,
  handleSubjectChange,
  handleQuestionTypeChange,
  fillFormFromData
} = useQuestionForm()

const { showToast } = useToast()
const authStore = useAuthStore()
const aiAnswerVisible = ref(false)
const aiAnswerSource = computed(() => answerSourceFromForm(form))

/** 只填答案；题面或原答案在生成后变化时拒绝覆盖。 */
function applyGeneratedAnswer(candidate: AiAnswerCandidate): void {
  if (!props.visible || !authStore.isAdmin() || candidate.questionKind !== 'adaptation'
    || candidate.questionId !== Number(props.adaptationId)) return
  if (answerSourceKey(candidate.source) !== answerSourceKey(aiAnswerSource.value)) {
    showToast('题面或原答案已变化，未填入新答案，请重新生成', 'warning')
    return
  }
  form.answer = candidate.answer
  showToast('新答案已填入，点击保存后才会更新题库', 'success')
}
const {
  jsonInput,
  parseJsonWithRelaxedSupport,
  handlePasteJson,
  handleClearJson
} = useJsonImport()

const jsonImportVisible = ref(false)
const sources = ref<AdaptationSourceRefInput[]>([])
const questionTypeOptions = [
  { label: '选择题', value: 'CHOICE' },
  { label: '主观题', value: 'ESSAY' }
]
const difficultyOptions = [
  { label: '简单', value: 'EASY' },
  { label: '中等', value: 'MEDIUM' },
  { label: '困难', value: 'HARD' }
]

// 选项输入通过 toRef 绑定，保持与 form 的响应式关系
const optionFields = [
  { key: 'A' as const, model: toRef(form, 'optionA') },
  { key: 'B' as const, model: toRef(form, 'optionB') },
  { key: 'C' as const, model: toRef(form, 'optionC') },
  { key: 'D' as const, model: toRef(form, 'optionD') }
]

const sourceSummaryHint = computed(() => {
  const total = sources.value.length
  if (total === 0) return '当前未标注改编来源'
  return `已标注 ${total} 处来源`
})

const handleParseJson = async () => {
  if (!jsonInput.value.trim()) {
    showToast('请先粘贴 JSON 数据', 'warning')
    return
  }
  try {
    const data = parseJsonWithRelaxedSupport(jsonInput.value)
    if (data.questionType && !['CHOICE', 'ESSAY'].includes(data.questionType)) {
      showToast('questionType 必须是 CHOICE 或 ESSAY', 'error')
      return
    }
    if (data.difficulty && !['EASY', 'MEDIUM', 'HARD'].includes(data.difficulty)) {
      showToast('difficulty 必须是 EASY、MEDIUM 或 HARD', 'error')
      return
    }
    await fillFormFromData(data)
    if (data.sources) {
      sources.value = data.sources
    }
    showToast('JSON 解析成功，来源请在下方核对', 'success')
    jsonImportVisible.value = false
  } catch (error) {
    showToast(`JSON 格式错误：${error instanceof Error ? error.message : String(error)}`, 'error')
  }
}

const validateForm = () => {
  if (!form.content.trim()) {
    showToast('请输入题干', 'warning')
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

/** 加载改编题详情并填充表单与来源行 */
const loadAdaptationData = async (id: number | string) => {
  loading.value = true
  try {
    const response = await getAdaptationDetail(Number(id))
    const question = response.code === 200 ? response.data : null
    if (!question) {
      showToast(response.message || '改编题读取失败', 'error')
      return
    }
    await fillFormFromData(question)
    if (props.answerCandidate) applyGeneratedAnswer(props.answerCandidate)
    sources.value = (question.sources || []).map(source => ({
      sourceYear: source.sourceYear,
      sourceQuestionNumber: source.sourceQuestionNumber
    }))
  } catch (error) {
    showToast('改编题读取失败', 'error')
    console.error('加载改编题失败:', error)
  } finally {
    loading.value = false
  }
}

const resetDialog = () => {
  sources.value = []
  form.content = ''
  form.answer = ''
  form.optionA = ''
  form.optionB = ''
  form.optionC = ''
  form.optionD = ''
  form.category = []
  form.difficulty = ''
  form.subjectId = null
  form.questionType = 'ESSAY'
}

watch(() => props.visible, async visible => {
  aiAnswerVisible.value = false
  if (!visible) return
  resetDialog()
  if (!props.adaptationId) {
    // 每次新增独立复制初始来源，避免编辑来源时修改入口数据或沿用上次输入。
    sources.value = props.initialSources.map(source => ({ ...source }))
  }
  await loadSubjectOptions()
  if (props.adaptationId) {
    await loadAdaptationData(props.adaptationId)
  }
})

const handleClose = () => {
  if (saving.value) return
  dialogVisible.value = false
}

const handleSubmit = async () => {
  if (!validateForm()) return

  saving.value = true
  try {
    const payload = {
      questionType: form.questionType,
      content: form.content,
      subjectId: form.subjectId || null,
      category: form.category,
      difficulty: form.difficulty || null,
      answer: form.answer || null,
      options: form.questionType === 'CHOICE'
        ? { A: form.optionA, B: form.optionB, C: form.optionC, D: form.optionD }
        : null,
      sources: sources.value
    }

    const response = isEditMode.value
      ? await updateAdaptation(Number(props.adaptationId), payload)
      : await createAdaptation(payload)

    if (response.code === 200) {
      showToast(isEditMode.value ? '保存成功' : '创建成功', 'success')
      emit('success', response.data || null)
      dialogVisible.value = false
    } else {
      showToast(response.message || '保存失败', 'error')
    }
  } catch (error) {
    showToast('保存失败', 'error')
    console.error('保存改编题失败:', error)
  } finally {
    saving.value = false
  }
}
</script>
