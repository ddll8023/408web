<template>
  <div class="max-w-[1400px] mx-auto px-4 py-6 min-h-[calc(100vh-60px)]">
    <div class="bg-white rounded-lg shadow-sm">
      <!-- 头部 -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200">
        <h2 class="m-0 text-xl text-[#333] font-semibold">真题管理</h2>
        <div class="flex gap-2">
          <CustomButton type="primary" @click="handleAdd">
            <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
            新增真题
          </CustomButton>
        </div>
      </div>

      <!-- 筛选条件 -->
      <div class="mb-6 p-4 bg-[#efefef] rounded">
        <div class="flex flex-wrap gap-4 items-center">
          <!-- 年份筛选 -->
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600 whitespace-nowrap">年份</label>
            <WheelPicker
              v-model="filters.year"
              :options="yearOptions"
              placeholder="选择年份"
              aria-label="年份"
              clearable
              class="!w-[140px]"
            />
          </div>
          <!-- 科目筛选 -->
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600 whitespace-nowrap">科目</label>
            <Select
              v-model="filters.subjectId"
              :options="subjectOptions"
              placeholder="请选择科目"
              aria-label="科目"
              clearable
              class="!w-[180px]"
              @change="handleSubjectChange"
            />
          </div>
          <!-- 分类筛选 -->
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600 whitespace-nowrap">分类</label>
            <Select
              v-model="filters.category"
              :options="categoryOptions"
              placeholder="请选择分类"
              filterable
              filter-placeholder="搜索分类..."
              aria-label="分类"
              clearable
              class="!w-[220px]"
              :disabled="!filters.subjectId"
            />
          </div>
          <!-- 关键词搜索 -->
          <div class="flex items-center gap-2">
            <label class="text-sm text-gray-600 whitespace-nowrap">关键词</label>
            <CustomInput
              v-model="filters.keyword"
              placeholder="搜索题目内容"
              aria-label="关键词"
              clearable
              class="!w-[180px]"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <font-awesome-icon :icon="['fas', 'search']" class="text-gray-400" />
              </template>
            </CustomInput>
          </div>
          <!-- 仅显示无分类 -->
          <div class="flex items-center gap-2">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="filters.noCategory"
                type="checkbox"
                class="w-4 h-4 rounded border-gray-300 text-[#8B6F47] focus:ring-[#8B6F47]"
              />
              <span class="text-sm text-gray-600">仅显示无分类</span>
            </label>
          </div>
          <!-- 按钮组 -->
          <div class="flex items-center gap-2">
            <CustomButton type="primary" @click="handleSearch">查询</CustomButton>
            <CustomButton @click="handleReset">重置</CustomButton>
          </div>
        </div>
      </div>

      <div v-if="listError" class="mx-4 mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
        {{ listError }}
        <CustomButton size="sm" type="text" :disabled="loading" @click="loadExamList">重试</CustomButton>
      </div>

      <!-- 真题列表表格 -->
      <div class="p-4">
        <Table
          :data="exams"
          :columns="tableColumns"
          :loading="loading"
          size="lg"
          @sort-change="handleSortChange"
        >
          <!-- ID 列 -->
          <template #id="{ row }">
            {{ row.id }}
          </template>

          <!-- 年份列 -->
          <template #year="{ row }">
            {{ row.year }}
          </template>

          <!-- 题号列 -->
          <template #questionNumber="{ row }">
            {{ row.questionNumber }}
          </template>

          <!-- 题型列 -->
          <template #questionType="{ row }">
            <Tag :type="row.questionType === 'CHOICE' ? 'success' : 'primary'">
              {{ row.questionType === 'CHOICE' ? '选择题' : '主观题' }}
            </Tag>
          </template>

          <!-- 标题列 -->
          <template #title="{ row }">
            <span class="hover:!text-[#8B6F47]">{{ row.title }}</span>
          </template>

          <!-- 分类列 -->
          <template #category="{ row }">
            <div class="flex flex-wrap gap-1">
              <Tag
                v-for="cat in (Array.isArray(row.category) ? row.category : [])"
                :key="cat"
                type="info"
                size="sm"
              >
                {{ cat }}
              </Tag>
            </div>
          </template>

          <!-- 难度列 -->
          <template #difficulty="{ row }">
            <Tag v-if="row.difficulty" :type="getDifficultyType(row.difficulty)" size="sm">
              {{ getDifficultyLabel(row.difficulty) }}
            </Tag>
            <span v-else class="text-gray-400">-</span>
          </template>

          <!-- 更新时间列 -->
          <template #updateTime="{ row }">
            {{ formatDateTime(row.updateTime) }}
          </template>

          <!-- 操作列 -->
          <template #actions="{ row }">
            <div class="flex items-center justify-center gap-1 whitespace-nowrap">
              <CustomButton
                type="text"
                size="sm"
                class="!px-2.5 whitespace-nowrap shrink-0"
                @click="handleView(row)"
              >查看</CustomButton>
              <CustomButton
                type="text-primary"
                size="sm"
                class="!px-2.5 whitespace-nowrap shrink-0"
                @click="handleEdit(row)"
              >编辑</CustomButton>
              <CustomButton
                type="text-danger"
                size="sm"
                class="!px-2.5 whitespace-nowrap shrink-0"
                :loading="row.deleteLoading"
                @click="handleDelete(row)"
              >
                删除
              </CustomButton>
            </div>
          </template>
        </Table>

        <!-- 分页 -->
        <div class="flex justify-end mt-6">
          <Pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            @current-change="loadExamList"
            @size-change="loadExamList"
          />
        </div>
      </div>
    </div>

    <!-- 返回顶部 -->
    <BackTop :right="32" :bottom="32">
      <div class="w-10 h-10 rounded-full bg-[#8B6F47] flex items-center justify-center text-white shadow-lg">
        <font-awesome-icon :icon="['fas', 'arrow-up']" />
      </div>
    </BackTop>

    <!-- 编辑弹窗 -->
    <ExamEditDialog
      v-model:visible="editDialogVisible"
      :exam-id="editingExamId"
      @success="handleEditSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import type { ExamQuestion } from "@/types"
