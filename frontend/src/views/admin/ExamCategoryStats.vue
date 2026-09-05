<template>
  <div class="max-w-[1400px] mx-auto p-4 md:p-6 min-h-[calc(100vh-60px)]">
    <CustomCard shadow>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="m-0 text-xl text-[#333] font-semibold">真题分类统计</h2>
          <CustomButton type="default" disabled title="分类统计导出接口尚未提供">
            <font-awesome-icon :icon="['fas', 'download']" class="mr-2" aria-hidden="true" />
            导出统计（暂不可用）
          </CustomButton>
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

      <!-- 分类引用总数：一题多分类时会分别计入各分类 -->
      <div class="mb-4 text-lg text-[#333]">
        <strong>分类引用总数：{{ totalCategoryReferences }}</strong>
        <span class="ml-2 text-sm font-normal text-gray-500">一题多分类会分别计入对应分类</span>
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
 * 功能描述：展示真题按分类的统计数据，支持按科目筛选；分类统计导出等待后端接口
 * 依赖组件：CustomCard, CustomButton, Select, Table, Toast
 */

// 1. Vue 官方 API
import { ref, computed, onMounted } from 'vue'

// 2. API 接口定义
import { getExamCategoryStats } from '@/api/exam'
import { getEnabledSubjects } from '@/api/subject'

// 3. 子组件导入
import CustomCard from '@/components/basic/CustomCard.vue'
import CustomButton from '@/components/basic/CustomButton.vue'
import Select from '@/components/basic/Select.vue'
import Table from '@/components/basic/Table.vue'
import Toast from '@/utils/toast'
import type { Subject } from '@/types'

// State
const statsLoading = ref(false)
const statsData = ref<{subjectName: string; category: string; choiceCount: number; subjectiveCount: number; count: number}[]>([])
const statsSubjectId = ref<number | null>(null)
const subjectOptions = ref<Subject[]>([])
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
    } else {
      statsData.value = []
      statsError.value = res.message || '获取统计数据失败，请重试。'
      Toast.error(res.message || '获取统计数据失败')
    }
  } catch (error) {
    if (requestVersion !== statsLoadVersion) return
    statsData.value = []
    statsError.value = '获取统计数据失败，请重试。'
    console.error('获取统计数据失败:', error)
    Toast.error('获取统计数据失败')
  } finally {
    if (requestVersion === statsLoadVersion) statsLoading.value = false
  }
}

/**
 * 计算分类引用总数（一题多分类分别计入）
 */
const totalCategoryReferences = computed(() => {
  return statsData.value.reduce((sum, item) => sum + (item.count || 0), 0)
})

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
