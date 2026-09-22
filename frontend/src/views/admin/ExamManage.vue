<!-- 真题管理页面：筛选、表格与分页按视口自适应。 -->
<template>
  <main class="admin-manage-page mx-auto min-h-[var(--app-page-height)] w-full max-w-[1600px] min-w-0 px-2 py-4 sm:px-4 sm:py-6">
    <CustomCard shadow>
      <template #header>
        <header class="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 class="m-0 text-xl text-ink font-semibold">真题管理</h2>
          <div class="flex gap-2">
            <CustomButton type="primary" @click="handleAdd">
              <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
              新增真题
            </CustomButton>
          </div>
        </header>
      </template>

      <!-- 筛选条件 -->
      <div class="mb-6 rounded-xl border border-[#eadfd4] bg-white/70 p-3 shadow-sm backdrop-blur-sm sm:p-5">
        <div class="grid grid-cols-1 items-end gap-4 sm:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-6">
          <!-- 年份筛选 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">年份</label>
            <WheelPicker
              v-model="filters.year"
              :options="yearOptions"
              placeholder="选择年份"
              aria-label="年份"
              clearable
              class="w-full"
            />
          </div>
          <!-- 科目筛选 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">科目</label>
            <Select
              v-model="filters.subjectId"
              :options="subjectOptions"
              placeholder="请选择科目"
              aria-label="科目"
              clearable
              class="w-full"
              @change="handleSubjectChange"
            />
          </div>
          <!-- 分类筛选 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">分类</label>
            <MultiSelectCascader
              v-model="categorySelection"
              :options="categoryTreeOptions"
              placeholder="请选择分类"
              aria-label="分类"
              class="w-full min-w-0"
              :disabled="!filters.subjectId"
              :multiple="false"
              @change="handleCategoryFilterChange"
            />
          </div>
          <!-- 关键词搜索 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">关键词</label>
            <CustomInput
              v-model="filters.keyword"
              placeholder="搜索题目内容"
              aria-label="关键词"
              clearable
              class="w-full"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <font-awesome-icon :icon="['fas', 'search']" class="text-gray-400" />
              </template>
            </CustomInput>
          </div>
          <!-- 仅显示无分类 -->
          <div class="flex flex-col gap-1.5 pb-2">
            <label class="flex items-center gap-2 cursor-pointer select-none">
              <input
                v-model="filters.noCategory"
                type="checkbox"
                class="w-4 h-4 rounded border-gray-300 text-accent focus:ring-accent focus:ring-2 focus:ring-offset-0 transition-colors cursor-pointer"
              />
              <span class="text-sm text-gray-700">仅显示无分类</span>
            </label>
          </div>
          <!-- 按钮组 -->
          <div class="flex justify-end gap-2 pb-0.5">
            <CustomButton type="primary" @click="handleSearch">
              <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="mr-1.5" />
              查询
            </CustomButton>
            <CustomButton type="default" @click="handleReset">
              <font-awesome-icon :icon="['fas', 'sync']" class="mr-1.5" />
              重置
            </CustomButton>
          </div>
        </div>
      </div>

      <div v-if="listError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
        {{ listError }}
        <CustomButton size="sm" type="text" :disabled="loading" @click="loadExamList">重试</CustomButton>
      </div>

      <!-- 真题列表表格 -->
      <section class="mt-6">
        <Table
          :data="exams"
          :columns="tableColumns"
          :loading="loading"
          size="md"
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
            <Tag :type="row.questionType === 'CHOICE' ? 'success' : 'primary'" size="sm">
              {{ row.questionType === 'CHOICE' ? '选择题' : '主观题' }}
            </Tag>
          </template>

          <!-- 标题列 -->
          <template #title="{ row }">
            <button
              type="button"
              class="cursor-pointer border-0 bg-transparent p-0 text-left hover:text-accent transition-colors line-clamp-2"
              @click="handleView(row)"
              :title="row.title ?? ''"
            >
              {{ row.title }}
            </button>
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

          <!-- 窄屏卡片：保留题目定位、编辑和删除操作。 -->
          <template #mobile="{ row }">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <button type="button" class="block max-w-full truncate border-0 bg-transparent p-0 text-left text-base font-semibold text-accent hover:underline" @click="handleView(row)">
                  {{ row.year }} 年第 {{ row.questionNumber ?? '-' }} 题
                </button>
                <p class="m-0 mt-1 line-clamp-2 text-sm text-gray-600">{{ row.title || '未填写标题' }}</p>
              </div>
              <Tag :type="row.questionType === 'CHOICE' ? 'success' : 'primary'" size="sm" class="shrink-0">
                {{ row.questionType === 'CHOICE' ? '选择题' : '主观题' }}
              </Tag>
            </div>
            <div class="mt-3 flex flex-wrap gap-1">
              <Tag v-for="cat in (Array.isArray(row.category) ? row.category : [])" :key="cat" type="info" size="sm">{{ cat }}</Tag>
              <Tag v-if="row.difficulty" :type="getDifficultyType(row.difficulty)" size="sm">{{ getDifficultyLabel(row.difficulty) }}</Tag>
            </div>
            <div class="mt-3 flex items-center justify-between gap-2 border-t border-gray-100 pt-2 text-xs text-gray-500">
              <span>{{ formatDateTime(row.updateTime) }}</span>
              <div class="flex flex-wrap justify-end gap-1">
                <CustomButton type="text" size="sm" @click="handleView(row)">查看</CustomButton>
                <CustomButton type="text-primary" size="sm" @click="handleEdit(row)">编辑</CustomButton>
                <CustomButton type="text-danger" size="sm" :loading="row.deleteLoading" @click="handleDelete(row)">删除</CustomButton>
              </div>
            </div>
          </template>
        </Table>

        <!-- 分页 -->
        <footer class="admin-pagination mt-6 flex justify-end border-t border-gray-100 pt-4">
          <Pagination
            v-model:currentPage="pagination.page"
            v-model:pageSize="pagination.size"
            :pageSizes="[10, 20, 50, 100]"
            :total="pagination.total"
            showTotal
            showSizes
            showJumper
            @current-change="loadExamList"
            @size-change="loadExamList"
          />
        </footer>
      </section>
    </CustomCard>

    <!-- 返回顶部 -->
    <BackTop :right="32" :bottom="32">
      <div class="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-white shadow-lg transition-transform hover:scale-110">
        <font-awesome-icon :icon="['fas', 'arrow-up']" />
      </div>
    </BackTop>

    <!-- 编辑弹窗 -->
    <ExamEditDialog
      v-model:visible="editDialogVisible"
      :exam-id="editingExamId"
      @success="handleEditSuccess"
    />
  </main>
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
import { getEnabledCategoryTreeBySubject } from '@/api/category'

