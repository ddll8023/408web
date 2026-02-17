<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEditMode ? '编辑模拟题' : '新增模拟题'"
    width="86%"
    top="5vh"
    :append-to-body="true"
    :destroy-on-close="true"
    :close-on-click-modal="false"
  >
    <!-- JSON快速导入区域 -->
    <el-collapse v-model="jsonImportVisible" style="margin-bottom: 20px">
      <el-collapse-item title="从JSON格式导入" name="jsonImport">
        <el-alert type="info" :closable="false" style="margin-bottom: 12px">
          <template #title>
            <div style="font-size: 13px">
              粘贴单个题目的JSON数据，点击"解析并填充"后自动填充到下方表单。
              <el-link type="primary" :underline="false" href="#" style="margin-left: 8px" @click.prevent="showJsonExample('mock')">
                查看格式示例
              </el-link>
            </div>
          </template>
        </el-alert>
        <el-input v-model="jsonInput" type="textarea" :rows="8" placeholder="粘贴JSON数据..." style="font-family: monospace" />
        <div style="margin-top: 12px; display: flex; gap: 12px; flex-wrap: wrap">
          <CustomButton @click="handlePasteJson">粘贴</CustomButton>
          <CustomButton type="primary" @click="handleParseJson">
            <el-icon style="margin-right: 6px"><Check /></el-icon>
            解析并填充
          </CustomButton>
          <CustomButton @click="handleClearJson">
            <el-icon style="margin-right: 6px"><Delete /></el-icon>
            清空
          </CustomButton>
        </div>
      </el-collapse-item>
    </el-collapse>

    <el-form ref="formRef" :model="form" :rules="formRules" label-width="80px" v-loading="loading">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="6">
          <el-form-item label="题型" prop="questionType">
            <el-select v-model="form.questionType" placeholder="请选择题型" style="width: 100%" @change="handleQuestionTypeChange">
              <el-option label="选择题" value="CHOICE" />
              <el-option label="主观题" value="ESSAY" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-form-item label="来源" prop="source">
            <InputSelect
              v-model="form.source"
              :options="sourceOptions"
              placeholder="请选择或输入来源"
              :clearable="true"
            />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-form-item label="科目">
            <el-select v-model="form.subjectId" placeholder="请选择科目" style="width: 100%" clearable @change="handleSubjectChange">
              <el-option v-for="subject in subjectOptions" :key="subject.id" :label="subject.name" :value="subject.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="6">
          <el-form-item label="题号">
            <el-input-number v-model="form.questionNumber" :min="1" :step="1" style="width: 100%" placeholder="请输入题号" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="标题">
        <!-- 使用 InputSelect 组件：支持从下拉选项选择或手动输入 -->
        <InputSelect 
          v-model="form.title" 
          :options="titleOptions" 
          placeholder="请选择或输入题目标题（可选）"
          :clearable="true"
        />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :xs="24" :sm="12">
          <el-form-item label="分类" prop="category">
            <!-- 级联选择器：支持多选，可选择任意层级分类 -->
            <el-cascader
              v-model="form.category"
              :options="categoryTreeOptions"
              :props="{
                multiple: true,
                checkStrictly: true,
                emitPath: false,
                value: 'value',
                label: 'label',
                children: 'children'
              }"
              placeholder="请选择分类（支持多个）"
              :disabled="!form.subjectId"
              clearable
              filterable
              collapse-tags
              collapse-tags-tooltip
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12">
          <el-form-item label="难度">
            <el-select v-model="form.difficulty" placeholder="请选择难度（可选）" style="width: 100%" clearable>
              <el-option label="简单" value="EASY" />
              <el-option label="中等" value="MEDIUM" />
              <el-option label="困难" value="HARD" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 选择题表单 -->
      <template v-if="form.questionType === 'CHOICE'">
        <el-form-item label="题干" prop="content" class="editor-form-item">
          <MarkdownEditor v-model="form.content" height="260px" placeholder="请输入选择题题干..." />
        </el-form-item>
        <el-form-item label="选项A" prop="optionA" class="editor-form-item">
          <MarkdownEditor v-model="form.optionA" height="140px" placeholder="请输入选项A的内容..." />
        </el-form-item>
        <el-form-item label="选项B" prop="optionB" class="editor-form-item">
          <MarkdownEditor v-model="form.optionB" height="140px" placeholder="请输入选项B的内容..." />
        </el-form-item>
        <el-form-item label="选项C" prop="optionC" class="editor-form-item">
          <MarkdownEditor v-model="form.optionC" height="140px" placeholder="请输入选项C的内容..." />
        </el-form-item>
        <el-form-item label="选项D" prop="optionD" class="editor-form-item">
          <MarkdownEditor v-model="form.optionD" height="140px" placeholder="请输入选项D的内容..." />
        </el-form-item>
        <el-form-item label="答案解析" prop="answer" class="editor-form-item">
          <MarkdownEditor v-model="form.answer" height="260px" placeholder="请输入答案与解析..." />
        </el-form-item>
      </template>

      <!-- 主观题表单 -->
      <template v-else>
        <el-form-item label="题目内容" prop="content" class="editor-form-item">
          <MarkdownEditor v-model="form.content" height="320px" placeholder="请输入题目内容..." />
        </el-form-item>
        <el-form-item label="答案解析" class="editor-form-item">
          <MarkdownEditor v-model="form.answer" height="260px" placeholder="请输入答案解析（可选）..." />
        </el-form-item>
      </template>

      <el-form-item>
        <CustomButton type="primary" :loading="saving" @click="handleSubmit">{{ isEditMode ? '更新' : '创建' }}</CustomButton>
        <CustomButton style="margin-left: 16px" @click="handleCancel">取消</CustomButton>
      </el-form-item>
    </el-form>
  </el-dialog>
