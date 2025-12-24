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

<style lang="scss" scoped>
/**
 * 真题索引页面样式
 * 使用Sass变量和mixins统一管理主题
 */

.exam-index-container {
  min-height: calc(100vh - #{$nav-height});
  padding: $spacing-lg $spacing-md;
  background-color: $color-primary;
  @include flex-center;
}

.index-content {
  width: 100%;
  max-width: $container-width-lg;
}

/* 头部介绍 */
.index-header {
  text-align: center;
  padding: $spacing-lg 0;
  
  .index-title {
    margin: 0 0 $spacing-md 0;
    font-size: $font-size-xxl;
    color: $color-text-primary;
    font-weight: $font-weight-bold;
  }
  
  .index-description {
    margin: 0;
    font-size: $font-size-medium;
    color: $color-text-regular;
    line-height: 1.8;
    max-width: 800px;
    margin: 0 auto;
  }
}

/* 年份卡片网格 */
.year-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: $spacing-md;
  margin: $spacing-lg 0;
}

.year-card {
  padding: $spacing-md;
  background-color: $color-bg-white;
  border-radius: $border-radius-base;
  border: 2px solid $color-border-light;
  cursor: pointer;
  transition: all $transition-base;
  @include flex-column;
  
  &:hover {
    border-color: $color-accent;
    box-shadow: 0 4px 12px rgba(139, 111, 71, 0.15);
    transform: translateY(-4px);
    
    .year-number {
      color: $color-accent;
    }
  }
  
  .year-card-header {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: $spacing-xs - 2px;
    
    .year-number {
      margin: 0;
      font-size: 48px;
      font-weight: $font-weight-bold;
      color: $color-text-primary;
      transition: color $transition-base;
      line-height: 1;
    }
    
    .year-label {
      font-size: $font-size-large;
      color: $color-text-secondary;
    }
  }
  
  .year-card-body {
    flex: 1;
    padding: $spacing-sm 0;
    
    .year-stat {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: $spacing-xs - 2px;
      
      .stat-icon {
        font-size: $font-size-large;
        color: $color-accent;
      }
      
      .stat-text {
        font-size: $font-size-base;
        color: $color-text-regular;
      }
    }
  }
  
  .year-card-footer {
    display: flex;
    justify-content: center;
    padding-top: $spacing-sm;
    
    .button-icon {
      margin-left: $spacing-xs - 4px;
      transition: transform $transition-base;
    }
  }
  
  &:hover .button-icon {
    transform: translateX(4px);
  }
}

/* 底部提示 */
.index-footer {
  margin-top: $spacing-lg;
  
  .footer-tips {
    margin: 0;
    padding-left: $spacing-md;
    color: $color-text-regular;
    line-height: 1.8;
    
    li {
      margin: $spacing-xs - 2px 0;
    }
  }
}

/* 响应式布局 */
@include mobile {
  .exam-index-container {
    padding: $spacing-md $spacing-sm;
  }
  
  .index-header .index-title {
    font-size: $font-size-xl;
  }
  
  .year-cards {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: $spacing-sm;
  }
  
  .year-card .year-card-header .year-number {
    font-size: 36px;
  }
}
</style>

