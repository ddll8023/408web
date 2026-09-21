<!-- 改编题管理页面：筛选、表格、来源展示与分页按视口自适应。 -->
<template>
  <main class="admin-manage-page mx-auto min-h-[var(--app-page-height)] w-full max-w-[1600px] min-w-0 px-2 py-4 sm:px-4 sm:py-6">
    <CustomCard shadow>
      <template #header>
        <header class="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 class="m-0 text-xl font-semibold text-ink">改编题管理</h2>
          <div class="flex gap-2">
            <CustomButton type="primary" @click="handleAdd">
              <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" />
              新增改编题
            </CustomButton>
          </div>
        </header>
      </template>

      <!-- 筛选条件 -->
      <div class="mb-6 rounded-xl border border-[#eadfd4] bg-white/70 p-3 shadow-sm backdrop-blur-sm sm:p-5">
        <div class="grid grid-cols-1 items-end gap-4 sm:grid-cols-2 xl:grid-cols-6 2xl:grid-cols-8">
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">来源年份</label>
            <WheelPicker
              v-model="filters.sourceYear"
              :options="yearOptions"
              placeholder="选择年份"
              aria-label="来源年份"
              clearable
              class="w-full"
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">来源题号</label>
            <InputNumber
              :model-value="filters.sourceQuestionNumber ?? 0"
              :min="1"
              :max="47"
              placeholder="题号"
              aria-label="来源题号"
              @update:model-value="handleSourceNumberChange"
            />
          </div>
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">来源状态</label>
            <Select
              v-model="filters.sourceState"
              :options="sourceStateOptions"
              placeholder="全部"
              aria-label="来源状态"
              class="w-full"
            />
          </div>
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
          <div class="flex flex-col gap-1.5">
            <label class="text-sm font-medium text-gray-700">题型</label>
            <Select
              v-model="filters.questionType"
              :options="questionTypeOptions"
              placeholder="全部"
              aria-label="题型"
              clearable
              class="w-full"
            />
          </div>
          <div class="flex flex-col gap-1.5 sm:col-span-2 2xl:col-span-1">
            <label class="text-sm font-medium text-gray-700">关键词</label>
            <CustomInput
              v-model="filters.keyword"
              placeholder="搜索题干"
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
          <div class="flex justify-end gap-2 pb-0.5 sm:col-span-2 xl:col-span-1 xl:col-start-6 2xl:col-span-1 2xl:col-start-8 justify-self-end">
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
        <CustomButton size="sm" type="text" :disabled="loading" @click="loadAdaptationList">重试</CustomButton>
      </div>

      <section class="mt-6">
        <Table
          :data="questions"
          :columns="tableColumns"
          :loading="loading"
          size="md"
          @sort-change="handleSortChange"
        >
          <template #id="{ row }">{{ row.id }}</template>

          <template #questionType="{ row }">
            <Tag :type="row.questionType === 'CHOICE' ? 'success' : 'primary'" size="sm">
              {{ row.questionType === 'CHOICE' ? '选择题' : '主观题' }}
            </Tag>
          </template>

          <template #sourceSummary="{ row }">
            <span v-if="row.sources.length === 0" class="text-amber-600">未标注来源</span>
            <div v-else class="flex flex-wrap gap-1.5">
              <Tag
                v-for="source in row.sources"
                :key="`${source.sourceYear}-${source.sourceQuestionNumber}`"
                :type="source.sourceExists ? 'success' : 'warning'"
                size="sm"
                :title="source.sourceExists ? (source.examTitle || '已解析来源') : '真题库中未找到该来源'"
              >
                {{ source.sourceYear }}-{{ source.sourceQuestionNumber }}
              </Tag>
            </div>
          </template>

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

          <template #difficulty="{ row }">
            <Tag v-if="row.difficulty" :type="getDifficultyType(row.difficulty)" size="sm">
              {{ getDifficultyLabel(row.difficulty) }}
            </Tag>
            <span v-else class="text-gray-400">-</span>
          </template>

          <template #updateTime="{ row }">
            {{ formatDateTime(row.updateTime) }}
          </template>

          <template #actions="{ row }">
            <div class="flex items-center justify-center gap-1 whitespace-nowrap">
              <CustomButton
                type="text-primary"
                size="sm"
                class="!px-2.5 shrink-0 whitespace-nowrap"
                @click="handleEdit(row)"
              >编辑</CustomButton>
              <CustomButton
                type="text-danger"
                size="sm"
                class="!px-2.5 shrink-0 whitespace-nowrap"
                :loading="row.deleteLoading"
                @click="handleDelete(row)"
              >
                删除
              </CustomButton>
            </div>
          </template>
        </Table>

        <footer class="admin-pagination mt-6 flex justify-end border-t border-gray-100 pt-4">
          <Pagination
            v-model:currentPage="pagination.page"
            v-model:pageSize="pagination.size"
            :pageSizes="[10, 20, 50, 100]"
            :total="pagination.total"
            showTotal
            showSizes
            showJumper
            @current-change="loadAdaptationList"
            @size-change="loadAdaptationList"
          />
        </footer>
      </section>
    </CustomCard>

    <BackTop :right="32" :bottom="32">
      <div class="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-white shadow-lg transition-transform hover:scale-110">
        <font-awesome-icon :icon="['fas', 'arrow-up']" />
      </div>
    </BackTop>

    <AdaptationEditDialog
      v-model:visible="editDialogVisible"
      :adaptation-id="editingAdaptationId"
      @success="loadAdaptationList"
    />
  </main>
