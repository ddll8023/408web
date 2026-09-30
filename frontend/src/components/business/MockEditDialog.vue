<!-- 模拟题编辑弹窗：表单在桌面与移动视口内自适应。 -->
<template>
  <ResponsiveDialog
    v-model:visible="dialogVisible"
    :title="isEditMode ? '编辑模拟题' : '新增模拟题'"
    width="1200px"
    max-width="1600px"
  >
    <div ref="contentRef" class="edit-form">
            <QuestionJsonImportPanel
              v-model="jsonInput"
              v-model:visible="jsonImportVisible"
              show-content-only
              show-example
              @paste="handlePasteJson"
              @parse="handleParseJson"
              @parse-content="handleParseContentJson"
              @clear="handleClearJson"
              @show-example="() => showJsonExample('mock')"
            />

            <!-- 表单 -->
            <div class="edit-form" :class="{ 'relative': loading }" :aria-busy="loading">
              <div v-if="loading" class="edit-loading" role="status" aria-live="polite">
                <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-accent" aria-hidden="true" />
                <span>正在加载...</span>
              </div>

              <!-- 来源与标题联动保持不变，统一基础信息的排布。 -->
              <section class="edit-section">
                <div class="edit-section-heading">
                  <h4 class="edit-section-title"><font-awesome-icon :icon="['fas', 'cog']" aria-hidden="true" />基础信息</h4>
                  <span class="edit-hint m-0">标有 * 的字段为必填</span>
                </div>
                <div class="edit-grid edit-grid--four">
                  <div>
                    <FormLabel label="题型" required for-id="mock-question-type" />
                    <Select
                      id="mock-question-type"
                      v-model="form.questionType"
                      :options="questionTypeOptions"
                      placeholder="请选择题型"
                      @change="handleQuestionTypeChange"
                    />
                  </div>
                  <div>
                    <FormLabel label="来源" required for-id="mock-source" />
                    <InputSelect
                      id="mock-source"
                      v-model="form.source"
                      :options="sourceOptions"
                      placeholder="请选择或输入来源"
                    />
                  </div>
                  <div>
                    <FormLabel label="科目" for-id="mock-subject" />
                    <Select
                      id="mock-subject"
                      v-model="form.subjectId"
                      :options="subjectOptions"
                      placeholder="请选择科目"
                      @change="handleSubjectChange"
                    />
                  </div>
                  <div>
                    <FormLabel label="题号" for-id="mock-question-number" hint="可选" />
                    <input
                      id="mock-question-number"
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
                  <FormLabel label="标题" for-id="mock-title" />
                  <InputSelect
                    id="mock-title"
                    v-model="form.title"
                    :options="titleOptions"
                    placeholder="请选择或输入题目标题（可选）"
                  />
                </div>
                <div>
                  <FormLabel label="难度" for-id="mock-difficulty" />
                  <Select
                    id="mock-difficulty"
                    v-model="form.difficulty"
                    :options="difficultyOptions"
                    placeholder="请选择难度（可选）"
                  />
                </div>
                <div class="edit-span-full">
                  <FormLabel label="分类" for-id="mock-category" />
                  <!-- 多选级联选择器 -->
                  <MultiSelectCascader
                    id="mock-category"
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
                <FormLabel :label="form.questionType === 'CHOICE' ? '题干' : '题目内容'" required :for-id="form.questionType === 'CHOICE' ? 'mock-choice-content' : 'mock-essay-content'" />
                <MarkdownEditor :id="form.questionType === 'CHOICE' ? 'mock-choice-content' : 'mock-essay-content'" aria-label="题干" v-model="form.content" :height="form.questionType === 'CHOICE' ? '260px' : '320px'" placeholder="请输入题目内容（支持 Markdown、公式和图片）..." />
                <div v-if="form.questionType === 'CHOICE'" class="edit-options-grid mt-4">
                  <div class="edit-option">
                    <FormLabel label="选项 A" required for-id="mock-option-a" />
                    <MarkdownEditor id="mock-option-a" content-role="option" aria-label="选项 A" v-model="form.optionA" height="140px" placeholder="请输入选项 A 的内容..." />
                  </div>
                  <div class="edit-option">
                    <FormLabel label="选项 B" required for-id="mock-option-b" />
                    <MarkdownEditor id="mock-option-b" content-role="option" aria-label="选项 B" v-model="form.optionB" height="140px" placeholder="请输入选项 B 的内容..." />
                  </div>
                  <div class="edit-option">
                    <FormLabel label="选项 C" required for-id="mock-option-c" />
                    <MarkdownEditor id="mock-option-c" content-role="option" aria-label="选项 C" v-model="form.optionC" height="140px" placeholder="请输入选项 C 的内容..." />
                  </div>
                  <div class="edit-option">
                    <FormLabel label="选项 D" required for-id="mock-option-d" />
                    <MarkdownEditor id="mock-option-d" content-role="option" aria-label="选项 D" v-model="form.optionD" height="140px" placeholder="请输入选项 D 的内容..." />
                  </div>
                </div>
              </section>
              <section class="edit-section">
                <div class="edit-section-heading"><h4 class="edit-section-title">答案解析</h4><span class="edit-hint m-0">可选</span></div>
                <MarkdownEditor :id="form.questionType === 'CHOICE' ? 'mock-choice-answer' : 'mock-essay-answer'" aria-label="答案解析" v-model="form.answer" height="260px" placeholder="请输入答案与解析..." />
              </section>
            </div>
          </div>

    <template #footer>
      <div class="edit-footer">
        <span class="edit-hint m-0">保存前请核对题干、选项与解析</span>
        <div class="edit-footer-actions">
          <CustomButton @click="handleCancel">取消</CustomButton>
          <CustomButton type="primary" :loading="saving" @click="handleSubmit">
            <font-awesome-icon :icon="isEditMode ? ['fas', 'save'] : ['fas', 'plus']" />
            {{ isEditMode ? '保存修改' : '创建模拟题' }}
          </CustomButton>
        </div>
      </div>
    </template>
  </ResponsiveDialog>
