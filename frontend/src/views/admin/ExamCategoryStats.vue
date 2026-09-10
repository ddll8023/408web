<template>
  <div class="max-w-[1400px] mx-auto p-4 md:p-6 min-h-[calc(100vh-60px)]">
    <CustomCard shadow>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="m-0 text-xl text-[#333] font-semibold">真题分类统计</h2>
          <Dropdown
            trigger="click"
            :disabled="statsLoading || exportLoading || statsData.length === 0"
            @command="handleExportCommand"
          >
            <template #trigger>
              <CustomButton
                type="success"
                :loading="exportLoading"
                :disabled="statsData.length === 0"
                title="导出当前科目筛选范围的分类统计"
              >
                <font-awesome-icon :icon="['fas', 'download']" class="mr-2" aria-hidden="true" />
                导出统计
              </CustomButton>
            </template>

            <template #dropdown>
              <DropdownItem command="markdown">导出为 Markdown</DropdownItem>
              <DropdownItem command="xlsx">导出为 Excel 文件（.xlsx）</DropdownItem>
            </template>
          </Dropdown>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="mb-6 p-4 bg-gray-100 rounded flex items-center justify-between flex-wrap gap-4">
        <div class="flex items-center gap-4 flex-nowrap flex-shrink-0" style="min-width: max-content;">
          <span class="font-bold text-[#666] whitespace-nowrap">科目筛选:</span>
          <Select
            v-model="statsSubjectId"
            :options="subjectOptions"
            placeholder="全部科目"
            aria-label="科目筛选"
            clearable
            @change="loadStats"
            class="w-52"
          />
        </div>

        <CustomButton type="primary" @click="loadStats">
          <font-awesome-icon :icon="['fas', 'sync']" class="mr-2" />
          刷新数据
        </CustomButton>
      </div>

      <div v-if="statsError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
        {{ statsError }}
        <CustomButton size="sm" type="text" :disabled="statsLoading" @click="loadStats">重试</CustomButton>
      </div>

      <!-- 统计口径：去重总数与分类引用总数分开显示 -->
      <div class="mb-1 text-lg text-[#333]">
        <strong>去重题目总数：{{ totalExamCount }}</strong>
        <span class="ml-2 text-sm font-normal text-gray-500">
          分类引用总数：{{ totalCategoryReferences }}（一题多分类会分别计入）
        </span>
      </div>
      <p class="mb-4 text-sm text-gray-500">
        展示层级：科目 → 章节 → 知识点；有子级的目录节点显示子树合计，叶子知识点按直接引用统计；点击三个数量列的表头可切换升序/降序。
      </p>

      <!-- 统计表格 -->
      <Table
        :data="sortedStatsData"
        :columns="tableColumns"
        :loading="statsLoading"
        row-key="id"
        size="lg"
        @sort-change="handleSortChange"
      >
        <template #subjectName="{ row }">
          {{ row.subjectName }}
        </template>
        <template #category="{ row }">
          <div class="flex items-center gap-2" :style="{ paddingLeft: `${row.level * 1.5}rem` }">
            <span
              class="shrink-0 rounded px-1.5 py-0.5 text-xs"
              :class="row.isUnfiled ? 'bg-gray-100 text-gray-500' : row.isChapter ? 'bg-[#8B6F47]/10 text-[#8B6F47]' : 'bg-blue-50 text-blue-600'"
            >
              {{ row.isUnfiled && row.isChapter ? '待整理' : row.isChapter ? '章节' : '知识点' }}
            </span>
            <span :class="{ 'text-gray-400': !row.enabled && !row.isUnfiled }">{{ row.category }}</span>
            <span v-if="!row.enabled && !row.isUnfiled" class="text-xs text-orange-500">已禁用</span>
          </div>
        </template>
        <template #scope="{ row }">
          <span class="text-sm text-gray-500">{{ row.scope }}</span>
        </template>
        <template #choiceCount="{ row }">
          {{ row.choiceCount }}
        </template>
        <template #subjectiveCount="{ row }">
          {{ row.subjectiveCount }}
        </template>
        <template #count="{ row }">
          {{ row.count }}
        </template>
      </Table>
    </CustomCard>
  </div>
</template>

<script setup lang="ts">
/**
 * 真题分类统计页面
 * 功能描述：按科目、章节和知识点层级展示真题分类统计，支持三个数量列升序/降序和 Markdown/Excel 导出
 * 依赖组件：CustomCard, CustomButton, Dropdown, DropdownItem, Select, Table, Toast
 */