// 4. 组合式函数
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'
import { useAdminTable } from '@/composables/useAdminTable'

// 5. 子组件导入
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import MultiSelectCascader from '@/components/basic/MultiSelectCascader.vue'
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
  categoryTreeOptions,
  sorting,
  pagination,
  subjectMap,
  getDifficultyLabel,
  getDifficultyType,
  formatDateTime,
  loadSubjectOptions,
  handleSortChange: baseSortChange,
  loadSubjectCategoryTreeOptions,
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
  { prop: 'id', label: 'ID', width: '80px', align: 'center', sortable: true },
  { prop: 'year', label: '年份', width: '150px', align: 'center', sortable: true },
  { prop: 'questionNumber', label: '题号', width: '80px', align: 'center', sortable: true },
  { prop: 'questionType', label: '题型', width: '100px', align: 'center' },
  { prop: 'title', label: '标题', minWidth: '250px' },
  { prop: 'category', label: '分类', width: '200px' },
  { prop: 'difficulty', label: '难度', width: '100px', align: 'center' },
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
const categorySelection = ref<string[]>([])

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
  categorySelection.value = []
  await loadSubjectCategoryTreeOptions(
    filters.subjectId,
    getEnabledCategoryTreeBySubject,
    getExamCategoriesBySubject,
  )
}

const handleCategoryFilterChange = (values: string[]) => {
  filters.category = values[0] || ''
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
  categoryTreeOptions.value = []
  categorySelection.value = []
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
@media (max-width: 767px) {
  .admin-pagination {
    justify-content: center;
  }
}
</style>
