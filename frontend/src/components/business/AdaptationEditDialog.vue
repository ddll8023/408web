<!-- 改编题编辑弹窗：维护改编题内容与来源引用，保存前提示查重结果。 -->
<template>
  <Dialog
    v-model:visible="dialogVisible"
    :title="isEditMode ? '编辑改编题' : '新增改编题'"
    width="1000px"
    max-width="calc(100vw - 24px)"
    @close="handleClose"
  >
    <form id="adaptation-edit-form" class="space-y-6" @submit.prevent="handleSubmit">
      <!-- 基础信息 -->
      <section>
        <h4 class="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-accent">
          <font-awesome-icon :icon="['fas', 'cog']" />
          基础信息
        </h4>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
            <FormLabel label="标题" hint="题集分组" for-id="adaptation-title" />
            <CustomInput
              id="adaptation-title"
              v-model="form.title"
              placeholder="如 2027 真题改编卷一"
              :maxlength="200"
              clearable
            />
          </div>
          <div>
            <FormLabel label="题号" hint="题集内序号" for-id="adaptation-question-number" />
            <InputNumber
              id="adaptation-question-number"
              :model-value="form.questionNumber ?? 0"
              :min="0"
              :max="1000"
              placeholder="题号"
              @update:model-value="handleQuestionNumberChange"
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
          <div class="sm:col-span-2">
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

      <!-- JSON 导入 -->
      <section class="rounded-xl border border-accent/10 bg-surface/40 p-3">
        <button
          type="button"
          class="flex w-full items-center justify-between border-0 bg-transparent p-0 text-left text-sm font-semibold text-accent"
          :aria-expanded="jsonImportVisible"
          @click="jsonImportVisible = !jsonImportVisible"
        >
          <span class="flex items-center gap-2">
            <font-awesome-icon :icon="['fas', 'code']" />
            从 JSON 导入题目内容
          </span>
          <font-awesome-icon :icon="jsonImportVisible ? ['fas', 'chevron-up'] : ['fas', 'chevron-down']" />
        </button>
        <div v-if="jsonImportVisible" class="mt-3 space-y-3">
          <textarea
            v-model="jsonInput"
            rows="5"
            class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 font-mono text-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
            placeholder="粘贴题目 JSON；导入后来源仍需在下方单独核对"
          />
          <div class="flex flex-wrap gap-2">
            <CustomButton size="sm" @click="handlePasteJson">粘贴</CustomButton>
            <CustomButton type="primary" size="sm" @click="handleParseJson">解析并填充</CustomButton>
            <CustomButton size="sm" @click="showJsonExample('exercise')">查看格式示例</CustomButton>
            <CustomButton size="sm" @click="handleClearJson">清空</CustomButton>
          </div>
        </div>
      </section>

      <!-- 改编来源 -->
      <section>
        <h4 class="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-accent">
          <font-awesome-icon :icon="['fas', 'link-slash']" />
          改编来源
        </h4>
        <AdaptationSourceEditor v-model="sources" :disabled="loading || saving" />
      </section>

      <!-- 题目内容 -->
      <section>
        <h4 class="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-accent">
          <font-awesome-icon :icon="['fas', 'file-lines']" />
          题目内容
        </h4>
        <FormLabel label="题干" required for-id="adaptation-content" />
        <MarkdownEditor
          id="adaptation-content"
          v-model="form.content"
          height="320px"
          placeholder="请输入题干（支持 Markdown 与 LaTeX）"
          aria-label="题干"
        />

        <div v-if="form.questionType === 'CHOICE'" class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div v-for="option in optionFields" :key="option.key">
            <FormLabel
              :label="`选项 ${option.key}`"
              required
              :for-id="`adaptation-option-${option.key}`"
            />
            <CustomInput
              :id="`adaptation-option-${option.key}`"
              v-model="option.model.value"
              :placeholder="`请输入选项 ${option.key}`"
            />
          </div>
        </div>

        <div class="mt-4">
          <FormLabel label="答案解析" for-id="adaptation-answer" />
          <MarkdownEditor
            id="adaptation-answer"
            v-model="form.answer"
            height="240px"
            placeholder="请输入答案解析"
            aria-label="答案解析"
          />
        </div>
      </section>
    </form>

    <template #footer>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <span class="text-xs text-ink-soft">
          {{ sourceSummaryHint }}
        </span>
        <div class="flex gap-2">
          <CustomButton type="default" :disabled="saving" @click="dialogVisible = false">
            取消
          </CustomButton>
          <CustomButton type="primary" :loading="saving" @click="handleSubmit">
            保存
          </CustomButton>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