</template>

<script setup lang="ts">
import type { MockCreateRequest, MockQuestion } from '@/types'
import type { PropType } from 'vue'
/**
 * MockEditDialog 模拟题编辑弹窗组件
 * 功能：创建和编辑模拟题题目，支持选择题和主观题两种题型
 * 遵循原则：KISS（保持简洁）、YAGNI（不会需要）
 * 依赖：MarkdownEditor、CustomButton、InputSelect、Select、FormLabel、MultiSelectCascader 基础组件
 * 依赖：useQuestionForm、useJsonImport、useToast composables
 */
import { ref, computed, watch } from 'vue'
import { getMockQuestionById, updateMockQuestion, createMockQuestion, getAllMockSources, getMockTitlesBySource } from '@/api/mock'
import { useQuestionForm } from '@/composables/useQuestionForm'
import { useJsonImport } from '@/composables/useJsonImport'
import { useToast } from '@/composables/useToast'
import MarkdownEditor from '@/components/basic/MarkdownEditor.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import InputSelect from '@/components/basic/InputSelect.vue'
import MultiSelectCascader from '@/components/basic/MultiSelectCascader.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import QuestionJsonImportPanel from '@/components/business/QuestionJsonImportPanel.vue'
import Select from '@/components/basic/Select.vue'
import '@/styles/edit-form.css'

const props = defineProps({
  visible: { type: Boolean, default: false },
  mockId: { type: [Number, String] as PropType<number | string | null>, default: null },
  mockData: { type: Object as PropType<MockQuestion | null>, default: null }  // 优先使用的编辑数据（来自列表）
})

const emit = defineEmits<{ 'update:visible': [visible: boolean]; success: [question: MockQuestion | null] }>()

const contentRef = ref<HTMLElement | null>(null)

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

// 是否为编辑模式：优先使用显式 ID，也兼容只传入完整题目数据的调用方
const editId = computed(() => props.mockId ?? props.mockData?.id ?? null)
const isEditMode = computed(() => editId.value !== null)

// 使用公共 composable
const {
  form, loading, saving,
  subjectOptions, categoryTreeOptions,
  loadSubjectOptions,
  handleSubjectChange, handleQuestionTypeChange,
  resetForm, fillFormFromData, fillContentFromData, buildSubmitData
} = useQuestionForm({
  extraFields: { source: '', questionNumber: null }
})

const { showToast } = useToast()

const {
  jsonInput,
  parseJsonWithRelaxedSupport, handlePasteJson,
  handleClearJson, showJsonExample
} = useJsonImport()

