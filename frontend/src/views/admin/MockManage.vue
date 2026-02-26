<template>
  <main class="mx-auto px-4 py-6 min-h-[calc(100vh-60px)] max-w-[1400px]">
    <CustomCard shadow>
      <template #header>
        <header class="flex items-center justify-between">
          <h2 class="m-0 text-xl text-[#333] font-semibold">模拟题管理</h2>
          <div class="flex gap-2">
            <CustomButton type="primary" @click="handleAdd">
              <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
              新增模拟题
            </CustomButton>
          </div>
        </header>
      </template>

      <!-- 筛选条件 -->
      <section class="mb-6 p-4 bg-[#efefef] rounded">
        
        <div class="flex flex-wrap items-end gap-4">
          <!-- 来源机构 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">来源机构</label>
            <Select
              v-model="filters.source"
              :options="sourceOptions || []"
              placeholder="请选择来源"
              clearable
              filterable
              class="w-[180px]"
            />
          </div>

          <!-- 科目 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">科目</label>
            <Select
              v-model="filters.subjectId"
              :options="(subjectOptions || []).map(s => ({ label: s.name, value: s.id }))"
              placeholder="请选择科目"
              clearable
              class="w-[150px]"
              @change="handleSubjectChange"
            />
          </div>

          <!-- 分类 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">分类</label>
            <InputSelect
              v-model="filters.category"
              :options="categoryOptions"
              placeholder="请选择或输入分类"
              class="w-[180px]"
              :disabled="!filters.subjectId"
            />
          </div>

          <!-- 关键词 -->
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">关键词</label>
            <CustomInput
              v-model="filters.keyword"
              placeholder="搜索题目内容"
              clearable
              class="w-[180px]"
              @keyup.enter="handleSearch"
            />
          </div>

          <!-- 仅显示无分类 -->
          <div class="flex flex-col gap-1.5 pb-2">
            <label class="flex items-center gap-2 cursor-pointer select-none">
              <input
                v-model="filters.noCategory"
                type="checkbox"
                class="w-4 h-4 rounded border-gray-300 text-[#8B6F47] focus:ring-[#8B6F47] focus:ring-2 focus:ring-offset-0 transition-colors cursor-pointer"
              >
              <span class="text-sm text-gray-700">仅显示无分类</span>
            </label>
          </div>

          <!-- 按钮组 -->
          <div class="flex gap-2 ml-auto pb-0.5">
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
      </section>

      <!-- 模拟题列表表格 -->
      <section class="mt-6">
        <Table
          :data="mockQuestions"
          :columns="tableColumns"
          :loading="loading"
          size="md"
          @sort-change="handleSortChange"
        >
          <!-- 题型列 -->
          <template #questionType="{ row }">
            <Tag :type="row.questionType === 'CHOICE' ? 'success' : 'primary'" size="small">
              {{ row.questionType === 'CHOICE' ? '选择题' : '主观题' }}
            </Tag>
          </template>

          <!-- 标题列 -->
          <template #title="{ row }">
            <span
              class="cursor-pointer hover:text-[#8B6F47] transition-colors line-clamp-2"
              @click="handleView(row)"
              :title="row.title"
            >
              {{ row.title }}
            </span>
          </template>

          <!-- 分类列 -->
          <template #category="{ row }">
            <div class="flex flex-wrap gap-1">
              <Tag
                v-for="cat in (Array.isArray(row.category) ? row.category : [])"
                :key="cat"
                type="info"
                size="small"
              >
                {{ cat }}
              </Tag>
            </div>
          </template>

          <!-- 难度列 -->
          <template #difficulty="{ row }">
            <Tag v-if="row.difficulty" :type="getDifficultyType(row.difficulty)" size="small">
              {{ getDifficultyLabel(row.difficulty) }}
            </Tag>
            <span v-else class="text-gray-400">-</span>
          </template>

          <!-- 更新时间列 -->
          <template #updateTime="{ row }">
            <span class="text-gray-600 text-sm">{{ formatDateTime(row.updateTime) }}</span>
          </template>

          <!-- 操作列 -->
          <template #actions="{ row }">
            <div class="flex items-center gap-2">
              <CustomButton type="text" size="sm" @click="handleView(row)">查看</CustomButton>
              <CustomButton type="text-primary" size="sm" @click="handleEdit(row)">编辑</CustomButton>
              <CustomButton
                type="text-danger"
                size="sm"
                :loading="row.deleteLoading"
                @click="handleDelete(row)"
              >
                删除
              </CustomButton>
            </div>
          </template>
        </Table>
      </section>

      <!-- 分页 -->
      <footer class="flex justify-end mt-6 pt-4 border-t border-gray-100">
        <Pagination
          v-model:currentPage="pagination.page"
          v-model:pageSize="pagination.size"
          :pageSizes="[10, 20, 50, 100]"
          :total="pagination.total"
          showTotal
          showSizes
          showJumper
          @current-change="loadMockList"
          @size-change="loadMockList"
        />
      </footer>
    </CustomCard>

    <!-- 返回顶部 -->
    <BackTop :right="32" :bottom="32">
      <div class="w-10 h-10 rounded-full bg-[#8B6F47] flex items-center justify-center text-white shadow-lg transition-transform hover:scale-110">
        <font-awesome-icon :icon="['fas', 'arrow-up']" />
      </div>
    </BackTop>

    <!-- 编辑弹窗 -->
    <MockEditDialog
      v-model:visible="editDialogVisible"
      :mock-id="editingMockId"
      :mock-data="editingMockData"
      @success="handleEditSuccess"
    />
  </main>