/**
 * AdaptationEditDialog 改编题编辑弹窗
 * 功能：新增或编辑改编题，维护题干、选项、答案解析与来源引用
 * 依赖：Dialog、MarkdownEditor、Select、MultiSelectCascader 等基础组件
 * 依赖：useQuestionForm、useToast composables 与 AdaptationSourceEditor 业务组件
 */
import type { AdaptationQuestion, AdaptationSourceRefInput } from '@/types'
import type { PropType } from 'vue'
import { computed, ref, toRef, watch } from 'vue'
import {
  checkAdaptationDuplicate,
  createAdaptation,
  getAdaptationDetail,
  updateAdaptation
} from '@/api/adaptation'
import { useJsonImport } from '@/composables/useJsonImport'
import { useQuestionForm } from '@/composables/useQuestionForm'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import Dialog from '@/components/basic/Dialog.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import InputNumber from '@/components/basic/InputNumber.vue'
import MarkdownEditor from '@/components/basic/MarkdownEditor.vue'
import MultiSelectCascader from '@/components/basic/MultiSelectCascader.vue'
import Select from '@/components/basic/Select.vue'
import AdaptationSourceEditor from '@/components/business/AdaptationSourceEditor.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  adaptationId: { type: [Number, String] as PropType<number | string | null>, default: null }
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
const {
  jsonInput,
  parseJsonWithRelaxedSupport,
  handlePasteJson,
  handleClearJson,
  showJsonExample
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

const handleQuestionNumberChange = (value: number | null) => {
  form.questionNumber = typeof value === 'number' && value > 0 ? value : null
}

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
    form.questionNumber = data.questionNumber ?? null
    showToast('JSON 解析成功，来源请在下方单独核对', 'success')
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
    form.title = question.title || ''
    form.questionNumber = question.questionNumber ?? null
    sources.value = (question.sources || []).map(source => ({
      sourceYear: source.sourceYear,
      sourceQuestionNumber: source.sourceQuestionNumber,
      sourcePart: source.sourcePart || null
    }))
  } catch (error) {
    showToast('改编题读取失败', 'error')
    console.error('加载改编题失败:', error)
  } finally {
    loading.value = false
  }
}

const resetDialog = () => {
  form.title = ''
  form.questionNumber = null
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
  if (!visible) return
  resetDialog()
  await loadSubjectOptions()
  if (props.adaptationId) {
    await loadAdaptationData(props.adaptationId)
  }
})

const handleClose = () => {
  if (saving.value) return
  dialogVisible.value = false
}

/** 保存前查重：标题题号重复直接阻止，同源引用只提示不阻断 */
const checkDuplicateBeforeSave = async () => {
  const response = await checkAdaptationDuplicate({
    title: form.title || null,
    questionNumber: form.questionNumber,
    excludeId: isEditMode.value ? Number(props.adaptationId) : null,
    sources: sources.value
  })
  if (response.code !== 200) return true

  const result = response.data
  if (result?.isDuplicate) {
    const existing = result.existingQuestion
    showToast(
      `该标题下题号 ${form.questionNumber} 已存在：${existing?.title || '未命名'}（ID ${existing?.id}）`,
      'error'
    )
    return false
  }
  if (result?.reusedSources?.length) {
    const names = result.reusedSources
      .map(item => `${item.sourceYear} 年第 ${item.sourceQuestionNumber} 题（${item.title || '未命名'}）`)
      .join('、')
    showToast(`以下来源已被其他改编题引用，仍会保存：${names}`, 'warning')
  }
  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return

  saving.value = true
  try {
    const passed = await checkDuplicateBeforeSave()
    if (!passed) return

    const payload = {
      title: form.title || null,
      questionNumber: form.questionNumber,
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
