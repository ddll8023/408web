<!-- 改编题阅读页面：按科目与分类浏览改编题，并展示改编来源标注。 -->
<template>
  <main class="mx-auto min-h-[var(--app-page-height)] w-full max-w-[1200px] min-w-0 px-2 py-4 sm:px-4 sm:py-6">
    <header class="mb-4">
      <h1 class="m-0 text-xl font-semibold text-ink">真题改编题</h1>
      <p class="mt-1 text-sm text-ink-soft">
        改编题标注了对应的真题年份与题号，可对照原题复习同一知识点。
      </p>
    </header>

    <!-- 筛选区 -->
    <section class="mb-5 rounded-xl border border-[#eadfd4] bg-white/70 p-3 shadow-sm sm:p-4">
      <div class="grid grid-cols-1 items-end gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-sm font-medium text-gray-700">科目</label>
          <Select
            v-model="subjectId"
            :options="subjectOptions"
            placeholder="请选择科目"
            aria-label="科目"
            clearable
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
            :disabled="!subjectId"
            :multiple="false"
            @change="handleCategoryChange"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="text-sm font-medium text-gray-700">关键词</label>
          <CustomInput
            v-model="keyword"
            placeholder="搜索题干"
            aria-label="关键词"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <font-awesome-icon :icon="['fas', 'search']" class="text-gray-400" />
            </template>
          </CustomInput>
        </div>
        <div class="flex justify-end gap-2">
          <CustomButton type="primary" @click="handleSearch">
            <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="mr-1.5" />
            查询
          </CustomButton>
          <CustomButton type="default" @click="handleReset">重置</CustomButton>
        </div>
      </div>
    </section>

    <!-- 定位题目（来自管理端查看跳转） -->
    <section v-if="locatedQuestion" class="mb-5 rounded-xl border border-accent/30 bg-accent/5 p-4">
      <div class="mb-2 flex items-center justify-between gap-2">
        <Tag type="primary" size="sm">定位题目</Tag>
        <CustomButton type="text" size="sm" @click="clearLocatedQuestion">关闭</CustomButton>
      </div>
      <QuestionBody :question="locatedQuestion" :default-expanded="true" />
    </section>

    <div v-if="listError" class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">
      {{ listError }}
      <CustomButton size="sm" type="text" :disabled="loading" @click="loadQuestions">重试</CustomButton>
    </div>

    <section class="space-y-4">
      <article
        v-for="question in questions"
        :key="question.id"
        :id="`adaptation-${question.id}`"
        class="rounded-xl border border-[#eadfd4] bg-white/80 p-4 shadow-sm"
      >
        <QuestionBody :question="question" />
      </article>
    </section>

    <div v-if="!loading && questions.length === 0 && !listError" class="py-14">
      <Empty description="暂无符合条件的改编题" />
    </div>

    <footer v-if="pagination.total > 0" class="mt-6 flex justify-end border-t border-gray-100 pt-4">
      <Pagination
        v-model:currentPage="pagination.page"
        v-model:pageSize="pagination.size"
        :pageSizes="[10, 20, 50]"
        :total="pagination.total"
        showTotal
        @current-change="loadQuestions"
        @size-change="loadQuestions"
      />
    </footer>
  </main>
</template>

<script setup lang="ts">
/**
 * 改编题阅读页面
 * 功能：按科目与分类浏览改编题，展示来源标注，并支持按 ID 定位单题
 * 依赖：QuestionBody 子组件渲染题干、选项与答案
 */
import type { AdaptationQuestion, CategoryTreeNode } from '@/types'
import type { CascaderOption } from '@/components/basic/types'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getAdaptationDetail, getAdaptationList, getAdaptationSubjectStats } from '@/api/adaptation'
import { getEnabledCategoryTreeBySubjectWithStats } from '@/api/category'
import { getEnabledSubjects } from '@/api/subject'
import { useToast } from '@/composables/useToast'
import CustomButton from '@/components/basic/CustomButton.vue'
import CustomInput from '@/components/basic/CustomInput.vue'
import Empty from '@/components/basic/Empty.vue'
import MultiSelectCascader from '@/components/basic/MultiSelectCascader.vue'
import Pagination from '@/components/basic/Pagination.vue'
import Select from '@/components/basic/Select.vue'
import Tag from '@/components/basic/Tag.vue'
import QuestionBody from '@/components/business/AdaptationQuestionBody.vue'

const route = useRoute()
const { showToast } = useToast()

