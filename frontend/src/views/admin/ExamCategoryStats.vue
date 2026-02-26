<template>
  <div class="max-w-[1400px] mx-auto p-4 md:p-6 min-h-[calc(100vh-60px)]">
    <CustomCard shadow>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="m-0 text-xl text-[#333] font-semibold">真题分类统计</h2>
          <Dropdown trigger="click" @command="handleExportCommand">
            <template #trigger>
              <CustomButton type="success">
                <font-awesome-icon :icon="['fas', 'download']" class="mr-2" />
                导出统计
              </CustomButton>
            </template>

            <template #dropdown>
              <DropdownItem :command="'markdown-no-answer'">导出为 Markdown（不含答案）</DropdownItem>
              <DropdownItem :command="'markdown-with-answer'">导出为 Markdown（含答案）</DropdownItem>
              <DropdownItem :command="'xlsx'">导出为 Excel 文件 (.xlsx)</DropdownItem>
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

      <!-- 总计题目 -->
      <div class="mb-4 text-lg text-[#333]">
        <strong>总计题目：{{ totalQuestions }}</strong>
      </div>

      <!-- 统计表格 -->
      <Table :data="statsData" :columns="tableColumns" :loading="statsLoading">
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

<script setup>
/**
 * 真题分类统计页面
 * 功能描述：展示真题按分类的统计数据，支持按科目筛选和导出功能
 * 依赖组件：CustomCard, CustomButton, Dropdown, DropdownItem, Select, Table, Toast
 */

// 1. Vue 官方 API
import { ref, computed, onMounted } from 'vue'

// 2. API 接口定义
import { getExamCategoryStats } from '@/api/exam'
import { getEnabledSubjects } from '@/api/subject'

// 3. 子组件导入
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import Select from '@/components/basic/Select.vue'
import Table from '@/components/basic/Table.vue'
import Toast from '@/components/basic/Toast.vue'

// State
const statsLoading = ref(false)
const statsData = ref([])
const statsSubjectId = ref(null)
const subjectOptions = ref([])

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
  }
}

/**
 * 加载统计数据
 */
const loadStats = async () => {
  statsLoading.value = true
  try {
    const res = await getExamCategoryStats(statsSubjectId.value || undefined)
    if (res.code === 200 && res.data) {
      // 从 response 中提取 stats 数组
      const statsArray = res.data.stats || []
      // 转换字段名：从 snake_case 转为 camelCase
      statsData.value = statsArray.map(item => ({
        subjectName: res.data.subject_name || '全部科目',
        category: item.category,
        choiceCount: item.choice_count,
        subjectiveCount: item.subjective_count,
        count: item.count
      }))
    } else {
      Toast.error(res.message || '获取统计数据失败')
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    Toast.error('获取统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

/**
 * 计算总题数
 */
const totalQuestions = computed(() => {
  return statsData.value.reduce((sum, item) => sum + (item.count || 0), 0)
})

const handleExportCommand = (command) => {
  switch (command) {
    case 'markdown-no-answer':
      exportStats('markdown', false)
      break
    case 'markdown-with-answer':
      exportStats('markdown', true)
      break
    case 'xlsx':
      exportStats('xlsx', false)
      break
    default:
      Toast.warning('不支持的导出格式')
  }
}

const exportStats = (format, includeAnswer = false) => {
  if (!statsData.value || statsData.value.length === 0) {
    Toast.warning('暂无数据可导出')
    return
  }

  const subjectId = statsSubjectId.value

  let subjectName = '全部科目'
  if (subjectId !== null && subjectId !== undefined) {
    const found = subjectOptions.value.find((s) => s.id === subjectId)
    subjectName = (found && found.name) ? found.name : `科目${subjectId}`
  }

  let url = `/api/exam/category-stats/export?format=${format}&includeAnswer=${includeAnswer}`
  if (subjectId !== null && subjectId !== undefined) {
    url += `&subjectId=${subjectId}`
  }

  const link = document.createElement('a')
  link.href = url
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const dateStr = `${year}${month}${day}`

  let ext = 'md'
  if (format === 'docx') {
    ext = 'docx'
  } else if (format === 'xlsx') {
    ext = 'xlsx'
  }

  link.download = `真题分类统计_${subjectName}_${dateStr}.${ext}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  Toast.success('导出已开始')
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