</template>

<script setup>
/**
 * 模拟题管理页面
 * 功能：模拟题的CRUD操作（仅ADMIN可访问）
 * 遵循KISS原则：简单的表格+筛选实现
 * 使用 useAdminTable composable 复用公共逻辑
 *
 * Source: 基于Vue 3 + 自定义组件库构建
 */

import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

// API接口
import {
  getMockQuestions,
  deleteMockQuestion,
  getAllMockSources,
  getMockCategoriesBySubject
} from '@/api/mock'

// 自定义基础组件
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import Select from '@/components/basic/Select.vue'
import InputSelect from '@/components/basic/InputSelect.vue'
import Table from '@/components/basic/Table.vue'
import Pagination from '@/components/basic/Pagination.vue'
import Tag from '@/components/basic/Tag.vue'
import BackTop from '@/components/basic/BackTop.vue'

// 业务组件
import MockEditDialog from '@/components/business/MockEditDialog.vue'

// Composables
import { useAdminTable } from '@/composables/useAdminTable'
import { useToast } from '@/composables/useToast'
import { useConfirm } from '@/composables/useConfirm'

const route = useRoute()
const { showToast } = useToast()
const { showConfirm } = useConfirm()

// ========== 表格配置 ==========

// 表格列定义
const tableColumns = [
  { prop: 'id', label: 'ID', width: '80px', align: 'center' },
  { prop: 'source', label: '来源机构', width: '150px', sortable: true },
  { prop: 'questionNumber', label: '题号', width: '80px', align: 'center', sortable: true },
  { prop: 'questionType', label: '题型', width: '100px', align: 'center' },
  { prop: 'title', label: '标题', minWidth: '250px' },
  { prop: 'category', label: '分类', width: '200px' },
  { prop: 'difficulty', label: '难度', width: '100px', align: 'center' },
  { prop: 'updateTime', label: '更新时间', width: '160px', sortable: true },
  { prop: 'actions', label: '操作', width: '200px', align: 'center', fixed: 'right' }
]

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
const editingMockId = ref(null)
const editingMockData = ref(null)  // 编辑时传递的完整数据（避免重复请求API）

// 模拟题列表
const mockQuestions = ref([])

// 来源机构选项（模拟题特有）
const sourceOptions = ref([])

// 筛选条件
const filters = reactive({
  source: '',
  subjectId: null,
  category: '',
  keyword: '',
  noCategory: false
})

/**
 * 加载来源机构选项（模拟题特有）
 */
const loadSourceOptions = async () => {
  try {
    const res = await getAllMockSources()
    if (res.code === 200) {
      // 后端返回的是 { sources: [{source, question_count}, ...] } 格式
      // 提取 source 字段为字符串数组
      sourceOptions.value = res.data?.sources?.map(item => item.source) || []
    }
  } catch (error) {
    console.error('加载来源机构列表失败:', error)
  }
}

/**
 * 加载模拟题列表
 */
