<template>
  <teleport to="body">
    <transition name="dialog-fade">
      <div v-show="dialogVisible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <!-- 遮罩层 -->
        <div
          class="fixed inset-0 bg-black/50 transition-opacity"
          @click="handleBackdropClick"
        />

        <!-- 弹窗主体 -->
        <div
          class="relative z-10 bg-white rounded-xl shadow-2xl overflow-hidden border border-gray-100 w-[1200px] min-w-[800px] max-w-[1600px] max-h-[calc(100vh-10vh-80px)] flex flex-col"
        >
          <!-- 头部 -->
          <header class="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-[#FBF7F2] to-white border-b border-[#8B6F47]/10">
            <div class="flex items-center gap-3">
              <!-- 装饰图标 -->
              <span class="w-8 h-8 rounded-lg bg-[#8B6F47] flex items-center justify-center text-white shadow-sm">
                <font-awesome-icon :icon="['fas', 'pencil-alt']" />
              </span>
              <h3 class="text-lg font-bold text-[#333] tracking-wide">
                {{ isEditMode ? '编辑模拟题' : '新增模拟题' }}
              </h3>
            </div>
            <button
              class="p-2 text-gray-400 hover:text-[#8B6F47] hover:bg-[#8B6F47]/5 rounded-lg transition-all duration-200"
              @click="handleCancel"
              aria-label="关闭"
            >
              <font-awesome-icon :icon="['fas', 'times']" class="text-lg" />
            </button>
          </header>

          <!-- 内容区 -->
          <div class="flex-1 overflow-y-auto p-6">
            <!-- JSON快速导入区域 -->
            <section class="mb-6">
              <!-- 折叠面板头部 -->
              <div
                class="group flex items-center justify-between px-5 py-3.5 bg-gradient-to-r from-[#FBF7F2]/80 to-transparent border-l-4 border-[#8B6F47] rounded-r-lg cursor-pointer hover:from-[#FBF7F2] hover:shadow-sm transition-all duration-200"
                @click="toggleJsonImport"
              >
                <div class="flex items-center gap-3">
                  <font-awesome-icon :icon="['fas', 'code']" class="text-[#8B6F47]" />
                  <span class="font-semibold text-[#333]">从 JSON 格式导入</span>
                  <span class="text-xs text-[#8B6F47]/60 bg-[#8B6F47]/10 px-2 py-0.5 rounded-full">批量录入</span>
                </div>
                <font-awesome-icon
                  class="text-[#8B6F47]/60 group-hover:text-[#8B6F47] transition-transform duration-300"
                  :icon="jsonImportVisible ? ['fas', 'chevron-up'] : ['fas', 'chevron-down']"
                />
              </div>

              <!-- 折叠面板内容 -->
              <transition name="slide-fade">
                <div v-show="jsonImportVisible" class="mt-3 p-5 bg-white border border-gray-100 rounded-xl shadow-sm">
                  <!-- 提示信息卡片 -->
                  <div class="flex items-start gap-3 p-4 mb-4 bg-[#FBF7F2] rounded-lg border border-[#8B6F47]/10">
                    <font-awesome-icon :icon="['fas', 'info-circle']" class="text-[#8B6F47] mt-0.5" />
                    <div class="text-sm text-[#666]">
                      粘贴单个题目的JSON数据，点击"解析并填充"后自动填充到下方表单。
                      <a href="#" class="text-[#8B6F47] hover:text-[#a88559] ml-2 underline underline-offset-2" @click.prevent="showJsonExample('mock')">查看格式示例</a>
                    </div>
                  </div>
                  <textarea
                    v-model="jsonInput"
                    class="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#8B6F47]/30 focus:border-[#8B6F47] bg-gray-50/50 font-mono text-sm transition-all duration-200"
                    rows="8"
                    placeholder="粘贴JSON数据..."
                  ></textarea>
                  <div class="mt-4 flex flex-wrap gap-3">
                    <CustomButton size="sm" @click="handlePasteJson">
                      <font-awesome-icon :icon="['fas', 'clipboard']" class="mr-1.5" />粘贴
                    </CustomButton>
                    <CustomButton type="primary" size="sm" @click="handleParseJson">
                      <font-awesome-icon :icon="['fas', 'check']" class="mr-1.5" />解析并填充
                    </CustomButton>
                    <CustomButton size="sm" @click="handleClearJson">
                      <font-awesome-icon :icon="['fas', 'trash']" class="mr-1.5" />清空
                    </CustomButton>
                  </div>
                </div>
              </transition>
            </section>

            <!-- 表单 -->
            <div :class="{ 'relative': loading }">
              <!-- 加载遮罩 -->
              <div v-if="loading" class="absolute inset-0 bg-white/90 backdrop-blur-sm flex items-center justify-center z-50">
                <div class="flex flex-col items-center gap-4">
                  <div class="relative">
                    <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-3xl text-[#8B6F47]" />
                    <div class="absolute inset-0 bg-[#8B6F47]/20 rounded-full animate-ping"></div>
                  </div>
                  <span class="text-sm text-[#666] font-medium">正在加载...</span>
                </div>
              </div>

              <!-- 基础信息分组 -->
              <div class="mb-6">
                <h4 class="flex items-center gap-2 text-sm font-semibold text-[#8B6F47] uppercase tracking-wider mb-4">
                  <font-awesome-icon :icon="['fas', 'cog']" />
                  基础信息
                </h4>
                <!-- 第一行：题型、来源、科目、题号 -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
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
                      class="w-full px-4 py-2.5 h-[42px] bg-white border border-gray-200 rounded-lg text-gray-700 text-base focus:outline-none focus:ring-2 focus:ring-[#8B6F47]/30 focus:border-[#8B6F47] transition-all duration-200"
                      placeholder="请输入题号（可选）"
                    />
                  </div>
                </div>
              </div>

              <!-- 标题 -->
              <div class="mb-6">
                <FormLabel label="标题" for-id="mock-title" />
                <InputSelect
                  v-model="form.title"
                  :options="titleOptions"
                  placeholder="请选择或输入题目标题（可选）"
                />
              </div>

              <!-- 分类与难度 -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                <div>
                  <FormLabel label="分类" for-id="mock-category" />
                  <!-- 多选级联选择器 -->
                  <MultiSelectCascader
                    v-model="form.category"
                    :options="categoryTreeOptions"
                    placeholder="请选择分类（支持多个）"
                    :disabled="!form.subjectId"
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
              </div>

              <!-- 选择题表单 -->
              <template v-if="form.questionType === 'CHOICE'">
                <div class="mb-6">
                  <h4 class="flex items-center gap-2 text-sm font-semibold text-[#8B6F47] uppercase tracking-wider mb-4">
                    <font-awesome-icon :icon="['fas', 'list-ol']" />
                    选择题内容
                  </h4>
                </div>
                <div class="mb-4">
                  <FormLabel label="题干" required for-id="mock-choice-content" />
                  <MarkdownEditor id="mock-choice-content" v-model="form.content" height="260px" placeholder="请输入选择题题干（支持Markdown、代码、图片等）..." />
                </div>
                <div class="mb-4">
                  <FormLabel label="选项A" required for-id="mock-option-a" />
                  <MarkdownEditor id="mock-option-a" v-model="form.optionA" height="140px" placeholder="请输入选项A的内容..." />
                </div>
                <div class="mb-4">
                  <FormLabel label="选项B" required for-id="mock-option-b" />
                  <MarkdownEditor id="mock-option-b" v-model="form.optionB" height="140px" placeholder="请输入选项B的内容..." />
                </div>
                <div class="mb-4">
                  <FormLabel label="选项C" required for-id="mock-option-c" />
                  <MarkdownEditor id="mock-option-c" v-model="form.optionC" height="140px" placeholder="请输入选项C的内容..." />
                </div>
                <div class="mb-4">
                  <FormLabel label="选项D" required for-id="mock-option-d" />
                  <MarkdownEditor id="mock-option-d" v-model="form.optionD" height="140px" placeholder="请输入选项D的内容..." />
                </div>
                <div class="mb-4">
                  <FormLabel label="答案解析" for-id="mock-choice-answer" />
                  <MarkdownEditor id="mock-choice-answer" v-model="form.answer" height="260px" placeholder="请输入Markdown格式的答案与解析..." />
                </div>
              </template>

              <!-- 主观题表单 -->
              <template v-else>
                <div class="mb-6">
                  <h4 class="flex items-center gap-2 text-sm font-semibold text-[#8B6F47] uppercase tracking-wider mb-4">
                    <font-awesome-icon :icon="['fas', 'pencil']" />
                    主观题内容
                  </h4>
                </div>
                <div class="mb-4">
                  <FormLabel label="题目内容" required for-id="mock-essay-content" />
                  <MarkdownEditor id="mock-essay-content" v-model="form.content" height="320px" placeholder="请输入Markdown格式题目内容..." />
                </div>
                <div class="mb-4">
                  <FormLabel label="答案解析" for-id="mock-essay-answer" />
                  <MarkdownEditor id="mock-essay-answer" v-model="form.answer" height="260px" placeholder="请输入Markdown格式答案解析（可选）..." />
                </div>
              </template>
            </div>
          </div>

          <!-- 底部 -->
          <footer class="flex-shrink-0 px-6 py-4 bg-gradient-to-r from-gray-50 to-[#FBF7F2]/30 border-t border-gray-100 flex items-center justify-between">
            <!-- 左侧提示 -->
            <div class="text-xs text-gray-400 hidden sm:block">
              <font-awesome-icon :icon="['fas', 'info-circle']" class="mr-1" />
              按 <kbd class="px-1.5 py-0.5 bg-white border border-gray-200 rounded text-[10px] font-mono">Ctrl</kbd> + <kbd class="px-1.5 py-0.5 bg-white border border-gray-200 rounded text-[10px] font-mono">Enter</kbd> 快速提交
            </div>

            <!-- 右侧按钮 -->
            <div class="flex items-center gap-3">
              <CustomButton @click="handleCancel">取消</CustomButton>
              <CustomButton type="primary" :loading="saving" @click="handleSubmit">
                <font-awesome-icon :icon="isEditMode ? ['fas', 'save'] : ['fas', 'plus']" />
                {{ isEditMode ? '保存修改' : '创建模拟题' }}
              </CustomButton>
            </div>
          </footer>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
/**
 * MockEditDialog 模拟题编辑弹窗组件
 * 功能：创建和编辑模拟题题目，支持选择题和主观题两种题型
 * 遵循原则：KISS（保持简洁）、YAGNI（不会需要）
 * 依赖：MarkdownEditor、CustomButton、InputSelect、Select、FormLabel、MultiSelectCascader 基础组件
 * 依赖：useQuestionForm、useJsonImport composables
 */
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getMockQuestionById, updateMockQuestion, createMockQuestion, getAllMockSources, getMockTitlesBySource } from '@/api/mock'
import { useQuestionForm } from '@/composables/useQuestionForm'
import { useJsonImport } from '@/composables/useJsonImport'
import MarkdownEditor from '@/components/basic/MarkdownEditor.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import InputSelect from '@/components/basic/InputSelect.vue'
import MultiSelectCascader from '@/components/basic/MultiSelectCascader.vue'
import FormLabel from '@/components/basic/FormLabel.vue'
import Select from '@/components/basic/Select.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  mockId: { type: [Number, String], default: null },
  mockData: { type: Object, default: null }  // 优先使用的编辑数据（来自列表）
})