// JSON 导入区域显示状态
const jsonImportVisible = ref(false)

const resetContentScroll = () => {
  if (!contentRef.value) return
  contentRef.value.scrollTop = 0
  contentRef.value.scrollLeft = 0
}

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

// 来源选项
const sourceOptions = ref<string[]>([])

// 标题选项（根据来源动态加载）
const titleOptions = ref<string[]>([])
let sourceRequestVersion = 0

// 表单验证规则（简化版：手动验证）
const validateForm = () => {
  if (!form.questionType) {
    showToast('请选择题型', 'warning')
    return false
  }
  if (!form.source) {
    showToast('请选择或输入来源', 'warning')
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

// 加载来源选项
const loadSourceOptions = async () => {
  try {
    const response = await getAllMockSources()
    if (response.code === 200) {
      sourceOptions.value = response.data.sources.map(item => item.source)
    }
  } catch (error) {
    console.error('加载来源列表失败:', error)
  }
}

// 加载模拟题数据
const loadMockData = async (id: number | string | null) => {
  if (!id) return
  loading.value = true
  try {
    const response = await getMockQuestionById(Number(id))
    if (response.code === 200) {
      const data = response.data
      await fillFormFromData(data)
      form.source = data.source || ''
      form.questionNumber = data.questionNumber ?? null
    } else {
      showToast(response.message || '加载失败', 'error')
    }
  } catch (error) {
    showToast('加载模拟题数据失败', 'error')
    console.error('加载模拟题数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化弹窗
const initDialog = async () => {
  // 优先使用传入的数据对象（来自列表页），避免重复请求API
  const hasData = !!props.mockData
  const hasId = editId.value !== null

  if (hasData || hasId) {
    // 编辑模式：先显示 loading 状态
    loading.value = true
    jsonImportVisible.value = false // 编辑模式收起 JSON 导入区域
  } else {
    // 新建模式：清空上一次编辑内容，并展开 JSON 导入区域
    resetForm({ source: '', questionNumber: null })
    resetContentScroll()
    jsonInput.value = ''
    titleOptions.value = []
    jsonImportVisible.value = true
  }

  // 加载科目选项和来源选项（所有模式都需要）
  await Promise.all([loadSubjectOptions(), loadSourceOptions()])

  // 编辑模式：加载已有数据
  // 优先使用传入的数据，否则调用API获取
  if (props.mockData) {
    await fillFormFromData(props.mockData)
    // 还需要填充额外字段（模拟题特有的字段）
    form.source = props.mockData.source || ''
    form.questionNumber = props.mockData.questionNumber ?? null
    loading.value = false  // 关闭 loading 状态
  } else if (hasId) {
    await loadMockData(editId.value)
  }
}

watch(() => props.visible, async (visible) => {
  if (visible) {
    await initDialog()
    if (!isEditMode.value) resetContentScroll()
  }
})

// 监听来源变化，动态加载该来源下的标题选项
watch(() => form.source, async (newSource) => {
  const requestVersion = ++sourceRequestVersion
  if (newSource) {
    try {
      const response = await getMockTitlesBySource(newSource)
      if (requestVersion !== sourceRequestVersion) return
      if (response.code === 200) {
        titleOptions.value = response.data || []
      }
    } catch (error) {
      if (requestVersion !== sourceRequestVersion) return
      console.error('加载标题列表失败:', error)
      titleOptions.value = []
    }
  } else {
    titleOptions.value = []
  }
})

// 解析JSON并填充表单
const handleParseJson = async () => {
  if (!jsonInput.value.trim()) {
    showToast('请先粘贴JSON数据', 'warning')
    return
  }

  try {
    const data = parseJsonWithRelaxedSupport(jsonInput.value)

    // 宽松验证：仅验证questionType格式（如果提供）
    if (data.questionType && !['CHOICE', 'ESSAY'].includes(data.questionType)) {
      showToast('questionType必须是CHOICE或ESSAY', 'error')
      return
    }

    await fillFormFromData(data)
    form.source = data.source || form.source
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
    const data = buildSubmitData({
      source: form.source,
      questionNumber: form.questionNumber || null
    })

    let response
    if (isEditMode.value) {
      // 编辑模式：调用更新API
      const id = Number(editId.value)
      response = await updateMockQuestion(id, data)
    } else {
      // 新建模式：调用创建API
      response = await createMockQuestion(data)
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
