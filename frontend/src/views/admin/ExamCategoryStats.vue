<!-- 真题分类统计页面：按科目展示章节权重带与两层明细行（名称行 + 度量行），支持筛选、排序、折叠与导出。 -->
<template>
  <main class="min-h-[var(--app-page-height)]">
    <div class="stats-page mx-auto max-w-[1400px] px-4 py-6 md:px-6 md:py-8">
      <!-- 页面标题与操作 -->
      <header class="mb-6 flex flex-col gap-5 border-b border-accent/10 pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div class="mb-2 flex items-center gap-2 text-xs font-semibold tracking-[0.16em] text-accent">
            <span class="inline-flex h-6 w-6 items-center justify-center rounded-md bg-accent text-white shadow-sm">
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
        class="mb-6 flex flex-col gap-4 rounded-2xl border border-accent/10 bg-white/80 p-4 shadow-sm lg:flex-row lg:items-center lg:justify-between"
        aria-label="统计筛选与视图工具"
      >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label for="stats-subject" class="whitespace-nowrap text-sm font-semibold text-gray-700">统计科目</label>
          <Select
            id="stats-subject"
            v-model="statsSubjectId"
            :options="subjectOptions"
            placeholder="请选择科目"
            aria-label="统计科目"
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
          <div class="flex flex-wrap gap-1 rounded-lg bg-surface p-1" role="group" aria-label="分类明细排序">
            <button
              v-for="option in sortOptions"
              :key="option.label"
              type="button"
              class="inline-flex h-8 items-center gap-1 rounded-md px-2.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-1"
              :class="isSortActive(option.prop)
                ? 'bg-accent text-white shadow-sm'
                : 'text-gray-600 hover:bg-white hover:text-accent'"
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
        <section class="overflow-hidden rounded-2xl border border-accent/10 bg-white shadow-sm" aria-labelledby="category-detail-title" :aria-busy="statsLoading">
          <header class="flex flex-col gap-3 border-b border-gray-100 px-5 py-4 md:flex-row md:items-center md:justify-between md:px-6">
            <div>
              <div class="flex items-center gap-2">
                <h2 id="category-detail-title" class="m-0 text-lg font-semibold text-gray-900">分类明细</h2>
                <span v-if="statsLoading" class="inline-flex items-center gap-1 text-xs font-normal text-accent" role="status">
                  <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin" aria-hidden="true" />
                  正在刷新
                </span>
              </div>
              <ul class="stats-legend" aria-label="分类明细阅读说明">
                <li><span class="stats-legend__marker is-parent" aria-hidden="true"></span>分类组（汇总其下级知识点）</li>
                <li><span class="stats-legend__marker is-leaf" aria-hidden="true"></span>知识点（自身引用题数）</li>
                <li><span class="stats-legend__tick" aria-hidden="true"></span>0 题只留刻度，不画空轨道</li>
                <li>题量右侧「选 · 主」＝选择题 · 主观题</li>
                <li class="stats-legend__wide">
                  <span class="stats-legend__seg" aria-hidden="true"><i class="is-choice"></i><i class="is-subject"></i></span>
                  条长按分组最大值等比缩放：章级满格＝本科目最大章节题量，子级满格＝同章节最大知识点，只用于同组内比较。
                </li>
              </ul>
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
                class="mb-3 rounded-lg bg-surface px-3 py-2 text-sm"
              >
                <div class="flex flex-wrap items-center gap-2 font-semibold text-accent">
                  <font-awesome-icon :icon="['fas', 'folder']" aria-hidden="true" />
                  <span>{{ view.group.subjectName }}</span>
                  <span class="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-gray-600">
                    {{ formatNumber(view.group.totalCount) }} 道去重题目
                  </span>
                </div>
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
                    class="stats-band"
                    :class="{ 'is-unfiled': section.row.isUnfiled }"
                    :aria-expanded="isSectionExpanded(section.key)"
                    :aria-controls="`${getSectionDomId(section.key)}-content`"
                    @click="toggleSection(section.key)"
                  >
                    <span class="stats-band__no">{{ section.chapterNo }}</span>
                    <span class="stats-band__name">
                      <span class="stats-band__title">{{ section.row.category }}</span>
                      <span v-if="!section.row.enabled && !section.row.isUnfiled" class="stats-band__tag">已禁用</span>
                    </span>
                    <span class="stats-band__count">
                      <b>{{ formatNumber(section.row.count) }}</b><span class="unit"> 题</span>
                    </span>
                    <span class="stats-band__share">占科目 {{ getShare(section.row.count, view.group.totalCount) }}</span>
                    <span class="stats-band__caret" aria-hidden="true"></span>
                    <span class="sr-only">
                      选择题 {{ formatNumber(section.row.choiceCount) }} 题，主观题 {{ formatNumber(section.row.subjectiveCount) }} 题
                    </span>
                    <span class="stats-band__strip" aria-hidden="true">
                      <i class="is-choice" :style="{ width: getBarWidth(section.row.choiceCount, view.maxChapterCount) }"></i>
                      <i
                        class="is-subject"
                        :style="{
                          left: getBarWidth(section.row.choiceCount, view.maxChapterCount),
                          width: getBarWidth(section.row.subjectiveCount, view.maxChapterCount)
                        }"
                      ></i>
                    </span>
                  </button>

                  <div v-show="isSectionExpanded(section.key)" :id="`${getSectionDomId(section.key)}-content`" class="border-t border-gray-100 bg-white">
                    <div v-if="section.children.length > 0">
                      <ul
                        class="stats-rows"
                        :aria-label="`${section.row.category}下级分类统计`"
                      >
                        <li
                          v-for="row in section.children"
                          :key="row.id"
                          class="stats-row"
                          :data-level="getRowDepth(row.level)"
                          :class="{
                            'is-group': row.hasChildren,
                            'is-disabled': !row.enabled && !row.isUnfiled,
                            'is-unfiled': row.isUnfiled
                          }"
                        >
                          <span class="stats-row__name">
                            <i class="stats-row__marker" :class="row.hasChildren ? 'is-parent' : 'is-leaf'" aria-hidden="true"></i>
                            <span class="stats-row__text" :title="row.category">{{ row.category }}</span>
                            <span v-if="!row.enabled && !row.isUnfiled" class="stats-row__tag is-disabled">已禁用</span>
                            <span v-if="row.isUnfiled" class="stats-row__tag is-unfiled">未归档</span>
                          </span>
                          <span class="stats-row__count">
                            <b>{{ formatNumber(row.count) }}</b><span class="unit"> 题</span>
                          </span>
                          <span class="stats-row__types">
                            <span class="key">选</span><b class="is-choice">{{ formatNumber(row.choiceCount) }}</b>
                            <span class="sep">·</span>
                            <span class="key">主</span><b class="is-subject">{{ formatNumber(row.subjectiveCount) }}</b>
                          </span>
                          <span class="stats-row__rail" :data-zero="row.count <= 0" aria-hidden="true">
                            <i :style="{ width: getBarWidth(row.count, section.maxChildCount) }"></i>
                          </span>
                        </li>
                      </ul>
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
      <div v-else class="rounded-2xl border border-dashed border-accent/20 bg-white/70 px-6 py-16 text-center shadow-sm">
        <font-awesome-icon :icon="['fas', 'inbox']" class="mb-4 text-4xl text-accent/30" aria-hidden="true" />
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
  category: string
  level: number
  hasChildren: boolean
  enabled: boolean
  isUnfiled: boolean
}