const emit = defineEmits(['update:visible', 'success'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

// 是否为编辑模式（有数据或有ID为编辑，无数据无ID为新建）
const isEditMode = computed(() => !!props.mockData || !!props.mockId)

// 使用公共 composable
const {
  formRef, form, loading, saving,
  subjectOptions, categoryTreeOptions, baseFormRules,
  resetForm, loadSubjectOptions,
  handleSubjectChange, handleQuestionTypeChange,
  fillFormFromData, buildSubmitData
} = useQuestionForm({
  extraFields: { source: '', questionNumber: null }
})

const {
  jsonInput,
  parseJsonWithRelaxedSupport, handlePasteJson,
  handleClearJson, showJsonExample
} = useJsonImport()

// JSON 导入区域显示状态
const jsonImportVisible = ref(false)

// 切换 JSON 导入区域
const toggleJsonImport = () => {
  jsonImportVisible.value = !jsonImportVisible.value
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
const sourceOptions = ref([])

// 标题选项（根据来源动态加载）
const titleOptions = ref([])

// 表单验证规则（简化版：手动验证）
const validateForm = () => {
  if (!form.questionType) {
    ElMessage.warning('请选择题型')
    return false
  }
  if (!form.source) {
    ElMessage.warning('请选择或输入来源')
    return false
  }
  if (!form.content) {
    ElMessage.warning('请输入题目内容')
    return false
  }
  if (form.questionType === 'CHOICE') {
    if (!form.optionA || !form.optionB || !form.optionC || !form.optionD) {
      ElMessage.warning('请完善选择题选项')
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
      sourceOptions.value = response.data || []
    }
  } catch (error) {
    console.error('加载来源列表失败:', error)
  }
}

// 加载模拟题数据
const loadMockData = async (id) => {
  if (!id) return
  loading.value = true
  try {
    const response = await getMockQuestionById(id)
    if (response.code === 200) {
      const data = response.data
      await fillFormFromData(data)
      form.source = data.source || ''
      form.questionNumber = data.questionNumber
    } else {
      ElMessage.error(response.message || '加载失败')
    }
  } catch (error) {
    ElMessage.error('加载模拟题数据失败')
    console.error('加载模拟题数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 点击遮罩层关闭
const handleBackdropClick = () => {
  // 不自动关闭，需要点击取消按钮
}

// 初始化弹窗
const initDialog = async () => {
  // 优先使用传入的数据对象（来自列表页），避免重复请求API
  const hasData = !!props.mockData
  const hasId = !!props.mockId

  if (hasData || hasId) {
    // 编辑模式：先显示 loading 状态
    loading.value = true
    jsonImportVisible.value = false // 编辑模式收起 JSON 导入区域
  } else {
    // 新建模式：直接设置默认值并显示
    form.source = ''
    form.questionNumber = null
    jsonInput.value = ''
    jsonImportVisible.value = true // 新建模式展开 JSON 导入区域
  }

  // 加载科目选项和来源选项（所有模式都需要）
  await Promise.all([loadSubjectOptions(), loadSourceOptions()])

  // 编辑模式：加载已有数据
  // 优先使用传入的数据，否则调用API获取
  if (hasData) {
    await fillFormFromData(props.mockData)
    // 还需要填充额外字段（模拟题特有的字段）
    form.source = props.mockData.source || ''
    form.questionNumber = props.mockData.questionNumber ?? props.mockData.question_number
    loading.value = false  // 关闭 loading 状态
  } else if (hasId) {
    await loadMockData(props.mockId)
  }
}

watch(() => props.visible, async (visible) => {
  if (visible) await initDialog()
})

// 监听来源变化，动态加载该来源下的标题选项
watch(() => form.source, async (newSource) => {
  if (newSource) {
    try {
      const response = await getMockTitlesBySource(newSource)
      if (response.code === 200) {
        titleOptions.value = response.data || []
      }
    } catch (error) {
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
    ElMessage.warning('请先粘贴JSON数据')
    return
  }

  try {
    const data = parseJsonWithRelaxedSupport(jsonInput.value)

    // 宽松验证：仅验证questionType格式（如果提供）
    if (data.questionType && !['CHOICE', 'ESSAY'].includes(data.questionType)) {
      ElMessage.error('questionType必须是CHOICE或ESSAY')
      return
    }

    await fillFormFromData(data)
    form.source = data.source || form.source
    form.questionNumber = data.questionNumber || null

    if (data.questionType === 'CHOICE' && data.options) {
      const options = typeof data.options === 'string' ? JSON.parse(data.options) : data.options
      form.optionA = options.A || ''
      form.optionB = options.B || ''
      form.optionC = options.C || ''
      form.optionD = options.D || ''
    }

    ElMessage.success('JSON解析成功，已填充到表单')
    jsonImportVisible.value = false
  } catch (e) {
    ElMessage.error('JSON格式错误：' + e.message)
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
      const id = Number(props.mockId)
      response = await updateMockQuestion(id, { ...data, id })
    } else {
      // 新建模式：调用创建API
      response = await createMockQuestion(data)
    }

    if (response.code === 200) {
      ElMessage.success(isEditMode.value ? '更新成功' : '创建成功')
      emit('success', response.data || null)
      dialogVisible.value = false
    } else {
      ElMessage.error(response.message || (isEditMode.value ? '更新失败' : '创建失败'))
    }
  } catch (error) {
    ElMessage.error(isEditMode.value ? '更新失败' : '创建失败')
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
/* 弹窗遮罩层过渡 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-active .bg-white,
.dialog-fade-leave-active .bg-white {
  transition: opacity 0.3s ease, transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.dialog-fade-enter-from .bg-white,
.dialog-fade-leave-to .bg-white {
  opacity: 0;
  transform: scale(0.95) translateY(-10px);
}

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