const loadMockList = async () => {
  loading.value = true
  try {
    const response = await getMockQuestions({
      page: pagination.page,
      page_size: pagination.size,
      source: filters.source || undefined,
      subject_id: filters.subjectId || undefined,
      category: filters.category || undefined,
      keyword: filters.keyword || undefined,
      no_category: filters.noCategory || undefined,
      sort_field: sorting.sortField || undefined,
      sort_order: sorting.sortOrder || undefined
    })

    if (response.code === 200) {
      mockQuestions.value = response.data.data || []
      pagination.total = response.data.total || 0
    } else {
      showToast(response.message || '加载失败', 'error')
    }
  } catch (error) {
    console.error('加载模拟题列表失败:', error)
    showToast('加载失败，请检查网络连接', 'error')
  } finally {
    loading.value = false
  }
}

/**
 * 科目筛选变更
 */
const handleSubjectChange = async (subjectId) => {
  filters.subjectId = subjectId || null
  filters.category = ''
  await loadSubjectCategoryOptions(filters.subjectId, getMockCategoriesBySubject)
}

/**
 * 处理查询
 */
const handleSearch = () => {
  pagination.page = 1
  loadMockList()
}

/**
 * 处理重置
 */
const handleReset = () => {
  filters.source = ''
  filters.subjectId = null
  filters.category = ''
  filters.keyword = ''
  filters.noCategory = false
  categoryOptions.value = []
  sorting.sortField = null
  sorting.sortOrder = null
  pagination.page = 1
  clearUrlKeyword()
  loadMockList()
}

/**
 * 处理排序变化（使用公共方法进行字段名和排序方向转换）
 */
const handleSortChange = (sortInfo) => {
  baseSortChange(sortInfo, loadMockList)
}

/**
 * 处理新增（打开编辑弹窗，不传ID表示新建）
 */
const handleAdd = () => {
  editingMockId.value = null
  editDialogVisible.value = true
}

/**
 * 处理查看（在新标签页打开题目浏览页）
 * 构建URL: /mock?subject=科目名称#mock-题目ID
 */
const handleView = (row) => {
  const subjectName = subjectMap.value[row.subjectId]
  if (!subjectName) {
    showToast('无法获取题目所属科目信息', 'warning')
    return
  }
  // 构建URL，使用hash定位到具体题目卡片
  const url = `/mock?subject=${encodeURIComponent(subjectName)}#mock-${row.id}`
  window.open(url, '_blank')
}

/**
 * 处理编辑（打开编辑弹窗）
 */
const handleEdit = (row) => {
  editingMockId.value = row.id
  editingMockData.value = row  // 传递完整数据，避免重复请求API
  editDialogVisible.value = true
}

/**
 * 编辑成功回调
 */
const handleEditSuccess = () => {
  loadMockList()
  // 重置编辑数据
  editingMockId.value = null
  editingMockData.value = null
}

/**
 * 处理删除
 */
const handleDelete = async (row) => {
  try {
    // 使用自定义Confirm替代ElMessageBox
    const confirmed = await showConfirm({
      title: '确认删除',
      message: `确定要删除模拟题"${row.title || row.source + ' 第' + row.questionNumber + '题'}"吗？`,
      confirmText: '确定删除',
      cancelText: '取消',
      type: 'danger'
    })

    if (!confirmed) return

    row.deleteLoading = true
    const response = await deleteMockQuestion(row.id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      loadMockList()
    } else {
      showToast(response.message || '删除失败', 'error')
    }
  } catch (error) {
    console.error('删除失败:', error)
    showToast('删除失败，请稍后重试', 'error')
  } finally {
    if (row) row.deleteLoading = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadSourceOptions()
  loadSubjectOptions()
  // 从URL获取keyword参数
  const urlKeyword = getUrlKeyword()
  if (urlKeyword) {
    filters.keyword = urlKeyword
  }
  loadMockList()
})

// 监听路由变化，支持导航栏搜索跳转
watch(() => route.query.keyword, (newKeyword) => {
  if (newKeyword !== undefined) {
    filters.keyword = newKeyword || ''
    pagination.page = 1
    loadMockList()
  }
})
</script>

<style scoped>
/**
 * 模拟题管理页面样式
 * 大部分样式已迁移到Tailwind类
 */

/* 响应式布局 */
@media (max-width: 768px) {
  .max-w-\[1400px\] {
    padding-left: 8px;
    padding-right: 8px;
  }
}

/* 固定操作列样式 */
:deep(.actions-cell) {
  position: sticky;
  right: 0;
  background: white;
}
</style>
