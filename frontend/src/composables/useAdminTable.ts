/**
 * 管理页面通用表格逻辑
 * 提取 ExamManage 和 MockManage 的公共逻辑
 * 遵循 DRY 原则，避免代码重复
 */
import type { CascaderOption, TableSort } from '@/components/basic/types'
import type { ApiResponse, CategoryTreeNode, SortOrder } from '@/types'
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'
import { formatDateTime } from '@/utils/format'
import { useSubjects } from './useSubjects'

/**
 * 排序字段名映射：前端驼峰 -> 后端下划线
 * 遵循 `规范文档/前端规范文档.md` 的 API 数据格式约定
 */
const SORT_FIELD_MAPPING: Record<string, string> = {
  questionNumber: 'question_number',
  updateTime: 'update_time',
  createTime: 'create_time'
}

/**
 * 管理表格通用逻辑
 */
export function useAdminTable() {
  const router = useRouter()
  const route = useRoute()

  // 加载状态
  const loading = ref(false)

  // 引入科目相关逻辑
  const { subjectOptions, subjectMap, loadSubjectOptions } = useSubjects()

  // 分类选项
  const categoryOptions = ref<{ label: string; value: string }[]>([])
  const categoryTreeOptions = ref<CascaderOption[]>([])
  let categoryTreeRequestVersion = 0

  // 排序条件
  const sorting = reactive<{ sortField: string | null; sortOrder: SortOrder | null }>({
    sortField: null,
    sortOrder: null
  })

  // 分页配置
  const pagination = reactive({
    page: 1,
    size: 20,
    total: 0
  })

  /**
   * 按科目加载分类选项
   * @param {Number} subjectId 科目ID
   * @param {Function} loadCategoryFn 加载分类的API函数
   */
  const loadSubjectCategoryOptions = async (subjectId: number | null, loadCategoryFn: (id: number) => Promise<ApiResponse<string[]>>) => {
    if (!subjectId) {
      categoryOptions.value = []
      return
    }

    try {
      const res = await loadCategoryFn(subjectId)
      if (res.code === 200) {
        const list = res.data || []
        categoryOptions.value = list.map(name => ({
          label: name,
          value: name
        }))
      }
    } catch (error) {
      console.error('按科目加载分类失败:', error)
    }
  }

  /**
   * 按科目加载分类树，并补充题目历史数据中存在但目录未收录的分类。
   */
  const loadSubjectCategoryTreeOptions = async (
    subjectId: number | null,
    loadCategoryTreeFn: (id: number) => Promise<ApiResponse<CategoryTreeNode[]>>,
    loadCategoryNamesFn: (id: number) => Promise<ApiResponse<string[]>>,
  ) => {
    const requestVersion = ++categoryTreeRequestVersion
    categoryTreeOptions.value = []
    if (!subjectId) return

    try {
      const [treeResponse, namesResponse] = await Promise.all([
        loadCategoryTreeFn(subjectId),
        loadCategoryNamesFn(subjectId),
      ])

      if (requestVersion !== categoryTreeRequestVersion) return
      if (treeResponse.code !== 200 || namesResponse.code !== 200) return

      const knownNames = new Set<string>()
      const mapNode = (node: CategoryTreeNode): CascaderOption => {
        knownNames.add(node.name)
        return {
          value: node.name,
          label: node.name,
          children: node.children.length > 0
            ? node.children.map(mapNode)
            : undefined,
        }
      }

      const options = (treeResponse.data || []).map(mapNode)
      const unfiledNames = (namesResponse.data || [])
        .filter(name => name && !knownNames.has(name))

      if (unfiledNames.length > 0) {
        options.push({
          value: '__unfiled_categories__',
          label: '未归档分类',
          selectable: false,
          children: unfiledNames.map(name => ({
            value: name,
            label: name,
          })),
        })
      }

      categoryTreeOptions.value = options
    } catch (error) {
      if (requestVersion !== categoryTreeRequestVersion) return
      categoryTreeOptions.value = []
      console.error('按科目加载分类树失败:', error)
    }
  }

  /**
   * 处理排序变化
   * @param {Function} loadListFn 加载列表的回调函数
   */
  const handleSortChange = ({ prop, order }: TableSort, loadListFn?: () => void) => {
    if (order && prop) {
      // 转换字段名：前端驼峰 -> 后端下划线
      sorting.sortField = SORT_FIELD_MAPPING[prop] || prop
      sorting.sortOrder = order === 'ascending' ? 'asc' : 'desc'
    } else {
      sorting.sortField = null
      sorting.sortOrder = null
    }
    pagination.page = 1
    loadListFn?.()
  }

  /**
   * 清除URL中的keyword参数
   */
  const clearUrlKeyword = () => {
    router.replace({ path: route.path })
  }

  /**
   * 从URL获取keyword参数
   */
  const getUrlKeyword = () => {
    const keyword = route.query.keyword
    return typeof keyword === 'string' ? keyword : ''
  }

  return {
    // 状态
    loading,
    subjectOptions,
    categoryOptions,
    categoryTreeOptions,
    sorting,
    pagination,
    subjectMap,
    // 方法
    getDifficultyLabel,
    getDifficultyType,
    formatDateTime,
    loadSubjectOptions,
    loadSubjectCategoryOptions,
    loadSubjectCategoryTreeOptions,
    handleSortChange,
    clearUrlKeyword,
    getUrlKeyword
  }
}
