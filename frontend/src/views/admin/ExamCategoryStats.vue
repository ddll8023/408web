<template>
  <main class="min-h-[calc(100vh-60px)]">
    <div class="stats-page mx-auto max-w-[1400px] px-4 py-6 md:px-6 md:py-8">
      <!-- 页面标题与操作 -->
      <header class="mb-6 flex flex-col gap-5 border-b border-[#8B6F47]/10 pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div class="mb-2 flex items-center gap-2 text-xs font-semibold tracking-[0.16em] text-[#8B6F47]">
            <span class="inline-flex h-6 w-6 items-center justify-center rounded-md bg-[#8B6F47] text-white shadow-sm">
              <font-awesome-icon :icon="['fas', 'chart-bar']" aria-hidden="true" />
            </span>
            <span>统计看板</span>
            <span class="font-normal tracking-normal text-gray-400">/</span>
            <span class="font-normal tracking-normal text-gray-500">按科目查看分类明细</span>
          </div>
          <h1 class="m-0 text-2xl font-semibold tracking-tight text-gray-900 md:text-[1.75rem]">真题分类统计</h1>
          <p class="mb-0 mt-2 text-sm text-gray-500">
            按科目查看章节与知识点明细，支持折叠和题型排序。
          </p>
        </div>

        <Dropdown
          trigger="click"
          :disabled="statsLoading || exportLoading || !hasStats"
          @command="handleExportCommand"
        >
          <template #trigger>
            <CustomButton
              type="success"
              :loading="exportLoading"
              :disabled="!hasStats"
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
      </header>

      <!-- 筛选与明细排序 -->
      <section
        class="mb-6 flex flex-col gap-4 rounded-2xl border border-[#8B6F47]/10 bg-white/80 p-4 shadow-sm lg:flex-row lg:items-center lg:justify-between"
        aria-label="统计筛选与视图工具"
      >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label for="stats-subject" class="whitespace-nowrap text-sm font-semibold text-gray-700">统计科目</label>
          <Select
            id="stats-subject"
            v-model="statsSubjectId"
            :options="subjectOptions"
            placeholder="全部科目"
            aria-label="统计科目"
            clearable
            @change="loadStats"
            class="w-full sm:w-64"
          />
          <CustomButton type="primary" size="sm" :loading="statsLoading" @click="loadStats">
            <font-awesome-icon :icon="['fas', 'sync']" class="mr-1.5" aria-hidden="true" />
            刷新数据
          </CustomButton>
        </div>

        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end">
          <span class="whitespace-nowrap text-xs font-semibold text-gray-500">明细排序</span>
          <div class="flex flex-wrap gap-1 rounded-lg bg-[#FBF7F2] p-1" role="group" aria-label="分类明细排序">
            <button
              v-for="option in sortOptions"
              :key="option.label"
              type="button"
              class="inline-flex h-8 items-center gap-1 rounded-md px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#8B6F47] focus-visible:ring-offset-1"
              :class="isSortActive(option.prop)
                ? 'bg-[#8B6F47] text-white shadow-sm'
                : 'text-gray-600 hover:bg-white hover:text-[#8B6F47]'"
              :aria-pressed="isSortActive(option.prop)"
              @click="handleSortOption(option.prop)"
            >
              <span>{{ option.label }}</span>
              <font-awesome-icon
                v-if="option.prop && isSortActive(option.prop)"
                :icon="sortConfig.order === 'ascending' ? ['fas', 'sort-up'] : ['fas', 'sort-down']"
                aria-hidden="true"
              />
            </button>
          </div>
        </div>
      </section>

      <div
        v-if="statsError"
        class="mb-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        role="alert"
      >
        {{ statsError }}
        <CustomButton size="sm" type="text" :disabled="statsLoading" @click="loadStats">重试</CustomButton>
      </div>

      <!-- 首次加载骨架屏 -->
      <div v-if="statsLoading && !hasStats" class="space-y-5" aria-busy="true" aria-live="polite">
        <div class="h-96 animate-pulse rounded-2xl bg-white/70 shadow-sm"></div>
      </div>

      <template v-else-if="hasStats">
        <!-- 分组明细 -->
        <section class="overflow-hidden rounded-2xl border border-[#8B6F47]/10 bg-white shadow-sm" aria-labelledby="category-detail-title" :aria-busy="statsLoading">
          <header class="flex flex-col gap-3 border-b border-gray-100 px-5 py-4 md:flex-row md:items-center md:justify-between md:px-6">
            <div>
              <div class="flex items-center gap-2">
                <h2 id="category-detail-title" class="m-0 text-lg font-semibold text-gray-900">分类明细</h2>
                <span v-if="statsLoading" class="inline-flex items-center gap-1 text-xs font-normal text-[#8B6F47]" role="status">
                  <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin" aria-hidden="true" />
                  正在刷新
                </span>
              </div>
              <p class="mb-0 mt-1 text-xs text-gray-500">章节显示子树合计，知识点显示自身直接引用；数字旁的条形用于快速比较。</p>
            </div>
            <div class="flex items-center gap-1">
              <CustomButton type="text" size="sm" @click="expandAllSections">
                <font-awesome-icon :icon="['fas', 'chevron-down']" class="mr-1" aria-hidden="true" />
                全部展开
              </CustomButton>
              <CustomButton type="text" size="sm" @click="collapseAllSections">
                <font-awesome-icon :icon="['fas', 'chevron-right']" class="mr-1" aria-hidden="true" />
                全部收起
              </CustomButton>
            </div>
          </header>

          <div class="space-y-5 p-4 md:p-6">
            <div v-for="view in detailGroups" :key="`detail-${view.group.subjectId ?? 'unassigned'}`">
              <div
                v-if="showSubjectGroupLabels"
                class="mb-3 flex items-center justify-between gap-3 rounded-lg bg-[#FBF7F2] px-3 py-2 text-sm"
              >
                <span class="flex items-center gap-2 font-semibold text-[#8B6F47]">
                  <font-awesome-icon :icon="['fas', 'folder']" aria-hidden="true" />
                  {{ view.group.subjectName }}
                </span>
                <span class="text-xs text-gray-500">{{ formatNumber(view.group.totalCount) }} 道去重题目</span>
              </div>

              <div class="space-y-3">
                <section
                  v-for="section in view.sections"
                  :id="getSectionDomId(section.key)"
                  :key="section.key"
                  class="scroll-mt-6 overflow-hidden rounded-xl border"
                  :class="section.row.isUnfiled ? 'border-amber-200' : 'border-gray-100'"
                >
                  <button
                    type="button"
                    class="flex w-full flex-col gap-3 px-4 py-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#8B6F47] md:flex-row md:items-center md:justify-between"
                    :class="section.row.isUnfiled ? 'bg-amber-50 hover:bg-amber-100' : 'bg-[#FBF7F2]/70 hover:bg-[#FBF7F2]'"
                    :aria-expanded="isSectionExpanded(section.key)"
                    :aria-controls="`${getSectionDomId(section.key)}-content`"
                    @click="toggleSection(section.key)"
                  >
                    <div class="flex min-w-0 items-center gap-3">
                      <span
                        class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs"
                        :class="section.row.isUnfiled ? 'bg-amber-100 text-amber-700' : 'bg-[#8B6F47]/10 text-[#8B6F47]'"
                      >
                        <font-awesome-icon
                          :icon="isSectionExpanded(section.key) ? ['fas', 'chevron-down'] : ['fas', 'chevron-right']"
                          aria-hidden="true"
                        />
                      </span>
                      <span
                        class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md"
                        :class="section.row.isUnfiled ? 'bg-amber-500 text-white' : 'bg-[#8B6F47] text-white'"
                      >
                        <font-awesome-icon :icon="section.row.isUnfiled ? ['fas', 'triangle-exclamation'] : ['fas', 'folder-open']" aria-hidden="true" />
                      </span>
                      <span class="min-w-0 truncate font-semibold" :class="section.row.isUnfiled ? 'text-amber-900' : 'text-gray-800'">
                        {{ section.row.category }}
                      </span>
                      <span
                        class="shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium"
                        :class="section.row.isUnfiled ? 'bg-white/80 text-amber-700' : 'bg-white text-[#8B6F47]'"
                      >
                        {{ section.row.scope }}
                      </span>
                      <span v-if="!section.row.enabled && !section.row.isUnfiled" class="shrink-0 rounded-full bg-orange-50 px-2 py-0.5 text-[11px] font-medium text-orange-600">已禁用</span>
                    </div>

                    <div class="flex shrink-0 items-center gap-3 pl-20 text-xs text-gray-500 md:pl-0">
                      <span class="whitespace-nowrap"><b class="text-lg font-semibold text-gray-900">{{ formatNumber(section.row.count) }}</b><span class="ml-1">题</span></span>
                      <span class="whitespace-nowrap"><b class="font-semibold text-[#5D88AE]">{{ formatNumber(section.row.choiceCount) }}</b> 选择</span>
                      <span class="whitespace-nowrap"><b class="font-semibold text-[#B87542]">{{ formatNumber(section.row.subjectiveCount) }}</b> 主观</span>
                    </div>
                  </button>

                  <div v-show="isSectionExpanded(section.key)" :id="`${getSectionDomId(section.key)}-content`" class="border-t border-gray-100 bg-white">
                    <div v-if="section.children.length > 0" class="overflow-x-auto">
                      <table class="category-detail-table w-full min-w-[720px] border-collapse">
                        <thead>
                          <tr class="border-b border-gray-100 bg-gray-50/80 text-left text-xs font-semibold text-gray-500">
                            <th scope="col" class="px-4 py-3 md:px-5">分类</th>
                            <th scope="col" class="w-[190px] px-4 py-3 text-right md:px-5">总题数（相对题量）</th>
                            <th scope="col" class="w-[110px] px-4 py-3 text-right md:px-5">选择题</th>
                            <th scope="col" class="w-[110px] px-4 py-3 text-right md:px-5">主观题</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr
                            v-for="row in section.children"
                            :key="row.id"
                            class="border-b border-gray-50 transition-colors last:border-0 hover:bg-[#FBF7F2]/60"
                          >
                            <td class="px-4 py-3 md:px-5">
                              <div class="flex min-w-0 items-center gap-2" :style="{ paddingLeft: `${Math.max(0, row.level - 1) * 1.25}rem` }">
                                <span class="tree-marker" :class="row.hasChildren ? 'tree-marker-parent' : 'tree-marker-leaf'" aria-hidden="true"></span>
                                <span class="min-w-0 truncate text-sm" :class="row.enabled || row.isUnfiled ? 'text-gray-700' : 'text-gray-400'">{{ row.category }}</span>
                                <span
                                  class="shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium"
                                  :class="row.isUnfiled ? 'bg-gray-100 text-gray-500' : row.hasChildren ? 'bg-[#8B6F47]/10 text-[#8B6F47]' : 'bg-blue-50 text-blue-600'"
                                >
                                  {{ row.scope }}
                                </span>
                                <span v-if="!row.enabled && !row.isUnfiled" class="shrink-0 text-[10px] text-orange-500">已禁用</span>
                              </div>
                            </td>
                            <td class="px-4 py-3 text-right md:px-5">
                              <div class="flex flex-col items-end gap-1.5">
                                <span class="text-sm font-semibold text-gray-800">{{ formatNumber(row.count) }}</span>
                                <div class="h-1.5 w-full max-w-[130px] overflow-hidden rounded-full bg-gray-100" aria-hidden="true">
                                  <div class="h-full rounded-full bg-[#8B6F47]/65 transition-[width] duration-300" :style="{ width: getBarWidth(row.count, section.maxChildCount) }"></div>
                                </div>
                              </div>
                            </td>
                            <td class="px-4 py-3 text-right text-sm font-medium text-[#5D88AE] md:px-5">{{ formatNumber(row.choiceCount) }}</td>
                            <td class="px-4 py-3 text-right text-sm font-medium text-[#B87542] md:px-5">{{ formatNumber(row.subjectiveCount) }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                    <p v-else class="mb-0 px-5 py-5 text-sm text-gray-400">
                      当前章节暂无下级知识点，章节题量已在上方合计。
                    </p>
                  </div>
                </section>
              </div>
            </div>
          </div>
        </section>

        <!-- 数据质量提示 -->
        <section
          v-if="hasDataQualityNotice"
          class="mt-6 rounded-2xl border border-amber-200 bg-amber-50/80 p-4 md:p-5"
          aria-labelledby="data-quality-title"
        >
          <div class="flex items-start gap-3">
            <span class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-500 text-white">
              <font-awesome-icon :icon="['fas', 'triangle-exclamation']" aria-hidden="true" />
            </span>
            <div class="min-w-0">
              <h2 id="data-quality-title" class="m-0 text-sm font-semibold text-amber-900">需要留意的分类数据</h2>
              <p class="mb-0 mt-1 text-sm leading-6 text-amber-800">
                <template v-if="unfiledTagCount > 0">有 <b>{{ formatNumber(unfiledTagCount) }}</b> 个标签未归档，已在明细末尾单独列出。</template>
                <template v-if="unfiledTagCount > 0 && disabledCategoryCount > 0">；</template>
                <template v-if="disabledCategoryCount > 0">有 <b>{{ formatNumber(disabledCategoryCount) }}</b> 个分类已禁用，但历史统计仍予以保留。</template>
              </p>
            </div>
          </div>
        </section>
      </template>

      <!-- 空状态 -->
      <div v-else class="rounded-2xl border border-dashed border-[#8B6F47]/20 bg-white/70 px-6 py-16 text-center shadow-sm">
        <font-awesome-icon :icon="['fas', 'inbox']" class="mb-4 text-4xl text-[#8B6F47]/30" aria-hidden="true" />
        <h2 class="m-0 text-lg font-semibold text-gray-700">当前范围暂无分类统计</h2>
        <p class="mb-0 mt-2 text-sm text-gray-400">请先录入带有分类的真题，或切换其他科目。</p>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
/**
 * 真题分类统计页面
 * 功能描述：按科目以可折叠分组明细展示真题分类统计，支持题型排序与 Markdown/Excel 导出
 * 依赖组件：CustomButton, Dropdown, DropdownItem, Select, Toast
 */

// 1. Vue 官方 API
import { computed, onMounted, ref } from 'vue'

// 2. API 接口定义
import { exportExamCategoryStats, getExamCategoryStats } from '@/api/exam'
import { getEnabledSubjects } from '@/api/subject'

// 3. 子组件导入
import CustomButton from '@/components/basic/CustomButton.vue'
import Dropdown from '@/components/basic/Dropdown.vue'
import DropdownItem from '@/components/basic/DropdownItem.vue'
import Select from '@/components/basic/Select.vue'
import Toast from '@/utils/toast'
import type { TableSort } from '@/components/basic/types'
import type {
  ExamCategoryStatsTreeItem,
  ExamSubjectCategoryStats,
  Subject
} from '@/types'

type FrequencySortProp = 'choiceCount' | 'subjectiveCount' | 'count'

type DisplayCounts = {
  count: number
  choiceCount: number
  subjectiveCount: number
}

type StatsRow = DisplayCounts & {
  id: string
  subjectName: string
  category: string
  scope: string
  level: number
  isChapter: boolean
  hasChildren: boolean
  enabled: boolean
  isUnfiled: boolean
}

type CategorySection = {
  key: string
  row: StatsRow
  children: StatsRow[]
  maxChildCount: number
}

type StatsGroupView = {
  group: ExamSubjectCategoryStats
  chapters: CategorySection[]
  unfiled: CategorySection[]
  sections: CategorySection[]
}

const statsLoading = ref(false)
const exportLoading = ref(false)
const statsData = ref<StatsRow[]>([])
const statsTree = ref<ExamSubjectCategoryStats[]>([])
const statsSubjectId = ref<number | null>(null)
const subjectOptions = ref<Subject[]>([])
const statsError = ref('')
const expandedSections = ref<Set<string>>(new Set())
let statsLoadVersion = 0

const sortConfig = ref<TableSort>({ prop: null, order: null })
const sortOptions = [
  { prop: null, label: '目录顺序' },
  { prop: 'count', label: '总题数' },
  { prop: 'choiceCount', label: '选择题' },
  { prop: 'subjectiveCount', label: '主观题' }
] as const satisfies ReadonlyArray<{ prop: FrequencySortProp | null; label: string }>

const isFrequencySortProp = (prop: string | null): prop is FrequencySortProp => {
  return prop === 'choiceCount' || prop === 'subjectiveCount' || prop === 'count'
}

const formatNumber = (value: number) => value.toLocaleString('zh-CN')

const getSubjectKey = (group: ExamSubjectCategoryStats) => `subject:${group.subjectId ?? 'unassigned'}`

const getNodeKey = (node: ExamCategoryStatsTreeItem, parentKey: string) => {
  return node.categoryId === null
    ? `${parentKey}:${node.categoryName}`
    : `${parentKey}:${node.categoryId}`
}

const getDisplayCounts = (node: ExamCategoryStatsTreeItem, level: number): DisplayCounts => {
  const useSubtree = node.children.length > 0 || level === 0
  return {
    count: useSubtree ? node.subtreeCount : node.count,
    choiceCount: useSubtree ? node.subtreeChoiceCount : node.choiceCount,
    subjectiveCount: useSubtree ? node.subtreeSubjectiveCount : node.subjectiveCount
  }
}

const getScope = (node: ExamCategoryStatsTreeItem, level: number) => {
  const isChapter = level === 0
  const hasChildren = node.children.length > 0
  if (node.isUnfiled && isChapter) return '待整理汇总'
  if (isChapter) return '章节合计'
  if (hasChildren) return '分类组汇总'
  if (node.isUnfiled) return '未归档标签'
  return '知识点直接引用'
}

const createStatsRow = (
  node: ExamCategoryStatsTreeItem,
  level: number,
  parentKey: string,
  subjectName = ''
): StatsRow => {
  const counts = getDisplayCounts(node, level)
  return {
    ...counts,
    id: getNodeKey(node, parentKey),
    subjectName,
    category: node.categoryName,
    scope: getScope(node, level),
    level,
    isChapter: level === 0,
    hasChildren: node.children.length > 0,
    enabled: node.enabled,
    isUnfiled: node.isUnfiled
  }
}

const getNodeSortValue = (
  node: ExamCategoryStatsTreeItem,
  level: number,
  prop: FrequencySortProp
) => {
  return getDisplayCounts(node, level)[prop]
}

const getSortedNodes = (nodes: ExamCategoryStatsTreeItem[], level: number) => {
  const { prop, order } = sortConfig.value
  if (!isFrequencySortProp(prop) || !order) return nodes

  const direction = order === 'ascending' ? 1 : -1
  return [...nodes].sort((left, right) => {
    const valueDifference = getNodeSortValue(left, level, prop) - getNodeSortValue(right, level, prop)
    if (valueDifference !== 0) return direction * valueDifference
    const orderDifference = left.orderNum - right.orderNum
    if (orderDifference !== 0) return orderDifference
    return (left.categoryId ?? 0) - (right.categoryId ?? 0)
  })
}

const flattenNodes = (
  nodes: ExamCategoryStatsTreeItem[],
  level: number,
  parentKey: string,
  subjectName: string,
  shouldSort: boolean
): StatsRow[] => {
  const rows: StatsRow[] = []
  const orderedNodes = shouldSort ? getSortedNodes(nodes, level) : nodes

  orderedNodes.forEach(node => {
    const row = createStatsRow(node, level, parentKey, subjectName)
    rows.push(row)
    rows.push(...flattenNodes(node.children, level + 1, row.id, subjectName, shouldSort))
  })

  return rows
}

/**
 * 根据分类统计树生成默认表格数据，保持科目和目录树的原始顺序。
 */
const flattenCategoryTree = (groups: ExamSubjectCategoryStats[]): StatsRow[] => {
  const rows: StatsRow[] = []

  groups.forEach(group => {
    const subjectKey = getSubjectKey(group)
    rows.push(...flattenNodes(group.categories, 0, subjectKey, group.subjectName, false))
  })

  return rows
}

const buildSection = (
  node: ExamCategoryStatsTreeItem,
  parentKey: string,
  subjectName: string
): CategorySection => {
  const row = createStatsRow(node, 0, parentKey, subjectName)
  const children = flattenNodes(node.children, 1, row.id, subjectName, true)
  return {
    key: row.id,
    row,
    children,
    maxChildCount: Math.max(0, ...children.map(child => child.count))
  }
}

const detailGroups = computed<StatsGroupView[]>(() => {
  return statsTree.value.map(group => {
    const subjectKey = getSubjectKey(group)
    const formalNodes = getSortedNodes(
      group.categories.filter(node => !node.isUnfiled),
      0
    )
    const unfiledNodes = group.categories.filter(node => node.isUnfiled)
    const chapters = formalNodes.map(node => buildSection(node, subjectKey, group.subjectName))
    const unfiled = unfiledNodes.map(node => buildSection(node, subjectKey, group.subjectName))

    return {
      group,
      chapters,
      unfiled,
      sections: [...chapters, ...unfiled]
    }
  })
})

const sectionKeys = computed(() => detailGroups.value.flatMap(view => view.sections.map(section => section.key)))
const hasStats = computed(() => statsData.value.length > 0)
const showSubjectGroupLabels = computed(() => statsSubjectId.value === null || statsTree.value.length > 1)

const countUnfiledTags = (nodes: ExamCategoryStatsTreeItem[]): number => {
  return nodes.reduce(
    (total, node) => total + (node.isUnfiled && node.children.length === 0 ? 1 : 0) + countUnfiledTags(node.children),
    0
  )
}

const unfiledTagCount = computed(() => {
  return statsTree.value.reduce((total, group) => total + countUnfiledTags(group.categories), 0)
})

const countDisabledCategories = (nodes: ExamCategoryStatsTreeItem[]): number => {
  return nodes.reduce(
    (total, node) => total + (!node.isUnfiled && !node.enabled ? 1 : 0) + countDisabledCategories(node.children),
    0
  )
}

const disabledCategoryCount = computed(() => {
  return statsTree.value.reduce((total, group) => total + countDisabledCategories(group.categories), 0)
})

const hasDataQualityNotice = computed(() => unfiledTagCount.value > 0 || disabledCategoryCount.value > 0)

const isSectionExpanded = (key: string) => expandedSections.value.has(key)

const expandAllSections = () => {
  expandedSections.value = new Set(sectionKeys.value)
}

const collapseAllSections = () => {
  expandedSections.value = new Set()
}

const toggleSection = (key: string) => {
  const next = new Set(expandedSections.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  expandedSections.value = next
}

const getSectionDomId = (key: string) => `stats-section-${encodeURIComponent(key)}`

const getBarWidth = (value: number, max: number) => {
  if (value <= 0 || max <= 0) return '0%'
  return `${Math.min(100, Math.max(0, (value / max) * 100))}%`
}

const isSortActive = (prop: FrequencySortProp | null) => {
  return prop === null ? sortConfig.value.prop === null : sortConfig.value.prop === prop
}

const handleSortOption = (prop: FrequencySortProp | null) => {
  if (prop === null) {
    sortConfig.value = { prop: null, order: null }
    return
  }

  if (sortConfig.value.prop !== prop || !sortConfig.value.order) {
    sortConfig.value = { prop, order: 'descending' }
    return
  }

  sortConfig.value = {
    prop,
    order: sortConfig.value.order === 'descending' ? 'ascending' : 'descending'
  }
}

/**
 * 加载科目选项。
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
 * 加载统计数据，并在成功后默认展开所有章节明细。
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
      expandedSections.value = new Set(sectionKeys.value)
    } else {
      statsTree.value = []
      statsData.value = []
      expandedSections.value = new Set()
      statsError.value = res.message || '获取统计数据失败，请重试。'
      Toast.error(res.message || '获取统计数据失败')
    }
  } catch (error) {
    if (requestVersion !== statsLoadVersion) return
    statsTree.value = []
    statsData.value = []
    expandedSections.value = new Set()
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

  const encodedFilename = /filename\\*=UTF-8''([^;]+)/i.exec(contentDisposition)?.[1]
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
  if (!hasStats.value) {
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
.stats-page {
  color-scheme: light;
}

.tree-marker {
  position: relative;
  display: inline-block;
  width: 10px;
  height: 10px;
  flex: 0 0 10px;
}

.tree-marker-parent::before {
  position: absolute;
  top: 1px;
  left: 1px;
  width: 8px;
  height: 8px;
  border: 2px solid #8b6f47;
  border-radius: 3px;
  content: '';
}

.tree-marker-leaf::before {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 5px;
  height: 5px;
  border-radius: 9999px;
  background: #9ca3af;
  content: '';
}

.category-detail-table th,
.category-detail-table td {
  vertical-align: middle;
}

@media (prefers-reduced-motion: reduce) {
  .stats-page *,
  .stats-page *::before,
  .stats-page *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
