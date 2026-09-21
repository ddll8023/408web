<!-- 改编覆盖统计页面：按年份展示真题改编进度，并可反查引用某道真题的改编题。 -->
<template>
  <main class="admin-manage-page mx-auto min-h-[var(--app-page-height)] w-full max-w-[1600px] min-w-0 px-2 py-4 sm:px-4 sm:py-6">
    <CustomCard shadow>
      <template #header>
        <header class="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 class="m-0 text-xl font-semibold text-ink">真题改编覆盖</h2>
          <div class="flex flex-wrap items-end gap-2">
            <Select
              v-model="subjectId"
              :options="subjectOptions"
              placeholder="全部科目"
              aria-label="科目"
              clearable
              class="w-full min-w-[180px] sm:w-auto"
              @change="handleSubjectChange"
            />
            <CustomButton type="primary" :loading="loading" @click="loadCoverage">
              <font-awesome-icon :icon="['fas', 'rotate']" class="mr-1.5" />
              刷新
            </CustomButton>
          </div>
        </header>
      </template>

      <p class="mb-4 text-sm text-ink-soft">
        覆盖统计以真题库为分母：年份内真题总题数、已被至少一道改编题引用的题数、尚未改编的题号；
        悬空来源指来源标注的年份题号在真题库中找不到，需要核对录入。
      </p>

      <div v-if="listError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
        {{ listError }}
        <CustomButton size="sm" type="text" :disabled="loading" @click="loadCoverage">重试</CustomButton>
      </div>

      <div v-if="!loading && coverage.length === 0 && !listError" class="py-10">
        <Empty description="暂无可统计的真题年份" />
      </div>

      <section v-else class="space-y-4">
        <article
          v-for="item in coverage"
          :key="item.year"
          class="rounded-xl border border-[#eadfd4] bg-white/70 p-4 shadow-sm"
        >
          <header class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <span class="text-lg font-semibold text-ink">{{ item.year }} 年</span>
              <Tag :type="item.adapted === item.total ? 'success' : 'info'" size="sm">
                已改编 {{ item.adapted }} / {{ item.total }}
              </Tag>
              <Tag v-if="item.danglingSources > 0" type="warning" size="sm">
                悬空来源 {{ item.danglingSources }}
              </Tag>
            </div>
            <CustomButton type="text-primary" size="sm" @click="toggleDetail(item.year)">
              {{ expandedYear === item.year ? '收起题号明细' : '查看题号明细' }}
            </CustomButton>
          </header>

          <div class="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              class="h-full rounded-full bg-accent transition-all"
              :style="{ width: `${coverageRate(item)}%` }"
            />
          </div>

          <p class="mt-3 text-sm text-ink-soft">
            未改编题号：
            <span v-if="item.missingNumbers.length === 0" class="text-emerald-600">全部已改编</span>
            <span v-else>{{ formatNumberRange(item.missingNumbers) }}</span>
          </p>

          <div v-if="expandedYear === item.year" class="mt-4">
            <div class="flex flex-wrap gap-2">
              <button
                v-for="countItem in item.counts"
                :key="countItem.questionNumber"
                type="button"
                class="min-w-[46px] rounded-md border px-2 py-1 text-xs transition-colors"
                :class="countItem.adaptationCount > 0
                  ? 'border-accent/30 bg-accent/10 text-accent hover:bg-accent/20'
                  : 'border-gray-200 bg-gray-50 text-gray-400 hover:bg-gray-100'"
                @click="openSourceDetail(item.year, countItem.questionNumber)"
              >
                {{ countItem.questionNumber }}
                <span v-if="countItem.adaptationCount > 0" class="ml-1">×{{ countItem.adaptationCount }}</span>
              </button>
            </div>
            <p class="mt-2 text-xs text-ink-soft">点击题号可反查引用它的改编题。</p>
          </div>
        </article>
      </section>
    </CustomCard>

    <Dialog
      v-model:visible="detailVisible"
      :title="detailTitle"
      width="720px"
      max-width="calc(100vw - 24px)"
    >
      <div v-if="detailLoading" class="py-8 text-center text-sm text-ink-soft">正在加载…</div>
      <div v-else-if="detailItems.length === 0" class="py-8">
        <Empty description="该题暂未被改编题引用" />
      </div>
      <ul v-else class="space-y-2">
        <li
          v-for="item in detailItems"
          :key="item.id"
          class="rounded-lg border border-gray-200 bg-white/70 p-3"
        >
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="font-medium text-ink">
              {{ item.title || '（未命名）' }}
            </span>
            <div class="flex items-center gap-2">
              <Tag :type="item.questionType === 'CHOICE' ? 'success' : 'primary'" size="sm">
                {{ item.questionType === 'CHOICE' ? '选择题' : '主观题' }}
              </Tag>
            </div>
          </div>
          <p class="mt-1 text-xs text-ink-soft">
            {{ item.subjectName || '未设置科目' }} · 更新于 {{ formatDateTime(item.updateTime) }}
          </p>
        </li>
      </ul>
    </Dialog>
  </main>
