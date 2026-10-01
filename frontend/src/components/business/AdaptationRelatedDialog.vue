<!-- 真题关联改编题弹窗：懒加载关联摘要，管理员可携带当前真题来源新增改编题。 -->
<template>
  <ResponsiveDialog
    v-model:visible="dialogVisible"
    :title="dialogTitle"
    width="760px"
    max-width="calc(100vw - 24px)"
    :loading="loading"
  >
    <div class="space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-accent/15 bg-surface/60 px-4 py-3">
        <span class="text-sm text-ink-soft">当前真题：{{ sourceLabel }}</span>
        <div class="flex flex-wrap items-center gap-2">
          <Tag type="info" size="sm">共 {{ total }} 道</Tag>
          <CustomButton v-if="canCreate" size="sm" type="primary" @click="handleAdd">
            <font-awesome-icon :icon="['fas', 'plus']" class="mr-1.5" aria-hidden="true" />
            新增改编题
          </CustomButton>
        </div>
      </div>

      <div v-if="errorMessage" class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
        <span>{{ errorMessage }}</span>
        <CustomButton size="sm" type="text-danger" @click="handleRetry">重试</CustomButton>
      </div>

      <Empty v-else-if="adaptations.length === 0" description="暂无关联改编题" />

      <div v-else class="flex flex-col gap-3">
        <article
          v-for="adaptation in adaptations"
          :key="adaptation.id"
          class="rounded-lg border border-gray-200 bg-white p-4 transition-colors hover:border-accent/40"
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <h3 class="m-0 min-w-0 flex-1 text-base font-semibold text-ink">
              <a
                :href="getAdaptationHref(adaptation)"
                target="_blank"
                rel="noopener noreferrer"
                class="transition-colors hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1"
              >
                改编题 #{{ adaptation.id }}
              </a>
            </h3>
            <div class="flex shrink-0 flex-wrap gap-1.5">
              <Tag :type="adaptation.questionType === 'CHOICE' ? 'success' : 'primary'" size="sm">
                {{ adaptation.questionType === 'CHOICE' ? '选择题' : '主观题' }}
              </Tag>
              <Tag v-if="adaptation.difficulty" :type="getDifficultyType(adaptation.difficulty)" size="sm">
                {{ getDifficultyLabel(adaptation.difficulty) }}
              </Tag>
            </div>
          </div>

          <p class="mt-2 line-clamp-2 text-sm leading-6 text-ink-soft">
            {{ getContentPreview(adaptation.content) }}
          </p>

          <div class="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-mute">
            <span v-if="adaptation.subjectName">{{ adaptation.subjectName }}</span>
            <span v-for="category in getCategories(adaptation)" :key="category" class="rounded bg-surface px-1.5 py-0.5">
              {{ category }}
            </span>
            <span v-if="adaptation.sourceSummary">{{ adaptation.sourceSummary }}</span>
          </div>

          <div class="mt-3 flex justify-end">
            <a
              :href="getAdaptationHref(adaptation)"
              target="_blank"
              rel="noopener noreferrer"
              class="rounded-md px-2.5 py-1.5 text-sm font-medium text-accent transition-colors hover:bg-accent/10 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1"
            >
              查看完整题目
            </a>
          </div>
        </article>
      </div>

      <Pagination
        v-if="total > pageSize"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        :show-sizes="false"
        :show-jumper="false"
        class="mt-2"
        @current-change="handlePageChange"
      />
    </div>
  </ResponsiveDialog>

  <AdaptationEditDialog
    v-model:visible="createDialogVisible"
    :initial-sources="initialSources"
    @success="handleCreateSuccess"
  />
</template>

<script setup lang="ts">
/**
 * 展示与当前真题存在来源关系的改编题摘要。
 * 仅在弹窗打开时请求，避免真题列表为每道题预加载改编题数据。
 */
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { AdaptationQuestion, AdaptationSourceRefInput, ExamQuestion } from '@/types'
import { useAuthStore } from '@/stores/auth'
import { getAdaptationList } from '@/api/adaptation'
import { getDifficultyLabel, getDifficultyType } from '@/constants/exam'
import CustomButton from '@/components/basic/CustomButton.vue'
import ResponsiveDialog from '@/components/basic/ResponsiveDialog.vue'
import Empty from '@/components/basic/Empty.vue'
import Pagination from '@/components/basic/Pagination.vue'
import Tag from '@/components/basic/Tag.vue'
import AdaptationEditDialog from '@/components/business/AdaptationEditDialog.vue'