</template>

<script setup>
/**
 * 模拟题编辑弹窗组件
 * 使用 useQuestionForm 和 useJsonImport composable 重构
 */
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Delete } from '@element-plus/icons-vue'
import { getMockQuestionById, updateMockQuestion, createMockQuestion, getAllMockSources, getMockTitlesBySource } from '@/api/mock'
import { useQuestionForm } from '@/composables/useQuestionForm'
import { useJsonImport } from '@/composables/useJsonImport'
import MarkdownEditor from '@/components/basic/MarkdownEditor.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import InputSelect from '@/components/basic/InputSelect.vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  mockId: { type: [Number, String], default: null }
})

const emit = defineEmits(['update:visible', 'success'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

// 是否为编辑模式（有ID为编辑，无ID为新建）
const isEditMode = computed(() => !!props.mockId)

// 使用公共 composable
const {
  formRef, form, loading, saving,
  subjectOptions, categoryTreeOptions, baseFormRules,
  resetForm, loadSubjectOptions,
  handleSubjectChange, handleQuestionTypeChange,
  fillFormFromData, buildSubmitData, validateForm
} = useQuestionForm({
  extraFields: { source: '', questionNumber: null }
})

const {
  jsonImportVisible, jsonInput,
  parseJsonWithRelaxedSupport, handlePasteJson,
  handleClearJson, showJsonExample
} = useJsonImport()

// 来源选项
const sourceOptions = ref([])

// 标题选项（根据来源动态加载）
const titleOptions = ref([])

// 表单验证规则
const formRules = reactive({
  ...baseFormRules,
  source: [{ required: true, message: '请选择或输入来源', trigger: 'change' }]
})

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

// 初始化弹窗
const initDialog = async () => {
  resetForm({ source: '', questionNumber: null })
  jsonInput.value = ''
  // 新建模式默认展开JSON导入栏，编辑模式默认收起
  jsonImportVisible.value = props.mockId ? [] : ['jsonImport']
  await Promise.all([loadSubjectOptions(), loadSourceOptions()])
  // 编辑模式：加载已有数据；新建模式：显示空表单
  if (props.mockId) {
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
    jsonImportVisible.value = []
  } catch (e) {
    ElMessage.error('JSON格式错误：' + e.message)
  }
}

// 提交表单
const handleSubmit = async () => {
  const valid = await validateForm()
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
/* 编辑器表单项样式 - 修复标签与编辑器对齐 */
.editor-form-item {
  align-items: flex-start !important;
}

.editor-form-item :deep(.el-form-item__label) {
  padding-top: 10px;
  line-height: 20px;
}

.editor-form-item :deep(.el-form-item__content) {
  flex: 1;
  min-width: 0;
  line-height: normal;
}
</style>