</template>

<script setup lang="ts">
/**
 * 改编题管理页面
 * 功能：改编题的查询、新增、编辑、删除与来源标注状态筛选（仅 ADMIN 可访问）
 * 依赖：useAdminTable 复用筛选、分页与排序逻辑
 */
import type { AdaptationQuestion, QuestionType } from '@/types'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { queryString } from '@/utils/storage'
import {
  deleteAdaptation,
  getAdaptationCategoriesBySubject,
  getAdaptationList
} from '@/api/adaptation'
import { getEnabledCategoryTreeBySubject } from '@/api/category'
import { useAdminTable } from '@/composables/useAdminTable'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import BackTop from '@/components/basic/BackTop.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import InputNumber from '@/components/basic/InputNumber.vue'
import MultiSelectCascader from '@/components/basic/MultiSelectCascader.vue'
import Pagination from '@/components/basic/Pagination.vue'
import Select from '@/components/basic/Select.vue'
import Table from '@/components/basic/Table.vue'
import Tag from '@/components/basic/Tag.vue'
import WheelPicker from '@/components/basic/WheelPicker.vue'
import AdaptationEditDialog from '@/components/business/AdaptationEditDialog.vue'

type QuestionRow = AdaptationQuestion & { deleteLoading?: boolean }

const route = useRoute()
const { showToast } = useToast()
const { showConfirm } = useConfirm()

const {
  loading,
  subjectOptions,
  categoryTreeOptions,
  sorting,
  pagination,
  getDifficultyLabel,
  getDifficultyType,
  formatDateTime,
  loadSubjectOptions,
  loadSubjectCategoryTreeOptions,
  handleSortChange: baseSortChange
} = useAdminTable()

const questions = ref<QuestionRow[]>([])
const listError = ref('')
let listRequestVersion = 0

const editDialogVisible = ref(false)
const editingAdaptationId = ref<number | null>(null)

const FIRST_EXAM_YEAR = 2009
const yearOptions = computed(() => {
  const lastYear = Math.max(new Date().getFullYear(), FIRST_EXAM_YEAR)
  const options: { label: string; value: number }[] = []
  for (let year = lastYear; year >= FIRST_EXAM_YEAR; year--) {
    options.push({ label: `${year} 年`, value: year })
  }
  return options
})

const questionTypeOptions = [
  { label: '选择题', value: 'CHOICE' },
  { label: '主观题', value: 'ESSAY' }
]
const sourceStateOptions = [
  { label: '全部', value: 'all' },
  { label: '已标注来源', value: 'with_source' },
  { label: '未标注来源', value: 'without_source' }
]

const tableColumns = [
  { prop: 'id', label: 'ID', width: '80px', align: 'center', sortable: true },
  { prop: 'questionType', label: '题型', width: '100px', align: 'center' },
  { prop: 'sourceSummary', label: '改编来源', minWidth: '240px' },
  { prop: 'category', label: '分类', width: '200px' },
  { prop: 'difficulty', label: '难度', width: '100px', align: 'center' },
  { prop: 'updateTime', label: '更新时间', width: '160px', sortable: true },
  { prop: 'actions', label: '操作', width: '220px', align: 'center', fixed: 'right' }
]