const subjects = ref<{ subjectId: number; subjectName: string; count: number }[]>([])
const subjectOptions = computed(() =>
  subjects.value.map(item => ({ label: `${item.subjectName}（${item.count}）`, value: item.subjectId }))
)
const categoryTreeOptions = ref<CascaderOption[]>([])

const subjectId = ref<number | null>(null)
const categorySelection = ref<string[]>([])
const category = ref('')
const keyword = ref('')

const questions = ref<AdaptationQuestion[]>([])
const loading = ref(false)
const listError = ref('')
let listRequestVersion = 0

const pagination = reactive({ page: 1, size: 10, total: 0 })

const locatedQuestion = ref<AdaptationQuestion | null>(null)

/** 加载启用科目，供科目筛选与统计展示 */
const loadSubjects = async () => {
  try {
    const [subjectResponse, statResponse] = await Promise.all([
      getEnabledSubjects(),
      getAdaptationSubjectStats()
    ])
    if (subjectResponse.code !== 200) return
    const countMap = new Map(
      (statResponse.code === 200 ? statResponse.data || [] : [])
        .map(item => [item.subjectId, item.count])
    )
    subjects.value = (subjectResponse.data || []).map(subject => ({
      subjectId: subject.id,
      subjectName: subject.name,
      count: countMap.get(subject.id) || 0
    }))
  } catch (error) {
    console.error('加载科目失败:', error)
  }
}

/** 分类选项来自目录树，当前只用于单值筛选 */
const loadCategoryOptions = async (id: number) => {
  try {
    const response = await getEnabledCategoryTreeBySubjectWithStats(id, 'adaptation')
    if (response.code !== 200) {
      categoryTreeOptions.value = []
      return
    }
    const transform = (nodes: CategoryTreeNode[]): CascaderOption[] =>
      (nodes || []).map(node => ({
        value: node.name,
        label: node.name,
        children: node.children && node.children.length > 0 ? transform(node.children) : undefined
      }))
    categoryTreeOptions.value = transform(response.data || [])
  } catch (error) {
    categoryTreeOptions.value = []
    console.error('加载分类失败:', error)
  }
}

const loadQuestions = async () => {
  const requestVersion = ++listRequestVersion
  loading.value = true
  listError.value = ''
  try {
    const response = await getAdaptationList({
      page: pagination.page,
      pageSize: pagination.size,
      subjectId: subjectId.value,
      category: category.value || undefined,
      keyword: keyword.value || undefined
    })
    if (requestVersion !== listRequestVersion) return
    if (response.code === 200) {
      questions.value = response.data?.lists || []
      pagination.total = response.data?.pagination?.total || 0
    } else {
      questions.value = []
      listError.value = response.message || '改编题读取失败，请重试。'
    }
  } catch (error) {
    if (requestVersion !== listRequestVersion) return
    questions.value = []
    listError.value = '改编题读取失败，请重试。'
    console.error('加载改编题失败:', error)
  } finally {
    if (requestVersion === listRequestVersion) loading.value = false
  }
}

const handleSubjectChange = async (value: number | string | null) => {
  subjectId.value = value ? Number(value) : null
  category.value = ''
  categorySelection.value = []
  categoryTreeOptions.value = []
  if (subjectId.value) {
    await loadCategoryOptions(subjectId.value)
  }
  handleSearch()
}

const handleCategoryChange = (values: string[]) => {
  category.value = values[0] || ''
  handleSearch()
}

const handleSearch = () => {
  pagination.page = 1
  loadQuestions()
}

const handleReset = () => {
  subjectId.value = null
  category.value = ''
  categorySelection.value = []
  categoryTreeOptions.value = []
  keyword.value = ''
  pagination.page = 1
  loadQuestions()
}

/** 管理端「查看」跳转时按 ID 定位单题 */
const loadLocatedQuestion = async (id: number) => {
  try {
    const response = await getAdaptationDetail(id)
    if (response.code === 200) {
      locatedQuestion.value = response.data
      if (response.data?.subjectId) {
        subjectId.value = response.data.subjectId
        await loadCategoryOptions(response.data.subjectId)
      }
    }
  } catch (error) {
    showToast('定位题目失败', 'error')
    console.error('定位改编题失败:', error)
  }
}

const clearLocatedQuestion = () => {
  locatedQuestion.value = null
}

onMounted(async () => {
  await loadSubjects()
  const id = route.query.id
  if (typeof id === 'string' && id) {
    await loadLocatedQuestion(Number(id))
  }
  loadQuestions()
})

watch(() => route.query.id, value => {
  if (typeof value === 'string' && value) {
    void loadLocatedQuestion(Number(value))
  }
})
</script>
