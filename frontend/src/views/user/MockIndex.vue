<template>
  <div class="min-h-[calc(100vh-60px)] bg-[#FBF7F2] px-4 py-8 flex items-center justify-center">
    <div class="w-full max-w-[1200px]">
      <!-- 头部介绍 -->
      <div class="text-center py-8">
        <h1 class="m-0 mb-6 text-[#333] font-semibold text-2xl">408模拟题库</h1>
        <p class="m-0 text-[#666] text-base leading-relaxed max-w-[800px] mx-auto">
          收录各机构408模拟题，包含数据结构、操作系统、计算机网络、计算机组成原理四大科目。
          提供完整题目、详细解答，助力考研模拟练习。
        </p>
      </div>

      <el-divider />

      <!-- 来源卡片列表 -->
      <div v-loading="loading" class="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4 my-8">
        <div
          v-for="sourceData in sourceList"
          :key="sourceData.source"
          class="p-4 bg-white rounded border-2 border-[#dfe2e5] cursor-pointer transition-all duration-300 flex flex-col hover:border-[#8B6F47] hover:shadow-[0_4px_12px_rgba(139,111,71,0.15)] hover:-translate-y-1"
          @click="goToSource(sourceData.source)"
        >
          <div class="flex items-center justify-center">
            <h2 class="m-0 font-semibold text-xl text-[#333] text-center transition-colors duration-300">{{ sourceData.source }}</h2>
          </div>
          <el-divider />
          <div class="flex-1 py-2">
            <div class="flex items-center justify-center gap-1.5">
              <el-icon class="text-[#8B6F47]" :size="18"><Document /></el-icon>
              <span class="text-[#666] text-sm">共 {{ sourceData.count }} 题</span>
            </div>
          </div>
          <div class="flex justify-center pt-2">
            <CustomButton type="primary" size="small">
              查看题目
              <el-icon class="ml-1 transition-transform duration-300"><ArrowRight /></el-icon>
            </CustomButton>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty
          v-if="!loading && sourceList.length === 0"
          description="暂无模拟题数据"
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
              <li class="my-1.5">点击来源卡片查看该机构的所有模拟题</li>
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
 * 模拟题索引/入口页面
 * 功能：展示来源机构卡片，点击跳转到对应来源的题目页面
 * 遵循KISS原则：简洁的入口页面设计
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, ArrowRight } from '@element-plus/icons-vue'
import { getMockSourceStats } from '@/api/mock'
import CustomButton from '@/components/basic/CustomButton.vue'

const router = useRouter()

// 来源列表数据
const sourceList = ref([])
const loading = ref(false)

/**
 * 加载来源统计数据
 */
const loadSourceData = async () => {
  loading.value = true
  try {
    const response = await getMockSourceStats()

    if (response.code === 200) {
      sourceList.value = (response.data || [])
        .map(item => ({
          source: item.source,
          count: item.count
        }))
        .sort((a, b) => b.count - a.count)
    } else {
      ElMessage.error(response.message || '加载失败')
    }
  } catch (error) {
    ElMessage.error('加载模拟题数据失败')
    console.error('加载模拟题数据失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 跳转到指定来源的题目页面
 */
const goToSource = (source) => {
  router.push({
    path: `/mock/${encodeURIComponent(source)}`
  })
}

// 组件挂载时加载数据
onMounted(() => {
  loadSourceData()
})
</script>

<style scoped>
/**
 * 模拟题索引页面样式
 * 使用 Tailwind CSS
 */
</style>