type CategorySection = {
  key: string
  row: StatsRow
  children: StatsRow[]
  maxChildCount: number
  /** 章号：本科目目录顺序序号，未归档块为「!」；切换排序后保持不变 */
  chapterNo: string
}

type StatsGroupView = {
  group: ExamSubjectCategoryStats
  chapters: CategorySection[]
  unfiled: CategorySection[]
  sections: CategorySection[]
  /** 本科目最大正式章节题量，作为章级权重带的满格基准 */
  maxChapterCount: number
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

const createStatsRow = (
  node: ExamCategoryStatsTreeItem,
  level: number,
  parentKey: string
): StatsRow => {
  const counts = getDisplayCounts(node, level)
  return {
    ...counts,
    id: getNodeKey(node, parentKey),
    category: node.categoryName,
    level,
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
  shouldSort: boolean
): StatsRow[] => {
  const rows: StatsRow[] = []
  const orderedNodes = shouldSort ? getSortedNodes(nodes, level) : nodes

  orderedNodes.forEach(node => {
    const row = createStatsRow(node, level, parentKey)
    rows.push(row)
    rows.push(...flattenNodes(node.children, level + 1, row.id, shouldSort))
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
    rows.push(...flattenNodes(group.categories, 0, subjectKey, false))
  })

  return rows
}

const buildSection = (
  node: ExamCategoryStatsTreeItem,
  parentKey: string,
  chapterNo: string
): CategorySection => {
  const row = createStatsRow(node, 0, parentKey)
  const children = flattenNodes(node.children, 1, row.id, true)
  return {
    key: row.id,
    row,
    children,
    maxChildCount: Math.max(0, ...children.map(child => child.count)),
    chapterNo
  }
}

const detailGroups = computed<StatsGroupView[]>(() => {
  return statsTree.value.map(group => {
    const subjectKey = getSubjectKey(group)
    const formalNodes = group.categories.filter(node => !node.isUnfiled)
    const sortedFormalNodes = getSortedNodes(formalNodes, 0)
    const unfiledNodes = group.categories.filter(node => node.isUnfiled)

    // 章号取自未排序的目录顺序，避免切换排序后编号与视觉顺序矛盾
    const chapterNoMap = new Map<string, number>()
    formalNodes.forEach((node, index) => {
      chapterNoMap.set(getNodeKey(node, subjectKey), index + 1)
    })

    const chapters = sortedFormalNodes.map(node =>
      buildSection(node, subjectKey, String(chapterNoMap.get(getNodeKey(node, subjectKey)) ?? ''))
    )

    const unfiled = unfiledNodes.map(node => buildSection(node, subjectKey, '!'))

    const maxChapterCount = Math.max(0, ...formalNodes.map(node => getDisplayCounts(node, 0).count))

    return {
      group,
      chapters,
      unfiled,
      sections: [...chapters, ...unfiled],
      maxChapterCount
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

/**
 * 明细行的层级深度，封顶 4 级（与样式中的 --tree-slot 宽度对应）。
 */
const getRowDepth = (level: number) => Math.min(Math.max(level, 1), 4)

/**
 * 占本科目题量的百分比文案；总量缺失时用破折号占位。
 */
const getShare = (count: number, total: number) => {
  if (total <= 0) return '—'
  return `${((count / total) * 100).toFixed(1)}%`
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
 * 加载科目选项，并把统计科目默认设为第一个启用科目。
 */
const loadSubjectOptions = async () => {
  try {
    const res = await getEnabledSubjects()
    if (res.code === 200) {
      subjectOptions.value = res.data || []
      statsSubjectId.value = subjectOptions.value[0]?.id ?? null
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

onMounted(async () => {
  await loadSubjectOptions()
  loadStats()
})
</script>

<style scoped>
.stats-page {
  color-scheme: light;

  /* 明细行几何与层级配色（配色 B：只有分类组带一档底色，其余白底）。
     导轨、分隔线、轨道色由品牌色 --brand-accent(#8B6F47) 降透明度得到，改色只需改 tailwind.css。 */
  --tree-step: 22px;
  --tree-slot: 88px;
  --rail-max: 620px;
  --guide: rgba(139, 111, 71, 0.16);
  --row-track: rgba(139, 111, 71, 0.14);
  --row-divider: rgba(139, 111, 71, 0.09);
  --row-divider-strong: rgba(139, 111, 71, 0.16);
  --row-hover: rgba(139, 111, 71, 0.04);
  --row-group-bg: #f6f4f0;
  --row-unfiled: #e7d3ae;
  --row-unfiled-ink: #8a6b3e;
  --row-unfiled-fill: #c79a5b;
  --row-disabled-ink: #c2703a;
  /* 主观题橙：页面既有配色，无对应令牌 */
  --row-subject: #b87542;
}

/* ==================== 图例：全页只出现一次，替代原先逐行重复的范围标签 ==================== */
.stats-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  color: var(--brand-ink-soft);
  font-size: 12px;
}

.stats-legend > li {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stats-legend__wide { flex: 1 1 100%; }

.stats-legend__marker { display: block; }

.stats-legend__marker.is-parent {
  width: 9px;
  height: 9px;
  border-radius: 1px;
  background: var(--brand-accent);
  transform: rotate(45deg);
}

.stats-legend__marker.is-leaf {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--brand-ink-mute);
}

.stats-legend__tick {
  display: block;
  width: 8px;
  height: 2px;
  border-radius: 2px;
  background: var(--brand-line);
}

.stats-legend__seg { display: inline-flex; }

.stats-legend__seg i {
  display: block;
  width: 18px;
  height: 6px;
}

.stats-legend__seg i.is-choice {
  border-radius: 3px 0 0 3px;
  background: var(--theme-exam-accent);
}

.stats-legend__seg i.is-subject {
  border-radius: 0 3px 3px 0;
  background: var(--row-subject);
}

/* ==================== 章级带：章号 + 名称 + 题量 + 占比 + 全宽权重带 ==================== */
.stats-band {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) 66px 104px 18px;
  grid-template-rows: auto auto;
  align-items: center;
  gap: 4px 12px;
  width: 100%;
  padding: 12px 16px 10px;
  border: 0;
  background: var(--brand-surface);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color 150ms ease;
}

.stats-band:hover { background: #f6f0e7; }

.stats-band:focus-visible {
  outline: 2px solid var(--brand-accent);
  outline-offset: -3px;
}

.stats-band.is-unfiled { box-shadow: inset 3px 0 0 var(--row-unfiled-fill); }

.stats-band__no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: var(--brand-accent);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.stats-band.is-unfiled .stats-band__no { background: var(--row-unfiled-fill); }

.stats-band__name {
  grid-column: 2;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: 15.5px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.stats-band__title { min-width: 0; overflow-wrap: anywhere; }

.stats-band__tag {
  flex: 0 0 auto;
  padding: 1.5px 7px;
  border: 1px solid rgba(194, 112, 58, 0.3);
  border-radius: 999px;
  background: #fff;
  color: var(--row-disabled-ink);
  font-size: 10.5px;
  font-weight: 500;
  line-height: 1.5;
}

.stats-band__count {
  grid-column: 3;
  text-align: right;
  color: var(--theme-exam-strong);
  font-size: 15px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stats-band__count .unit {
  font-size: 10.5px;
  font-weight: 500;
  color: var(--brand-ink-mute);
}

.stats-band__share {
  grid-column: 4;
  text-align: right;
  color: var(--brand-ink-mute);
  font-size: 11.5px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stats-band__caret {
  grid-column: 5;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--brand-accent);
}

.stats-band__caret::before {
  content: '';
  width: 7px;
  height: 7px;
  border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor;
  transform: translateY(-2px) rotate(45deg);
  transition: transform 150ms ease;
}

.stats-band[aria-expanded='false'] .stats-band__caret::before {
  transform: translateY(-1px) rotate(-45deg);
}

/* 章级权重带：满格 = 本科目最大正式章节题量，蓝段为选择题、棕段为主观题 */
.stats-band__strip {
  position: relative;
  grid-column: 1 / -1;
  grid-row: 2;
  height: 6px;
  margin-top: 6px;
  border-radius: 3px;
  background: var(--brand-line);
  overflow: hidden;
}

.stats-band__strip i {
  position: absolute;
  top: 0;
  height: 100%;
  transition: width 200ms ease;
}

.stats-band__strip i.is-choice { left: 0; background: var(--theme-exam-accent); }

.stats-band__strip i.is-subject {
  border-radius: 0 3px 3px 0;
  background: var(--row-subject);
}

.stats-band.is-unfiled .stats-band__strip i.is-choice { background: var(--row-unfiled-fill); }

/* ==================== 明细行：名称行（标记 + 名称 + 题量 + 选/主）+ 度量行（条形） ==================== */
.stats-rows {
  margin: 0;
  padding: 0;
  list-style: none;
}

.stats-row {
  position: relative;
  display: grid;
  grid-template-columns: minmax(140px, 240px) 62px 116px minmax(0, 1fr);
  grid-template-rows: auto auto;
  align-items: center;
  gap: 3px 10px;
  padding: 9px 16px 8px 8px;
  background: #fff;
}

.stats-row + .stats-row { border-top: 1px solid var(--row-divider); }

/* 层级只由导轨与标记位置表达；配色 B 只给分类组一档底色 */
.stats-row[data-level='1'] { --depth: 1; }

.stats-row[data-level='2'] {
  --depth: 2;
  border-top-color: var(--row-divider-strong);
}

.stats-row[data-level='3'] {
  --depth: 3;
  border-top-color: var(--row-divider-strong);
}

.stats-row[data-level='4'] {
  --depth: 4;
  border-top-color: var(--row-divider-strong);
}

/* 导轨：每深一级多一条竖线，位置只由层级决定，因此跨行严格对齐 */
.stats-row::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  left: 8px;
  width: calc((var(--depth) - 1) * var(--tree-step));
  background-image: repeating-linear-gradient(
    to right,
    var(--guide) 0 1px,
    transparent 1px var(--tree-step)
  );
  background-repeat: repeat;
  background-position: calc(var(--tree-step) / 2) 0;
  background-size: var(--tree-step) 100%;
  pointer-events: none;
}

/* hover 用叠加层，避免盖掉层级底色 */
.stats-row::after {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--row-hover);
  opacity: 0;
  pointer-events: none;
  transition: opacity 150ms ease;
}

.stats-row:hover::after { opacity: 1; }

.stats-row.is-group { background: var(--row-group-bg); }

.stats-row.is-unfiled { box-shadow: inset 2px 0 0 var(--row-unfiled); }

.stats-row__name {
  grid-column: 1;
  grid-row: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding-left: calc((var(--depth) - 1) * var(--tree-step) + 6px);
  color: var(--brand-ink-soft);
  font-size: 13.5px;
  font-weight: 500;
}

.stats-row.is-group .stats-row__name {
  color: var(--brand-ink);
  font-size: 14px;
  font-weight: 600;
}

.stats-row.is-disabled .stats-row__name { color: var(--brand-ink-mute); }

.stats-row__marker {
  display: flex;
  flex: 0 0 10px;
  align-items: center;
  justify-content: center;
  width: 10px;
  height: 10px;
}

.stats-row__marker::before { content: ''; display: block; }

.stats-row__marker.is-parent::before {
  width: 9px;
  height: 9px;
  border-radius: 1px;
  background: var(--brand-accent);
  transform: rotate(45deg);
}

.stats-row__marker.is-leaf::before {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--brand-ink-mute);
}

.stats-row__text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stats-row__tag {
  flex: 0 0 auto;
  padding: 1.5px 7px;
  border: 1px solid transparent;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 500;
  line-height: 1.5;
}

.stats-row__tag.is-disabled {
  border-color: rgba(194, 112, 58, 0.3);
  background: #fff;
  color: var(--row-disabled-ink);
}

.stats-row__tag.is-unfiled {
  border-color: var(--row-unfiled);
  background: #fff;
  color: var(--row-unfiled-ink);
}

.stats-row__count {
  grid-column: 2;
  grid-row: 1;
  text-align: right;
  color: var(--theme-exam-strong);
  font-size: 14px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stats-row__count .unit {
  font-size: 10px;
  font-weight: 500;
  color: var(--brand-ink-mute);
}

.stats-row.is-disabled .stats-row__count { color: var(--brand-ink-mute); }

.stats-row__types {
  grid-column: 3;
  grid-row: 1;
  display: flex;
  align-items: baseline;
  gap: 3px;
  font-size: 12.5px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.stats-row__types .key,
.stats-row__types .sep {
  color: var(--brand-ink-mute);
  font-size: 11px;
}

.stats-row__types .sep { margin: 0 1px; }

.stats-row__types .is-choice {
  color: var(--theme-exam-accent);
  font-weight: 600;
}

.stats-row__types .is-subject {
  color: var(--row-subject);
  font-weight: 600;
}

.stats-row.is-disabled .stats-row__types .is-choice { color: var(--brand-ink-mute); }

/* 度量行：条形起点固定（对齐树槽宽度），封顶 --rail-max；0 题只留刻度 */
.stats-row__rail {
  position: relative;
  grid-column: 1 / -1;
  grid-row: 2;
  height: 8px;
  margin-left: var(--tree-slot);
  max-width: var(--rail-max);
  border-radius: 4px;
  background: var(--row-track);
  overflow: hidden;
}

.stats-row__rail i {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: var(--theme-exam-accent);
  transition: width 200ms ease;
}

.stats-row__rail[data-zero='true'] { background: transparent; }

.stats-row__rail[data-zero='true']::before {
  content: '';
  position: absolute;
  top: 3px;
  left: 0;
  width: 8px;
  height: 2px;
  border-radius: 2px;
  background: var(--brand-line);
}

.stats-row.is-disabled .stats-row__rail i { background: rgba(86, 115, 138, 0.32); }

.stats-row.is-unfiled .stats-row__rail i { background: var(--row-unfiled-fill); }

/* ==================== 窄屏：名称行 + 题型行 + 条形独占，题量右上角 ==================== */
@media (max-width: 639px) {
  .stats-band { grid-template-columns: 32px minmax(0, 1fr) 66px 18px; }
  .stats-band__count { grid-column: 3; }
  .stats-band__share {
    grid-column: 2 / 4;
    grid-row: 3;
    text-align: left;
  }
  .stats-band__caret { grid-column: 4; }
  .stats-band__strip { grid-row: 4; }

  .stats-row { display: block; padding: 11px 14px 8px 8px; }

  .stats-row::before {
    left: 0;
    width: calc((var(--depth) - 1) * 14px);
    background-position: 7px 0;
    background-size: 14px 100%;
  }

  .stats-row__name {
    padding-left: calc((var(--depth) - 1) * 14px + 2px);
    padding-right: 72px;
  }

  .stats-row__text {
    overflow: visible;
    white-space: normal;
    text-overflow: clip;
  }

  .stats-row__count {
    position: absolute;
    top: 12px;
    right: 14px;
  }

  .stats-row__types { margin-top: 3px; }

  .stats-row__rail {
    width: 100%;
    max-width: none;
    margin-top: 6px;
    margin-left: 0;
  }
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