// 1. Vue 官方 API
import { computed, ref, onMounted } from 'vue'

// 2. API 接口定义
import { exportExamCategoryStats, getExamCategoryStats } from '@/api/exam'
import { getEnabledSubjects } from '@/api/subject'

// 3. 子组件导入
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import Select from '@/components/basic/Select.vue'
import Table from '@/components/basic/Table.vue'
import Toast from '@/utils/toast'
import type { TableSort } from '@/components/basic/types'
import type {
  ExamCategoryStatsTreeItem,
  ExamSubjectCategoryStats,
  Subject
} from '@/types'

type StatsRow = {
  id: string
  subjectName: string
  category: string
  scope: string
  level: number
  isChapter: boolean
  enabled: boolean
  isUnfiled: boolean
  choiceCount: number
  subjectiveCount: number
  count: number
}

type FrequencySortProp = 'choiceCount' | 'subjectiveCount' | 'count'

// State
const statsLoading = ref(false)
const exportLoading = ref(false)
const statsData = ref<StatsRow[]>([])
const statsTree = ref<ExamSubjectCategoryStats[]>([])
const statsSubjectId = ref<number | null>(null)
const subjectOptions = ref<Subject[]>([])
const totalExamCount = ref(0)
const totalCategoryReferences = ref(0)
const statsError = ref('')
let statsLoadVersion = 0

// 表格列配置
const tableColumns = [
  { prop: 'subjectName', label: '科目', width: '160' },
  { prop: 'category', label: '章节 / 知识点', minWidth: '280' },
  { prop: 'scope', label: '统计口径', width: '150' },
  { prop: 'choiceCount', label: '选择题数量', width: '130', sortable: true },
  { prop: 'subjectiveCount', label: '主观题数量', width: '130', sortable: true },
  { prop: 'count', label: '总题数', width: '120', sortable: true }
]

/**
 * 根据分类统计树生成默认表格行；默认顺序保持科目和目录树层级。
 */
const flattenCategoryTree = (
  groups: ExamSubjectCategoryStats[],
  sortProp: FrequencySortProp | null = null,
  direction = 1
): StatsRow[] => {
  const rows: StatsRow[] = []

  const getNodeSortValue = (node: ExamCategoryStatsTreeItem, level: number) => {
    const useSubtree = node.children.length > 0 || level === 0
    if (sortProp === 'choiceCount') {
      return useSubtree ? node.subtreeChoiceCount : node.choiceCount
    }
    if (sortProp === 'subjectiveCount') {
      return useSubtree ? node.subtreeSubjectiveCount : node.subjectiveCount
    }
    return useSubtree ? node.subtreeCount : node.count
  }

  groups.forEach(group => {
    const appendNodes = (
      nodes: ExamCategoryStatsTreeItem[],
      level: number,
      parentKey: string
    ) => {
      const orderedNodes = sortProp
        ? [...nodes].sort((left, right) => {
            const valueDifference = getNodeSortValue(left, level) - getNodeSortValue(right, level)
            if (valueDifference !== 0) return direction * valueDifference
            const orderDifference = left.orderNum - right.orderNum
            if (orderDifference !== 0) return orderDifference
            return (left.categoryId ?? 0) - (right.categoryId ?? 0)
          })
        : nodes

      orderedNodes.forEach(node => {
        const isChapter = level === 0
        const hasChildren = node.children.length > 0
        const useSubtree = hasChildren || isChapter
        const scope = node.isUnfiled && isChapter
          ? '未归档汇总'
          : isChapter
            ? '章节合计'
            : hasChildren
              ? '知识点组汇总'
              : node.isUnfiled
                ? '未归档标签'
                : '知识点直接引用'
        const nodeKey = node.categoryId === null
          ? `${parentKey}:${node.categoryName}`
          : `${parentKey}:${node.categoryId}`

        rows.push({
          id: nodeKey,
          subjectName: group.subjectName,
          category: node.categoryName,
          scope,
          level,
          isChapter,
          enabled: node.enabled,
          isUnfiled: node.isUnfiled,
          choiceCount: useSubtree ? node.subtreeChoiceCount : node.choiceCount,
          subjectiveCount: useSubtree ? node.subtreeSubjectiveCount : node.subjectiveCount,
          count: useSubtree ? node.subtreeCount : node.count
        })
        appendNodes(node.children, level + 1, nodeKey)
      })
    }

    appendNodes(group.categories, 0, `subject:${group.subjectId ?? 'unassigned'}`)
  })

  return rows
}