</template>

<script setup lang="ts">
/**
 * 改编覆盖统计页面
 * 功能：按年份展示真题改编覆盖率、未改编题号与悬空来源，并反查引用某道真题的改编题
 */
import type { AdaptationBySourceItem, AdaptationCoverageItem } from '@/types'
import { computed, onMounted, ref } from 'vue'
import { findAdaptationsBySource, getAdaptationCoverage } from '@/api/adaptation'
import { useAdminTable } from '@/composables/useAdminTable'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomCard from '@/components/basic/CustomCard.vue'
import Dialog from '@/components/basic/Dialog.vue'
import Empty from '@/components/basic/Empty.vue'
import Select from '@/components/basic/Select.vue'
import Tag from '@/components/basic/Tag.vue'

const { showToast } = useToast()
const { subjectOptions, loadSubjectOptions, formatDateTime } = useAdminTable()

const subjectId = ref<number | null>(null)
const coverage = ref<AdaptationCoverageItem[]>([])
const loading = ref(false)
const listError = ref('')
let coverageRequestVersion = 0

const expandedYear = ref<number | null>(null)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailItems = ref<AdaptationBySourceItem[]>([])
const detailSource = ref<{ year: number; number: number } | null>(null)

const detailTitle = computed(() => {
  if (!detailSource.value) return '引用该真题的改编题'
  return `引用 ${detailSource.value.year} 年第 ${detailSource.value.number} 题的改编题`
})

const coverageRate = (item: AdaptationCoverageItem) => {
  if (item.total === 0) return 0
  return Math.round((item.adapted / item.total) * 100)
}

/** 把题号数组压缩为连续区间文案，避免长列表占满页面 */
const formatNumberRange = (numbers: number[]) => {
  if (numbers.length === 0) return '无'
  const sorted = [...numbers].sort((a, b) => a - b)
  const ranges: string[] = []
  let start = sorted[0]
  let previous = sorted[0]
  for (let index = 1; index <= sorted.length; index++) {
    const current = sorted[index]
    if (current !== undefined && current === previous + 1) {
      previous = current
      continue
    }
    ranges.push(start === previous ? `${start}` : `${start}-${previous}`)
    if (current !== undefined) {
      start = current
      previous = current
    }
  }
  return ranges.join('、')
}

const loadCoverage = async () => {
  const requestVersion = ++coverageRequestVersion
  loading.value = true
  listError.value = ''
  expandedYear.value = null
  try {
    const response = await getAdaptationCoverage({ subjectId: subjectId.value })
    if (requestVersion !== coverageRequestVersion) return
    if (response.code === 200) {
      coverage.value = response.data || []
    } else {
      coverage.value = []
      listError.value = response.message || '覆盖统计读取失败，请重试。'
    }
  } catch (error) {
    if (requestVersion !== coverageRequestVersion) return
    coverage.value = []
    listError.value = '覆盖统计读取失败，请重试。'
    console.error('加载改编覆盖统计失败:', error)
  } finally {
    if (requestVersion === coverageRequestVersion) loading.value = false
  }
}

const handleSubjectChange = (value: number | string | null) => {
  subjectId.value = value ? Number(value) : null
  void loadCoverage()
}

const toggleDetail = (year: number) => {
  expandedYear.value = expandedYear.value === year ? null : year
}

const openSourceDetail = async (year: number, questionNumber: number) => {
  detailSource.value = { year, number: questionNumber }
  detailVisible.value = true
  detailLoading.value = true
  detailItems.value = []
  try {
    const response = await findAdaptationsBySource({
      sourceYear: year,
      sourceQuestionNumber: questionNumber
    })
    if (response.code === 200) {
      detailItems.value = response.data || []
    } else {
      showToast(response.message || '反查失败', 'error')
    }
  } catch (error) {
    showToast('反查失败', 'error')
    console.error('反查改编题失败:', error)
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  loadSubjectOptions()
  loadCoverage()
})
</script>
