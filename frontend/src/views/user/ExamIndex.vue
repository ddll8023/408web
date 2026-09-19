<!-- 真题年份入口页面：年份卡片按可用宽度自动排列。 -->
<template>
  <div class="flex min-h-[var(--app-page-height)] items-center justify-center bg-surface px-4 py-6 sm:py-8">
    <div class="w-full max-w-[1200px]">
      <!-- 头部介绍 -->
      <div class="text-center py-8">
        <h1 class="m-0 mb-4 text-3xl font-semibold text-ink sm:mb-6 sm:text-4xl">408考研真题</h1>
        <p class="m-0 text-ink-soft text-base leading-relaxed max-w-[800px] mx-auto">
          收录408统考真题,包含数据结构、操作系统、计算机网络、计算机组成原理四大科目。
          提供完整题目和详细解答,助力考研备考。
        </p>
      </div>

      <hr class="my-6 border-[#e5e7eb]" />

      <!-- 年份卡片列表 -->
      <div v-if="loading" class="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-6 my-8" role="status" aria-live="polite">
        <div class="col-span-full flex items-center justify-center py-20">
          <font-awesome-icon :icon="['fas', 'spinner']" class="fa-spin text-4xl text-accent" aria-hidden="true" />
        </div>
      </div>
      <div v-else class="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-6 my-8">
        <div v-if="loadError" class="col-span-full rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">
          {{ loadError }}
          <CustomButton type="text" size="sm" @click="loadYearData">重试</CustomButton>
        </div>
        <div
          v-for="yearData in yearList"
          :key="yearData.year"
          class="p-5 bg-white rounded border-2 border-[#dfe2e5] cursor-pointer transition-all duration-300 flex flex-col min-h-[200px] hover:border-accent hover:shadow-[0_4px_12px_color-mix(in srgb, var(--brand-accent) 15%, transparent)] hover:-translate-y-1"
          role="button"
          tabindex="0"
          :aria-label="`查看 ${yearData.year} 年真题`"
          @click="goToYear(yearData.year)"
          @keydown.enter.prevent="goToYear(yearData.year)"
          @keydown.space.prevent="goToYear(yearData.year)"
        >
          <div class="flex items-baseline justify-center gap-2 mb-3">
            <h2 class="m-0 font-semibold text-5xl text-ink leading-tight transition-colors duration-300">{{ yearData.year }}</h2>
            <span class="text-ink-soft text-lg">年</span>
          </div>
          <hr class="my-3 border-[#e5e7eb]" />
          <div class="flex-1 flex items-center justify-center py-2">
            <div class="flex items-center gap-2">
              <font-awesome-icon :icon="['fas', 'file-lines']" class="text-accent" />
              <span class="text-ink-soft text-sm">共 {{ yearData.count }} 题</span>
            </div>
          </div>
          <div class="flex justify-center pt-3 mt-auto">
            <CustomButton type="primary" size="sm" @click.stop="goToYear(yearData.year)">
              查看真题
              <font-awesome-icon :icon="['fas', 'arrow-right']" class="ml-1 transition-transform duration-300" />
            </CustomButton>
          </div>
        </div>

        <!-- 空状态 -->
        <Empty
          v-if="!loadError && yearList.length === 0"
          description="暂无真题数据"
          :icon="['fas', 'folder-open']"
        />
      </div>

      <!-- 底部提示 -->
      <div class="mt-8">
        <Alert title="使用提示" type="info">
          <ul class="m-0 pl-4 text-ink-soft leading-relaxed">
            <li class="my-1.5">点击年份卡片查看该年份的所有真题</li>
            <li class="my-1.5">每道题目都配有详细解答</li>
            <li class="my-1.5">支持按题型、科目、难度筛选查看</li>
          </ul>
        </Alert>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { queryString } from "@/utils/storage"
/**
 * 真题索引/入口页面
 * 功能:展示年份卡片,点击跳转到对应年份的真题页面
 * 遵循KISS原则:简洁的入口页面设计
 */
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { toast } from '@/utils/toast'
import { getExamYearStats } from '@/api/exam'
import CustomButton from '@/components/basic/CustomButton.vue'
import Empty from '@/components/basic/Empty.vue'
import Alert from '@/components/basic/Alert.vue'

const router = useRouter()
const route = useRoute()

// 年份列表数据
const yearList = ref<{year: number; count: number}[]>([])
const loading = ref(false)
const loadError = ref('')
let loadVersion = 0

// 当前分类（来自路由查询参数）
const activeCategory = ref(queryString(route.query.category))

/**
 * 加载真题年份统计数据（可按分类过滤）
 */
const loadYearData = async () => {
  const requestVersion = ++loadVersion
  loading.value = true
  try {
    const response = await getExamYearStats({
      category: activeCategory.value || undefined
    })

    if (requestVersion !== loadVersion) return
    if (response.code === 200) {
      loadError.value = ''
      yearList.value = (response.data || [])
        .map(item => ({
          year: item.year,
          count: item.count
        }))
        .sort((a, b) => b.year - a.year)
    } else {
      loadError.value = response.message || '加载失败，请重试。'
      toast.error(loadError.value)
    }
  } catch (error) {
    if (requestVersion !== loadVersion) return
    loadError.value = '加载真题数据失败，请重试。'
    toast.error(loadError.value)
    console.error('加载真题数据失败:', error)
  } finally {
    if (requestVersion === loadVersion) loading.value = false
  }
}

/**
 * 跳转到指定年份的真题页面
 */
const goToYear = (year: number) => {
  // 保留当前分类查询参数
  const query = activeCategory.value
    ? { category: activeCategory.value }
    : {}
  router.push({
    path: `/exam/${year}`,
    query
  })
}

// 监听路由分类变化，重新加载年份统计
watch(
  () => route.query.category,
  (newCategory) => {
    activeCategory.value = queryString(newCategory)
    loadYearData()
  }
)

// 组件挂载时加载数据
onMounted(() => {
  loadYearData()
})
</script>

<style scoped>
/**
 * 真题索引页面样式
 * 使用 Tailwind CSS
 */
</style>
