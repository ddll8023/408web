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

<style lang="scss" scoped>
.mock-index-container {
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

/* 来源卡片网格 */
.source-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: $spacing-md;
  margin: $spacing-lg 0;
}

.source-card {
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
    
    .source-name {
      color: $color-accent;
    }
  }
  
  .source-card-header {
    display: flex;
    align-items: center;
    justify-content: center;
    
    .source-name {
      margin: 0;
      font-size: $font-size-xl;
      font-weight: $font-weight-bold;
      color: $color-text-primary;
      transition: color $transition-base;
      text-align: center;
    }
  }
  
  .source-card-body {
    flex: 1;
    padding: $spacing-sm 0;
    
    .source-stat {
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
  
  .source-card-footer {
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
  .mock-index-container {
    padding: $spacing-md $spacing-sm;
  }
  
  .index-header .index-title {
    font-size: $font-size-xl;
  }
  
  .source-cards {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: $spacing-sm;
  }
  
  .source-card .source-card-header .source-name {
    font-size: $font-size-large;
  }
}
</style>