const isFrequencySortProp = (prop: string | null): prop is FrequencySortProp => {
  return prop === 'choiceCount' || prop === 'subjectiveCount' || prop === 'count'
}

const sortConfig = ref<TableSort>({ prop: null, order: null })
const sortedStatsData = computed(() => {
  const { prop, order } = sortConfig.value
  if (!isFrequencySortProp(prop) || !order) return statsData.value
  return flattenCategoryTree(
    statsTree.value,
    prop,
    order === 'ascending' ? 1 : -1
  )
})

const handleSortChange = (sort: TableSort) => {
  sortConfig.value = sort
}

/**
 * 加载科目选项
 */
const loadSubjectOptions = async () => {
  try {
    const res = await getEnabledSubjects()
    if (res.code === 200) {
      subjectOptions.value = res.data || []
    }
  } catch (error) {
    console.error('加载科目列表失败:', error)
    Toast.error('加载科目列表失败')
  }
}

/**
 * 加载统计数据
 */
const loadStats = async () => {
  const requestVersion = ++statsLoadVersion
  statsLoading.value = true
  try {
    const res = await getExamCategoryStats(statsSubjectId.value || undefined)
    if (requestVersion !== statsLoadVersion) return
    if (res.code === 200 && res.data) {
      statsError.value = ''
      statsTree.value = res.data.categoryTree || []
      statsData.value = flattenCategoryTree(statsTree.value)
      totalExamCount.value = res.data.totalCount ?? 0
      totalCategoryReferences.value = res.data.categoryReferenceCount ?? res.data.stats.reduce(
        (sum, item) => sum + (item.count || 0),
        0
      )
    } else {
      statsTree.value = []
      statsData.value = []
      totalExamCount.value = 0
      totalCategoryReferences.value = 0
      statsError.value = res.message || '获取统计数据失败，请重试。'
      Toast.error(res.message || '获取统计数据失败')
    }
  } catch (error) {
    if (requestVersion !== statsLoadVersion) return
    statsTree.value = []
    statsData.value = []
    totalExamCount.value = 0
    totalCategoryReferences.value = 0
    statsError.value = '获取统计数据失败，请重试。'
    console.error('获取统计数据失败:', error)
    Toast.error('获取统计数据失败')
  } finally {
    if (requestVersion === statsLoadVersion) statsLoading.value = false
  }
}

type ExportFormat = 'markdown' | 'xlsx'

const getExportFormat = (command: string): ExportFormat | null => {
  if (command === 'markdown' || command === 'xlsx') return command
  return null
}

const fallbackFilename = (format: ExportFormat) => {
  const subject = subjectOptions.value.find(item => item.id === statsSubjectId.value)
  const subjectName = (subject?.name || '全部科目').replace(/[\\/:*?"<>|]/g, '_')
  const date = new Date()
  const dateText = [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0')
  ].join('')
  return `真题分类统计_${subjectName}_${dateText}.${format === 'xlsx' ? 'xlsx' : 'md'}`
}

const getFilenameFromHeaders = (contentDisposition: unknown, fallback: string) => {
  if (typeof contentDisposition !== 'string') return fallback

  const encodedFilename = /filename\*=UTF-8''([^;]+)/i.exec(contentDisposition)?.[1]
  if (encodedFilename) {
    try {
      return decodeURIComponent(encodedFilename)
    } catch {
      return fallback
    }
  }

  const filename = /filename="?([^";]+)"?/i.exec(contentDisposition)?.[1]
  return filename || fallback
}

const downloadBlob = (blob: Blob, filename: string) => {
  const downloadUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(downloadUrl)
}

const handleExportCommand = async (command: string) => {
  const format = getExportFormat(command)
  if (!format) {
    Toast.warning('不支持的导出格式')
    return
  }
  if (statsData.value.length === 0) {
    Toast.warning('暂无数据可导出')
    return
  }

  exportLoading.value = true
  try {
    const response = await exportExamCategoryStats(statsSubjectId.value || undefined, format)
    const filename = getFilenameFromHeaders(
      response.headers['content-disposition'],
      fallbackFilename(format)
    )
    downloadBlob(response.data, filename)
    Toast.success(`${format === 'xlsx' ? 'Excel' : 'Markdown'} 导出已开始`)
  } catch (error) {
    console.error('导出分类统计失败:', error)
    Toast.error('导出失败，请重试')
  } finally {
    exportLoading.value = false
  }
}

onMounted(() => {
  loadSubjectOptions()
  loadStats()
})
</script>

<style scoped>
/**
 * 真题分类统计页面样式
 * 主要样式已迁移至 Tailwind CSS
 */
</style>