import { queryString } from "@/utils/storage"
type QuestionRow = ExamQuestion & { deleteLoading?: boolean }
/**
 * 真题管理页面
 * 功能：真题的CRUD操作（仅ADMIN可访问）
 * 遵循KISS原则：简单的表格+筛选实现
 * 使用 useAdminTable composable 复用公共逻辑
 */
// 1. Vue 官方 API
import { ref, reactive, computed, onMounted, watch } from 'vue'

// 2. Vue Router 相关
import { useRoute } from 'vue-router'

// 3. API 接口定义
import { getExamList, deleteExam, getExamCategoriesBySubject } from '@/api/exam'

// 4. 组合式函数
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { useAdminTable } from '@/composables/useAdminTable'

// 5. 子组件导入
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import WheelPicker from '@/components/basic/WheelPicker.vue'
import Select from '@/components/basic/Select.vue'
import Tag from '@/components/basic/Tag.vue'
import Table from '@/components/basic/Table.vue'
import BackTop from '@/components/basic/BackTop.vue'
import Pagination from '@/components/basic/Pagination.vue'
import ExamEditDialog from '@/components/business/ExamEditDialog.vue'

const route = useRoute()

// 使用 Toast 和 Confirm
const { showToast } = useToast()
const { showConfirm } = useConfirm()

// 使用公共管理表格逻辑
const {
  loading,
  subjectOptions,
  categoryOptions,
  sorting,
  pagination,
  subjectMap,
  getDifficultyLabel,
  getDifficultyType,
  formatDateTime,
  loadSubjectOptions,
  loadSubjectCategoryOptions,
  handleSortChange: baseSortChange,
  clearUrlKeyword,
  getUrlKeyword
} = useAdminTable()

// 编辑弹窗状态
const editDialogVisible = ref(false)
const editingExamId = ref<number | null>(null)

// 真题列表
const exams = ref<QuestionRow[]>([])
const listError = ref('')
let listRequestVersion = 0

// 年份选项（2009 - 当前年份，倒序排列）
const currentYear = new Date().getFullYear()
const yearOptions = computed(() => {
  const options = []
  for (let year = currentYear; year >= 2009; year--) {
    options.push({ label: `${year}年`, value: year })
  }
  return options
})

// 表格列配置
const tableColumns = [
  { prop: 'id', label: 'ID', width: '80px' },
  { prop: 'year', label: '年份', width: '100px', sortable: true },
  { prop: 'questionNumber', label: '题号', width: '80px', sortable: true },
  { prop: 'questionType', label: '题型', width: '100px' },
  { prop: 'title', label: '标题', minWidth: '250px' },
  { prop: 'category', label: '分类', width: '200px' },
  { prop: 'difficulty', label: '难度', width: '100px' },
  { prop: 'updateTime', label: '更新时间', width: '160px', sortable: true },
  { prop: 'actions', label: '操作', width: '220px', align: 'center', fixed: 'right' }
]

// 筛选条件
const filters = reactive({
  year: null as number | null,
  subjectId: null as number | null,
  category: '',
  keyword: '',
  noCategory: false
})

/**
 * 加载真题列表
 */