interface Props {
  visible: boolean
  exam: ExamQuestion | null
}

const props = defineProps<Props>()
const emit = defineEmits<{ 'update:visible': [visible: boolean] }>()
const router = useRouter()
const authStore = useAuthStore()
const activeDialog = ref<'related' | 'create' | null>('related')

const dialogVisible = computed({
  get: () => props.visible && activeDialog.value === 'related',
  set: value => emit('update:visible', value)
})

const createDialogVisible = computed({
  get: () => props.visible && activeDialog.value === 'create',
  set: value => {
    if (!value) void switchDialog('related')
  }
})

const canCreate = computed(() => authStore.isAdmin() && props.exam?.questionNumber != null)
const initialSources = computed<AdaptationSourceRefInput[]>(() => {
  const exam = props.exam
  if (!exam || exam.questionNumber == null) return []
  return [{ sourceYear: exam.year, sourceQuestionNumber: exam.questionNumber }]
})

/** 先关闭当前弹层再打开目标弹层，避免焦点与页面滚动锁相互覆盖。 */
const switchDialog = async (target: 'related' | 'create') => {
  activeDialog.value = null
  await nextTick()
  if (props.visible) activeDialog.value = target
}

const handleAdd = () => {
  if (canCreate.value) void switchDialog('create')
}

const adaptations = ref<AdaptationQuestion[]>([])
const loading = ref(false)
const errorMessage = ref('')
const page = ref(1)
const total = ref(0)
const pageSize = 20
let requestVersion = 0

const sourceLabel = computed(() => {
  if (!props.exam || props.exam.questionNumber == null) return '当前真题'
  return `${props.exam.year} 年第 ${props.exam.questionNumber} 题`
})

const dialogTitle = computed(() => `${sourceLabel.value} · 关联改编题`)

const getCategories = (question: AdaptationQuestion) => {
  if (!Array.isArray(question.category)) return []
  return question.category.filter(Boolean)
}

const getAdaptationHref = (question: AdaptationQuestion) => {
  const category = getCategories(question)[0]
  return router.resolve({
    name: 'adaptation',
    query: {
      subject: question.subjectName || undefined,
      category: category || undefined,
    },
    hash: `#adaptation-${question.id}`,
  }).href
}

const getContentPreview = (content: string) => {
  const plainText = content
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[`*_>#~-]/g, '')
    .replace(/\s+/g, ' ')
    .trim()

  if (!plainText) return '暂无题干摘要'
  return plainText.length > 120 ? `${plainText.slice(0, 120)}…` : plainText
}

const loadAdaptations = async (targetPage = 1) => {
  const exam = props.exam
  if (!exam || exam.questionNumber == null) {
    requestVersion += 1
    adaptations.value = []
    total.value = 0
    loading.value = false
    return
  }

  const currentRequestVersion = ++requestVersion
  page.value = targetPage
  adaptations.value = []
  errorMessage.value = ''
  loading.value = true

  try {
    const response = await getAdaptationList({
      page: targetPage,
      pageSize,
      sourceYear: exam.year,
      sourceQuestionNumber: exam.questionNumber,
      sortField: 'update_time',
      sortOrder: 'desc'
    })

    if (currentRequestVersion !== requestVersion) return

    if (response.code === 200) {
      adaptations.value = response.data?.lists || []
      total.value = response.data?.pagination?.total || 0
    } else {
      errorMessage.value = response.message || '关联改编题读取失败，请重试。'
      total.value = 0
    }
  } catch (error) {
    if (currentRequestVersion !== requestVersion) return
    errorMessage.value = '关联改编题读取失败，请重试。'
    total.value = 0
    console.error('加载关联改编题失败:', error)
  } finally {
    if (currentRequestVersion === requestVersion) loading.value = false
  }
}

/** 新增后重新读取第一页，让关联列表与总数以实际保存的来源为准。 */
const handleCreateSuccess = () => {
  if (props.visible) void loadAdaptations(1)
}

const handlePageChange = (targetPage: number) => {
  void loadAdaptations(targetPage)
}

const handleRetry = () => {
  void loadAdaptations(page.value)
}

watch(
  () => [props.visible, props.exam?.id] as const,
  ([visible]) => {
    activeDialog.value = 'related'
    if (visible) void loadAdaptations(1)
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  requestVersion += 1
})
</script>
