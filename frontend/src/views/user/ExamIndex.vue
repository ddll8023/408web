<template>
  <div class="exam-index-container">
    <div class="index-content">
      <!-- 头部介绍 -->
      <div class="index-header">
        <h1 class="index-title">408考研真题</h1>
        <p class="index-description">
          收录408统考真题,包含数据结构、操作系统、计算机网络、计算机组成原理四大科目。
          提供完整题目和详细解答,助力考研备考。
        </p>
      </div>

      <el-divider />

      <!-- 年份卡片列表 -->
      <div v-loading="loading" class="year-cards">
        <div
          v-for="yearData in yearList"
          :key="yearData.year"
          class="year-card"
          @click="goToYear(yearData.year)"
        >
          <div class="year-card-header">
            <h2 class="year-number">{{ yearData.year }}</h2>
            <span class="year-label">年</span>
          </div>
          <el-divider />
          <div class="year-card-body">
            <div class="year-stat">
              <el-icon class="stat-icon"><Document /></el-icon>
              <span class="stat-text">共 {{ yearData.count }} 题</span>
            </div>
          </div>
          <div class="year-card-footer">
            <CustomButton type="primary" size="small">
              查看真题
              <el-icon class="button-icon"><ArrowRight /></el-icon>
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
      <div class="index-footer">
        <el-alert
          title="使用提示"
          type="info"
          :closable="false"
        >
          <template #default>
            <ul class="footer-tips">
              <li>点击年份卡片查看该年份的所有真题</li>
              <li>每道题目都配有详细解答</li>
              <li>支持按题型、科目、难度筛选查看</li>
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

.exam-index-container {
  min-height: calc(100vh - 60px);
  padding: 32px 16px;
  background-color: #FBF7F2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-content {
  width: 100%;
  max-width: 1200px;
}

/* 头部介绍 */
.index-header {
  text-align: center;
  padding: 32px 0;
}

.index-header .index-title {
  margin: 0 0 24px 0;
  font-size: 28px;
  color: #333;
  font-weight: 600;
}

.index-header .index-description {
  margin: 0;
  font-size: 16px;
  color: #666;
  line-height: 1.8;
  max-width: 800px;
  margin: 0 auto;
}

/* 年份卡片网格 */
.year-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin: 32px 0;
}

.year-card {
  padding: 16px;
  background-color: #fff;
  border-radius: 4px;
  border: 2px solid #dfe2e5;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.year-card:hover {
  border-color: #8B6F47;
  box-shadow: 0 4px 12px rgba(139, 111, 71, 0.15);
  transform: translateY(-4px);
}

.year-card:hover .year-number {
  color: #8B6F47;
}

.year-card .year-card-header {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
}

.year-card .year-card-header .year-number {
  margin: 0;
  font-size: 48px;
  font-weight: 600;
  color: #333;
  transition: color 0.3s ease;
  line-height: 1;
}

.year-card .year-card-header .year-label {
  font-size: 18px;
  color: #666;
}

.year-card .year-card-body {
  flex: 1;
  padding: 8px 0;
}

.year-card .year-card-body .year-stat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.year-card .year-card-body .year-stat .stat-icon {
  font-size: 18px;
  color: #8B6F47;
}

.year-card .year-card-body .year-stat .stat-text {
  font-size: 14px;
  color: #666;
}

.year-card .year-card-footer {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

.year-card .year-card-footer .button-icon {
  margin-left: 4px;
  transition: transform 0.3s ease;
}

.year-card:hover .button-icon {
  transform: translateX(4px);
}

/* 底部提示 */
.index-footer {
  margin-top: 32px;
}

.index-footer .footer-tips {
  margin: 0;
  padding-left: 16px;
  color: #666;
  line-height: 1.8;
}

.index-footer .footer-tips li {
  margin: 6px 0;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .exam-index-container {
    padding: 16px 8px;
  }

  .index-header .index-title {
    font-size: 20px;
  }

  .year-cards {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 8px;
  }

  .year-card .year-card-header .year-number {
    font-size: 36px;
  }
}
</style>