const loadExamList = async () => {
  const requestVersion = ++listRequestVersion
  listError.value = ''
  loading.value = true
  try {
    const response = await getExamList({
      page: pagination.page,
      pageSize: pagination.size,
      year: filters.year || undefined,
      subjectId: filters.subjectId || undefined,
      category: filters.category || undefined,
      keyword: filters.keyword || undefined,
      noCategory: filters.noCategory || undefined,
      sortField: sorting.sortField || undefined,
      sortOrder: sorting.sortOrder || undefined
    })

    if (requestVersion !== listRequestVersion) return
    if (response.code === 200) {
      listError.value = ''
      exams.value = response.data?.lists || []
      pagination.total = response.data?.pagination?.total || 0
    } else {
      exams.value = []
      listError.value = response.message || '真题列表读取失败，请重试。'
      showToast(response.message || '加载失败', 'error')
    }
  } catch (error) {
    if (requestVersion !== listRequestVersion) return
    exams.value = []
    listError.value = '真题列表读取失败，请重试。'
    showToast('加载真题列表失败', 'error')
    console.error('加载真题列表失败:', error)
  } finally {
    if (requestVersion === listRequestVersion) loading.value = false
  }
}

/**
 * 科目筛选变更
 */
const handleSubjectChange = async (subjectId: string | number | null) => {
  filters.subjectId = subjectId ? Number(subjectId) : null
  filters.category = ''
  await loadSubjectCategoryOptions(filters.subjectId, getExamCategoriesBySubject)
}

/**
 * 处理查询
 */
const handleSearch = () => {
  pagination.page = 1
  loadExamList()
}

/**
 * 处理重置
 */
const handleReset = () => {
  filters.year = null
  filters.subjectId = null
  filters.category = ''
  filters.keyword = ''
  filters.noCategory = false
  categoryOptions.value = []
  sorting.sortField = null
  sorting.sortOrder = null
  pagination.page = 1
  clearUrlKeyword()
  loadExamList()
}

/**
 * 处理排序变化（使用公共逻辑）
 */
const handleSortChange = (sortInfo: Parameters<typeof baseSortChange>[0]) => {
  baseSortChange(sortInfo, loadExamList)
}

/**
 * 处理新增（打开编辑弹窗，不传ID表示新建）
 */
const handleAdd = () => {
  editingExamId.value = null
  editDialogVisible.value = true
}

/**
 * 处理查看（在新标签页打开题目浏览页）
 * 构建URL: /exam/classify?subject=科目名称#exam-题目ID
 */
const handleView = (row: QuestionRow) => {
  const subjectName = (row.subjectId == null ? '' : subjectMap.value[row.subjectId])
  if (!subjectName) {
    showToast('无法获取题目所属科目信息', 'warning')
    return
  }
  // 构建URL，使用hash定位到具体题目卡片
  const url = `/exam/classify?subject=${encodeURIComponent(subjectName)}#exam-${row.id}`
  window.open(url, '_blank')
}

/**
 * 处理编辑（打开编辑弹窗）
 */
const handleEdit = (row: QuestionRow) => {
  editingExamId.value = row.id
  editDialogVisible.value = true
}

/**
 * 编辑成功回调
 */
const handleEditSuccess = () => {
  loadExamList()
}

/**
 * 处理删除
 */
const handleDelete = async (row: QuestionRow) => {
  const ok = await showConfirm({
    title: '警告',
    message: `确定要删除真题"${row.title || row.year + '年 第' + row.questionNumber + '题'}"吗？`,
    confirmText: '确定',
    cancelText: '取消',
    type: 'warning'
  })

  if (!ok) return

  row.deleteLoading = true
  try {
    const response = await deleteExam(row.id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      loadExamList()
    } else {
      showToast(response.message || '删除失败', 'error')
    }
  } catch (error) {
    showToast('删除失败', 'error')
    console.error('删除失败:', error)
  } finally {
    if (row) row.deleteLoading = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadSubjectOptions()
  // 从URL获取keyword参数
  const urlKeyword = getUrlKeyword()
  if (urlKeyword) {
    filters.keyword = urlKeyword
  }
  loadExamList()
})

// 监听路由变化，支持导航栏搜索跳转
watch(() => route.query.keyword, (newKeyword) => {
  if (newKeyword !== undefined) {
    filters.keyword = queryString(newKeyword)
    pagination.page = 1
    loadExamList()
  }
})
</script>

<style scoped>
/**
 * 真题管理页面样式
 * 大部分样式已迁移到Tailwind类
 */

/* 响应式布局 */
@media (max-width: 768px) {
  .max-w-\[1400px\] {
    padding: 16px 8px;
  }

  .flex.justify-end {
    overflow-x: auto;
  }
}
</style>