const filters = reactive({
  sourceYear: null as number | null,
  sourceQuestionNumber: null as number | null,
  sourceState: 'all' as 'all' | 'with_source' | 'without_source',
  subjectId: null as number | null,
  category: '',
  questionType: null as QuestionType | null,
  keyword: ''
})
const categorySelection = ref<string[]>([])

const handleSourceNumberChange = (value: number | null) => {
  filters.sourceQuestionNumber = typeof value === 'number' && value > 0 ? value : null
}

/** 加载改编题列表 */
const loadAdaptationList = async () => {
  const requestVersion = ++listRequestVersion
  listError.value = ''
  loading.value = true
  try {
    const response = await getAdaptationList({
      page: pagination.page,
      pageSize: pagination.size,
      sourceYear: filters.sourceYear || undefined,
      sourceQuestionNumber: filters.sourceQuestionNumber || undefined,
      sourceState: filters.sourceState,
      subjectId: filters.subjectId || undefined,
      category: filters.category || undefined,
      questionType: filters.questionType || undefined,
      keyword: filters.keyword || undefined,
      sortField: sorting.sortField || undefined,
      sortOrder: sorting.sortOrder || undefined
    })

    if (requestVersion !== listRequestVersion) return
    if (response.code === 200) {
      questions.value = response.data?.lists || []
      pagination.total = response.data?.pagination?.total || 0
    } else {
      questions.value = []
      listError.value = response.message || '改编题列表读取失败，请重试。'
      showToast(response.message || '加载失败', 'error')
    }
  } catch (error) {
    if (requestVersion !== listRequestVersion) return
    questions.value = []
    listError.value = '改编题列表读取失败，请重试。'
    showToast('加载改编题列表失败', 'error')
    console.error('加载改编题列表失败:', error)
  } finally {
    if (requestVersion === listRequestVersion) loading.value = false
  }
}

const handleSubjectChange = async (subjectId: string | number | null) => {
  filters.subjectId = subjectId ? Number(subjectId) : null
  filters.category = ''
  categorySelection.value = []
  await loadSubjectCategoryTreeOptions(
    filters.subjectId,
    getEnabledCategoryTreeBySubject,
    getAdaptationCategoriesBySubject,
  )
}

const handleCategoryFilterChange = (values: string[]) => {
  filters.category = values[0] || ''
}

const handleSearch = () => {
  pagination.page = 1
  loadAdaptationList()
}

const handleReset = () => {
  filters.sourceYear = null
  filters.sourceQuestionNumber = null
  filters.sourceState = 'all'
  filters.subjectId = null
  filters.category = ''
  filters.questionType = null
  filters.keyword = ''
  categoryTreeOptions.value = []
  categorySelection.value = []
  sorting.sortField = null
  sorting.sortOrder = null
  pagination.page = 1
  loadAdaptationList()
}

const handleSortChange = (sortInfo: Parameters<typeof baseSortChange>[0]) => {
  baseSortChange(sortInfo, loadAdaptationList)
}

const handleAdd = () => {
  editingAdaptationId.value = null
  editDialogVisible.value = true
}

const handleEdit = (row: QuestionRow) => {
  editingAdaptationId.value = row.id
  editDialogVisible.value = true
}

const handleDelete = async (row: QuestionRow) => {
  const label = `ID ${row.id}`
  const ok = await showConfirm({
    title: '警告',
    message: `确定要删除改编题"${label}"吗？其来源引用会一并删除。`,
    confirmText: '确定',
    cancelText: '取消',
    type: 'warning'
  })
  if (!ok) return

  row.deleteLoading = true
  try {
    const response = await deleteAdaptation(row.id)
    if (response.code === 200) {
      showToast('删除成功', 'success')
      loadAdaptationList()
    } else {
      showToast(response.message || '删除失败', 'error')
    }
  } catch (error) {
    showToast('删除失败', 'error')
    console.error('删除改编题失败:', error)
  } finally {
    row.deleteLoading = false
  }
}

onMounted(() => {
  loadSubjectOptions()
  const urlKeyword = route.query.keyword
  if (urlKeyword) {
    filters.keyword = queryString(urlKeyword)
  }
  loadAdaptationList()
})

watch(() => route.query.keyword, newKeyword => {
  if (newKeyword !== undefined) {
    filters.keyword = queryString(newKeyword)
    pagination.page = 1
    loadAdaptationList()
  }
})
</script>

<style scoped>
@media (max-width: 767px) {
  .admin-pagination {
    justify-content: center;
  }
}
</style>
