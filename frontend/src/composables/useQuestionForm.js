/**
 * 题目表单公共逻辑 composable
 * 抽取真题/模拟题编辑弹窗的公共逻辑
 */
import { ref, reactive, computed } from 'vue'
import { getEnabledSubjects } from '@/api/subject'
import { getEnabledCategoriesBySubject, getEnabledCategoryTreeBySubject } from '@/api/category'

/**
 * 创建题目表单的公共状态和方法
 * @param {Object} options - 配置选项
 * @param {Array} options.extraFields - 额外的表单字段定义
 * @returns {Object} 表单状态和方法
 */
export function useQuestionForm(options = {}) {
  const { extraFields = {} } = options

  // 基础状态
  const formRef = ref(null)
  const loading = ref(false)
  const saving = ref(false)

  // 选项数据
  const subjectOptions = ref([])
  const categoryOptions = ref([])
  // 树形分类数据（用于级联选择器）
  const categoryTreeOptions = ref([])

  // 基础表单字段
  const baseFormFields = {
    questionType: 'ESSAY',
    subjectId: null,
    title: '',
    content: '',
    optionA: '',
    optionB: '',
    optionC: '',
    optionD: '',
    answer: '',
    category: [],
    difficulty: ''
  }

  // 合并额外字段
  const form = reactive({
    ...baseFormFields,
    ...extraFields
  })

  // 基础验证规则
  const baseFormRules = {
    questionType: [
      { required: true, message: '请选择题型', trigger: 'change' }
    ],
    content: [
      { required: true, message: '请输入题目内容', trigger: 'blur' }
    ],
    optionA: [
      {
        required: computed(() => form.questionType === 'CHOICE'),
        message: '请输入选项A',
        trigger: 'blur'
      }
    ],
    optionB: [
      {
        required: computed(() => form.questionType === 'CHOICE'),
        message: '请输入选项B',
        trigger: 'blur'
      }
    ],
    optionC: [
      {
        required: computed(() => form.questionType === 'CHOICE'),
        message: '请输入选项C',
        trigger: 'blur'
      }
    ],
    optionD: [
      {
        required: computed(() => form.questionType === 'CHOICE'),
        message: '请输入选项D',
        trigger: 'blur'
      }
    ]
  }

  /**
   * 重置表单到初始状态
   * @param {Object} extraDefaults - 额外字段的默认值
   */
  const resetForm = (extraDefaults = {}) => {
    Object.assign(form, {
      ...baseFormFields,
      ...extraFields,
      ...extraDefaults
    })
    categoryOptions.value = []
    categoryTreeOptions.value = []
  }

  /**
   * 加载科目选项
   */
  const loadSubjectOptions = async () => {
    try {
      const response = await getEnabledSubjects()
      if (response.code === 200) {
        subjectOptions.value = response.data || []
      }
    } catch (error) {
      console.error('加载科目列表失败:', error)
    }
  }

  /**
   * 根据科目加载分类选项（扁平列表，兼容旧逻辑）
   * @param {Number} subjectId - 科目ID
   */
  const loadSubjectCategoryOptions = async (subjectId) => {
    if (!subjectId) {
      categoryOptions.value = []
      return
    }

    try {
      const res = await getEnabledCategoriesBySubject(subjectId)
      if (res.code === 200) {
        const options = (res.data || []).map(cat => ({
          label: cat.name,
          value: cat.name
        }))

        // 兼容历史数据：将当前已选择但未定义的分类添加到选项中
        if (Array.isArray(form.category)) {
          form.category.forEach(cat => {
            if (cat && !options.some(option => option.value === cat)) {
              options.unshift({ label: cat + ' (未定义)', value: cat })
            }
          })
        }

        categoryOptions.value = options
      }
    } catch (error) {
      console.error('加载分类标签失败:', error)
    }
  }

  /**
   * 根据科目加载树形分类选项（用于级联选择器）
   * @param {Number} subjectId - 科目ID
   */
  const loadSubjectCategoryTreeOptions = async (subjectId) => {
    if (!subjectId) {
      categoryTreeOptions.value = []
      return
    }

    try {
      const res = await getEnabledCategoryTreeBySubject(subjectId)
      if (res.code === 200) {
        // 转换为级联选择器需要的格式
        // 注意：checkStrictly: true 允许选择任意层级分类
        const transformTree = (nodes) => {
          return (nodes || []).map(node => ({
            value: node.name,
            label: node.name,
            children: node.children && node.children.length > 0
              ? transformTree(node.children)
              : undefined
          }))
        }
        categoryTreeOptions.value = transformTree(res.data || [])
      }
    } catch (error) {
      console.error('加载树形分类标签失败:', error)
    }
  }

  /**
   * 处理科目变更
   * @param {Number} subjectId - 科目ID
   */
  const handleSubjectChange = async (subjectId) => {
    if (!subjectId) {
      form.subjectId = null
      form.category = []
      categoryOptions.value = []
      categoryTreeOptions.value = []
      return
    }

    form.subjectId = subjectId
    form.category = []
    // 同时加载扁平和树形分类数据
    await Promise.all([
      loadSubjectCategoryOptions(subjectId),
      loadSubjectCategoryTreeOptions(subjectId)
    ])
  }

  /**
   * 处理题型变更
   */
  const handleQuestionTypeChange = () => {
    if (form.questionType === 'CHOICE') {
      form.content = ''
      form.answer = ''
    } else {
      form.optionA = ''
      form.optionB = ''
      form.optionC = ''
      form.optionD = ''
      form.answer = ''
    }
  }

  /**
   * 从API响应数据填充表单
   * @param {Object} data - API返回的题目数据
   */
  const fillFormFromData = async (data) => {
    form.questionType = data.questionType || 'ESSAY'
    form.subjectId = data.subjectId || null
    form.title = data.title || ''
    form.content = data.content || ''
    form.category = Array.isArray(data.category)
      ? data.category
      : (data.category ? [data.category] : [])
    form.difficulty = data.difficulty || ''

    // 加载分类选项（扁平和树形）
    if (form.subjectId) {
      await Promise.all([
        loadSubjectCategoryOptions(form.subjectId),
        loadSubjectCategoryTreeOptions(form.subjectId)
      ])
    } else {
      categoryOptions.value = []
      categoryTreeOptions.value = []
    }

    // 处理选择题选项
    if (data.questionType === 'CHOICE') {
      if (data.options) {
        try {
          const options = typeof data.options === 'string'
            ? JSON.parse(data.options)
            : data.options
          form.optionA = options.A || ''
          form.optionB = options.B || ''
          form.optionC = options.C || ''
          form.optionD = options.D || ''
        } catch (e) {
          console.error('解析选项失败:', e)
        }
      }
      form.answer = data.answer || ''
    } else {
      form.answer = data.answer || ''
      form.optionA = ''
      form.optionB = ''
      form.optionC = ''
      form.optionD = ''
    }
  }

  /**
   * 构建提交数据
   * @param {Object} extraData - 额外的提交字段
   * @returns {Object} 提交数据
   */
  const buildSubmitData = (extraData = {}) => {
    const data = {
      questionType: form.questionType,
      subjectId: form.subjectId || null,
      title: form.title || null,
      category: form.category,
      difficulty: form.difficulty || null,
      ...extraData
    }

    if (form.questionType === 'CHOICE') {
      data.content = form.content
      data.options = JSON.stringify({
        A: form.optionA,
        B: form.optionB,
        C: form.optionC,
        D: form.optionD
      })
      data.answer = form.answer || null
    } else {
      data.content = form.content
      data.options = null
      data.answer = form.answer || null
    }

    return data
  }

  /**
   * 验证表单
   * @returns {Promise<boolean>} 验证结果
   */
  const validateForm = async () => {
    if (!formRef.value) return false
    return formRef.value.validate().catch(() => false)
  }

  return {
    // 状态
    formRef,
    form,
    loading,
    saving,
    subjectOptions,
    categoryOptions,
    categoryTreeOptions,
    baseFormRules,

    // 方法
    resetForm,
    loadSubjectOptions,
    loadSubjectCategoryOptions,
    loadSubjectCategoryTreeOptions,
    handleSubjectChange,
    handleQuestionTypeChange,
    fillFormFromData,
    buildSubmitData,
    validateForm
  }
}
