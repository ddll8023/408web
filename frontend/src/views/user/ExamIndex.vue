<template>
  <div class="min-h-[calc(100vh-60px)] bg-[#FBF7F2] px-4 py-8 flex items-center justify-center">
    <div class="w-full max-w-[1200px]">
      <!-- 头部介绍 -->
      <div class="text-center py-8">
        <h1 class="m-0 mb-6 text-[#333] font-semibold text-4xl">408考研真题</h1>
        <p class="m-0 text-[#666] text-base leading-relaxed max-w-[800px] mx-auto">
          收录408统考真题,包含数据结构、操作系统、计算机网络、计算机组成原理四大科目。
          提供完整题目和详细解答,助力考研备考。
        </p>
      </div>

      <hr class="my-6 border-[#e5e7eb]" />

      <!-- 年份卡片列表 -->
      <div v-loading="loading" class="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-6 my-8">
        <div
          v-for="yearData in yearList"
          :key="yearData.year"
          class="p-5 bg-white rounded border-2 border-[#dfe2e5] cursor-pointer transition-all duration-300 flex flex-col min-h-[200px] hover:border-[#8B6F47] hover:shadow-[0_4px_12px_rgba(139,111,71,0.15)] hover:-translate-y-1"
          @click="goToYear(yearData.year)"
        >
          <div class="flex items-baseline justify-center gap-2 mb-3">
            <h2 class="m-0 font-semibold text-5xl text-[#333] leading-tight transition-colors duration-300">{{ yearData.year }}</h2>
            <span class="text-[#666] text-lg">年</span>
          </div>
          <hr class="my-3 border-[#e5e7eb]" />
          <div class="flex-1 flex items-center justify-center py-2">
            <div class="flex items-center gap-2">
              <el-icon class="text-[#8B6F47]" :size="18"><Document /></el-icon>
              <span class="text-[#666] text-sm">共 {{ yearData.count }} 题</span>
            </div>
          </div>
          <div class="flex justify-center pt-3 mt-auto">
            <CustomButton type="primary" size="sm">
              查看真题
              <el-icon class="ml-1 transition-transform duration-300"><ArrowRight /></el-icon>
            </CustomButton>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty
          v-if="!loading && yearList.length === 0"
          description="暂无真题数据"
          :image-size="200"
        />
      </div>

      <!-- 底部提示 -->
      <div class="mt-8">
        <el-alert
          title="使用提示"
          type="info"
          :closable="false"
        >
          <template #default>
            <ul class="m-0 pl-4 text-[#666] leading-relaxed">
              <li class="my-1.5">点击年份卡片查看该年份的所有真题</li>
              <li class="my-1.5">每道题目都配有详细解答</li>
              <li class="my-1.5">支持按题型、科目、难度筛选查看</li>
            </ul>
          </template>
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 真题索引/入口页面
 * 功能:展示年份卡片,点击跳转到对应年份的真题页面
 * 遵循KISS原则:简洁的入口页面设计
 */
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, ArrowRight } from '@element-plus/icons-vue'
import { getExamYearStats } from '@/api/exam'
import CustomButton from '@/components/basic/CustomButton.vue'

const router = useRouter()
const route = useRoute()

// 年份列表数据
const yearList = ref([])
const loading = ref(false)

// 当前分类（来自路由查询参数）
const activeCategory = ref(route.query.category || '')

/**
 * 加载真题年份统计数据（可按分类过滤）
 */
const loadYearData = async () => {
  loading.value = true
  try {
    const response = await getExamYearStats({
      category: activeCategory.value || undefined
    })

    if (response.code === 200) {
      yearList.value = (response.data || [])
        .map(item => ({
          year: item.year,
          count: item.count
        }))
        .sort((a, b) => b.year - a.year)
    } else {
      ElMessage.error(response.message || '加载失败')
    }
  } catch (error) {
    ElMessage.error('加载真题数据失败')
    console.error('加载真题数据失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到指定年份的真题页面
 */
const goToYear = (year) => {
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
    activeCategory.value = newCategory || ''
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

