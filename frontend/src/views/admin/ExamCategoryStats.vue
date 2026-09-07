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
      <div class="mb-4 text-lg text-[#333]">
        <strong>去重题目总数：{{ totalExamCount }}</strong>
        <span class="ml-2 text-sm font-normal text-gray-500">
          分类引用总数：{{ totalCategoryReferences }}（一题多分类会分别计入）
        </span>
      </div>

      <!-- 统计表格 -->
      <Table :data="statsData" :columns="tableColumns" :loading="statsLoading" size="lg">
        <template #subjectName="{ row }">
          {{ row.subjectName }}
        </template>
        <template #category="{ row }">
          {{ row.category }}
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
 * 功能描述：展示真题按分类的统计数据，支持按科目筛选和 Markdown/Excel 导出
 * 依赖组件：CustomCard, CustomButton, Dropdown, DropdownItem, Select, Table, Toast
 */

// 1. Vue 官方 API
import { ref, onMounted } from 'vue'

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
import type { Subject } from '@/types'

// State
const statsLoading = ref(false)
const exportLoading = ref(false)
const statsData = ref<{subjectName: string; category: string; choiceCount: number; subjectiveCount: number; count: number}[]>([])
const statsSubjectId = ref<number | null>(null)
const subjectOptions = ref<Subject[]>([])
const totalExamCount = ref(0)
const totalCategoryReferences = ref(0)
const statsError = ref('')
let statsLoadVersion = 0

// 表格列配置
const tableColumns = [
  { prop: 'subjectName', label: '科目', width: '180' },
  { prop: 'category', label: '分类', minWidth: '200' },
  { prop: 'choiceCount', label: '选择题数量', width: '130' },
  { prop: 'subjectiveCount', label: '主观题数量', width: '130' },
  { prop: 'count', label: '总题数', width: '120' }
]

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
      // 从 response 中提取 stats 数组
      const statsArray = res.data.stats || []
      // 响应键名已被拦截器统一转为驼峰，默认按总题数降序
      statsData.value = statsArray
        .map(item => ({
          subjectName: res.data.subjectName || '全部科目',
          category: item.categoryName,
          choiceCount: item.choiceCount,
          subjectiveCount: item.subjectiveCount,
          count: item.count
        }))
        .sort((a, b) => (b.count || 0) - (a.count || 0))
      totalExamCount.value = res.data.totalCount || 0
      totalCategoryReferences.value = res.data.categoryReferenceCount ?? statsArray.reduce(
        (sum, item) => sum + (item.count || 0),
        0
      )
    } else {
      statsData.value = []
      totalExamCount.value = 0
      totalCategoryReferences.value = 0
      statsError.value = res.message || '获取统计数据失败，请重试。'
      Toast.error(res.message || '获取统计数据失败')
    }
  } catch (error) {
    if (requestVersion !== statsLoadVersion) return
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
