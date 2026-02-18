<template>
  <div class="mock-index-container">
    <div class="index-content">
      <!-- 头部介绍 -->
      <div class="index-header">
        <h1 class="index-title">408模拟题库</h1>
        <p class="index-description">
          收录各机构408模拟题，包含数据结构、操作系统、计算机网络、计算机组成原理四大科目。
          提供完整题目、详细解答，助力考研模拟练习。
        </p>
      </div>

      <el-divider />

      <!-- 来源卡片列表 -->
      <div v-loading="loading" class="source-cards">
        <div
          v-for="sourceData in sourceList"
          :key="sourceData.source"
          class="source-card"
          @click="goToSource(sourceData.source)"
        >
          <div class="source-card-header">
            <h2 class="source-name">{{ sourceData.source }}</h2>
          </div>
          <el-divider />
          <div class="source-card-body">
            <div class="source-stat">
              <el-icon class="stat-icon"><Document /></el-icon>
              <span class="stat-text">共 {{ sourceData.count }} 题</span>
            </div>
          </div>
          <div class="source-card-footer">
            <CustomButton type="primary" size="small">
              查看题目
              <el-icon class="button-icon"><ArrowRight /></el-icon>
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
      <div class="index-footer">
        <el-alert
          title="使用提示"
          type="info"
          :closable="false"
        >
          <template #default>
            <ul class="footer-tips">
              <li>点击来源卡片查看该机构的所有模拟题</li>
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

.mock-index-container {
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

/* 来源卡片网格 */
.source-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin: 32px 0;
}

.source-card {
  padding: 16px;
  background-color: #fff;
  border-radius: 4px;
  border: 2px solid #dfe2e5;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.source-card:hover {
  border-color: #8B6F47;
  box-shadow: 0 4px 12px rgba(139, 111, 71, 0.15);
  transform: translateY(-4px);
}

.source-card:hover .source-name {
  color: #8B6F47;
}

.source-card .source-card-header {
  display: flex;
  align-items: center;
  justify-content: center;
}

.source-card .source-card-header .source-name {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
  transition: color 0.3s ease;
  text-align: center;
}

.source-card .source-card-body {
  flex: 1;
  padding: 8px 0;
}

.source-card .source-card-body .source-stat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.source-card .source-card-body .source-stat .stat-icon {
  font-size: 18px;
  color: #8B6F47;
}

.source-card .source-card-body .source-stat .stat-text {
  font-size: 14px;
  color: #666;
}

.source-card .source-card-footer {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

.source-card .source-card-footer .button-icon {
  margin-left: 4px;
  transition: transform 0.3s ease;
}

.source-card:hover .button-icon {
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
  .mock-index-container {
    padding: 16px 8px;
  }

  .index-header .index-title {
    font-size: 20px;
  }

  .source-cards {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 8px;
  }

  .source-card .source-card-header .source-name {
    font-size: 18px;
  }
}
</style>
